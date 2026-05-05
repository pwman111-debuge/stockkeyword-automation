import json
import os
import re
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE_DIR = Path(__file__).parent.parent
SESSION_FILE = BASE_DIR / "tistory_session.json"
BLOG_NAME = os.environ.get("TISTORY_BLOG_NAME", "증시키워드분석")
CATEGORY = os.environ.get("POST_CATEGORY", "증시분석")
HEADLESS = os.environ.get("HEADLESS", "False").lower() == "true"
EMAIL = os.environ.get("TISTORY_EMAIL", "")
PASSWORD = os.environ.get("TISTORY_PASSWORD", "")


def post_to_tistory(title: str, html: str, tags: list[str] | None = None) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        if SESSION_FILE.exists():
            context.add_cookies(json.loads(SESSION_FILE.read_text(encoding="utf-8")))

        page = context.new_page()
        page.goto(f"https://{BLOG_NAME}.tistory.com/manage/newpost/")
        page.wait_for_load_state("networkidle", timeout=30000)

        if "login" in page.url or "kakao" in page.url or "auth" in page.url:
            _kakao_login(page, BLOG_NAME)
            _save_session(context)
            print("  세션 저장 완료")

        alerts: list[str] = []

        def on_dialog(d):
            print(f"  [Dialog] {d.type}: {d.message}")
            if d.type == "alert":
                alerts.append(d.message)
            d.accept()

        page.on("dialog", on_dialog)
        page.wait_for_timeout(2000)
        _dismiss_restore_popup(page)

        _fill_title(page, title)
        _inject_html(page, html)
        _set_category(page, CATEGORY)
        _set_tags(page, tags or [])
        post_url = _publish(page, alerts)

        _save_session(context)
        browser.close()
        return post_url


def _kakao_login(page, blog_name: str) -> None:
    print("  카카오 자동 로그인 시도 중...")
    page.wait_for_load_state("networkidle", timeout=15000)

    if "tistory.com/auth/login" in page.url:
        page.get_by_role("link", name="카카오계정으로 로그인").click()
        page.wait_for_load_state("networkidle", timeout=15000)

    page.get_by_role("textbox", name="계정 정보 입력").fill(EMAIL)
    page.get_by_role("textbox", name="비밀번호 입력").fill(PASSWORD)
    page.get_by_role("button", name="로그인", exact=True).click()

    page.wait_for_url(f"**{blog_name}.tistory.com/manage/**", timeout=60000)
    print("  카카오 로그인 완료")


def _fill_title(page, title: str) -> None:
    page.wait_for_selector("#post-title-inp", timeout=10000)
    page.fill("#post-title-inp", title)


def _dismiss_restore_popup(page) -> None:
    for btn_text in ["새 글 작성", "취소", "아니오", "닫기"]:
        try:
            btn = page.locator(f"button:has-text('{btn_text}')").first
            if btn.is_visible(timeout=1000):
                btn.click()
                page.wait_for_timeout(800)
                print(f"  [팝업 처리] '{btn_text}' 클릭")
                return
        except Exception:
            continue


def _inject_html(page, html: str) -> None:
    page.wait_for_function(
        "() => !!(window.tinymce && tinymce.activeEditor && tinymce.activeEditor.initialized)",
        timeout=15000,
    )
    page.wait_for_timeout(1500)

    for attempt in range(4):
        _dismiss_restore_popup(page)
        page.evaluate("(content) => tinymce.activeEditor.setContent(content)", html)
        page.wait_for_timeout(2000)

        current = page.evaluate("() => tinymce.activeEditor.getContent()")
        if current and len(current) > 200:
            page.evaluate("() => tinymce.activeEditor.save()")
            page.wait_for_timeout(500)
            print(f"  [본문 주입] 성공 ({len(current)}자)")
            return
        print(f"  [본문 주입] 시도 {attempt + 1}: 비어있음, 재시도")
        page.wait_for_timeout(1500)

    raise RuntimeError("본문 주입 실패 -- TinyMCE에 내용이 들어가지 않음")


def _set_tags(page, tags: list[str]) -> None:
    if not tags:
        return
    try:
        tag_input = page.locator("input[placeholder*='태그']").first
        if not tag_input.is_visible(timeout=2000):
            return
        for tag in tags[:8]:
            tag_input.click()
            tag_input.fill(tag)
            page.keyboard.press("Enter")
            page.wait_for_timeout(300)
        print(f"  [태그] {', '.join(tags[:8])}")
    except Exception:
        pass


def _set_category(page, category: str) -> None:
    try:
        page.get_by_role("combobox", name="카테고리 선택").click(timeout=3000)
        page.wait_for_timeout(300)
        page.get_by_role("option", name=category).click(timeout=3000)
    except Exception:
        pass


def _publish(page, alerts: list[str]) -> str:
    page.evaluate("() => tinymce.activeEditor.save()")
    page.wait_for_timeout(500)
    final = page.evaluate("() => tinymce.activeEditor.getContent()")
    print(f"  [발행 직전 본문] {len(final or '')}자")

    old_url = _latest_post_url()

    page.click("#publish-layer-btn", timeout=5000)
    page.wait_for_selector("#publish-btn", timeout=10000)
    page.wait_for_timeout(1000)

    try:
        page.locator("input[type='radio'][value='20']").check(force=True, timeout=3000)
        page.wait_for_timeout(300)
    except Exception:
        try:
            page.get_by_role("radio", name=re.compile(r"^공개$")).check(force=True, timeout=3000)
            page.wait_for_timeout(300)
        except Exception:
            pass

    selected = page.evaluate(
        "() => document.querySelector('input[type=radio][name=\"visibility\"]:checked')?.value "
        "?? document.querySelector('input[type=radio]:checked')?.value"
    )
    print(f"  [공개 설정] visibility={selected}")
    if selected != "20":
        raise RuntimeError(f"공개 라디오 선택 실패 — visibility={selected} (20=공개)")

    publish_btn = page.locator("#publish-btn")
    publish_btn.scroll_into_view_if_needed()
    box = publish_btn.bounding_box()
    if box:
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        page.mouse.move(cx, cy)
        page.wait_for_timeout(200)
        page.mouse.down()
        page.wait_for_timeout(80)
        page.mouse.up()
    else:
        publish_btn.click(force=True, timeout=5000)

    page.wait_for_timeout(3000)
    if alerts:
        raise RuntimeError(f"티스토리 발행 거부 — alert: {alerts[-1]}")

    for _ in range(15):
        page.wait_for_timeout(3000)
        new_url = _latest_post_url()
        if new_url != old_url:
            return new_url
        if alerts:
            raise RuntimeError(f"티스토리 발행 거부 — alert: {alerts[-1]}")

    raise RuntimeError(f"발행 후 45초간 새 URL 미감지 — 티스토리 발행 실패 (직전 URL: {old_url})")


def _latest_post_url() -> str:
    try:
        rss_url = f"https://{BLOG_NAME}.tistory.com/rss"
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            rss = r.read().decode("utf-8")
        match = re.search(r"<guid[^>]*>(https://[^<]+tistory\.com/\d+)</guid>", rss)
        if match:
            return match.group(1)
        match = re.search(r"<link>(https://[^<]+tistory\.com/entry/[^<]+)</link>", rss)
        if match:
            return match.group(1)
    except Exception:
        pass
    return f"https://{BLOG_NAME}.tistory.com"


def _save_session(context) -> None:
    cookies = context.cookies()
    SESSION_FILE.write_text(json.dumps(cookies, ensure_ascii=False), encoding="utf-8")
