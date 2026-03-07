# GUI 模块说明

本目录包含晋江小说下载器的图形界面组件，采用模块化设计。

## 📂 模块结构

```
gui/
├── __init__.py              # 模块入口，导出公共接口 (24 行)
├── base.py                  # 基类和辅助函数 (41 行)
├── worker.py                # 下载工作线程 (30 行)
├── basic_page.py            # 基本设置页面 (310 行)
├── css_page.py              # CSS 设置页面 (42 行)
├── chapter_list_page.py     # 章节列表展示页面 (207 行)
├── download_page.py         # 下载页面 (83 行)
├── main_window.py           # 主窗口 (164 行)
└── README.md                # 本文档

main.py                      # 启动入口 (30 行) - 从 700+ 行简化！
```

**模块化成果**：
- 原 `main.py`：700+ 行
- 新 `main.py`：**30 行**（仅启动代码）
- GUI 逻辑：完全模块化到 `gui/` 目录

## 🚀 启动方式

**从项目根目录运行：**

```bash
python main.py
```

`main.py` 是 GUI 的启动入口，它会导入 `gui/` 模块中的组件并组装成完整的应用程序。

## 📦 模块说明

### `base.py` - 基类和辅助函数

提供 GUI 页面的基础组件：

- **`SettingPanel`**：设置面板基类，所有页面都继承自此类
- **`_make_card()`**：创建带圆角阴影的卡片容器
- **`_make_group_label()`**：创建分组标题标签

### `worker.py` - 下载工作线程

- **`DownloadWorker`**：QObject 子类，在独立线程中执行下载任务
- 通过信号与主线程通信，避免阻塞 GUI
- 发出日志、进度和完成信号

### `css_page.py` - CSS 设置页面

- 提供 EPUB 格式的自定义 CSS 编辑功能
- 包含默认 CSS 模板
- 仅对 EPUB2/EPUB3 格式生效

### `chapter_list_page.py` - 章节列表展示页面

**功能特性：**
- 输入小说网址，解析并展示所有章节
- 表格显示章节详情：
  - 序号
  - 标题
  - 内容提要
  - VIP 标识（💎 表示需购买）
  - 锁章标识（🔒 表示被作者锁定）
- 顶部显示小说信息：书名、作者、总章节数、VIP 章节数、锁章数

**使用方法：**
1. 在"章节列表"页面输入小说网址
2. 点击"解析章节列表"按钮
3. 等待解析完成，查看章节详情

## 🔧 开发说明

### 添加新页面

1. 在 `gui/` 目录下创建新的页面文件，如 `new_page.py`
2. 继承 `SettingPanel` 基类：
   ```python
   from .base import SettingPanel, _make_card
   
   class NewPage(SettingPanel):
       def __init__(self, parent=None):
           super().__init__(parent)
           self._init_ui()
       
       def _init_ui(self):
           # 使用 _make_card() 创建卡片
           # 使用 self._add_group() 添加分组
           pass
   ```
3. 在 `gui/__init__.py` 中导出新页面
4. 在 `main.py` 中导入并添加到主窗口

### 注意事项

- **不要直接运行 `gui/` 目录下的文件**，它们是模块，需要从 `main.py` 启动
- 所有页面都应继承 `SettingPanel` 以保持一致的样式
- 使用 `_make_card()` 和 `_add_group()` 保持 UI 风格统一
- 长时间操作应使用 `QThread` 避免阻塞 GUI

## 📚 相关文档

- 主文档：[../README.md](../README.md)
- AI 工具文档：[../references/](../references/)
- 工具接口：[../tools/](../tools/)
