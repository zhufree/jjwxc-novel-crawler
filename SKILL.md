---
name: 晋江小说下载器
slug: jjwxc-novel-downloader
version: 2.0.0
author: zhufree
description: 从晋江文学城（jjwxc.net）下载小说，支持 TXT / EPUB2 / EPUB3 输出、繁简转换、章节范围筛选、按章保存。无需 token 可查询信息，下载收费章节需要 token。
---

从晋江文学城下载小说为本地文件。先查询确认，再下载。

## When to use

- "帮我下载这本小说"
- "下载晋江小说 epub / txt"
- "查一下这本小说的章节列表"
- "把这本小说下载成 epub3"
- "只下载第 50 到 100 章"

## Tools

| 工具 | 说明 | 需要 token |
|------|------|-----------|
| `get_novel_info` | 查询书名、作者、章节数、简介 | 否 |
| `list_chapters` | 获取完整章节列表（含收费标记） | 否 |
| `download_novel` | 下载为 TXT / EPUB2 / EPUB3 | 收费章节需要 |

```python
from tools import get_tools, call_tool
tools = get_tools()                          # OpenAI function-calling schema
result = call_tool("get_novel_info", {"url": "https://www.jjwxc.net/onebook.php?novelid=<id>"})
```

## Commands

- **下载小说**："帮我下载 https://www.jjwxc.net/onebook.php?novelid=xxx"
- **查看章节**："列出这本小说的章节：<url>"
- **指定格式/范围**："下载第 1-50 章，epub3 格式，token 是 xxx"

## References（按需加载）

- `references/INSTRUCTIONS.md` — 完整行为规则与 token 读取逻辑
- `references/TOKEN.md` — token 抓包方法（用户问如何获取 token 时加载）
- `references/QUICKREF.md` — 所有参数速查与错误处理
- `references/EXAMPLES.md` — 完整调用示例
