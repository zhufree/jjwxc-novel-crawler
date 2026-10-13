"""Offline regressions for downloads and generated files (no live API calls)."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import requests

from lxml import etree

import chapter
import api
from downloader import NovelDownloader
from models import DownloadConfig
from tools.tools import DownloadInput, ListChaptersInput, list_chapters
from pydantic import ValidationError
import utils


URL = 'https://www.jjwxc.net/onebook.php?novelid=1'
META = {'novelName': 'AuditBook', 'authorName': 'Author', 'novelIntro': 'intro'}
CHAPTERS = [
    {'chaptertype': '0', 'chapterid': str(i), 'chaptername': f'chapter{i}',
     'chapterintro': '', 'islock': '0'} for i in range(1, 4)
]
RAW = {'content': 'body', 'sayBody': '', 'upDown': '', 'message': '',
       'chapterSize': '4', 'chapterDate': ''}


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.config = DownloadConfig()
        self.config.output_dir = self.temp.name
        self.config.thread_num = 2
        self.config.add_cover = False
        info = patch('api.fetch_novel_info', return_value=(META, CHAPTERS, None))
        info.start()
        self.addCleanup(info.stop)

    def test_request_exceptions_are_reported_without_overwriting_existing_book(self):
        existing = Path(self.temp.name) / 'AuditBook-Author.1.txt'
        existing.write_text('previous download', encoding='utf-8')
        dl = NovelDownloader(self.config)
        with patch('api.fetch_chapter_content', side_effect=RuntimeError('offline')):
            success, _, error = dl.download_novel(URL)
        self.assertFalse(success)
        self.assertTrue(error)
        self.assertEqual(dl.fail_info, ['1', '2', '3'])
        self.assertEqual(dl.percent, 0)
        self.assertEqual(existing.read_text(encoding='utf-8'), 'previous download')

    def test_range_download_does_not_include_previous_per_chapter_files(self):
        with patch('api.fetch_chapter_content', return_value=RAW):
            self.config.save_per_chapter = True
            _, first_dir, _ = NovelDownloader(self.config).download_novel(URL)
            self.config.save_per_chapter = False
            self.config.chapter_start = self.config.chapter_end = 2
            success, filename, _ = NovelDownloader(self.config).download_novel(URL)
        text = Path(filename).read_text(encoding='utf-8')
        self.assertTrue(success)
        self.assertNotIn('chapter1', text)
        self.assertNotIn('chapter3', text)
        self.assertEqual(text.count('chapter2'), 1)
        self.assertEqual(len(list(Path(first_dir).glob('*.txt'))), 4)

    def test_partial_download_counts_successes_and_preserves_complete_book(self):
        existing = Path(self.temp.name) / 'AuditBook-Author.1.txt'
        existing.write_text('complete book', encoding='utf-8')
        def fetch(url, token):
            if url.endswith('=1'):
                return RAW
            return dict(RAW, content='', message='not purchased')
        progress = []
        dl = NovelDownloader(self.config, progress_callback=lambda p, c, t: progress.append(p))
        with patch('api.fetch_chapter_content', side_effect=fetch):
            success, filename, _ = dl.download_novel(URL)
        self.assertFalse(success)
        self.assertEqual(dl.percent, 1)
        self.assertEqual(dl.fail_info, ['2', '3'])
        self.assertEqual(progress[-1], 100)
        self.assertIn('.partial.txt', filename)
        self.assertIn('body', Path(filename).read_text(encoding='utf-8'))
        self.assertEqual(existing.read_text(encoding='utf-8'), 'complete book')

    def test_duplicate_titles_keep_all_chapter_bodies(self):
        self.config.save_per_chapter = True
        self.config.custom_title = 'same'
        with patch('api.fetch_chapter_content', side_effect=lambda url, token: dict(
                RAW, content='body' + url.rsplit('=', 1)[-1])):
            success, folder, _ = NovelDownloader(self.config).download_novel(URL)
        bodies = [p.read_text(encoding='utf-8') for p in Path(folder).glob('*.txt')]
        self.assertTrue(success)
        for i in range(1, 4):
            self.assertEqual(sum(f'body{i}' in body for body in bodies), 1)

    def test_epub_resources_and_reading_order_from_another_output_directory(self):
        cwd = os.getcwd()
        for fmt in ('epub2', 'epub3'):
            with self.subTest(format=fmt):
                self.config.format_type = fmt
                with patch('api.fetch_chapter_content', return_value=RAW):
                    success, filename, _ = NovelDownloader(self.config).download_novel(URL)
                self.assertTrue(success)
                self.assertEqual(os.getcwd(), cwd)
                with zipfile.ZipFile(filename) as book:
                    opf = etree.fromstring(book.read('OEBPS/content.opf'))
                    ns = {'o': 'http://www.idpf.org/2007/opf'}
                    items = {item.get('id'): item.get('href') for item in
                             opf.xpath('//o:manifest/o:item', namespaces=ns)}
                    for href in items.values():
                        self.assertIn('OEBPS/' + href, book.namelist())
                    order = [items[item.get('idref')] for item in
                             opf.xpath('//o:spine/o:itemref', namespaces=ns)]
                    self.assertEqual([p for p in order if p.startswith('z')],
                                     ['z0001.xhtml', 'z0002.xhtml', 'z0003.xhtml'])

    def test_failed_chapter_is_complete_xml(self):
        self.config.format_type = 'epub3'
        body, failed = chapter.format_content(
            'title', dict(RAW, content='', message='not purchased & locked'), self.config, 1)
        self.assertTrue(failed)
        etree.fromstring(('<html><body>' + body).encode())

    def test_api_error_is_not_retried_and_temporary_failure_recovers(self):
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"message":"invalid token"}'
        with patch('api.requests.get', return_value=response) as get:
            result = api.fetch_chapter_content('https://example.test/chapter', 'invalid')
        self.assertEqual(result['message'], 'invalid token')
        self.assertEqual(get.call_count, 1)
        response = requests.Response()
        response.status_code = 200
        response._content = b'ok'
        with patch('api.requests.get', side_effect=[requests.Timeout(), response]), patch('api.time.sleep'):
            with api._get('https://example.test') as recovered:
                self.assertEqual(recovered.content, b'ok')

    def test_invalid_options_are_rejected_before_any_api_request(self):
        for options in ({'state': 'unknown'}, {'format_type': 'pdf'}, {'thread_num': 0},
                        {'chapter_start': 3, 'chapter_end': 1}):
            with self.subTest(options=options), patch('api.fetch_novel_info') as fetch:
                for name, value in options.items():
                    setattr(self.config, name, value)
                self.assertFalse(NovelDownloader(self.config).download_novel(URL)[0])
                with self.assertRaises(ValidationError):
                    DownloadInput(url=URL, validate_only=True, **options)
                fetch.assert_not_called()
                self.config = DownloadConfig()

    def test_indexed_titles_and_chapter_list_conversion(self):
        rows = [dict(CHAPTERS[0], chaptername='學習', chapterintro='閱讀')]
        data, _, _ = chapter.parse_chapters(rows, '1', self.config)
        data.href_list = tuple(data.href_list)
        self.config.custom_title = '$1'
        self.assertEqual(chapter.build_content_title(data.href_list[0], data, self.config, idx=0), '1 學習')
        with patch('api.fetch_novel_info', return_value=(META, rows, None)):
            result = list_chapters(ListChaptersInput(url=URL, state='s'))
        self.assertEqual(result['chapters'][0]['title'], '学习')
        self.assertEqual(result['chapters'][0]['summary'], '阅读')

    def test_repeated_conversion_loads_each_dictionary_once(self):
        utils._get_converter.cache_clear()
        self.addCleanup(utils._get_converter.cache_clear)
        with patch('utils.OpenCC', wraps=utils.OpenCC) as constructor:
            self.assertEqual(utils.convert_text('學習', 's'), '学习')
            self.assertEqual(utils.convert_text('閱讀', 's'), '阅读')
            self.assertEqual(utils.convert_text('学习', 't'), '學習')
            self.assertEqual(constructor.call_count, 2)


if __name__ == '__main__':
    unittest.main()
