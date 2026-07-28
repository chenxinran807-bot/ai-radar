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


def fetch_entries(source, timeout=20):
    """返回 [{source, url, title, summary, published}]。"""
    if source["type"] == "rss":
        feed = feedparser.parse(source["url"])
        return [{
            "source": source["name"],
            "url": e.get("link", ""),
            "title": e.get("title", "").strip(),
            "summary": e.get("summary", ""),
            "published": e.get("published", ""),
        } for e in feed.entries]
    if source["type"] != "scrape":
        raise ValueError(f"unknown source type: {source['type']}")
    resp = requests.get(source["url"], timeout=timeout, headers=USER_AGENT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    entries = []
    for a in soup.select(source["selector"]):
        href = a.get("href", "")
        if href.startswith("/"):
            href = source["base"] + href
        # 过滤分页、标签页和列表页自身等噪声链接
        if ("?page=" in href or "/tag/" in href
                or href.rstrip("/") == source["url"].rstrip("/")):
            continue
        entries.append({"source": source["name"], "url": href,
                        "title": a.get_text(strip=True),
                        "summary": "", "published": ""})
    return entries


def fetch_article_text(url, timeout=20, max_chars=8000):
    resp = requests.get(url, timeout=timeout, headers=USER_AGENT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    root = soup.find("article") or soup.body or soup
    return root.get_text("\n", strip=True)[:max_chars]


def collect(db_path="data/radar.db", sources_path="sources.yaml"):
    """抓全部源，存关键词命中的新条目，返回新 row id 列表。单源失败只记日志。"""
    conn = init_db(db_path)
    new_ids = []
    for source in load_sources(sources_path):
        try:
            entries = fetch_entries(source)
        except Exception as e:
            print(f"[fetch] {source['name']} failed: {e}")
            continue
        for entry in entries:
            if not passes_keywords(source, entry["title"], entry["summary"]):
                continue
            row_id = save_new(conn, entry)
            if row_id:
                new_ids.append(row_id)
        conn.commit()
        time.sleep(1)
    conn.close()
    return new_ids
