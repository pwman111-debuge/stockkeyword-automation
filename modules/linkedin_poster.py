import json
import os
import re
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

ENABLED = os.environ.get("LINKEDIN_ENABLED", "True").lower() == "true"


def _clean_summary(text: str) -> str:
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[Image #\d+\]', '', text)
    text = re.sub(r'\[이미지 #?\d*\]', '', text)
    text = re.sub(r' {2,}', ' ', text).strip()
    return text


def post_to_linkedin(summary: str, post_url: str) -> bool:
    if not ENABLED:
        return False

    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
    person_urn = os.environ.get("LINKEDIN_PERSON_URN", "")

    if not token or not person_urn:
        print("  [LinkedIn] LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN 미설정 — 건너뜀")
        return False

    clean = _clean_summary(summary)
    text = f"{clean}\n\n🔗 {post_url}\n\n#증시분석 #한국주식 #투자정보 #코스피"
    if len(text) > 3000:
        text = text[:2997] + "..."

    try:
        asset_urn = _upload_logo(token, person_urn)
        post_urn = _publish(token, person_urn, text, asset_urn)
        return bool(post_urn)
    except Exception as e:
        print(f"  [LinkedIn] 포스팅 실패: {e}")
        return False


LOGO_URL = "https://tistory1.daumcdn.net/tistory/7681604/attach/44954c97172a4fc2b9e92b4bcf7764cd"


def _upload_logo(token: str, person_urn: str) -> str | None:
    try:
        req = urllib.request.Request(LOGO_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            image_bytes = r.read()
        return _upload_image(token, person_urn, image_bytes)
    except Exception as e:
        print(f"  [LinkedIn] 로고 업로드 실패: {e}")
        return None


def _upload_image(token: str, person_urn: str, image_bytes: bytes) -> str:
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": person_urn,
            "serviceRelationships": [
                {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
            ],
        }
    }

    req = urllib.request.Request(register_url, data=json.dumps(payload).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Restli-Protocol-Version", "2.0.0")

    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read().decode("utf-8"))

    upload_url = result["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset_urn = result["value"]["asset"]

    upload_req = urllib.request.Request(upload_url, data=image_bytes, method="PUT")
    upload_req.add_header("Authorization", f"Bearer {token}")
    upload_req.add_header("Content-Type", "image/png")

    try:
        with urllib.request.urlopen(upload_req):
            pass
    except urllib.error.HTTPError as e:
        if e.code not in (200, 201):
            raise

    time.sleep(2)
    return asset_urn


def _publish(token: str, person_urn: str, text: str, asset_urn: str | None = None) -> str:
    if asset_urn:
        media_category = "IMAGE"
        media = [{"status": "READY", "media": asset_urn}]
    else:
        media_category = "NONE"
        media = []

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": media_category,
                **({"media": media} if media else {}),
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    req = urllib.request.Request(
        "https://api.linkedin.com/v2/ugcPosts",
        data=json.dumps(payload).encode(),
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Restli-Protocol-Version", "2.0.0")

    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read().decode("utf-8"))

    return result.get("id", "")
