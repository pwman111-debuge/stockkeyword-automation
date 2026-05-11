import json
import os
import re
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / ".env"
ENABLED = os.environ.get("THREADS_ENABLED", "True").lower() == "true"


def post_to_threads(summary: str, post_url: str) -> bool:
    if not ENABLED:
        return False

    user_id = os.environ.get("THREADS_USER_ID", "")
    token = os.environ.get("THREADS_ACCESS_TOKEN", "")

    if not user_id or not token:
        print("  [Threads] THREADS_USER_ID, THREADS_ACCESS_TOKEN 미설정 -- 건너뜀")
        return False

    token = _refresh_token(token)
    clean = _clean_summary(summary)
    text = f"{clean}\n\n{post_url}"
    if len(text) > 490:
        text = text[:487] + "..."

    for attempt in range(3):
        try:
            post_id = _publish(user_id, token, text)
            return bool(post_id)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code >= 500 and attempt < 2:
                print(f"  [Threads] HTTP {e.code} -- 15초 후 재시도 ({attempt + 1}/2)")
                time.sleep(15)
                continue
            print(f"  [Threads] 포스팅 실패: HTTP {e.code} {body}")
            return False
        except Exception as e:
            print(f"  [Threads] 포스팅 실패: {e}")
            return False
    return False


def _clean_summary(text: str) -> str:
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[Image #\d+\]', '', text)
    text = re.sub(r'\[이미지 #?\d*\]', '', text)
    text = re.sub(r' {2,}', ' ', text).strip()
    return text


def _refresh_token(token: str) -> str:
    url = "https://graph.threads.net/refresh_access_token"
    params = {"grant_type": "th_refresh_token", "access_token": token}
    req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}")
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode("utf-8"))
        new_token = data["access_token"]
        _save_token_to_env("THREADS_ACCESS_TOKEN", new_token)
        return new_token
    except Exception:
        return token


def _publish(user_id: str, token: str, text: str) -> str:
    image_url = "https://raw.githubusercontent.com/pwman111-debuge/solo-founder/master/tistory-automation/config/profile.jpg"
    url1 = f"https://graph.threads.net/v1.0/{user_id}/threads"

    creation_id = None
    params_image = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "text": text,
        "access_token": token,
    }
    data_image = urllib.parse.urlencode(params_image).encode("utf-8")
    req_image = urllib.request.Request(url1, data=data_image, method="POST")
    req_image.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req_image) as r:
            result_image = json.loads(r.read().decode("utf-8"))
        creation_id = result_image.get("id")
    except urllib.error.HTTPError:
        pass

    if not creation_id:
        params1 = {
            "media_type": "TEXT",
            "text": text,
            "access_token": token,
        }
        data1 = urllib.parse.urlencode(params1).encode("utf-8")
        req1 = urllib.request.Request(url1, data=data1, method="POST")
        req1.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req1) as r:
            result1 = json.loads(r.read().decode("utf-8"))
        creation_id = result1.get("id")

    if not creation_id:
        raise RuntimeError("컨테이너 생성 실패")

    time.sleep(2)

    url2 = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
    params2 = {"creation_id": creation_id, "access_token": token}
    data2 = urllib.parse.urlencode(params2).encode("utf-8")
    req2 = urllib.request.Request(url2, data=data2, method="POST")
    req2.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req2) as r:
        result2 = json.loads(r.read().decode("utf-8"))

    return result2.get("id", "")


def _save_token_to_env(key: str, value: str) -> None:
    if not ENV_PATH.exists():
        return
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    updated = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            updated.append(f"{key}={value}\n")
        else:
            updated.append(line)
    ENV_PATH.write_text("".join(updated), encoding="utf-8")
