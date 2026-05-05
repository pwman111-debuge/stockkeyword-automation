# 호칭 규칙

- 황원장님은 나(Claude Code)를 **우팀장**이라고 부른다.
- 나(Claude Code)는 사용자를 **황원장님**이라고 부른다.

---

# 프로젝트 개요

**증시키워드분석 티스토리 블로그 자동화 — 월 수익 1,000만원 달성**

- 구글 트렌드 급상승 증시 키워드 1~3위를 매일 수집
- 각 키워드별 한국 증시 대응 방안 블로그 글 1편씩 → 하루 3편 자동 발행
- 수익 구조: 애드센스 + 애드핏

### 핵심 채널
- 티스토리 블로그: 증시키워드분석 블로그
- SNS: Threads + LinkedIn 자동 포스팅

### 수익화 전략
- 구글 트렌드 급상승 증시 키워드 타게팅 → SEO 트래픽 유입
- 일 3편 반자동 발행 (황원장님 트리거 → 자동 실행)
- 애드센스/애드핏 광고 수익

---

# 운영 방식

- **반자동 트리거**: 황원장님이 `run.bat` 더블클릭 → 자동 실행
- **대화 트리거**: 황원장님이 "포스팅하자" 한 마디 → 우팀장이 즉시 `python post_stock.py` 실행
- 황원장님 일일 투자 시간: **5~8분** (트리거 + 검수)

---

# 기술 스택

| 역할 | 도구 |
|------|------|
| 트렌드 수집 | Google Trends RSS (urllib, xml) + pytrends 폴백 |
| 콘텐츠 생성 | Claude Code CLI (`claude -p`, Max×5 구독 내 처리) |
| 포맷 변환 | markdown-it-py → 티스토리 HTML |
| 자동 발행 | Playwright → 티스토리 |
| SNS 발행 | Threads Graph API + LinkedIn UGC Posts API |

---

# 프로젝트 폴더 구조

```
증시키워드자동화블로그/
├── CLAUDE.md
├── post_stock.py              ← 진입점
├── .env                        ← API 키, 계정 정보 (git 제외)
├── .env.example
├── requirements.txt
├── run.bat
├── modules/
│   ├── trend_picker.py         ← 구글 트렌드 수집 + 증시 필터링
│   ├── content_generator.py    ← Claude CLI로 글 생성
│   ├── html_converter.py       ← Markdown → HTML + 광고 슬롯
│   ├── tistory_poster.py       ← Playwright 발행
│   ├── threads_poster.py       ← Threads Graph API
│   └── linkedin_poster.py      ← LinkedIn UGC API
└── logs/
    ├── post_log.csv
    └── trend_log.csv
```

## 실행 명령어

```bash
# 기본 3편 발행 (트렌드 1~3위 각 1편씩)
python post_stock.py

# 발행 없이 콘텐츠 생성만 확인
python post_stock.py --dry-run

# 키워드 직접 지정 (강제 실행)
python post_stock.py --keyword "삼성전자 실적"
```

---

# 코드 규칙

- MUST: 변수/함수명은 명확하고 의미 있게 작성
- MUST NOT: 불필요한 주석 작성 금지
- MUST NOT: 요청 범위를 벗어난 추가 구현 금지

---

# 응답 스타일

- 답변은 간결하고 핵심만 전달
- 코드 참조 시 파일 경로와 라인 번호 함께 표기
- 불필요한 설명이나 반복 요약 금지
- "go!" 한 마디면 바로 실행 — 사전 설명 최소화

---

# 작업 경험 메모

## 티스토리 자동화
- 티스토리 OpenAPI 2014년 종료 → Playwright 브라우저 자동화로 대체
- 봇 감지 약함, 캡차 거의 없음 → 안정적 자동화 가능
- **티스토리 로그인**: `.env` 파일의 `TISTORY_EMAIL` / `TISTORY_PASSWORD` 확인 후 황원장님 승인 없이 자동 로그인 가능
- TinyMCE 에디터: `tinymce.activeEditor.setContent()` + `save()` 로 본문 주입
- 발행 후 URL: RSS 폴링(`/rss`)으로 새 포스트 URL 추출
- 카테고리 "증시분석"은 티스토리 블로그 `stockkeyword.tistory.com`에 생성 완료

## 구글 트렌드 수집
- RSS URL (변경됨): `https://trends.google.com/trending/rss?geo=KR` (구 URL `/trendingsearches/daily/rss` 404)
- pytrends 폴백 (429 오류 잦음 → RSS가 더 안정적)
- `logs/trend_log.csv`로 당일 사용 키워드 중복 방지

## 광고 승인
- 광고 슬롯은 빈 div로 준비
- 애드센스/애드핏 승인 후 `html_converter.py`의 `_build_ad_slot()` 반환값만 교체

## Claude Code CLI 콘텐츠 생성
- `claude -p --output-format json` + stdin으로 프롬프트 전달
- claude.cmd 경로: `C:\Users\hwang\AppData\Roaming\npm\claude.cmd`
- Max×5 구독 내 처리 — 별도 API 키 불필요
