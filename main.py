import json
import sys
from collections import defaultdict

import build_site
import fetch
import interpret
import push_lark


def run(db_path="data/radar.db", sources_path="sources.yaml"):
    fetch.collect(db_path, sources_path)
    conn = fetch.init_db(db_path)
    # 处理所有待解读文章（含上次 failed 的重试），不只本轮新抓到的
    new_ids = [r[0] for r in conn.execute(
        "SELECT id FROM articles WHERE status IN ('new', 'failed')")]
    done = []
    for row_id in new_ids:
        row = conn.execute(
            "SELECT id, source, url, title FROM articles WHERE id = ?",
            (row_id,)).fetchone()
        if not row:
            continue
        article = {"id": row[0], "source": row[1], "url": row[2],
                   "title": row[3]}
        try:
            text = fetch.fetch_article_text(article["url"])
            data = interpret.interpret(article, text)
        except Exception as e:
            print(f"[interpret] {article['url']} failed: {e}")
            conn.execute("UPDATE articles SET status = 'failed' WHERE id = ?",
                         (row_id,))
            conn.commit()
            continue
        if data is None:
            conn.execute("UPDATE articles SET status = 'skipped' WHERE id = ?",
                         (row_id,))
            conn.commit()
            continue
        if data["importance"] >= 4:
            try:
                deep = interpret.interpret(article, text, deep=True)
                if deep:
                    data = deep
            except Exception as e:
                print(f"[deep] 保留普通版: {e}")
        conn.execute(
            "UPDATE articles SET status = 'interpreted', importance = ?,"
            " interpretation = ? WHERE id = ?",
            (data["importance"], json.dumps(data, ensure_ascii=False), row_id))
        conn.commit()
        done.append((article, data))
    by_source = defaultdict(list)
    for article, data in done:
        by_source[article["source"]].append((article, data))
    for source, items in by_source.items():
        card = (push_lark.build_card(*items[0]) if len(items) == 1
                else push_lark.build_digest_card(source, items))
        if push_lark.send(card):
            for article, _ in items:
                conn.execute(
                    "UPDATE articles SET status = 'pushed',"
                    " pushed_at = datetime('now') WHERE id = ?",
                    (article["id"],))
            conn.commit()
    conn.close()
    build_site.build(db_path)


def baseline(db_path="data/radar.db", sources_path="sources.yaml"):
    """首次运行/新增源时调用：抓取并把全部未处理文章标为 skipped，防刷屏。"""
    fetch.collect(db_path, sources_path)
    conn = fetch.init_db(db_path)
    cur = conn.execute("UPDATE articles SET status = 'skipped'"
                       " WHERE status = 'new'")
    conn.commit()
    conn.close()
    print(f"[baseline] {cur.rowcount} 条存量文章已标记 skipped")


def weekly(db_path="data/radar.db"):
    conn = fetch.init_db(db_path)
    rows = conn.execute(
        "SELECT source, url, title, importance FROM articles"
        " WHERE status = 'pushed'"
        " AND pushed_at >= datetime('now', '-7 days')"
        " ORDER BY importance DESC").fetchall()
    conn.close()
    if not rows:
        print("[weekly] 本周无推送记录")
        return
    by_source = defaultdict(list)
    for source, url, title, importance in rows:
        by_source[source].append((title, url, importance))
    lines = []
    for source in sorted(by_source):
        lines.append(f"**{source}**")
        for title, url, importance in by_source[source]:
            lines.append(f"- [{title}]({url}) {'★' * importance}")
    best = rows[0]
    lines.append(f"\n**本周最值得关注**：[{best[2]}]({best[1]})")
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {"template": "orange",
                       "title": {"tag": "plain_text",
                                 "content": "AI Radar 本周汇总"}},
            "elements": [{"tag": "markdown", "content": "\n".join(lines)}],
        },
    }
    push_lark.send(card)


if __name__ == "__main__":
    if "--weekly" in sys.argv:
        weekly()
    elif "--baseline" in sys.argv:
        baseline()
    else:
        run()
