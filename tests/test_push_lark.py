import push_lark


ARTICLE = {"source": "OpenAI", "title": "GPT-X", "url": "https://x.com/a"}
INTERP = {"relevant": True, "importance": 5, "one_liner": "新模型",
          "value": "更好用", "comparison": "领先", "credibility": "official"}


def test_build_card_important_is_red():
    card = push_lark.build_card(ARTICLE, INTERP)
    assert card["msg_type"] == "interactive"
    assert card["card"]["header"]["template"] == "red"
    assert "OpenAI" in card["card"]["header"]["title"]["content"]


def test_build_card_normal_is_blue():
    interp = dict(INTERP, importance=2)
    card = push_lark.build_card(ARTICLE, interp)
    assert card["card"]["header"]["template"] == "blue"


def test_digest_card():
    items = [(ARTICLE, INTERP), (dict(ARTICLE, title="第二篇"), INTERP)]
    card = push_lark.build_digest_card("OpenAI", items)
    assert "连发 2 篇" in card["card"]["header"]["title"]["content"]


from unittest.mock import patch, MagicMock


def test_push_success():
    resp = MagicMock(ok=True)
    resp.json.return_value = {"code": 0}
    with patch("push_lark.requests.post", return_value=resp):
        assert push_lark.push({"msg_type": "interactive", "card": {}},
                              webhook="https://hook.example/x")


def test_push_retries_then_fails():
    with patch("push_lark.requests.post", side_effect=Exception("boom")), \
         patch("push_lark.time.sleep"):
        assert not push_lark.push({}, webhook="https://hook.example/x")
