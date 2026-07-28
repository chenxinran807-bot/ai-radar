import os
import time

import requests


def stars(n):
    return "★" * n + "☆" * (5 - n)


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
                 "content": f"**对你有什么用**：{interp['value']}"},
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
