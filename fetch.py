import hashlib
import sqlite3
import time

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

USER_AGENT = {"User-Agent": "ai-radar/0.1"}


def load_sources(path="sources.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["sources"]


SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    title_hash TEXT NOT NULL,
    summary TEXT DEFAULT '',
    published TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'new',
    importance INTEGER,
    interpretation TEXT,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    pushed_at TEXT
);
"""


def init_db(db_path="data/radar.db"):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def title_hash(title):
    return hashlib.sha1(title.strip().lower().encode()).hexdigest()


def passes_keywords(source, title, summary):
    kws = source.get("keywords")
    if not kws:
        return True
    text = (title + " " + (summary or "")).lower()
    return any(k.lower() in text for k in kws)


def save_new(conn, entry):
    """url 已存在则返回 None，否则插入并返回 row id。"""
    if not entry["url"] or not entry["title"]:
        return None
    if conn.execute("SELECT 1 FROM articles WHERE url = ?",
                    (entry["url"],)).fetchone():
        return None
    cur = conn.execute(
        "INSERT INTO articles (source, url, title, title_hash, summary, published)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (entry["source"], entry["url"], entry["title"],
         title_hash(entry["title"]), entry["summary"], entry["published"]))
    return cur.lastrowid
