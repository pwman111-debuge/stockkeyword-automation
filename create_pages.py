"""
개인정보처리방침 + 문의하기 포스트 발행 스크립트.
기존 검증된 post_to_tistory()를 사용해 일반 포스트로 발행.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv(Path(__file__).parent / ".env")

from modules.tistory_poster import post_to_tistory

PAGES = [
    {
        "title": "개인정보처리방침",
        "html": """<div style="font-family:'Noto Sans KR',sans-serif;font-size:16px;line-height:1.85;color:#222;max-width:760px;margin:0 auto;">
<h1>개인정보처리방침</h1>
<p>본 블로그(stockkeyword.tistory.com)는 이용자의 개인정보를 소중히 여기며, 「개인정보 보호법」 등 관련 법령을 준수합니다.</p>

<h2>1. 수집하는 개인정보</h2>
<p>본 블로그는 댓글 작성 시 닉네임, 이메일 주소를 수집할 수 있습니다.</p>

<h2>2. 개인정보의 이용 목적</h2>
<p>수집된 개인정보는 댓글 관리 및 스팸 방지 목적으로만 사용되며, 제3자에게 제공하지 않습니다.</p>

<h2>3. 쿠키(Cookie) 사용</h2>
<p>본 블로그는 Google Analytics 및 Google AdSense를 통해 방문 통계 수집과 광고 게재 목적으로 쿠키를 사용합니다. 이용자는 브라우저 설정을 통해 쿠키 저장을 거부할 수 있습니다.</p>

<h2>4. 제3자 광고 서비스</h2>
<p>본 블로그는 Google AdSense를 통해 광고를 게재합니다. Google은 쿠키를 사용하여 이용자의 관심사에 맞는 광고를 표시할 수 있습니다.</p>
<p>자세한 내용은 <a href="https://policies.google.com/privacy" target="_blank">Google 개인정보처리방침</a>을 참고하세요.</p>

<h2>5. 개인정보 보호 책임자</h2>
<p>이메일: pwman111@gmail.com</p>

<h2>6. 시행일</h2>
<p>본 방침은 2026년 5월 5일부터 시행됩니다.</p>
</div>""",
    },
    {
        "title": "문의하기",
        "html": """<div style="font-family:'Noto Sans KR',sans-serif;font-size:16px;line-height:1.85;color:#222;max-width:760px;margin:0 auto;">
<h1>문의하기</h1>
<p>증시키워드분석 블로그에 오신 것을 환영합니다.</p>
<p>블로그 관련 문의, 광고 제안, 콘텐츠 오류 제보는 아래 이메일로 연락주세요.</p>

<p><strong>이메일: pwman111@gmail.com</strong></p>
<p>확인 후 2~3 영업일 내 답변드립니다.</p>

<hr/>
<h2>블로그 소개</h2>
<p>본 블로그는 내과 황원장이 운영하는 한국 증시 키워드 분석 블로그입니다.<br/>
구글 트렌드 급상승 키워드를 바탕으로 매일 증시 분석 콘텐츠를 발행합니다.</p>
<ul>
<li>구글 트렌드 상위 키워드 기반 실시간 증시 분석</li>
<li>삼성전자, SK하이닉스 등 주요 종목 심층 분석</li>
<li>개인 투자자를 위한 실전 대응 전략 제공</li>
</ul>
</div>""",
    },
]


def main():
    for pg in PAGES:
        print(f"\n발행 중: {pg['title']}")
        try:
            url = post_to_tistory(pg["title"], pg["html"])
            print(f"완료: {url}")
        except Exception as e:
            print(f"오류: {e}")

    print("\n=== 완료 ===")


if __name__ == "__main__":
    main()
