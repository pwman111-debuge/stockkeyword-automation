import csv
import email.utils
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))

TREND_LOG = Path(__file__).parent.parent / "logs" / "trend_log.csv"
TREND_LOG_FIELDS = ["date", "keyword", "rank", "geo", "source"]
HT_NS = "https://trends.google.com/trends/trendingsearches"

# 구글 트렌드: 대한민국 / 지난 24시간 / 비즈니스 및 금융 카테고리
TRENDS_URL = "https://trends.google.com/trending/rss?geo=KR&hours=24&cat=7"


def pick_trends(max_count: int = 3) -> list[dict]:
    used_today = _load_used_today()

    candidates = [
        item for item in _fetch_rss_trends()
        if item["keyword"] not in used_today
    ]

    result = candidates[:max_count]
    for i, item in enumerate(result):
        item["rank"] = i + 1

    if result:
        _log_trends(result)

    return result


def _fetch_rss_trends() -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for attempt in range(3):
        try:
            req = urllib.request.Request(TRENDS_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read().decode("utf-8")

            root = ET.fromstring(raw)
            today_kst = datetime.now(KST).date()

            all_items = []
            for item in root.iter("item"):
                title_el = item.find("title")
                if title_el is None or not title_el.text:
                    continue

                item_date = None
                pub_date_el = item.find("pubDate")
                if pub_date_el is not None and pub_date_el.text:
                    try:
                        pub_dt = email.utils.parsedate_to_datetime(pub_date_el.text)
                        item_date = pub_dt.astimezone(KST).date()
                    except Exception:
                        pass

                traffic = 0
                traffic_el = item.find(f"{{{HT_NS}}}approx_traffic")
                if traffic_el is not None and traffic_el.text:
                    try:
                        traffic = int(traffic_el.text.replace(",", "").replace("+", "").strip())
                    except ValueError:
                        pass

                all_items.append({
                    "keyword": title_el.text.strip(),
                    "geo": "KR",
                    "item_date": item_date,
                    "traffic": traffic,
                    "source": "trend",
                })

            today_items = [i for i in all_items if i["item_date"] == today_kst]

            if not today_items:
                dated = [i for i in all_items if i["item_date"] is not None]
                if dated:
                    most_recent = max(i["item_date"] for i in dated)
                    today_items = [i for i in dated if i["item_date"] == most_recent]
                    print(f"  [트렌드] 오늘({today_kst}) 데이터 없음 → 최근 날짜({most_recent}) 사용")
                else:
                    today_items = all_items

            return [
                {
                    "keyword": item["keyword"],
                    "rank": rank,
                    "geo": "KR",
                    "traffic": item["traffic"],
                    "source": "trend",
                }
                for rank, item in enumerate(today_items[:20], start=1)
            ]

        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                print(f"  [트렌드] RSS 수집 실패: {e}")
    return []


def _load_used_today() -> set[str]:
    today = datetime.now(KST).date().isoformat()
    used = set()
    if not TREND_LOG.exists():
        return used
    with open(TREND_LOG, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("date", "").startswith(today):
                used.add(row.get("keyword", ""))
    return used


def _log_trends(trends: list[dict]) -> None:
    today = datetime.now(KST).date().isoformat()
    is_new = not TREND_LOG.exists() or TREND_LOG.stat().st_size == 0
    with open(TREND_LOG, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TREND_LOG_FIELDS)
        if is_new:
            writer.writeheader()
        for item in trends:
            writer.writerow({
                "date": today,
                "keyword": item["keyword"],
                "rank": item["rank"],
                "geo": item["geo"],
                "source": item.get("source", "trend"),
            })
