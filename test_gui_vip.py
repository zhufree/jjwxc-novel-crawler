# -*- coding: UTF-8 -*-
"""测试 GUI 中 VIP 章节显示"""
import sys
from PyQt5.QtWidgets import QApplication
from gui.chapter_list_page import ChapterListPage

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 创建章节列表页面
    page = ChapterListPage()
    page.resize(800, 600)
    
    # 设置测试 URL（这个小说有 VIP 章节）
    test_url = "https://www.jjwxc.net/onebook.php?novelid=9091462"
    page.url_edit.setText(test_url)
    
    page.show()
    
    print("=" * 60)
    print("测试说明：")
    print("1. 点击 '解析章节列表' 按钮")
    print("2. 检查表格中第 18-42 章是否显示 💎 图标")
    print("3. 检查标题栏是否显示 'VIP章节: 25'")
    print("=" * 60)
    
    sys.exit(app.exec_())
