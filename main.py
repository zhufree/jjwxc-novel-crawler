# -*- coding: UTF-8 -*-
"""
晋江小说下载器 - Fluent Design GUI (PyQt-Fluent-Widgets)
"""
import os
import re
import sys
import threading
import yaml

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSizePolicy, QFrame, QScrollArea, QFileDialog
)

from qfluentwidgets import (
    FluentWindow, FluentIcon as FIF,
    ScrollArea, LineEdit, ComboBox, CheckBox,
    PushButton, PrimaryPushButton, ProgressBar, PlainTextEdit,
    SpinBox, InfoBar, InfoBarPosition, setTheme, Theme,
    CardWidget, BodyLabel, StrongBodyLabel, CaptionLabel,
)

from models import DownloadConfig
from downloader import NovelDownloader

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(_BASE_DIR, 'config.yml')

DEFAULT_CSS = '''nav#landmarks {display:none;}
nav#page-list {display:none;}
ol {list-style-type: none;}/*epub3目录格式*/
h1{font-size:1.4em;text-align:center;}/*一级标题*/
h2{font-size:1.24em;text-align:center;}/*二级标题*/
.title{text-align:center;}/*文章名*/
.note{font-size:0.8em;text-align:right;}/*章节信息*/
body{text-indent:2em;}/*全局格式*/'''

STATE_MAP = {'不转换': '', '繁→简': 's', '简→繁': 't'}
STATE_MAP_REV = {v: k for k, v in STATE_MAP.items()}


# ================================================================
# 下载线程
# ================================================================
class DownloadWorker(QObject):
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


# ================================================================
# 辅助函数：创建分组标题标签
# ================================================================
def _make_group_label(text, parent=None):
    lbl = StrongBodyLabel(text, parent)
    return lbl


def _make_card(parent=None):
    """创建带圆角阴影的卡片容器"""
    card = CardWidget(parent)
    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    return card


# ================================================================
# 设置面板基类
# ================================================================
class SettingPanel(ScrollArea):
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


# ================================================================
# 基本设置页
# ================================================================
class BasicSettingPage(SettingPanel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        # ---- 下载地址 ----
        url_card = _make_card(self._scroll_widget)
        url_card_layout = QVBoxLayout(url_card)
        url_card_layout.setContentsMargins(20, 16, 20, 16)
        url_card_layout.setSpacing(6)
        url_card_layout.addWidget(BodyLabel('小说网址'))
        self.url_edit = LineEdit()
        self.url_edit.setPlaceholderText('https://www.jjwxc.net/onebook.php?novelid=xxx')
        self.url_edit.setClearButtonEnabled(True)
        url_card_layout.addWidget(self.url_edit)
        self._add_group('下载地址', url_card)

        # ---- Token ----
        token_card = _make_card(self._scroll_widget)
        token_layout = QVBoxLayout(token_card)
        token_layout.setContentsMargins(20, 16, 20, 16)
        token_layout.setSpacing(6)
        token_layout.addWidget(BodyLabel('Token（从晋江 App 抓包获取）'))
        self.token_edit = LineEdit()
        self.token_edit.setPlaceholderText('从晋江App抓包获取token')
        self.token_edit.setClearButtonEnabled(True)
        token_layout.addWidget(self.token_edit)
        self._add_group('认证信息', token_card)

        # ---- 格式与转换 ----
        fmt_card = _make_card(self._scroll_widget)
        fmt_outer = QVBoxLayout(fmt_card)
        fmt_outer.setContentsMargins(20, 16, 20, 16)
        fmt_outer.setSpacing(10)

        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(32)

        fmt_left = QVBoxLayout()
        fmt_left.setSpacing(4)
        fmt_left.addWidget(BodyLabel('输出格式'))
        self.fmt_combo = ComboBox()
        self.fmt_combo.addItems(['txt', 'epub2', 'epub3'])
        self.fmt_combo.setFixedWidth(130)
        self.fmt_combo.currentTextChanged.connect(self._on_format_changed)
        fmt_left.addWidget(self.fmt_combo)

        fmt_mid = QVBoxLayout()
        fmt_mid.setSpacing(4)
        fmt_mid.addWidget(BodyLabel('繁简转换'))
        self.state_combo = ComboBox()
        self.state_combo.addItems(['不转换', '繁→简', '简→繁'])
        self.state_combo.setFixedWidth(130)
        fmt_mid.addWidget(self.state_combo)

        fmt_right = QVBoxLayout()
        fmt_right.setSpacing(4)
        fmt_right.addWidget(BodyLabel('下载线程数'))
        self.thread_spin = SpinBox()
        self.thread_spin.setRange(1, 999)
        self.thread_spin.setValue(100)
        self.thread_spin.setFixedWidth(110)
        fmt_right.addWidget(self.thread_spin)

        fmt_row.addLayout(fmt_left)
        fmt_row.addLayout(fmt_mid)
        fmt_row.addLayout(fmt_right)
        fmt_row.addStretch(1)
        fmt_outer.addLayout(fmt_row)
        self._add_group('格式设置', fmt_card)

        # ---- 章节范围 ----
        range_card = _make_card(self._scroll_widget)
        range_outer = QVBoxLayout(range_card)
        range_outer.setContentsMargins(20, 16, 20, 16)
        range_outer.setSpacing(12)

        range_row = QHBoxLayout()
        range_row.setSpacing(8)
        range_row.addWidget(BodyLabel('从第'))
        self.ch_start_spin = SpinBox()
        self.ch_start_spin.setRange(0, 99999)
        self.ch_start_spin.setValue(0)
        self.ch_start_spin.setFixedWidth(150)
        range_row.addWidget(self.ch_start_spin)
        range_row.addWidget(BodyLabel('章  到第'))
        self.ch_end_spin = SpinBox()
        self.ch_end_spin.setRange(0, 99999)
        self.ch_end_spin.setValue(0)
        self.ch_end_spin.setFixedWidth(150)
        range_row.addWidget(self.ch_end_spin)
        range_row.addWidget(BodyLabel('章'))
        range_row.addStretch(1)

        chk_row = QHBoxLayout()
        chk_row.setSpacing(24)
        self.chk_save_per_ch = CheckBox('按章保存文件（仅txt）')
        self.chk_rm_blank = CheckBox('去除段间空行（仅txt）')
        chk_row.addWidget(self.chk_save_per_ch)
        chk_row.addWidget(self.chk_rm_blank)
        chk_row.addStretch(1)

        range_outer.addLayout(range_row)
        range_outer.addLayout(chk_row)
        self._add_group('章节范围（填 0 表示不限制）', range_card)

        # ---- 内容选项 ----
        opts_card = _make_card(self._scroll_widget)
        opts_layout = QVBoxLayout(opts_card)
        opts_layout.setContentsMargins(20, 16, 20, 16)
        opts_layout.setSpacing(12)

        row1 = QHBoxLayout()
        row1.setSpacing(24)
        self.chk_number = CheckBox('显示序号')
        self.chk_title_show = CheckBox('显示标题')
        self.chk_summary = CheckBox('显示提要')
        self.chk_chinfo = CheckBox('章节信息')
        for w in [self.chk_number, self.chk_title_show, self.chk_summary, self.chk_chinfo]:
            row1.addWidget(w)
        row1.addStretch(1)

        row2 = QHBoxLayout()
        row2.setSpacing(24)
        self.chk_cover = CheckBox('下载封面')
        self.chk_delthk = CheckBox('去除感谢')
        self.chk_special = CheckBox('网页文案')
        self.chk_htmlvol = CheckBox('HTML卷标')
        for w in [self.chk_cover, self.chk_delthk, self.chk_special, self.chk_htmlvol]:
            row2.addWidget(w)
        row2.addStretch(1)

        row3 = QHBoxLayout()
        row3.setSpacing(12)
        self.chk_selftitle = CheckBox('自定义标题')
        self.titlefmt_edit = LineEdit()
        self.titlefmt_edit.setPlaceholderText('$1序号  $2标题  $3提要')
        self.titlefmt_edit.setClearButtonEnabled(True)
        row3.addWidget(self.chk_selftitle)
        row3.addWidget(self.titlefmt_edit, 1)
        row3.addWidget(CaptionLabel('$1序号  $2标题  $3提要'))

        row4 = QHBoxLayout()
        row4.setSpacing(12)
        self.chk_selfvol = CheckBox('自定义卷标')
        self.volfmt_edit = LineEdit()
        self.volfmt_edit.setPlaceholderText('$1卷号  $2卷名')
        self.volfmt_edit.setClearButtonEnabled(True)
        row4.addWidget(self.chk_selfvol)
        row4.addWidget(self.volfmt_edit, 1)
        row4.addWidget(CaptionLabel('$1卷号  $2卷名'))

        opts_layout.addLayout(row1)
        opts_layout.addLayout(row2)
        opts_layout.addLayout(row3)
        opts_layout.addLayout(row4)
        self._add_group('标题与内容选项', opts_card)

        # ---- 输出目录 ----
        outdir_card = _make_card(self._scroll_widget)
        outdir_layout = QVBoxLayout(outdir_card)
        outdir_layout.setContentsMargins(20, 16, 20, 16)
        outdir_layout.setSpacing(6)
        outdir_layout.addWidget(BodyLabel('输出目录（下载文件保存位置）'))
        outdir_row = QHBoxLayout()
        outdir_row.setSpacing(8)
        self.outdir_edit = LineEdit()
        self.outdir_edit.setPlaceholderText('留空则保存到程序所在目录')
        self.outdir_edit.setClearButtonEnabled(True)
        self.outdir_browse_btn = PushButton(FIF.FOLDER, '浏览')
        self.outdir_browse_btn.setFixedWidth(90)
        self.outdir_browse_btn.clicked.connect(self._browse_outdir)
        outdir_row.addWidget(self.outdir_edit, 1)
        outdir_row.addWidget(self.outdir_browse_btn)
        outdir_layout.addLayout(outdir_row)
        self._add_group('输出目录', outdir_card)

        # 初始化格式相关状态
        self._on_format_changed(self.fmt_combo.currentText())

    def _browse_outdir(self):
        d = QFileDialog.getExistingDirectory(self, '选择输出目录', self.outdir_edit.text() or _BASE_DIR)
        if d:
            self.outdir_edit.setText(d)

    def _on_format_changed(self, fmt):
        is_txt = fmt == 'txt'
        self.chk_save_per_ch.setEnabled(is_txt)
        self.chk_rm_blank.setEnabled(is_txt)
        if not is_txt:
            self.chk_save_per_ch.setChecked(False)
            self.chk_rm_blank.setChecked(False)

    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        with open(CONFIG_FILE, encoding='utf-8') as f:
            conf = yaml.load(f.read(), Loader=yaml.FullLoader) or {}

        self.token_edit.setText(conf.get('token', ''))
        self.thread_spin.setValue(conf.get('ThreadPoolMaxNum', 100))

        fmt = conf.get('format', 'txt')
        idx = self.fmt_combo.findText(fmt)
        if idx >= 0:
            self.fmt_combo.setCurrentIndex(idx)

        state_label = STATE_MAP_REV.get(conf.get('state', ''), '不转换')
        idx = self.state_combo.findText(state_label)
        if idx >= 0:
            self.state_combo.setCurrentIndex(idx)

        ti = conf.get('titleInfo', '1 1 1').split(' ')
        while len(ti) < 3:
            ti.append('1')
        self.chk_number.setChecked(ti[0] != '0')
        self.chk_title_show.setChecked(ti[1] != '0')
        self.chk_summary.setChecked(ti[2] != '0')

        self.chk_chinfo.setChecked(bool(conf.get('chinfo', 0)))
        self.chk_cover.setChecked(bool(conf.get('cover', '')))
        self.chk_delthk.setChecked(bool(conf.get('delthk', 0)))
        self.chk_special.setChecked(bool(conf.get('special', 0)))
        self.chk_htmlvol.setChecked(bool(conf.get('htmlvol', 0)))

        if conf.get('selftitle') and isinstance(conf['selftitle'], str):
            self.chk_selftitle.setChecked(True)
            self.titlefmt_edit.setText(conf['selftitle'])
        if conf.get('volumn') and isinstance(conf['volumn'], str):
            self.chk_selfvol.setChecked(True)
            self.volfmt_edit.setText(conf['volumn'])
        self.outdir_edit.setText(conf.get('output_dir', ''))

    def save_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, encoding='utf-8') as f:
                doc = yaml.load(f.read(), Loader=yaml.FullLoader) or {}
        else:
            doc = {}

        doc['token'] = self.token_edit.text()
        doc['state'] = STATE_MAP.get(self.state_combo.currentText(), '')
        doc['format'] = self.fmt_combo.currentText()
        doc['ThreadPoolMaxNum'] = self.thread_spin.value()

        ti = ('1' if self.chk_number.isChecked() else '0') + ' ' + \
             ('1' if self.chk_title_show.isChecked() else '0') + ' ' + \
             ('1' if self.chk_summary.isChecked() else '0')
        doc['titleInfo'] = ti

        doc['chinfo'] = 1 if self.chk_chinfo.isChecked() else 0
        doc['cover'] = 'e' if self.chk_cover.isChecked() else ''
        doc['delthk'] = 1 if self.chk_delthk.isChecked() else 0
        doc['special'] = 1 if self.chk_special.isChecked() else 0
        doc['htmlvol'] = 1 if self.chk_htmlvol.isChecked() else 0
        doc['selftitle'] = self.titlefmt_edit.text() if self.chk_selftitle.isChecked() else 0
        doc['volumn'] = self.volfmt_edit.text() if self.chk_selfvol.isChecked() else 0
        doc['output_dir'] = self.outdir_edit.text().strip()

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(doc, f)

    def build_config(self):
        config = DownloadConfig()
        config.token = self.token_edit.text().strip()
        config.format_type = self.fmt_combo.currentText()
        config.state = STATE_MAP.get(self.state_combo.currentText(), '')
        config.thread_num = self.thread_spin.value()
        config.show_number = self.chk_number.isChecked()
        config.show_title = self.chk_title_show.isChecked()
        config.show_summary = self.chk_summary.isChecked()
        config.show_chinfo = self.chk_chinfo.isChecked()
        config.del_thanks = self.chk_delthk.isChecked()
        config.add_cover = self.chk_cover.isChecked()
        config.html_vol = self.chk_htmlvol.isChecked()
        config.special_intro = self.chk_special.isChecked()
        config.chapter_start = self.ch_start_spin.value()
        config.chapter_end = self.ch_end_spin.value()
        config.save_per_chapter = self.chk_save_per_ch.isChecked()
        config.remove_blank_lines = self.chk_rm_blank.isChecked()
        if self.chk_selftitle.isChecked():
            config.custom_title = self.titlefmt_edit.text()
        if self.chk_selfvol.isChecked():
            config.custom_vol = self.volfmt_edit.text()
        out = self.outdir_edit.text().strip()
        config.output_dir = out if out else _BASE_DIR
        return config


# ================================================================
# CSS 设置页
# ================================================================
class CssSettingPage(SettingPanel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        css_card = _make_card(self._scroll_widget)
        css_layout = QVBoxLayout(css_card)
        css_layout.setContentsMargins(20, 16, 20, 16)
        css_layout.setSpacing(10)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.reset_css_btn = PushButton(FIF.SYNC, '恢复默认')
        self.reset_css_btn.clicked.connect(self._reset_css)
        btn_row.addWidget(self.reset_css_btn)
        css_layout.addLayout(btn_row)

        self.css_edit = PlainTextEdit()
        self.css_edit.setPlaceholderText('输入自定义CSS样式...')
        self.css_edit.setMinimumHeight(320)
        css_layout.addWidget(self.css_edit)

        self._add_group('自定义 CSS（仅 EPUB 格式有效）', css_card)

    def _reset_css(self):
        self.css_edit.setPlainText(DEFAULT_CSS)

    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self.css_edit.setPlainText(DEFAULT_CSS)
            return
        with open(CONFIG_FILE, encoding='utf-8') as f:
            conf = yaml.load(f.read(), Loader=yaml.FullLoader) or {}
        css = conf.get('css', DEFAULT_CSS)
        self.css_edit.setPlainText(css or DEFAULT_CSS)

    def save_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, encoding='utf-8') as f:
                doc = yaml.load(f.read(), Loader=yaml.FullLoader) or {}
        else:
            doc = {}
        doc['css'] = self.css_edit.toPlainText()
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(doc, f)

    def get_css(self):
        return self.css_edit.toPlainText()


# ================================================================
# 下载页
# ================================================================
class DownloadPage(SettingPanel):
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


# ================================================================
# 主窗口
# ================================================================
class MainWindow(FluentWindow):
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

        self.download_page = DownloadPage(self)
        self.download_page.setObjectName('downloadPage')

        # 添加导航
        self.addSubInterface(self.basic_page, FIF.SETTING, '基本设置')
        self.addSubInterface(self.css_page, FIF.EDIT, '自定义CSS')
        self.addSubInterface(self.download_page, FIF.DOWNLOAD, '下载')

        # 连接按钮
        self.download_page.save_btn.clicked.connect(self._save_config)
        self.download_page.download_btn.clicked.connect(self._start_download)

    # ================================================================
    # 配置
    # ================================================================
    def _save_config(self):
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

    # ================================================================
    # 下载
    # ================================================================
    def _start_download(self):
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


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    setTheme(Theme.AUTO)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
