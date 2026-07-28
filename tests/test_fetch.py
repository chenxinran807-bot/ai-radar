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
