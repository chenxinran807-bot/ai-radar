from unittest.mock import patch

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


def test_call_api_uses_env(monkeypatch):
    from unittest.mock import patch, MagicMock
    monkeypatch.setenv("AI_RADAR_API_KEY", "sk-test")
    monkeypatch.setenv("AI_RADAR_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")
    monkeypatch.setenv("AI_RADAR_API_MODEL", "ep-123")
    resp = MagicMock()
    resp.json.return_value = {"choices": [{"message": {"content": "out"}}]}
    with patch("interpret.requests.post", return_value=resp) as post:
        out = interpret.call_api("hi")
    assert out == "out"
    assert post.call_args[0][0] == "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    assert post.call_args[1]["json"]["model"] == "ep-123"
    assert post.call_args[1]["headers"]["Authorization"] == "Bearer sk-test"


def test_all_api_switch(monkeypatch):
    monkeypatch.setenv("AI_RADAR_ALL_API", "1")
    article = {"source": "S", "title": "T", "url": "U"}
    with patch("interpret.call_api", return_value=GOOD) as api, \
         patch("interpret.run_kimi_cli") as cli:
        interpret.interpret(article, "text")
        api.assert_called_once()
        cli.assert_not_called()
