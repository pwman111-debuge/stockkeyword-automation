import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv(Path(__file__).parent / ".env")

EMAIL = os.environ["TISTORY_EMAIL"]
PASSWORD = os.environ["TISTORY_PASSWORD"]
BLOG_NAME = os.environ.get("TISTORY_BLOG_NAME", "stockkeyword")
SESSION_FILE = Path(__file__).parent / "tistory_session.json"


def login(page):
    page.wait_for_load_state("networkidle", timeout=15000)
    if "tistory.com/auth/login" in page.url or "kakao" in page.url:
        if "tistory.com/auth/login" in page.url:
            page.get_by_role("link", name="카카오계정으로 로그인").click()
            page.wait_for_load_state("networkidle", timeout=15000)
        page.get_by_role("textbox", name="계정 정보 입력").fill(EMAIL)
        page.get_by_role("textbox", name="비밀번호 입력").fill(PASSWORD)
        page.get_by_role("button", name="로그인", exact=True).click()
        page.wait_for_url(f"**{BLOG_NAME}.tistory.com/manage/**", timeout=60000)
        print("로그인 완료")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 900})

    if SESSION_FILE.exists():
        context.add_cookies(json.loads(SESSION_FILE.read_text(encoding="utf-8")))

    page = context.new_page()

    # 1. 페이지 관리 목록 접속
    page.goto(f"https://{BLOG_NAME}.tistory.com/manage/page/")
    page.wait_for_load_state("networkidle", timeout=20000)

    if "login" in page.url or "kakao" in page.url or "auth" in page.url:
        login(page)

    page.wait_for_timeout(2000)
    page.screenshot(path="debug1_pagelist.png")
    print(f"[1] 페이지 목록 URL: {page.url}")

    # 2. 이미 발행된 페이지가 있는지 확인
    print(f"[2] 페이지 내 모든 링크:")
    links = page.locator("a").all()
    for link in links[:30]:
        try:
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip()
            if text and ("/p/" in href or "page" in href.lower() or "개인" in text or "문의" in text):
                print(f"  - {text!r}: {href}")
        except Exception:
            pass

    input("엔터를 눌러 브라우저를 닫으세요...")
    browser.close()
