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


def call_api(prompt, timeout=120):
    """OpenAI 兼容接口（火山方舟 / Moonshot 等），由环境变量配置：
    AI_RADAR_API_KEY 必填；AI_RADAR_API_BASE / AI_RADAR_API_MODEL 有默认值。"""
    api_key = os.environ["AI_RADAR_API_KEY"]
    base = os.environ.get("AI_RADAR_API_BASE", "https://api.moonshot.cn/v1")
    model = os.environ.get("AI_RADAR_API_MODEL", DEEP_MODEL)
    resp = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model,
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.3},
        timeout=timeout)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def interpret(article, article_text, deep=False, runner=None):
    """返回解读 dict；文章与发布无关时返回 None。
    默认：日常 kimi CLI，deep 用 API；AI_RADAR_ALL_API=1 时全部走 API。"""
    prompt = build_prompt(load_prompt_template(), article, article_text)
    if runner is None:
        use_api = deep or os.environ.get("AI_RADAR_ALL_API") == "1"
        runner = call_api if use_api else run_kimi_cli
    data = parse_interpretation(runner(prompt))
    return data if data["relevant"] else None
