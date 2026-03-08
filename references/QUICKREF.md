# 参数速查 & 错误处理

## 核心参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `url` | str | 必填 | `https://www.jjwxc.net/onebook.php?novelid=<id>` |
| `token` | str | `""` | 晋江 App token，收费章节必填 |
| `format_type` | str | `"txt"` | `txt` / `epub2` / `epub3` |
| `state` | str | `""` | `""` 不转换 \| `"s"` 繁→简 \| `"t"` 简→繁 |
| `chapter_start` | int | `0` | 起始章序号（1-indexed，0=不限） |
| `chapter_end` | int | `0` | 结束章序号（0=不限） |

## TXT 专属

| 参数 | 默认 | 说明 |
|------|------|------|
| `save_per_chapter` | `False` | 每章保存为独立文件 |
| `remove_blank_lines` | `False` | 删除段落间空行 |

## EPUB 专属

| 参数 | 默认 | 说明 |
|------|------|------|
| `add_cover` | `True` | 下载并嵌入封面 |
| `html_vol` | `False` | 卷标作为独立 HTML 页（仅 epub2） |
| `css_text` | `""` | 自定义 CSS 字符串 |

## 标题模板

### custom_title（章节标题格式）
- `$1`：章节 ID（chapterId，如 1, 2, 3...）
- `$2`：章节标题文本
- `$3`：章节内容提要
- 示例：`"第$1章 $2"` → `"第1章 入学测试"`

### custom_vol（卷标格式）
- `$1`：卷号（1, 2, 3...）
- `$2`：卷名
- 示例：`"第$1卷 $2"` → `"第1卷 学院篇"`

## 章节状态

- **locked_chapters**：被作者锁定的章节（不可阅读），通常是作者主动隐藏的内容
- **vip_chapters**：VIP 章节（需要购买），需要用户在晋江账号中购买后才能下载

## 常见错误

| 错误 | 原因 | 处理 |
|------|------|------|
| `Invalid URL: must contain novelid=<digits>` | URL 格式错误 | 要求用户提供正确 URL |
| `Unsupported format '...'` | format_type 非法 | 提示用 `txt`/`epub2`/`epub3` |
| `success=False` + API message | 小说不存在或已下架 | 告知用户停止 |
| `failed` 列表不为空 | 章节未购买或 token 过期 | 加载 `references/TOKEN.md` 告知用户 |
| `231101:获取内容失败...请更新至最新版本` | **系统时区不正确** | 同步系统时间到正确时区（见下方说明） |
| `2016:浏览器标识异常` | User-Agent 时间戳验证失败 | 检查系统时间是否准确 |

## ⚠️ 重要：系统时区要求

**问题症状**：
- 错误代码：`231101` 或 `2016`
- 错误信息：`获取内容失败！为了进一步提升App安全性...请您更新至最新版本` 或 `浏览器标识异常`
- Token 已确认正确，但仍无法下载 VIP 章节

**根本原因**：
晋江 API 使用 `User-Agent: Mobile <时间戳>` 进行请求验证。如果运行环境的系统时间与真实时间相差过大（通常超过几分钟），服务器会拒绝请求。

**解决方法**：

1. **Docker/容器环境**：
   ```bash
   # 同步网络时间
   ntpdate pool.ntp.org
   # 或启用 NTP 服务
   timedatectl set-ntp true
   ```

2. **Linux/Unix 服务器**：
   ```bash
   # 检查当前时间
   date
   
   # 设置正确时区（中国大陆）
   timedatectl set-timezone Asia/Shanghai
   
   # 同步时间
   ntpdate ntp.aliyun.com
   ```

3. **验证时间是否正确**：
   ```python
   import time
   print("当前时间:", time.asctime())
   # 应该显示接近真实时间的值
   ```

**注意**：
- 容器环境的时间可能在启动时被冻结，需要手动同步
- 云服务器可能默认使用 UTC 时区，需要调整为本地时区
- 虚拟机需要确保与宿主机时间同步
