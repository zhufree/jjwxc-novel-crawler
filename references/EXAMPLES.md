# 调用示例

## 1. 查询小说信息

```json
{ "name": "get_novel_info", "arguments": { "url": "https://www.jjwxc.net/onebook.php?novelid=9091462" } }
```

返回 `title / author / total_chapters / locked_chapters / intro` 等。
如果 `locked_chapters` 不为空，说明有付费章节，下载前需要 token。

---

## 2. 验证 URL 和 token 是否有效（不执行下载）

```json
{
  "name": "download_novel",
  "arguments": {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462",
    "token": "abc123xyz",
    "validate_only": true
  }
}
```

返回 `success=true` 表示 URL 可达、token 字段已接收。`action_needed=null` 表示可以继续下载。

---

## 3. 下载全文 TXT（有 token）

```json
{
  "name": "download_novel",
  "arguments": {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462",
    "token": "abc123xyz",
    "format_type": "txt",
    "output_dir": "/Users/me/novels"
  }
}
```

---

## 4. 下载指定章节范围 EPUB3（繁→简）

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
    "add_cover": true,
    "output_dir": "/Users/me/novels"
  }
}
```

---

## 5. TXT 按章保存（无 token，仅免费章节）

```json
{
  "name": "download_novel",
  "arguments": {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462",
    "token": "",
    "format_type": "txt",
    "save_per_chapter": true,
    "output_dir": "/Users/me/novels"
  }
}
```

**失败处理**：若返回 `action_needed = "provide_token"`，表示有付费章节未下载。
告知用户：`failed` 列表中的章节需要 token，参考 `references/TOKEN.md` 获取方式。

---

## 6. 自定义章节标题格式（custom_title）

```json
{
  "name": "download_novel",
  "arguments": {
    "url": "https://www.jjwxc.net/onebook.php?novelid=9091462",
    "token": "abc123xyz",
    "format_type": "txt",
    "custom_title": "第$1章 $2",
    "custom_vol": "【第$1卷】$2",
    "show_summary": false,
    "output_dir": "/Users/me/novels"
  }
}
```

`custom_title` 变量：`$1`=章节序号，`$2`=标题，`$3`=提要。

---

## 7. 有 token 但收费章节仍失败的处理流程

```
1. download_novel 返回 failed=["0301","0302"], action_needed="provide_token"
2. 告知用户：第301、302章下载失败，token 可能已过期
3. 引导用户重新抓包（加载 references/TOKEN.md）
4. 用户提供新 token 后，用相同参数重试（chapter_start=301, chapter_end=302）
```

---

## 8. 网络错误重试

```
1. download_novel 返回 success=false, action_needed="retry_later"
2. 等待片刻（建议 30 秒）后用相同参数重新调用
3. 若连续失败 3 次，告知用户检查网络或晋江服务器状态
```
