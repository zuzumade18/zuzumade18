"""Fill README.md between <!-- BLOG:START --> and <!-- BLOG:END --> with the latest posts from the ZuzuMade blog feed.

Standard library only. Run by .github/workflows/blog.yml every few hours; safe to run locally too.
"""

import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = "https://zuzumade.com/blog/feed.xml"
README = Path(__file__).resolve().parents[2] / "README.md"
COUNT = 6
COLUMNS = 3
MEDIA = "{http://search.yahoo.com/mrss/}"
START, END = "<!-- BLOG:START -->", "<!-- BLOG:END -->"


def fetch() -> list[dict]:
    req = urllib.request.Request(FEED, headers={"User-Agent": "zuzumade-profile-readme"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    posts = []
    for item in root.iter("item"):
        image = None
        media = item.find(f"{MEDIA}content")
        if media is not None:
            image = media.get("url")
        if not image:
            enc = item.find("enclosure")
            image = enc.get("url") if enc is not None else None
        try:
            date = parsedate_to_datetime(item.findtext("pubDate", "")).strftime("%d %b %Y")
        except (TypeError, ValueError):
            date = ""
        posts.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "url": (item.findtext("link") or "").strip(),
                "category": (item.findtext("category") or "").strip(),
                "date": date,
                "image": image,
            }
        )
        if len(posts) == COUNT:
            break
    return posts


def card(p: dict) -> str:
    e = lambda s: html.escape(s, quote=True)
    img = f'<a href="{e(p["url"])}"><img src="{e(p["image"])}" width="260" alt="{e(p["title"])}" /></a><br />' if p["image"] else ""
    meta = " · ".join(x for x in (p["category"], p["date"]) if x)
    return (
        f'<td align="center" valign="top" width="33%">{img}'
        f'<a href="{e(p["url"])}"><b>{e(p["title"])}</b></a><br />'
        f"<sub>{e(meta)}</sub></td>"
    )


def render(posts: list[dict]) -> str:
    if not posts:
        return '<p align="center"><a href="https://zuzumade.com/blog">Read the ZuzuMade blog →</a></p>'
    rows = []
    for i in range(0, len(posts), COLUMNS):
        rows.append("<tr>" + "".join(card(p) for p in posts[i : i + COLUMNS]) + "</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def main() -> int:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("README has no blog markers", file=sys.stderr)
        return 1
    block = f"{START}\n{render(fetch())}\n{END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    if new != text:
        README.write_text(new, encoding="utf-8")
        print("README updated")
    else:
        print("No change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
