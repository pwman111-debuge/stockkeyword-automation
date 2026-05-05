import html
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET


def fetch_latest_news(keyword: str, max_count: int = 5) -> list[dict]:
    encoded = urllib.parse.quote(keyword)
    url = (
        f"https://news.google.com/rss/search"
        f"?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
    )
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8")

        root = ET.fromstring(raw)
        items = []

        for item in root.iter("item"):
            title_el = item.find("title")
            if title_el is None or not title_el.text:
                continue

            desc_el = item.find("description")
            pub_el = item.find("pubDate")
            source_el = item.find("source")

            items.append({
                "title": title_el.text.strip(),
                "description": _strip_html(desc_el.text or "") if desc_el is not None else "",
                "pub_date": pub_el.text.strip() if pub_el is not None else "",
                "source": source_el.text.strip() if source_el is not None else "",
            })

            if len(items) >= max_count:
                break

        return items

    except Exception as e:
        print(f"  [뉴스] 수집 실패 ({keyword}): {e}")
        return []


def build_news_block(news_items: list[dict]) -> str:
    if not news_items:
        return "관련 뉴스를 찾을 수 없습니다."

    lines = []
    for i, article in enumerate(news_items, start=1):
        lines.append(f"{i}. [{article['source']}] {article['title']}")
        if article["description"]:
            lines.append(f"   {article['description'][:300]}")
        if article["pub_date"]:
            lines.append(f"   발행: {article['pub_date']}")
        lines.append("")

    return "\n".join(lines).strip()


def _strip_html(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()
