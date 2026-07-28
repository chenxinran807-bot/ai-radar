import json
import sqlite3

import build_site
import fetch


def seed(db_path):
    conn = fetch.init_db(db_path)
    conn.execute(
        "INSERT INTO articles (source, url, title, title_hash, status,"
        " importance, interpretation, pushed_at) VALUES (?,?,?,?,?,?,?,"
        " datetime('now'))",
        ("OpenAI", "https://x.com/a", "GPT-X", "h", "pushed", 4,
         json.dumps({"one_liner": "新模型", "value": "更好用",
                     "comparison": "领先", "credibility": "official"},
                    ensure_ascii=False)))
    conn.commit()
    conn.close()


def test_build(tmp_path):
    db = str(tmp_path / "t.db")
    seed(db)
    out = str(tmp_path / "site")
    build_site.build(db, out)
    with open(f"{out}/index.html", encoding="utf-8") as f:
        page = f.read()
    assert "GPT-X" in page and "新模型" in page
