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


def run_kimi_cli(prompt, timeout=600):
    result = subprocess.run(["kimi", "-p", prompt],
                            capture_output=True, text=True, timeout=timeout)
    result.check_returncode()
    return result.stdout


def call_moonshot(prompt, timeout=120):
    api_key = os.environ["MOONSHOT_API_KEY"]
    resp = requests.post(
        "https://api.moonshot.cn/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": DEEP_MODEL,
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.3},
        timeout=timeout)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def interpret(article, article_text, deep=False, runner=None):
    """返回解读 dict；文章与发布无关时返回 None。"""
    prompt = build_prompt(load_prompt_template(), article, article_text)
    if runner is None:
        runner = call_moonshot if deep else run_kimi_cli
    data = parse_interpretation(runner(prompt))
    return data if data["relevant"] else None
