import html
import json
import os
import sqlite3
from collections import defaultdict

from push_lark import format_value

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "template.html")


def load_pushed(db_path="data/radar.db"):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT source, url, title, importance, interpretation, fetched_at"
        " FROM articles WHERE status = 'pushed'"
        " ORDER BY fetched_at DESC").fetchall()
    conn.close()
    items = []
    for source, url, title, importance, interp_json, fetched_at in rows:
        items.append({"source": source, "url": url, "title": title,
                      "importance": importance,
                      "interp": json.loads(interp_json),
                      "date": (fetched_at or "")[:10]})
    return items


def render_card(item):
    i = item["interp"]
    value_html = html.escape(format_value(i["value"])).replace("\n", "<br>\n")
    return (
        f'<article class="card">\n'
        f"  <h2>{html.escape(item['source'])}｜{html.escape(item['title'])}</h2>\n"
        f"  <p class=\"stars\">{'★' * item['importance']}</p>\n"
        f"  <p><b>一句话</b>：{html.escape(i['one_liner'])}</p>\n"
        f"  <p><b>对你有什么用</b>：<br>\n{value_html}</p>\n"
        f"  <p><b>和别家比</b>：{html.escape(i['comparison'])}</p>\n"
        f"  <p><a href=\"{html.escape(item['url'])}\">查看原文</a>"
        f" · {item['date']} · 可信度：{html.escape(i['credibility'])}</p>\n"
        f"</article>")


def render_page(template, nav, content):
    return template.replace("{nav}", nav).replace("{content}", content)


def build(db_path="data/radar.db", out_dir="data/site"):
    items = load_pushed(db_path)
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()
    by_source = defaultdict(list)
    for it in items:
        by_source[it["source"]].append(it)
    nav = " ".join(f'<a href="#{html.escape(s)}">{html.escape(s)}</a>'
                   for s in sorted(by_source))
    sections = []
    for source in sorted(by_source):
        cards = "\n".join(render_card(it) for it in by_source[source])
        sections.append(f'<section id="{html.escape(source)}">'
                        f"<h1>{html.escape(source)}</h1>\n{cards}</section>")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_page(template, nav, "\n".join(sections)))
    # 按月归档
    by_month = defaultdict(list)
    for it in items:
        by_month[it["date"][:7]].append(it)
    arch_dir = os.path.join(out_dir, "archive")
    os.makedirs(arch_dir, exist_ok=True)
    for month, month_items in by_month.items():
        cards = "\n".join(render_card(it) for it in month_items)
        with open(os.path.join(arch_dir, f"{month}.html"), "w",
                  encoding="utf-8") as f:
            f.write(render_page(template, "", cards))
