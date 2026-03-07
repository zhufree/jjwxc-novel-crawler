# -*- coding: UTF-8 -*-
"""
章节列表展示页面
"""
import re
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from qfluentwidgets import (
    PushButton, LineEdit, BodyLabel, InfoBar, InfoBarPosition,
    FluentIcon as FIF
)
from .base import SettingPanel, _make_card
import api
import chapter as chapter_mod
from models import DownloadConfig


class ChapterListPage(SettingPanel):
    """章节列表展示页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.chapter_data = None
        self.locked_ids = []
        self.vip_ids = []

    def _init_ui(self):
        # ---- URL 输入 ----
        url_card = _make_card(self._scroll_widget)
        url_layout = QVBoxLayout(url_card)
        url_layout.setContentsMargins(20, 16, 20, 16)
        url_layout.setSpacing(8)
        
        url_layout.addWidget(BodyLabel('小说网址'))
        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        self.url_edit = LineEdit()
        self.url_edit.setPlaceholderText('https://www.jjwxc.net/onebook.php?novelid=xxx')
        self.url_edit.setClearButtonEnabled(True)
        url_row.addWidget(self.url_edit, 1)
        
        self.parse_btn = PushButton(FIF.SEARCH, '解析章节列表')
        self.parse_btn.clicked.connect(self._parse_chapters)
        url_row.addWidget(self.parse_btn)
        
        url_layout.addLayout(url_row)
        self._add_group('章节列表查询', url_card)

        # ---- 章节列表表格 ----
        table_card = _make_card(self._scroll_widget)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(20, 16, 20, 16)
        table_layout.setSpacing(8)
        
        self.info_label = BodyLabel('请输入小说网址并点击"解析章节列表"')
        table_layout.addWidget(self.info_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['序号', '标题', '提要', 'VIP', '锁章'])
        # 隐藏默认行号，避免与序号列重复
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        table_layout.addWidget(self.table)
        
        self._add_group('章节详情', table_card)

    def _parse_chapters(self):
        """解析章节列表"""
        url = self.url_edit.text().strip()
        if not url:
            InfoBar.warning(
                title='提示',
                content='请输入小说网址',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self.window()
            )
            return

        m = re.search(r'novelid=(\d+)', url)
        if not m:
            InfoBar.error(
                title='网址错误',
                content='网址格式错误！请使用网页版网址',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self.window()
            )
            return

        novel_id = m.group(1)
        self.parse_btn.setEnabled(False)
        self.info_label.setText('正在解析章节列表...')
        
        try:
            # 获取小说信息和章节列表
            apicont, cdic, _ = api.fetch_novel_info(novel_id)
            
            if "message" in apicont and "novelIntro" not in apicont:
                InfoBar.error(
                    title='获取失败',
                    content=apicont.get("message", "获取小说信息失败"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self.window()
                )
                self.info_label.setText('获取失败，请检查网址是否正确')
                return

            # 解析章节
            config = DownloadConfig()
            self.chapter_data, self.locked_ids, self.vip_ids = chapter_mod.parse_chapters(cdic, novel_id, config)
            
            # 显示信息
            title = apicont.get("novelName", "")
            author = apicont.get("authorName", "")
            total = len(self.chapter_data.href_list)
            vip_count = len(self.vip_ids)
            locked_count = len(self.locked_ids)
            
            info_text = f'《{title}》 - {author} | 共 {total} 章'
            if vip_count > 0:
                info_text += f' | VIP章节: {vip_count}'
            if locked_count > 0:
                info_text += f' | 锁章: {locked_count}'
            self.info_label.setText(info_text)
            
            # 填充表格
            self._fill_table()
            
            InfoBar.success(
                title='解析成功',
                content=f'成功解析 {total} 个章节',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self.window()
            )
            
        except Exception as e:
            InfoBar.error(
                title='解析失败',
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self.window()
            )
            self.info_label.setText(f'解析失败: {str(e)}')
        finally:
            self.parse_btn.setEnabled(True)

    def _fill_table(self):
        """填充章节列表表格"""
        if not self.chapter_data:
            return
        
        self.table.setRowCount(len(self.chapter_data.href_list))
        
        for idx, (url, title, summary) in enumerate(zip(
            self.chapter_data.href_list,
            self.chapter_data.titleindex,
            self.chapter_data.summary_list
        )):
            # 提取 chapterId
            m = re.search(r'chapterId=(\d+)', url)
            chap_id = m.group(1) if m else ""
            
            # 序号
            self.table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            
            # 标题
            self.table.setItem(idx, 1, QTableWidgetItem(title))
            
            # 提要
            self.table.setItem(idx, 2, QTableWidgetItem(summary))
            
            # VIP（vip_ids 和 chap_id 都是字符串）
            is_vip = chap_id in self.vip_ids
            vip_item = QTableWidgetItem('💎' if is_vip else '')
            vip_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 3, vip_item)
            
            # 锁章（locked_ids 和 chap_id 都是字符串）
            is_locked = chap_id in self.locked_ids
            locked_item = QTableWidgetItem('🔒' if is_locked else '')
            locked_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(idx, 4, locked_item)

    def set_url(self, url):
        """设置URL并自动解析"""
        self.url_edit.setText(url)
        self._parse_chapters()
