import pytest

import interpret


TEMPLATE = "源:{source} 题:{title} 链:{url} 文:{content}"


def test_build_prompt():
    article = {"source": "OpenAI", "title": "GPT-X", "url": "https://x.com/a"}
    out = interpret.build_prompt(TEMPLATE, article, "正文内容")
    assert "源:OpenAI" in out and "正文内容" in out


def test_parse_interpretation_ok():
    text = '前言 {"relevant": true, "importance": 4, "one_liner": "a", "value": "b", "comparison": "c", "credibility": "official"} 后记'
    data = interpret.parse_interpretation(text)
    assert data["importance"] == 4


def test_parse_interpretation_bad():
    with pytest.raises(ValueError):
        interpret.parse_interpretation("no json here")
