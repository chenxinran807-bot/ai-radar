import json
import os
import re
import subprocess
import time

import requests


def stars(n):
    return "★" * n + "☆" * (5 - n)


def format_value(text):
    """value 字段按角色换行：普通用户 / 开发者 / 关注行业的人。"""
    return re.sub(r"(?<!\n)(开发者：|关注行业的人：)", r"\n\1", text)


def build_card(article, interp):
    color = "red" if interp["importance"] >= 4 else "blue"
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "template": color,
                "title": {"tag": "plain_text",
                          "content": f"{article['source']}｜{article['title']}"},
            },
            "elements": [
                {"tag": "markdown",
                 "content": f"**{stars(interp['importance'])}**\n\n**一句话**：{interp['one_liner']}"},
                {"tag": "markdown",
                 "content": f"**对你有什么用**：\n{format_value(interp['value'])}"},
                {"tag": "markdown",
                 "content": f"**和别家比**：{interp['comparison']}"},
                {"tag": "markdown",
                 "content": f"可信度：{interp['credibility']}"},
                {"tag": "action",
                 "actions": [{"tag": "button",
                              "text": {"tag": "plain_text", "content": "查看原文"},
                              "url": article["url"],
                              "type": "primary"}]},
            ],
        },
    }


def build_digest_card(source_name, items):
    lines = [f"- [{a['title']}]({a['url']}) {stars(i['importance'])} {i['one_liner']}"
             for a, i in items]
    return {
        "msg_type": "interactive",
        "card": {
            "header": {"template": "blue",
                       "title": {"tag": "plain_text",
                                 "content": f"{source_name}｜连发 {len(items)} 篇"}},
            "elements": [{"tag": "markdown", "content": "\n".join(lines)}],
        },
    }


def push(card, webhook=None, retries=3):
    webhook = webhook or os.environ["LARK_WEBHOOK_URL"]
    for attempt in range(retries):
        try:
            resp = requests.post(webhook, json=card, timeout=15)
            if resp.ok and resp.json().get("code", 0) == 0:
                return True
        except Exception as e:
            print(f"[push] attempt {attempt + 1} failed: {e}")
        time.sleep(2 ** attempt)
    return False


def push_lark_cli(card, chat_id=None, retries=3):
    """通过 lark-cli 发到群聊（LARK_CHAT_ID）。content 用卡片 1.0 JSON。"""
    chat_id = chat_id or os.environ["LARK_CHAT_ID"]
    content = json.dumps(card.get("card", card), ensure_ascii=False)
    for attempt in range(retries):
        try:
            result = subprocess.run(
                ["lark-cli", "im", "+messages-send", "--as", "bot",
                 "--chat-id", chat_id,
                 "--msg-type", "interactive",
                 "--content", content],
                capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return True
            print(f"[push] lark-cli attempt {attempt + 1}: "
                  f"{result.stderr[:200]}")
        except Exception as e:
            print(f"[push] lark-cli attempt {attempt + 1} failed: {e}")
        time.sleep(2 ** attempt)
    return False


def send(card):
    """优先 lark-cli（LARK_CHAT_ID），否则自定义机器人 webhook。"""
    if os.environ.get("LARK_CHAT_ID"):
        return push_lark_cli(card)
    return push(card)
