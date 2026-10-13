# 晋江小说下载器
一款用于下载晋江文学城小说的工具，支持 TXT 和 EPUB 格式输出，fork自 [jjwxcNovelCrawler](https://github.com/zhufree/jjwxcNovelCrawler)，添加了自己需要的章节下载功能及重写了GUI，并添加了适用于AI Agent的Skill说明文档。

> ⚠️ **声明**：此项目仅供学习交流使用，严禁用于商业用途，请在24小时之内删除。

---

## ✨ 功能特性

- **多格式输出**：支持 TXT、EPUB2、EPUB3 格式
- **章节范围下载**：可指定下载第 N 章到第 M 章
- **按章保存**：TXT 格式支持每章单独保存为文件
- **去除空行**：可选去除段落间的空行
- **繁简转换**：支持繁体转简体、简体转繁体
- **自定义标题**：支持自定义章节标题和卷标格式（`第$1章 $2`）
- **自定义 CSS**：EPUB 格式支持自定义样式
- **多线程下载**：支持设置线程数，加快下载速度
- **章节列表查看**：可预览小说所有章节，查看 VIP 章节和锁章状态
- **桌面 GUI**：基于 QFluentWidgets 的现代风格界面，模块化设计
- **AI Skill 接口**：可直接作为 OpenClaw 等 AI Agent 的工具使用
- **命令行 CLI**：查询信息、章节和下载，支持 JSON 输出与退出码

---

## 📥 下载安装

### 方式一：直接下载 EXE（推荐）

前往 Releases 下载最新版本的 exe 文件，双击即可运行。

### 方式二：从源码运行

1. **安装 Python 3.8+**

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行桌面 GUI**
   ```bash
   python main.py
   ```

4. **填写配置**（首次运行）
   - 程序启动后在「基础设置」页填入 Token 并保存，配置会写入 `config.yml`
   - 也可直接编辑项目根目录下的 `config.yml`（参考 `config.yml.example`）

---

## 🚀 使用方法

### 命令行（无需启动 GUI）

在项目根目录运行，也可将 `python cli.py` 替换为 `python -m cli`：

```powershell
python cli.py --help
python cli.py info "https://www.jjwxc.net/onebook.php?novelid=9091462"
python cli.py chapters "https://www.jjwxc.net/onebook.php?novelid=9091462" --state s --json
python cli.py download "https://www.jjwxc.net/onebook.php?novelid=9091462" --format epub3 --start 1 --end 50 -o ./downloads
python cli.py download "https://www.jjwxc.net/onebook.php?novelid=9091462" --save-per-chapter --remove-blank-lines --no-summary -o ./downloads
python cli.py download --help
```

Token 沿用现有读取顺序：`--token` → 项目根目录 `config.yml` 的 `token` → `JJWXC_TOKEN` 环境变量。
其他下载选项由命令行参数和默认值决定，不自动继承 GUI 配置。未指定 `-o` 时使用系统临时目录下的 `jjwxc_downloads`。

支持 `--threads`、`--state`、`--custom-title`、`--custom-vol`、`--css-text` / `--css-file`，
以及 `--number`、`--title`、`--summary`、`--chapter-info`、`--cover`、`--remove-thanks`、`--html-vol`、`--web-intro` 等开关。
布尔开关均可用对应的 `--no-*` 关闭；默认显示序号、标题、提要并下载 EPUB 封面。
PowerShell 中包含 `$1` 等占位符的模板请使用单引号，例如 `--custom-title '第$1章 $2'`。
`--validate-only` 只检查小说公开信息，不验证 Token 或付费章节权限。

`--json` 可放在子命令前或后；stdout 只输出 JSON 结果，日志和进度写入 stderr。
退出码：`0` 全部成功，`1` 运行失败或部分章节失败，`2` 参数错误，`130` 用户中断。
参数解析错误写入 stderr；模型校验错误在 `--json` 模式下输出 JSON。
部分下载的可用内容保留在返回的 `output_file`，合并文件带 `.partial` 后缀。

### 1. 获取 Token

Token 是登录晋江 App 后的身份凭证，用于下载收费章节。**免费章节无需 Token。**

#### 抓包步骤（Android）
1. 手机安装晋江 App 并登录账号
2. 安装抓包工具，推荐 **HttpCanary**（免费）或 **Charles**
3. 开启抓包，在晋江 App 中随意点开一章正文
4. 在抓包记录中找到请求域名含 `jjwxc.net` 的条目
5. 查看请求 URL 的 Query 参数，找到 `token=xxxxxxxx` 字段
6. 复制 token 值（通常为数字+字母组成的长字符串）

#### 保存 Token
- **GUI 用户**：在「基础设置」页的 Token 输入框中填入，点击「保存配置」即可持久化到 `config.yml`
- **命令行 / AI 调用**：在 `config.yml` 中手动填写 `token:` 字段，或在调用时直接作为参数传入

> ⚠️ Token 有效期有限，若下载收费章节失败，请重新抓包更新 Token。

### 2. 查看章节列表（可选）

在下载前，可以先查看小说的章节详情：

1. 切换到"章节列表"页面
2. 粘贴小说网址
3. 点击"解析章节列表"
4. 查看所有章节的标题、提要、VIP 状态和锁章状态
   - 💎 表示 VIP 章节（需购买）
   - 🔒 表示锁章（被作者锁定，不可阅读）

### 3. 下载小说

1. 切换到"基本设置"页面，粘贴小说网址（格式：`https://www.jjwxc.net/onebook.php?novelid=xxx`）
2. 填入 Token（下载 VIP 章节必需）
3. 选择输出格式和其他选项
4. 切换到"下载"页面，点击"开始下载"

### 4. 选项说明

| 选项 | 说明 |
|------|------|
| **章节范围** | 填 0 或留空表示不限制 |
| **按章保存文件** | 仅 TXT 格式可用，每章保存为单独文件 |
| **去除段间空行** | 仅 TXT 格式可用，去除段落之间的空行 |
| **显示序号/标题/提要** | 控制章节标题显示内容 |
| **章节信息** | 显示字数和发布日期 |
| **下载封面** | 下载并嵌入封面图片 |
| **去除感谢** | 去除作话中的一键感谢内容 |
| **繁简转换** | 繁体↔简体转换 |

---

## 📁 项目结构

下载时每个任务使用独立目录，按章保存的文件名会包含章节 ID，避免同名覆盖。
部分章节失败时返回失败状态并保留可用内容，合并文件带 `.partial` 后缀；全部失败时不会覆盖已有成品。
默认下载线程数为 8。`validate_only` 仅检查小说公开信息，不验证 Token。

离线回归检查：`python -m unittest test_download`（不会访问晋江接口）。

```
jjwxcNovelCrawler/
├── main.py              # 桌面版 GUI 启动入口（QFluentWidgets）
├── cli.py               # 命令行入口（info / chapters / download）
├── downloader.py        # 下载器核心逻辑
├── models.py            # 数据模型
├── chapter.py           # 章节内容处理
├── output.py            # 文件输出处理
├── api.py               # API 调用
├── utils.py             # 工具函数
├── DESCBC.py            # 解密模块
├── EPUB2.py             # EPUB2 生成
├── EPUB3.py             # EPUB3 生成
├── config.yml           # 配置文件（自动生成）
├── requirements.txt     # 依赖列表
│
├── gui/                 # GUI 模块（模块化组织）
│   ├── __init__.py      # 模块入口
│   ├── base.py          # 基类和辅助函数
│   ├── worker.py        # 下载线程
│   ├── css_page.py      # CSS 设置页面
│   ├── chapter_list_page.py  # 章节列表展示页面
│   └── README.md        # GUI 模块说明
│
├── tools/               # AI Agent / LLM 工具接口
│   ├── tools.py         # 工具函数（Pydantic 输入模型 + 英文 docstring）
│   ├── get_novel_info.json   # OpenAI JSON Schema
│   ├── list_chapters.json
│   └── download_novel.json
│
├── references/          # AI 工具文档
│   ├── INSTRUCTIONS.md  # AI 行为指令
│   ├── QUICKREF.md      # 参数速查
│   ├── EXAMPLES.md      # 调用示例
│   └── TOKEN.md         # Token 获取指南
│
├── SKILL.md             # AI Skill 元数据（YAML frontmatter）
└── README-AI.md         # AI Agent 集成指南
```

> AI Agent 使用者请直接查阅 [README-AI.md](README-AI.md)。

---

## ❓ 常见问题

**Q: 如何启动 GUI 程序？**
- 从项目根目录运行 `python main.py`
- 不要直接运行 `gui/` 目录下的文件，它们是模块，需要从 `main.py` 启动

**Q: 下载失败怎么办？**
- 检查 Token 是否正确、是否过期
- 检查网址格式是否正确
- 确认已购买 VIP 章节
- 在"章节列表"页面查看哪些章节是 VIP（💎）或锁章（🔒）

**Q: 出现 `231101` 或 `2016` 错误，提示"浏览器标识异常"或"请更新至最新版本"？**
- **原因**：系统时间不准确，与真实时间相差过大
- **解决**：同步系统时间到正确时区
  - Docker/容器：`ntpdate pool.ntp.org` 或 `timedatectl set-ntp true`
  - Linux 服务器：`timedatectl set-timezone Asia/Shanghai && ntpdate ntp.aliyun.com`
  - 验证时间：`python -c "import time; print(time.asctime())"`
- **说明**：晋江 API 使用时间戳验证请求，时间不准确会被拒绝

**Q: 如何查看小说有哪些 VIP 章节？**
- 切换到"章节列表"页面
- 输入小说网址并点击"解析章节列表"
- 表格中会显示每章的 VIP 状态（💎）和锁章状态（🔒）

**Q: 如何自定义章节标题格式？**
- 在"基本设置"页面勾选"自定义标题"
- 使用占位符：`$1`=章节序号，`$2`=标题，`$3`=提要
- 例如：`第$1章 $2` 会生成 "第1章 入学测试"

**Q: 如何打包成 EXE？**
```bash
pyinstaller --onefile --windowed main.py
```

**Q: config.yml 在哪里？**
- 首次运行 GUI 并保存配置后自动生成，位于项目根目录
- 可参考 `config.yml.example` 手动创建，`token` 字段填入抓包获取的值
