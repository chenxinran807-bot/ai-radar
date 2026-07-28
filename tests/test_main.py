import json
from unittest.mock import patch

import main


GOOD = {"relevant": True, "importance": 3, "one_liner": "a",
        "value": "b", "comparison": "c", "credibility": "official"}


def test_run_end_to_end(tmp_path):
    db = str(tmp_path / "t.db")
    src = str(tmp_path / "s.yaml")
    with open(src, "w") as f:
        f.write("sources: []\n")
    with patch("main.fetch.collect", return_value=[1]), \
         patch("main.fetch.init_db") as init_db, \
         patch("main.fetch.fetch_article_text", return_value="text"), \
         patch("main.interpret.interpret", return_value=GOOD), \
         patch("main.push_lark.build_card", return_value={}), \
         patch("main.push_lark.push", return_value=True), \
         patch("main.build_site.build"):
        import sqlite3
        conn = sqlite3.connect(db)
        conn.executescript(main.fetch.SCHEMA)
        conn.execute(
            "INSERT INTO articles (id, source, url, title, title_hash)"
            " VALUES (1, 'S', 'https://x.com/a', 'T', 'h')")
        conn.commit()
        init_db.return_value = conn
        main.run(db, src)
        status = conn.execute(
            "SELECT status FROM articles WHERE id = 1").fetchone()[0]
        conn.close()
    assert status == "pushed"
