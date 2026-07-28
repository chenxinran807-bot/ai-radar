import fetch


def test_save_new_dedup(tmp_path):
    conn = fetch.init_db(str(tmp_path / "t.db"))
    entry = {"source": "OpenAI", "url": "https://x.com/a",
             "title": "GPT-X 发布", "summary": "", "published": ""}
    first = fetch.save_new(conn, entry)
    second = fetch.save_new(conn, entry)
    assert first is not None
    assert second is None


def test_passes_keywords():
    src = {"keywords": ["gpt", "release"]}
    assert fetch.passes_keywords(src, "Introducing GPT-5", "")
    assert not fetch.passes_keywords(src, "Our hiring update", "")
    assert fetch.passes_keywords({"name": "NoKw"}, "anything", "")


def test_load_sources(tmp_path):
    p = tmp_path / "sources.yaml"
    p.write_text(
        "sources:\n"
        "  - name: OpenAI\n"
        "    type: rss\n"
        "    url: https://example.com/rss.xml\n"
        "    keywords: [gpt, release]\n",
        encoding="utf-8")
    sources = fetch.load_sources(str(p))
    assert sources[0]["name"] == "OpenAI"
    assert sources[0]["type"] == "rss"


def test_fetch_entries_rss():
    source = {"name": "OpenAI", "type": "rss",
              "url": "tests/fixtures/rss.xml"}
    entries = fetch.fetch_entries(source)
    assert entries[0]["title"] == "Introducing GPT-X"
    assert entries[0]["url"] == "https://example.com/gpt-x"
    assert entries[0]["source"] == "OpenAI"


from unittest.mock import patch


class FakeResp:
    def __init__(self, text):
        self.text = text
        self.ok = True

    def raise_for_status(self):
        pass


def load_fixture(name):
    with open(f"tests/fixtures/{name}", encoding="utf-8") as f:
        return f.read()


def test_fetch_entries_scrape():
    source = {"name": "Anthropic", "type": "scrape",
              "url": "https://www.anthropic.com/news",
              "selector": "a[href^='/news/']",
              "base": "https://www.anthropic.com"}
    with patch("fetch.requests.get", return_value=FakeResp(load_fixture("page.html"))):
        entries = fetch.fetch_entries(source)
    assert entries[0]["url"] == "https://www.anthropic.com/news/claude-y"
    assert entries[0]["title"] == "Claude Y Released"


def test_fetch_article_text():
    with patch("fetch.requests.get", return_value=FakeResp(load_fixture("page.html"))):
        text = fetch.fetch_article_text("https://x.com/a")
    assert "Full article body here." in text


def test_collect(tmp_path):
    p = tmp_path / "sources.yaml"
    p.write_text(
        "sources:\n"
        "  - name: OpenAI\n"
        "    type: rss\n"
        "    url: tests/fixtures/rss.xml\n"
        "    keywords: [gpt]\n",
        encoding="utf-8")
    with patch("fetch.time.sleep"):
        ids = fetch.collect(str(tmp_path / "t.db"), str(p))
    assert len(ids) == 1


def test_scrape_filters_junk_links():
    html = """<html><body>
    <a href="/blog/real-post">Real Post</a>
    <a href="/blog/?page=2">Next</a>
    <a href="/blog/tag/x">Tag</a>
    <a href="/blog">Blog Home</a>
    </body></html>"""
    source = {"name": "S", "type": "scrape", "url": "https://s.com/blog",
              "selector": "a[href^='/blog']", "base": "https://s.com"}
    with patch("fetch.requests.get", return_value=FakeResp(html)):
        entries = fetch.fetch_entries(source)
    assert [e["url"] for e in entries] == ["https://s.com/blog/real-post"]
