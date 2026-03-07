# -*- coding: UTF-8 -*-
"""
GUI基类和辅助函数
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from qfluentwidgets import ScrollArea, CardWidget, StrongBodyLabel


def _make_group_label(text, parent=None):
    """创建分组标题标签"""
    lbl = StrongBodyLabel(text, parent)
    return lbl


def _make_card(parent=None):
    """创建带圆角阴影的卡片容器"""
    card = CardWidget(parent)
    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    return card


class SettingPanel(ScrollArea):
    """设置面板基类"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('settingPanel')
        self.setWidgetResizable(True)
        self._scroll_widget = QWidget()
        self._layout = QVBoxLayout(self._scroll_widget)
        self._layout.setContentsMargins(36, 20, 36, 36)
        self._layout.setSpacing(16)
        self._layout.setAlignment(Qt.AlignTop)
        self.setWidget(self._scroll_widget)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.enableTransparentBackground()

    def _add_group(self, title, card):
        """往面板追加一个带标题的卡片组"""
        lbl = _make_group_label(title, self._scroll_widget)
        self._layout.addWidget(lbl)
        self._layout.addWidget(card)
