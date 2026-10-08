# phone-test-bot

Telegram 手机号检测机器人 (@hhzz00bot) —— Vercel Python webhook 版。

## 结构

- `api/webhook.py` —— 机器人全部逻辑,改这里即可
- `vercel.json` —— Vercel 部署配置

## 命令

| 命令 | 说明 |
|------|------|
| `/start` | 显示功能菜单 |
| `/test` | 普通测试 |
| `/phone <11位手机号>` | 打码显示 + 格式校验 |

## 自助更新

直接在 GitHub 网页/App 上编辑 `api/webhook.py` 并保存,
Vercel 会自动重新部署,约 1 分钟后生效。

## 环境变量(在 Vercel 项目设置里)

- `BOT_TOKEN` —— Telegram 机器人 Token
- `WEBHOOK_SECRET` —— webhook 校验密钥
