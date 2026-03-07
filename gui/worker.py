# -*- coding: UTF-8 -*-
"""
下载线程模块
"""
from PyQt5.QtCore import QObject, pyqtSignal
from downloader import NovelDownloader


class DownloadWorker(QObject):
    """下载工作线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int, int)
    finished_signal = pyqtSignal(bool, str, str, object)  # success, output, error, downloader

    def __init__(self, url, config):
        super().__init__()
        self.url = url
        self.config = config

    def run(self):
        downloader = NovelDownloader(
            config=self.config,
            log_callback=self.log_signal.emit,
            progress_callback=lambda p, c, t: self.progress_signal.emit(p, c, t)
        )
        try:
            success, output_file, error = downloader.download_novel(self.url)
            self.finished_signal.emit(success, output_file or '', error or '', downloader)
        except Exception as e:
            self.finished_signal.emit(False, '', str(e), None)
