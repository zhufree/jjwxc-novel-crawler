# 晋江小说下载器 — AI Agent 使用指南

专为 AI Agent / LLM 工具调用场景编写。普通用户请查阅 [README.md](README.md)。

## 快速集成

```python
from tools import get_tools, call_tool

# OpenAI / Anthropic function-calling
tools = get_tools()   # 直接传入 tools= 参数

# 通用调用分发器（AutoGen / LangChain / CrewAI 等）
result = call_tool("get_novel_info", {"url": "https://www.jjwxc.net/onebook.php?novelid=9091462"})
```

## 工具一览

| 工具 | 输入模型 | 需要 token | JSON Schema |
|------|----------|-----------|-------------|
| `get_novel_info` | `NovelUrl` | 否 | `tools/get_novel_info.json` |
| `list_chapters` | `ListChaptersInput` | 否 | `tools/list_chapters.json` |
| `download_novel` | `DownloadInput` | 收费章节需要 | `tools/download_novel.json` |

## 推荐调用顺序

```
1. get_novel_info(url)          → 确认书名、作者、章节数
2. list_chapters(url)           → 可选：查看章节列表、判断收费情况
3. download_novel(url, ...)     → 执行下载
```

## Token 获取与存储

### Token 是什么

Token 是晋江 App 的登录身份凭证，用于下载**收费（付费）章节**。查询小说信息、章节列表、下载免费章节均**无需 token**。

### 如何获取 Token

1. 手机安装晋江 App 并登录账号
2. 安装抓包工具：推荐 **HttpCanary**（Android 免费）或 **Charles**（桌面端）
3. 开启抓包，在晋江 App 中随意点开一章正文
4. 在抓包记录中找到域名含 `jjwxc.net` 的请求
5. 查看请求 URL 的 Query 参数，找到 `token=xxxxxxxx` 字段
6. 复制 token 值（通常为数字+字母组成的长字符串）

> ⚠️ Token 有效期有限，若下载收费章节时 `failed` 列表不为空，可能需要重新抓包更新。

### Token 本地存储方案

项目使用 `config.yml` 持久化所有配置，包括 token。

**方式一：直接写入 config.yml（推荐）**

```yaml
# config.yml（位于项目根目录）
token: "your_token_here"
format: txt
state: ''
# 其他字段见 config.yml.example
```

**方式二：AI Agent 在调用前读取 config.yml**

```python
import yaml, os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.yml")

def load_token() -> str:
    if not os.path.exists(CONFIG_FILE):
        return ""
    with open(CONFIG_FILE, encoding="utf-8") as f:
        conf = yaml.safe_load(f) or {}
    return conf.get("token", "")

# 调用时自动注入
from tools import call_tool
result = call_tool("download_novel", {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462",
    "token": load_token(),
    "format_type": "txt",
})
```

**方式三：环境变量（适合 CI / 服务器部署）**

```python
import os
token = os.environ.get("JJWXC_TOKEN", "")
```

> 在 OpenClaw 等平台配置 skill 时，可将 token 存入平台的 Secret / Environment Variable，在 `instructions.md` 中指示 AI 从环境变量读取，避免明文写入对话。

---

## 关键参数说明

### format_type
- `"txt"` — 纯文本，默认合并为单个 `.txt` 文件
- `"epub2"` — EPUB 2，兼容性最广
- `"epub3"` — EPUB 3，现代阅读器首选

### token
从晋江 App 网络请求中抓取（Charles / mitmproxy）。免费章节不需要 token；收费章节不提供 token 时，`failed` 列表会包含这些章节 ID。

### chapter_start / chapter_end
1-indexed。`chapter_start=10, chapter_end=50` 表示下载第 10～50 章（含）。两者均为 `0` 表示下载全部。

### state（繁简转换）
`""` 不转换 | `"s"` 繁→简 | `"t"` 简→繁

### custom_title / custom_vol（标题模板）
- `custom_title`：`$1`=章节ID，`$2`=标题，`$3`=提要，例如 `"$2"`
- `custom_vol`：`$1`=卷序号，`$2`=卷名，例如 `"第$1卷 $2"`

## 返回值说明

### download_novel 返回值

```python
{
    "success": bool,          # 是否成功
    "error": str,             # 错误信息（成功时为空字符串）
    "output_file": str,       # 输出文件路径或目录路径
    "novel_id": str,
    "title": str,
    "author": str,
    "total": int,             # 目标章节总数
    "downloaded": int,        # 实际成功下载数
    "failed": list[str],      # 失败的章节 ID 列表
}
```

`failed` 不为空时，通常原因：
- 章节为付费内容，token 未提供或已过期
- 网络超时（重新下载同一范围可恢复）

## 常见错误

| 错误信息 | 原因 | 处理建议 |
|----------|------|----------|
| `Invalid URL: must contain novelid=<digits>` | URL 格式错误 | 确认 URL 含 `novelid=` 参数 |
| `Unsupported format '...'` | format_type 不合法 | 只用 `txt` / `epub2` / `epub3` |
| `success=False` + API error message | 小说不存在或已下架 | 告知用户停止 |
| `failed` 列表不为空 | 章节未购买 或 token 过期 | 提示用户重新抓包更新 `config.yml` 中的 token |

## 完整调用示例

```python
from tools import get_tools, call_tool

# 1. 查询信息
info = call_tool("get_novel_info", {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462"
})
print(info["title"], info["total_chapters"])

# 2. 下载全文 TXT
result = call_tool("download_novel", {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462",
    "token": "YOUR_TOKEN",
    "format_type": "txt",
    "state": "s",
    "del_thanks": True,
})
print(result["output_file"], f'{result["downloaded"]}/{result["total"]}')

# 3. 下载指定范围 EPUB3
result = call_tool("download_novel", {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462",
    "token": "YOUR_TOKEN",
    "format_type": "epub3",
    "chapter_start": 1,
    "chapter_end": 100,
    "add_cover": True,
    "custom_vol": "第$1卷 $2",
})
```

## 依赖安装

```bash
# 核心功能（含 AI tool）
pip install -r requirements.txt

# 若需运行 GUI
pip install PyQt5 pyqt-fluent-widgets
```

## 参考文档

| 文件 | 说明 | 何时加载 |
|------|------|----------|
| [`references/INSTRUCTIONS.md`](references/INSTRUCTIONS.md) | 完整行为规则与 token 读取逻辑 | 每次启动时 |
| [`references/TOKEN.md`](references/TOKEN.md) | token 抓包获取与存储方法 | 用户询问 token 时 |
| [`references/QUICKREF.md`](references/QUICKREF.md) | 所有参数速查与错误处理 | 需要查参数时 |
| [`references/EXAMPLES.md`](references/EXAMPLES.md) | 完整调用示例 | 需要示例时 |
