# Example 2: Download Full Novel as TXT

## User Input

```
帮我下载这本小说的全文 TXT，token 是 abc123xyz
https://www.jjwxc.net/onebook.php?novelid=9091462
```

## Tool Call

```json
{
  "name": "download_novel",
  "arguments": {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462",
    "token": "abc123xyz",
    "format_type": "txt"
  }
}
```

## Tool Response

```json
{
  "success": true,
  "error": "",
  "output_file": "示例书名-示例作者.9091462.txt",
  "novel_id": "9091462",
  "title": "示例书名",
  "author": "示例作者",
  "total": 320,
  "downloaded": 320,
  "failed": []
}
```

## Assistant Reply

下载完成！

- 文件：`示例书名-示例作者.9091462.txt`
- 共下载 **320 / 320 章**，全部成功。
