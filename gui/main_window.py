# -*- coding: UTF-8 -*-
"""
主窗口
"""
import os
import re
import sys
import yaml
from PyQt5.QtCore import Qt, QThread
from qfluentwidgets import FluentWindow, FluentIcon as FIF, InfoBar, InfoBarPosition
from .basic_page import BasicSettingPage
from .css_page import CssSettingPage
from .chapter_list_page import ChapterListPage
from .download_page import DownloadPage
from .worker import DownloadWorker

def _get_base_dir():
    if getattr(sys, 'frozen', False) and hasattr(sys, 'executable'):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_BASE_DIR = _get_base_dir()
CONFIG_FILE = os.path.join(_BASE_DIR, 'config.yml')


class MainWindow(FluentWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle('晋江小说下载器')
        self.resize(900, 720)
        self.setMinimumSize(760, 580)

        # 创建子页面
        self.basic_page = BasicSettingPage(self)
        self.basic_page.setObjectName('basicPage')

        self.css_page = CssSettingPage(self)
        self.css_page.setObjectName('cssPage')

        self.chapter_list_page = ChapterListPage(self)
        self.chapter_list_page.setObjectName('chapterListPage')

        self.download_page = DownloadPage(self)
        self.download_page.setObjectName('downloadPage')

        # 添加导航
        self.addSubInterface(self.basic_page, FIF.SETTING, '基本设置')
        self.addSubInterface(self.css_page, FIF.EDIT, '自定义CSS')
        self.addSubInterface(self.chapter_list_page, FIF.MENU, '章节列表')
        self.addSubInterface(self.download_page, FIF.DOWNLOAD, '下载')

        # 连接按钮
        self.download_page.save_btn.clicked.connect(self._save_config)
        self.download_page.download_btn.clicked.connect(self._start_download)

    def _save_config(self):
        """保存配置"""
        self.basic_page.save_config()
        # 保存CSS
        css = self.css_page.get_css()
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, encoding='utf-8') as f:
                doc = yaml.load(f.read(), Loader=yaml.FullLoader) or {}
        else:
            doc = {}
        doc['css'] = css
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(doc, f)

        InfoBar.success(
            title='保存成功',
            content='配置已保存',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def _start_download(self):
        """开始下载"""
        if self.download_page._downloading:
            InfoBar.warning(
                title='提示',
                content='正在下载中，请等待...',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            return

        url = self.basic_page.url_edit.text().strip()
        if not re.findall(r'(http|https)://www.jjwxc.net/onebook.php\?novelid=[0-9]+', url):
            InfoBar.error(
                title='网址错误',
                content='网址格式错误！请使用网页版网址',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return

        config = self.basic_page.build_config()
        config.css_text = self.css_page.get_css()

        self.download_page.set_downloading(True)
        self.download_page.log_text.clear()
        self.download_page.progress_bar.setValue(0)
        self.download_page.progress_label.setText('准备中...')

        # 切换到下载页
        self.switchTo(self.download_page)

        # 启动线程
        self._worker = DownloadWorker(url, config)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.log_signal.connect(self.download_page.append_log)
        self._worker.progress_signal.connect(self.download_page.on_progress)
        self._worker.finished_signal.connect(self._on_download_done)
        self._worker.finished_signal.connect(self._thread.quit)

        self._thread.start()

    def _on_download_done(self, success, output_file, error, downloader):
        """下载完成回调"""
        self.download_page.set_downloading(False)

        if success:
            name = output_file
            if downloader and downloader.novel_info:
                info = downloader.novel_info
                name = f"{info.title}-{info.author}"
            self.download_page.progress_bar.setValue(100)
            self.download_page.progress_label.setText('下载完成！')
            InfoBar.success(
                title='下载完成',
                content=name,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self
            )
            if downloader and downloader.fail_info:
                InfoBar.warning(
                    title='部分章节失败',
                    content=f'共 {len(downloader.fail_info)} 章下载失败，请检查 token 是否正确',
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=5000,
                    parent=self
                )
        else:
            self.download_page.progress_label.setText('下载失败')
            InfoBar.error(
                title='下载失败',
                content=error or '未知错误',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self
            )
