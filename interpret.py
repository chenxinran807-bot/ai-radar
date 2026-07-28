import json
import os
import re
import subprocess

import requests

PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt.md")
DEEP_MODEL = os.environ.get("MOONSHOT_MODEL", "moonshot-v1-32k")


def load_prompt_template(path=PROMPT_PATH):
    with open(path, encoding="utf-8") as f:
        return f.read()


def build_prompt(template, article, article_text):
    return (template
            .replace("{source}", article["source"])
            .replace("{title}", article["title"])
            .replace("{url}", article["url"])
            .replace("{content}", article_text))


def parse_interpretation(text):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("no JSON object in model output")
    data = json.loads(m.group(0))
    for key in ("relevant", "importance", "one_liner", "value",
                "comparison", "credibility"):
        if key not in data:
            raise ValueError(f"missing key: {key}")
    return data
