import fetch


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
