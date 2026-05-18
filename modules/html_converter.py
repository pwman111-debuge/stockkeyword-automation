import os
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.coupang_links import get_coupang_items_for_keyword

md = MarkdownIt()

COUPANG_ENABLED = os.environ.get("COUPANG_ENABLED", "False").lower() == "true"

WRAPPER_STYLE = (
    "font-family:'Noto Sans KR',Apple SD Gothic Neo,sans-serif;"
    "font-size:16px;line-height:1.85;color:#222;max-width:760px;margin:0 auto;"
)

SUMMARY_BOX_STYLE = (
    "background:#f0f7ff;border-left:4px solid #1a6fc4;"
    "padding:18px 22px;border-radius:6px;margin:24px 0;"
)

DISCLAIMER_STYLE = (
    "font-size:12px;color:#999;border-top:1px solid #eee;"
    "margin-top:48px;padding-top:12px;"
)

COUPANG_TOP_NOTICE_STYLE = (
    "font-size:14px;font-weight:bold;color:#c0392b;"
    "background:#fff3cd;border:1px solid #f0ad4e;border-radius:4px;"
    "padding:12px 16px;margin-bottom:24px;display:block;"
)


def convert_to_html(markdown_text: str, keyword: str | None = None) -> str:
    body_html = md.render(markdown_text)

    body_html = _style_summary_box(body_html)

    parts = body_html.split("</h2>", 1)
    if len(parts) == 2:
        body_html = parts[0] + "</h2>" + _build_ad_slot("ad-top") + parts[1]
    else:
        body_html = _build_ad_slot("ad-top") + body_html

    coupang_bottom = ""
    if COUPANG_ENABLED and keyword:
        products = get_coupang_items_for_keyword(keyword, limit=2)
        if products:
            coupang_bottom = _build_coupang_block(products[0])
            if len(products) >= 2:
                body_html = _inject_mid_coupang(body_html, _build_coupang_block(products[1]))

    disclaimer = _build_disclaimer()
    body_html = body_html + _build_ad_slot("ad-bottom") + coupang_bottom + disclaimer

    top_notice = (
        f'<p style="{COUPANG_TOP_NOTICE_STYLE}">'
        "[광고] 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
        "</p>"
    )
    return f'<div style="{WRAPPER_STYLE}">{top_notice}{body_html}</div>'


def _style_summary_box(html: str) -> str:
    pattern = r'(<h2[^>]*>.*?(?:오늘의 핵심|핵심 이슈|핵심 요약|개요).*?</h2>)(.*?)(?=<h2|$)'
    match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    if match:
        header = match.group(1)
        content = match.group(2)
        box = f'<div style="{SUMMARY_BOX_STYLE}">{header}{content}</div>'
        html = html[:match.start()] + box + html[match.end():]
    return html


def _build_ad_slot(slot_id: str) -> str:
    return (
        f'<div class="ad-slot" id="{slot_id}" '
        f'style="margin:28px 0;text-align:center;">'
        f'<!-- 광고 코드 삽입 예정 -->'
        f'</div>'
    )


def _build_disclaimer() -> str:
    return (
        f'<p style="{DISCLAIMER_STYLE}">'
        "⚠️ 본 글은 투자 참고용 정보이며, 특정 종목의 매수·매도를 권유하지 않습니다. "
        "투자 손실에 대한 책임은 투자자 본인에게 있으며, 투자 결정 전 전문가 상담을 권장합니다."
        "</p>"
    )


def _build_coupang_block(product: dict) -> str:
    notice = (
        '<p style="font-size:13px;color:#e74c3c;font-weight:bold;margin-bottom:10px;">'
        '* 이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.'
        '</p>'
    )

    if product.get("html_snippet"):
        desc_html = (
            f'<p style="font-size:14px;color:#444;margin:6px 0 12px 0;line-height:1.6;">'
            f'<strong>{product["name"]}</strong> — {product["desc"]}'
            f'</p>'
        )
        return (
            '<div style="border-top:1px solid #eee;margin-top:32px;padding-top:18px;">'
            f'{notice}{desc_html}{product["html_snippet"]}'
            '</div>'
        )

    image_html = ""
    if product.get("image_url"):
        image_html = (
            f'<img src="{product["image_url"]}" alt="{product["name"]}" '
            'style="width:80px;height:160px;object-fit:cover;'
            'border-radius:4px;flex-shrink:0;">'
        )
    text_block = (
        f'<strong style="font-size:15px;display:block;margin-bottom:4px;">{product["name"]}</strong>'
        f'<span style="font-size:13px;color:#666;display:block;margin-bottom:8px;">{product["desc"]}</span>'
        '<span style="font-size:11px;color:#e74c3c;">COUPANG</span>'
    )
    padding = "12px" if image_html else "0"
    inner = f'{image_html}<div style="padding-left:{padding}">{text_block}</div>'
    return (
        '<div style="border-top:1px solid #eee;margin-top:32px;padding-top:18px;">'
        f'{notice}'
        f'<a href="{product["url"]}" target="_blank" rel="noopener sponsored" referrerpolicy="unsafe-url" '
        'style="display:flex;align-items:center;background:#fff;border:1px solid #e0e0e0;'
        'border-radius:8px;padding:16px 20px;text-decoration:none;color:#333;max-width:420px;">'
        f'{inner}'
        '</a>'
        '</div>'
    )


def _inject_mid_coupang(html: str, card_html: str) -> str:
    positions = []
    start = 0
    while True:
        pos = html.find("<h2", start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1
    if len(positions) < 2:
        return html
    target = positions[len(positions) // 2]
    return html[:target] + card_html + html[target:]
