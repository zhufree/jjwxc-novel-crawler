# Example 4: Per-Chapter Save with Partial Failure

## User Input

```
下载这本小说，每章保存为单独文件，不需要 token
https://www.jjwxc.net/onebook.php?novelid=9091462
```

## Tool Call

```json
{
  "name": "download_novel",
  "arguments": {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462",
    "token": "",
    "format_type": "txt",
    "save_per_chapter": true
  }
}
```

## Tool Response

```json
{
  "success": true,
  "error": "",
  "output_file": "示例书名-示例作者.9091462",
  "novel_id": "9091462",
  "title": "示例书名",
  "author": "示例作者",
  "total": 320,
  "downloaded": 317,
  "failed": ["0301", "0302", "0303"]
}
```

## Assistant Reply

下载完成！

- 输出目录：`示例书名-示例作者.9091462/`
- 成功下载 **317 / 320 章**，每章保存为独立文件
- ⚠️ 以下 3 章下载失败（未购买）：第 301、302、303 章

如需获取付费章节，请提供晋江 App token 后重新下载。
