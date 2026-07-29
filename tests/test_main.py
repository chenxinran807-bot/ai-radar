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
        conn.close()
        check = sqlite3.connect(db)
        status = check.execute(
            "SELECT status FROM articles WHERE id = 1").fetchone()[0]
        check.close()
    assert status == "pushed"


def test_baseline_marks_skipped(tmp_path):
    db = str(tmp_path / "t.db")
    with patch("main.fetch.collect", return_value=[1]), \
         patch("main.fetch.init_db") as init_db:
        import sqlite3
        conn = sqlite3.connect(db)
        conn.executescript(main.fetch.SCHEMA)
        conn.execute(
            "INSERT INTO articles (id, source, url, title, title_hash)"
            " VALUES (1, 'S', 'https://x.com/a', 'T', 'h')")
        conn.commit()
        init_db.return_value = conn
        main.baseline(db)
        conn.close()
        check = sqlite3.connect(db)
        status = check.execute(
            "SELECT status FROM articles WHERE id = 1").fetchone()[0]
        check.close()
    assert status == "skipped"


def test_load_env(tmp_path, monkeypatch):
    env = tmp_path / "env"
    env.write_text("AI_RADAR_API_KEY=sk-abc\n# comment\n\nOTHER=1\n")
    monkeypatch.delenv("AI_RADAR_API_KEY", raising=False)
    main.load_env(str(env))
    import os
    assert os.environ["AI_RADAR_API_KEY"] == "sk-abc"
    assert os.environ["OTHER"] == "1"
