import csv
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "logs" / "post_log.csv"
FIELDS = ["date", "keyword", "title", "post_url", "threads", "linkedin"]


def log_post(keyword: str, title: str, post_url: str, threads_ok: bool = False, linkedin_ok: bool = False) -> None:
    is_new = not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0
    with open(LOG_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "keyword": keyword,
            "title": title,
            "post_url": post_url,
            "threads": "✓" if threads_ok else "✗",
            "linkedin": "✓" if linkedin_ok else "✗",
        })
