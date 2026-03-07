# Token 获取与存储

Token 是晋江 App 的登录身份凭证，用于下载**收费（付费）章节**。查询信息、下载免费章节均无需 token。

## 抓包步骤（Android）

1. 手机安装晋江 App 并登录账号
2. 安装抓包工具：推荐 **HttpCanary**（Android 免费）或 **Charles**（桌面端）
3. 开启抓包，在 App 内随意点开一章正文
4. 在抓包记录中找到域名含 `jjwxc.net` 的请求
5. 查看请求 URL 的 Query 参数，找到 `token=xxxxxxxx` 字段
6. 复制 token 值（通常为数字+字母组成的长字符串）

> ⚠️ Token 有效期有限，若收费章节下载失败请重新抓包更新。

## 持久化存储

**方式一：写入 config.yml（推荐）**

```yaml
token: "your_token_here"
```

**方式二：环境变量（CI / 服务器）**

```bash
export JJWXC_TOKEN="your_token_here"
```

> 不要将 token 明文提交到版本控制，`config.yml` 已在 `.gitignore` 中。
