import json
import re
import subprocess

from modules.news_fetcher import fetch_latest_news, build_news_block

CLAUDE_PATH = r"C:\Users\hwang\AppData\Roaming\npm\claude.cmd"

PROMPT_TEMPLATE = """당신은 한국 증시 전문 애널리스트이자 투자 정보 블로거입니다.
독자: 국내 개인 투자자 (주식 초중급자)

[오늘의 키워드]
{keyword} (구글 트렌드 비즈니스·금융 카테고리 {rank}위, {geo_label})

[최신 뉴스]
{news_block}

위 뉴스를 분석하여 아래 구분자 형식으로 정확히 응답하세요 (구분자 외 다른 텍스트 없이):

===TITLE===
SEO 최적화 제목 (핵심 키워드 포함, 호기심 유발, 55자 이내)
===MARKDOWN===
전체 마크다운 글 (2000~3000자, 아래 구조 참고)
===SNS===
SNS 요약 (아래 형식 참고, 270자 이내)
===TAGS===
티스토리 태그 (쉼표 구분, 5~8개, 예: 삼성전자,반도체,코스피,주식투자)

--- 글 구조 (순서 유지) ---
## 오늘의 핵심 이슈
(키워드가 오늘 주목받는 배경과 뉴스 핵심 요약, 2~3문장)

## 뉴스 심층 분석
(제공된 뉴스를 바탕으로 사안의 맥락·의미·파급력 분석, 구체적 수치와 근거 포함)

[한국 증시와 실질적 연관이 있을 경우에만 아래 두 섹션 포함]
## 한국 증시 영향 분석
(코스피·코스닥 연관 섹터, 수혜·피해 종목 방향성, 외국인·기관 수급 흐름 예상)

## 투자 대응 전략
(개인 투자자 단기/중기 대응 방안, 리스크 관리 포인트)

[한국 증시와 연관성이 희박할 경우 위 두 섹션 대신 아래 섹션만 포함]
## 글로벌 시장 영향
(미국·유럽·아시아 시장 파급 효과, 글로벌 투자자 관점 정리)

## 핵심 체크리스트
(투자 전 반드시 확인할 3~5가지 포인트, 불릿 형식)

## 자주 묻는 질문 (FAQ)
(이 뉴스·키워드에 대한 독자 예상 질문 3개와 명확한 답변)

--- sns_summary 형식 ---
[{keyword}] 오늘의 핵심 뉴스 분석 📈
{sns_body}
#증시분석 #한국주식 #투자정보 #{keyword_tag}

--- 작성 규칙 ---
- 한국 증시 관련성 판단 기준: 해당 뉴스가 코스피·코스닥·환율·국내 기업 실적·외국인 수급에
  직접 또는 간접적으로 영향을 줄 수 있으면 "관련 있음"으로 판단
- 제공된 뉴스 외 불확실한 수치는 "약", "전후" 표현 사용
- 핵심 단어 **굵게**, 리스트 적극 활용
- 총 분량: 2000~3000자 (공백 포함)
"""


def generate_content(trend: dict) -> dict:
    keyword = trend["keyword"]
    rank = trend.get("rank", 1)
    geo = trend.get("geo", "KR")
    geo_label = "국내" if geo == "KR" else "글로벌"
    keyword_tag = _to_tag(keyword)

    print(f"  뉴스 수집 중: {keyword}")
    news_items = fetch_latest_news(keyword, max_count=5)
    if not news_items:
        raise ValueError(f"뉴스 없음 — 발행 건너뜀: {keyword}")

    news_block = build_news_block(news_items)
    sns_body = f"{keyword} 관련 최신 뉴스와 한국 증시 영향을 정리했습니다."

    prompt = PROMPT_TEMPLATE.format(
        keyword=keyword,
        rank=rank,
        geo_label=geo_label,
        news_block=news_block,
        sns_body=sns_body,
        keyword_tag=keyword_tag,
    )

    raw = _call_claude(prompt)
    return _parse_response(raw, keyword)



def _call_claude(prompt: str) -> str:
    result = subprocess.run(
        [CLAUDE_PATH, "-p", "--output-format", "json"],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI 오류: {result.stderr[:300]}")
    return result.stdout


def _parse_response(raw: str, keyword: str) -> dict:
    try:
        outer = json.loads(raw)
        output = outer.get("result") or outer.get("content") or raw
    except Exception:
        output = raw

    title = _extract_section(output, "TITLE") or f"{keyword} 한국 증시 대응 전략"
    markdown = _extract_section(output, "MARKDOWN") or ""
    sns_summary = _extract_section(output, "SNS") or f"{keyword} 증시 분석 #증시분석 #한국주식"
    tags_raw = _extract_section(output, "TAGS")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

    if not markdown:
        raise ValueError(f"본문 파싱 실패 -- 키워드: {keyword}")

    return {"title": title, "markdown": markdown, "sns_summary": sns_summary, "tags": tags}


def _extract_section(text: str, key: str) -> str:
    marker = f"==={key}==="
    start = text.find(marker)
    if start == -1:
        return ""
    start += len(marker)
    markers = ["===TITLE===", "===MARKDOWN===", "===SNS===", "===TAGS==="]
    end = len(text)
    for m in markers:
        pos = text.find(m, start)
        if pos != -1 and pos < end:
            end = pos
    return text[start:end].strip()


def _to_tag(keyword: str) -> str:
    return re.sub(r"[\s/·()\[\]]", "", keyword)
