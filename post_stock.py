import argparse
import sys
import time
from dotenv import load_dotenv
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(Path(__file__).parent / ".env")

from modules.trend_picker import pick_trends
from modules.content_generator import generate_content
from modules.html_converter import convert_to_html
from modules.tistory_poster import post_to_tistory
from modules.threads_poster import post_to_threads
from modules.linkedin_poster import post_to_linkedin
from modules.logger import log_post

DELAY_BETWEEN_POSTS = 120


def run_once(trend: dict, dry_run: bool = False) -> dict | None:
    keyword = trend["keyword"]
    rank = trend["rank"]
    print(f"\n[{rank}위 키워드] {keyword}")

    print("  콘텐츠 생성 중...")
    content = generate_content(trend)
    print(f"  제목: {content['title']}")
    print(f"  본문: {len(content['markdown'])}자")

    html = convert_to_html(content["markdown"])

    if dry_run:
        print("  [dry-run] 발행 건너뜀")
        return {"title": content["title"], "url": "(dry-run)"}

    print("  티스토리 발행 중...")
    post_url = post_to_tistory(content["title"], html, content.get("tags", []))
    print(f"  발행 완료: {post_url}")

    threads_ok = post_to_threads(content["sns_summary"], post_url)
    linkedin_ok = post_to_linkedin(content["sns_summary"], post_url)
    print(f"  Threads: {'OK' if threads_ok else 'FAIL'}  LinkedIn: {'OK' if linkedin_ok else 'FAIL'}")

    log_post(keyword, content["title"], post_url, threads_ok, linkedin_ok)

    return {"title": content["title"], "url": post_url}


def main() -> None:
    parser = argparse.ArgumentParser(description="증시 키워드 자동 포스팅")
    parser.add_argument("--dry-run", action="store_true", help="발행 없이 콘텐츠 생성만 확인")
    parser.add_argument("--keyword", type=str, default=None, help="키워드 직접 지정")
    args = parser.parse_args()

    if args.keyword:
        trends = [{"keyword": args.keyword, "rank": 1, "geo": "KR"}]
    else:
        print("구글 트렌드 수집 중...")
        trends = pick_trends(max_count=3)
        if not trends:
            print("트렌드 수집 실패 -- 실행을 중단합니다.")
            return
        print(f"수집된 키워드: {[t['keyword'] for t in trends]}")

    results = []
    for i, trend in enumerate(trends):
        try:
            result = run_once(trend, dry_run=args.dry_run)
            if result:
                results.append(result)
        except Exception as e:
            print(f"  [{trend['keyword']}] 오류 발생 -- 건너뜀: {e}")
        if i < len(trends) - 1:
            print(f"\n{DELAY_BETWEEN_POSTS}초 대기 중...")
            time.sleep(DELAY_BETWEEN_POSTS)

    print(f"\n=== 완료: {len(results)}편 발행 ===")
    for r in results:
        print(f"  - {r['title']}")
        print(f"    {r['url']}")


if __name__ == "__main__":
    main()
