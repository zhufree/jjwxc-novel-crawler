# Example 1: Query Novel Info

## User Input

```
帮我查一下这本小说的信息：https://www.jjwxc.net/onebook.php?novelid=9091462
```

## Tool Call

```json
{
  "name": "get_novel_info",
  "arguments": {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462"
  }
}
```

## Tool Response

```json
{
  "success": true,
  "error": "",
  "novel_id": "9091462",
  "title": "示例书名",
  "author": "示例作者",
  "author_id": "123456",
  "cover_url": "https://...",
  "total_chapters": 320,
  "novel_class": "现代言情",
  "novel_style": "轻松",
  "novel_tags": "甜文,HE,现代",
  "novel_size": "1200000",
  "protagonist": "女主A，男主B",
  "costar": "配角C",
  "intro_short": "一句话简介",
  "intro": "这是完整文案...",
  "locked_chapters": ["301", "302", "303"]
}
```

## Assistant Reply

《示例书名》，作者：示例作者
- 类型：现代言情 | 字数：约120万字
- 共 **320 章**，其中 3 章为付费章节（第301、302、303章）
- 简介：这是完整文案...

需要下载吗？请告诉我需要 TXT 还是 EPUB 格式。
