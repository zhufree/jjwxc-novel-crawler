# -*- coding: UTF-8 -*-
"""
CSS设置页面
"""
import os
from PyQt5.QtWidgets import QVBoxLayout
from qfluentwidgets import PlainTextEdit, BodyLabel
from .base import SettingPanel, _make_card

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_CSS = '''nav#landmarks {display:none;}
nav#page-list {display:none;}
ol {list-style-type: none;}/*epub3目录格式*/
h1{font-size:1.4em;text-align:center;}/*一级标题*/
h2{font-size:1.24em;text-align:center;}/*二级标题*/
.title{text-align:center;}/*文章名*/
.note{font-size:0.8em;text-align:right;}/*章节信息*/
body{text-indent:2em;}/*全局格式*/'''


class CssSettingPage(SettingPanel):
    """CSS设置页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        css_card = _make_card(self._scroll_widget)
        css_layout = QVBoxLayout(css_card)
        css_layout.setContentsMargins(20, 16, 20, 16)
        css_layout.setSpacing(6)
        css_layout.addWidget(BodyLabel('自定义CSS（仅EPUB格式）'))
        self.css_edit = PlainTextEdit()
        self.css_edit.setPlainText(DEFAULT_CSS)
        self.css_edit.setMinimumHeight(300)
        css_layout.addWidget(self.css_edit)
        self._add_group('CSS设置', css_card)

    def get_css(self):
        """获取CSS文本"""
        return self.css_edit.toPlainText()
