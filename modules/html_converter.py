import re

from markdown_it import MarkdownIt

md = MarkdownIt()

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


def convert_to_html(markdown_text: str) -> str:
    body_html = md.render(markdown_text)

    body_html = _style_summary_box(body_html)

    parts = body_html.split("</h2>", 1)
    if len(parts) == 2:
        body_html = parts[0] + "</h2>" + _build_ad_slot("ad-top") + parts[1]
    else:
        body_html = _build_ad_slot("ad-top") + body_html

    disclaimer = _build_disclaimer()
    body_html = body_html + _build_ad_slot("ad-bottom") + disclaimer

    return f'<div style="{WRAPPER_STYLE}">{body_html}</div>'


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
