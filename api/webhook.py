"""
Telegram "功能选择" 机器人 - Vercel Serverless Function (Python webhook 版)

部署后 Telegram webhook 指向 https://<project>.vercel.app/api/webhook
环境变量: BOT_TOKEN, WEBHOOK_SECRET

逻辑与原控制台脚本一致:
  /start  -> 显示功能菜单
  /test   -> 普通测试
  /phone <11位手机号> -> 打码显示 + 格式校验
"""

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

HELP_TEXT = (
    "请选择功能(原控制台菜单的 Telegram 版):\n\n"
    "/test - 普通测试\n"
    "/phone <手机号> - 手机号检测\n"
    "例如: /phone 13812345678"
)


def send_message(token, chat_id, text):
    data = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:  # noqa: BLE001 - 记录即可,不影响 webhook 响应
        print("sendMessage failed:", e)


def handle_phone(arg):
    phone = (arg or "").strip()
    if phone.isdigit() and len(phone) == 11:
        masked = phone[:3] + "****" + phone[-4:]
        return f"\n手机号:{masked}\n手机号格式正确。"
    return "\n手机号格式不正确。"


def handle_update(update):
    msg = update.get("message") or {}
    text = msg.get("text")
    if not isinstance(text, str):
        return
    chat_id = msg["chat"]["id"]
    parts = text.strip().split()
    command = parts[0].split("@")[0].lower()
    arg = " ".join(parts[1:])
    token = os.environ.get("BOT_TOKEN", "")

    if command in ("/start", "/help"):
        send_message(token, chat_id, HELP_TEXT)
    elif command == "/test":
        send_message(token, chat_id, "你选择了: 普通测试")
    elif command == "/phone":
        send_message(
            token,
            chat_id,
            handle_phone(arg) if arg else "用法: /phone <11位手机号>,例如 /phone 13812345678",
        )
    # 其他消息: 静默忽略


class handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, "phone-test-bot vercel function is running (python)")

    def do_POST(self):
        expected = os.environ.get("WEBHOOK_SECRET")
        if expected:
            got = self.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if got != expected:
                self._send(403, "forbidden")
                return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            update = json.loads(self.rfile.read(length) or b"{}")
        except Exception:  # noqa: BLE001 - 坏请求直接忽略
            update = {}
        handle_update(update)
        self._send(200, "ok")
