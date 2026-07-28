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
