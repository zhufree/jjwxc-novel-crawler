"""Command line interface: python cli.py --help (also python -m cli)."""
import argparse
import json
from pathlib import Path
import sys
from typing import get_args

from models import ConversionState, OutputFormat


def build_parser():
    parser = argparse.ArgumentParser(description='晋江小说下载器（无需启动 GUI）')
    parser.add_argument('--json', action='store_true', help='以 JSON 输出结果')
    commands = parser.add_subparsers(dest='command', required=True)
    info = commands.add_parser('info', help='查询小说信息')
    chapters = commands.add_parser('chapters', help='列出章节、VIP 和锁章状态')
    download = commands.add_parser('download', help='下载 TXT / EPUB2 / EPUB3')
    for command in (info, chapters, download):
        command.add_argument('url', help='包含 novelid 参数的小说网址')
        command.add_argument('--json', action='store_true', default=argparse.SUPPRESS,
                             help='以 JSON 输出结果')
    for command in (chapters, download):
        command.add_argument('--state', choices=get_args(ConversionState), default='',
                             help='s：繁转简；t：简转繁；默认不转换')
    download.add_argument('--token', default='', help='未指定时从 config.yml 或 JJWXC_TOKEN 读取')
    download.add_argument('--format', dest='format_type', choices=get_args(OutputFormat), default='txt')
    download.add_argument('-o', '--output-dir', default='', help='输出目录，默认系统临时目录下 jjwxc_downloads')
    download.add_argument('--threads', dest='thread_num', type=int, default=8, help='下载线程数，默认 8')
    download.add_argument('--start', '--chapter-start', dest='chapter_start', type=int, default=0)
    download.add_argument('--end', '--chapter-end', dest='chapter_end', type=int, default=0)
    download.add_argument('--custom-title', default='', help='$1=章节 ID，$2=标题，$3=提要')
    download.add_argument('--custom-vol', default='', help='$1=卷序号，$2=卷名')
    css = download.add_mutually_exclusive_group()
    css.add_argument('--css-text', default='', help='EPUB 的 CSS 文本')
    css.add_argument('--css-file', type=Path, help='读取 UTF-8 CSS 文件')
    for flag, field, help_text in (
        ('save-per-chapter', 'save_per_chapter', 'TXT 按章保存'),
        ('remove-blank-lines', 'remove_blank_lines', 'TXT 去除段间空行'),
        ('number', 'show_number', '显示章节序号（默认开启）'),
        ('title', 'show_title', '显示章节标题（默认开启）'),
        ('summary', 'show_summary', '显示提要（默认开启）'),
        ('chapter-info', 'show_chinfo', '显示字数和日期'),
        ('remove-thanks', 'del_thanks', '删除作话中的一键感谢'),
        ('cover', 'add_cover', 'EPUB 下载封面（默认开启）'),
        ('html-vol', 'html_vol', 'EPUB2 添加 HTML 目录页'),
        ('web-intro', 'special_intro', '使用网页文案'),
        ('validate-only', 'validate_only', '仅检查公开信息，不下载或验证 Token'),
    ):
        group = download.add_mutually_exclusive_group()
        group.add_argument('--' + flag, dest=field, action='store_true',
                           default=argparse.SUPPRESS, help=help_text)
        group.add_argument('--no-' + flag, dest=field, action='store_false',
                           default=argparse.SUPPRESS, help='关闭：' + help_text)
    return parser


def _print_result(command, result):
    if command == 'info' and result.get('success'):
        print(f"《{result['title']}》 — {result['author']}")
        print(f"小说 ID：{result['novel_id']}；章节数：{result['total_chapters']}")
        print(f"VIP：{len(result['vip_chapters'])}；锁章：{len(result['locked_chapters'])}")
        print(result['intro'])
    elif command == 'chapters' and result.get('success'):
        for chapter in result['chapters']:
            status = (' [VIP]' if chapter['is_vip'] else '') + (' [锁章]' if chapter['locked'] else '')
            print(f"{chapter['index']}\t{chapter['title']}{status}\t{chapter['summary']}")
        for volume in result['volumes']:
            print(f"卷标：{volume['name']}（位置 {volume['place_id']}）")
    elif command == 'download':
        print(f"成功章节：{result.get('downloaded', 0)}/{result.get('total', 0)}")
        if result.get('output_file'):
            print('输出：' + result['output_file'])
        if result.get('failed'):
            print('失败章节：' + ', '.join(result['failed']))
        if result.get('success') and not result.get('output_file'):
            print('公开信息检查通过；未验证 Token。')
    if not result.get('success'):
        print(result.get('error') or '操作失败', file=sys.stderr)


def main(argv=None):
    args = vars(build_parser().parse_args(argv))
    command = args.pop('command')
    as_json = args.pop('json')
    token = args.get('token', '')
    from pydantic import ValidationError
    try:
        # Help and argument parsing work without loading download dependencies.
        from tools import NovelUrl, ListChaptersInput, DownloadInput
        from tools import get_novel_info, list_chapters, download_novel
        if command == 'info':
            result = get_novel_info(NovelUrl(**args))
        elif command == 'chapters':
            result = list_chapters(ListChaptersInput(**args))
        else:
            css_file = args.pop('css_file', None)
            if css_file:
                args['css_text'] = css_file.read_text(encoding='utf-8-sig')
            result = download_novel(
                DownloadInput(**args),
                log_callback=lambda message: print(message, file=sys.stderr),
                progress_callback=lambda pct, current, total: print(
                    f'进度：{current}/{total} ({pct}%)', file=sys.stderr),
            )
        code = 0 if result.get('success') else 1
    except KeyboardInterrupt:
        result, code = {'success': False, 'error': '已中断'}, 130
    except Exception as exc:
        # Validation errors omit input values so tokens are never echoed.
        if isinstance(exc, ValidationError):
            message = '; '.join('.'.join(map(str, e['loc'])) + ': ' + e['msg'] for e in exc.errors())
            code = 2
        else:
            message, code = str(exc), 1
        result = {'success': False, 'error': message}
    if token and result.get('error'):
        result['error'] = result['error'].replace(token, '[token]')
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        _print_result(command, result)
    return code


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main())
