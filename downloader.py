# -*- coding: UTF-8 -*-
"""
下载编排器模块
组合api、chapter、output模块，编排完整的下载流程
"""
import os
import re
import tempfile
import concurrent.futures

import api
import chapter
import output
import utils
from models import DownloadConfig, NovelInfo


class NovelDownloader:
    """小说下载编排器"""

    def __init__(self, config=None, progress_callback=None, log_callback=None):
        """
        :param config: DownloadConfig 配置对象
        :param progress_callback: 进度回调 (percent, current, total)
        :param log_callback: 日志回调 (message)
        """
        self.config = config or DownloadConfig()
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.reset()

    def reset(self):
        """重置状态"""
        self.percent = 0
        self.fail_info = []
        self.current_title = ''
        self.novel_info = None
        self.chapter_data = None

    def _log(self, message):
        if self.log_callback:
            self.log_callback(message)

    def _update_progress(self, current, total):
        if self.progress_callback:
            pct = int(100 * current / total) if total > 0 else 0
            self.progress_callback(pct, current, total)

    def _download_and_save_chapter(self, chapter_url, idx):
        """下载并保存单个章节"""
        title = chapter.build_content_title(chapter_url, self.chapter_data, self.config, idx=idx)
        try:
            raw = api.fetch_chapter_content(chapter_url, self.config.token)
        except Exception as exc:
            message = str(exc)
            if self.config.token:
                message = message.replace(self.config.token, '[token]')
            raw = {'content': '', 'sayBody': '', 'upDown': '', 'message': message}
        content, failed = chapter.format_content(
            title, raw, self.config, self.chapter_data.fill_num
        )
        output.save_chapter_file(chapter_url, title, content, self.config, self._output_dir)
        return title, failed

    def download_novel(self, url, threadnum=None):
        """
        下载小说主流程
        :param url: 小说网址
        :param threadnum: 线程数（None则使用config中的值）
        :return: (success, output_file, error_message)
        """
        self.reset()
        threadnum = self.config.thread_num if threadnum is None else threadnum
        try:
            self.config.validate(thread_num=threadnum)
        except ValueError as exc:
            return False, None, str(exc)

        # 解析小说ID
        m = re.search(r'novelid=(\d+)', url)
        if not m:
            return False, None, "Invalid URL: must contain novelid=<digits>"
        nid = m.group(1)

        # 获取小说信息
        self._log("正在获取小说信息...")
        apicont, cdic, ress = api.fetch_novel_info(nid, include_web=self.config.special_intro)

        if "message" in apicont and "novelIntro" not in apicont:
            return False, None, apicont.get("message", "获取小说信息失败")

        # 构建小说信息
        info = NovelInfo()
        info.novel_id = nid
        info.title = apicont["novelName"]
        info.author = apicont["authorName"]
        info.author_id = apicont.get("authorId", "")
        info.cover_url = apicont.get("novelCover", "")
        info.apicont = apicont
        info.ress = ress
        self.novel_info = info

        ti = info.title + '-' + info.author
        ti = utils.convert_text(ti, self.config.state)
        self._log(f"网址：{url}\n小说信息：{ti}")

        # 解析章节列表
        self.chapter_data, loc, vip = chapter.parse_chapters(cdic, nid, self.config)
        info.locked_chapters = loc
        info.vip_chapters = vip
        total_chapters = len(self.chapter_data.href_list)
        info.chapter_count = total_chapters

        self._log(f"总章节数：{total_chapters}")
        if loc:
            self._log(f"被锁章节：{' '.join(loc)}")

        # 按章节范围筛选
        ch_start = self.config.chapter_start
        ch_end = self.config.chapter_end
        if ch_start > 0 or ch_end > 0:
            start_idx = max(0, ch_start - 1) if ch_start > 0 else 0
            end_idx = min(ch_end, total_chapters) if ch_end > 0 else total_chapters
            self.chapter_data.href_list = self.chapter_data.href_list[start_idx:end_idx]
            self.chapter_data.titleindex = self.chapter_data.titleindex[start_idx:end_idx]
            self.chapter_data.summary_list = self.chapter_data.summary_list[start_idx:end_idx]
            self._log(f"选定范围：第{start_idx+1}章 ~ 第{end_idx}章")

        section_ct = len(self.chapter_data.href_list)
        self._log(f"待下载章节数：{section_ct}")
        if not section_ct:
            return False, None, '选定范围内没有章节'

        if ch_start > 0 or ch_end > 0:
            first = int(re.search(r'chapterId=(\d+)', self.chapter_data.href_list[0]).group(1))
            last = int(re.search(r'chapterId=(\d+)', self.chapter_data.href_list[-1]).group(1))
            volumes = list(zip(self.chapter_data.roll_sign, self.chapter_data.roll_sign_place))
            preceding = [idx for idx, (_, place) in enumerate(volumes) if int(place) <= first]
            start_vol = preceding[-1] if preceding else 0
            selected = [(name, place) for name, place in volumes[start_vol:] if int(place) <= last]
            self.chapter_data.roll_sign = [name for name, _ in selected]
            self.chapter_data.roll_sign_place = [place for _, place in selected]

        # 准备输出目录
        ti = utils.sanitize_filename(ti) + '.' + nid
        cfg_out = getattr(self.config, 'output_dir', '')
        if cfg_out:
            base_path = os.path.abspath(cfg_out)
        else:
            base_path = os.path.join(tempfile.gettempdir(), 'jjwxc_downloads')
        os.makedirs(base_path, exist_ok=True)

        output_dir = tempfile.mkdtemp(prefix=ti + '-', dir=base_path)
        self._output_dir = output_dir

        # 保存卷标
        output.save_volume_files(self.chapter_data, self.config, output_dir)

        # 构建目录
        chapter.build_index(self.chapter_data, loc, self.config)

        # 保存封面
        if self.config.add_cover and self.config.format_type != "txt":
            cover_data = api.download_cover(info.cover_url)
            if not output.save_cover(cover_data, output_dir):
                self._log("【封面下载失败或为默认封面】")

        # 保存信息页
        output.save_info_page(info, loc, self.config, output_dir, url)

        # 多线程下载章节
        self._log("开始下载章节...")
        save_failed = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=threadnum) as executor:
            futures = {
                executor.submit(self._download_and_save_chapter, u, idx): u
                for idx, u in enumerate(self.chapter_data.href_list)
            }
            for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
                try:
                    self.current_title, failed = future.result()
                except Exception as exc:
                    failed = True
                    save_failed = True
                    self._log(f'章节保存失败：{exc}')
                if failed:
                    chap_id = re.search(r'chapterId=(\d+)', futures[future]).group(1)
                    self.fail_info.append(chap_id.zfill(self.chapter_data.fill_num))
                else:
                    self.percent += 1
                self._update_progress(completed, section_ct)

        self._log(f'\n下载完成，总进度：{self.percent}/{section_ct}')

        # 显示失败章节
        if self.fail_info:
            self.fail_info.sort()
            self._log(f"\n未购买或加载失败章节：\n{'|'.join(self.fail_info)}")
        if save_failed or self.percent == 0:
            self._log(f'本次章节文件保留在：{output_dir}')
            return False, output_dir, '下载失败，未覆盖已有成品文件'

        # 生成最终文件（全部使用绝对路径，不依赖 cwd）
        output_name = ti + ('.partial' if self.fail_info else '')
        if self.config.format_type == "txt":
            if self.config.save_per_chapter:
                output.rename_chapter_files(output_dir, self.chapter_data, self.config)
                output_file = output_dir
                self._log(f"\ntxt按章保存完成，目录：{output_dir}")
            else:
                output_file = os.path.join(base_path, output_name + ".txt")
                output.merge_txt_files(output_dir, output_file)
                self._log("\ntxt文件整合完成")
        else:
            output_file = os.path.join(base_path, output_name + ".epub")
            output.create_epub(
                output_file, info.author, info.title, output_dir,
                self.chapter_data.index, self.chapter_data.roll_sign,
                base_path, self.config
            )
            self._log("\nepub打包完成")

        if self.fail_info:
            return False, output_file, f'部分下载完成，{len(self.fail_info)} 章失败；文件：{output_file}'
        return True, output_file, None
