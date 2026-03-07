# Example 3: Download Chapter Range as EPUB3

## User Input

```
我只想要第 50 到 100 章，输出成 epub3，繁转简，token 是 abc123xyz
https://www.jjwxc.net/onebook.php?novelid=9091462
```

## Tool Call

```json
{
  "name": "download_novel",
  "arguments": {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462",
    "token": "abc123xyz",
    "format_type": "epub3",
    "chapter_start": 50,
    "chapter_end": 100,
    "state": "s",
    "add_cover": true
  }
}
```

## Tool Response

```json
{
  "success": true,
  "error": "",
  "output_file": "示例书名-示例作者.9091462.epub",
  "novel_id": "9091462",
  "title": "示例书名",
  "author": "示例作者",
  "total": 51,
  "downloaded": 51,
  "failed": []
}
```

## Assistant Reply

下载完成！

- 文件：`示例书名-示例作者.9091462.epub`
- 章节范围：第 50～100 章，共 **51 章**
- 格式：EPUB3，繁→简转换，含封面
