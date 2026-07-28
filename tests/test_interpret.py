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


GOOD = ('{"relevant": true, "importance": 3, "one_liner": "a",'
        ' "value": "b", "comparison": "c", "credibility": "official"}')


def test_interpret_relevant():
    article = {"source": "S", "title": "T", "url": "U"}
    data = interpret.interpret(article, "text", runner=lambda p: GOOD)
    assert data["importance"] == 3


def test_interpret_irrelevant():
    article = {"source": "S", "title": "T", "url": "U"}
    out = interpret.interpret(
        article, "text",
        runner=lambda p: GOOD.replace('"relevant": true', '"relevant": false'))
    assert out is None


def test_run_kimi_cli():
    from unittest.mock import patch, MagicMock
    fake = MagicMock(stdout="model output", returncode=0)
    with patch("interpret.subprocess.run", return_value=fake) as run:
        out = interpret.run_kimi_cli("hello")
    assert out == "model output"
    assert run.call_args[0][0][:2] == ["kimi", "-p"]
