"""Small offline checks for command routing, output and exit status."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
import unittest
from unittest.mock import patch

import cli


URL = 'https://www.jjwxc.net/onebook.php?novelid=1'


class CliTests(unittest.TestCase):
    def run_cli(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_query_commands_produce_clean_json(self):
        for command, function in [('info', 'get_novel_info'), ('chapters', 'list_chapters')]:
            with self.subTest(command=command), patch('tools.' + function, return_value={'success': True, 'title': '學習'}):
                code, stdout, stderr = self.run_cli(['--json', command, URL])
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(stdout)['title'], '學習')
                self.assertEqual(stderr, '')

    def test_download_options_progress_and_partial_exit(self):
        def download(inp, **callbacks):
            self.assertEqual((inp.format_type, inp.chapter_start, inp.chapter_end), ('epub3', 2, 4))
            self.assertFalse(inp.add_cover)
            self.assertFalse(inp.show_summary)
            self.assertEqual(inp.css_text, 'body {}')
            callbacks['progress_callback'](100, 3, 3)
            return {'success': False, 'downloaded': 2, 'total': 3, 'failed': ['3'],
                    'output_file': 'book.partial.epub', 'error': 'partial'}
        with patch('tools.download_novel', side_effect=download):
            code, stdout, stderr = self.run_cli(['download', URL, '--json', '--format', 'epub3',
                '--start', '2', '--end', '4', '--no-cover', '--no-summary', '--css-text', 'body {}'])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)['downloaded'], 2)
        self.assertIn('100%', stderr)

    def test_invalid_range_stops_before_network_and_does_not_echo_token(self):
        with patch('api.fetch_novel_info') as fetch:
            code, stdout, _ = self.run_cli(['download', URL, '--json', '--start', '5', '--end', '2', '--token', 'PRIVATE'])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(stdout)['success'])
        self.assertNotIn('PRIVATE', stdout)
        fetch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
