"""
Telegram "功能选择" 机器人 - Vercel Serverless Function (Python webhook 版)

部署后 Telegram webhook 指向 https://<project>.vercel.app/api/webhook
环境变量: BOT_TOKEN, WEBHOOK_SECRET

支持两种交互:
  命令式: /start /test /phone <11位手机号>
  自然语言: 直接发 1 / 2 / 11位号码,机器人能听懂
"""

import json
import os
import re
import urllib.request
from http.server import BaseHTTPRequestHandler

HELP_TEXT = (
    "请选择功能:\n\n"
    "1 - 普通测试(发: 1 或 /test)\n"
    "2 - 手机号检测(发: 2 或 /phone 13812345678)\n\n"
    "你也可以直接发 11 位手机号,我来帮你检测。"
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


def reply_for(text):
    """根据用户发来的文字决定回复,None 表示不回复。"""
    t = (text or "").strip()
    if not t:
        return None

    # ---- 1) 命令式 ----
    if t.startswith("/"):
        parts = t.split()
        command = parts[0].split("@")[0].lower()
        arg = " ".join(parts[1:])
        if command in ("/start", "/help"):
            return HELP_TEXT
        if command == "/test":
            return "你选择了: 普通测试"
        if command == "/phone":
            if arg:
                return handle_phone(arg)
            return "用法: /phone <11位手机号>,例如 /phone 13812345678"
        return None

    # ---- 2) 纯 11 位数字,直接检测 ----
    if t.isdigit() and len(t) == 11:
        return handle_phone(t)

    # ---- 3) 带分隔符的号码,如 138 1234 5678 / 138-1234-5678 ----
    digits = re.sub(r"\D", "", t)
    if len(digits) == 11 and re.fullmatch(r"[\d\s\-()（）]+", t):
        return handle_phone(digits)

    # ---- 4) 自然语言 ----
    low = t.lower()
    if low in ("1", "一", "测试", "普通测试", "test"):
        return "你选择了: 普通测试"
    if low in ("2", "二", "检测", "手机号", "手机号检测", "查号码", "查号", "phone"):
        return "好的,请直接发送 11 位手机号,我来帮你检测。"

    # ---- 5) 消息里夹带 11 位号码,顺手检测 ----
    m = re.search(r"(?<!\d)\d{11}(?!\d)", t)
    if m:
        return handle_phone(m.group(0)) + "\n(已从你的消息中识别出号码)"

    # ---- 6) 听不懂,给提示 ----
    return "我没太明白,可以这样用:\n\n" + HELP_TEXT


def handle_update(update):
    msg = update.get("message") or {}
    text = msg.get("text")
    if not isinstance(text, str):
        return
    reply = reply_for(text)
    if reply is None:
        return
    token = os.environ.get("BOT_TOKEN", "")
    send_message(token, msg["chat"]["id"], reply)


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
