# -*- coding: UTF-8 -*-
"""
下载页面
"""
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    PushButton, PrimaryPushButton, ProgressBar, PlainTextEdit,
    BodyLabel, FluentIcon as FIF
)
from .base import SettingPanel, _make_card


class DownloadPage(SettingPanel):
    """下载页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._worker = None
        self._downloading = False
        self._init_ui()

    def _init_ui(self):
        # 进度卡片
        prog_card = _make_card(self._scroll_widget)
        prog_layout = QVBoxLayout(prog_card)
        prog_layout.setContentsMargins(20, 16, 20, 16)
        prog_layout.setSpacing(12)

        self.progress_label = BodyLabel('等待开始...')
        prog_layout.addWidget(self.progress_label)

        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        prog_layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self.save_btn = PushButton(FIF.SAVE, '保存配置')
        self.download_btn = PrimaryPushButton(FIF.DOWNLOAD, '开始下载')
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.download_btn)
        btn_row.addStretch(1)
        prog_layout.addLayout(btn_row)

        self._add_group('下载进度', prog_card)

        # 日志卡片
        log_card = _make_card(self._scroll_widget)
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 16, 20, 16)
        log_layout.setSpacing(8)

        log_btn_row = QHBoxLayout()
        log_btn_row.addStretch(1)
        self.clear_log_btn = PushButton(FIF.DELETE, '清空日志')
        self.clear_log_btn.clicked.connect(self._clear_log)
        log_btn_row.addWidget(self.clear_log_btn)
        log_layout.addLayout(log_btn_row)

        self.log_text = PlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(340)
        log_layout.addWidget(self.log_text)

        self._add_group('下载日志', log_card)

    def _clear_log(self):
        self.log_text.clear()

    def append_log(self, msg):
        self.log_text.appendPlainText(msg)
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_progress(self, pct, current, total):
        self.progress_bar.setValue(pct)
        self.progress_label.setText(f'{current}/{total} ({pct}%)')

    def set_downloading(self, downloading):
        self._downloading = downloading
        self.download_btn.setEnabled(not downloading)
        self.download_btn.setText('下载中...' if downloading else '开始下载')
