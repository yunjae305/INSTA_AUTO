#!/usr/bin/env python3
"""ainews 신규 소식 → 텔레그램(@pasuin_bot) 실시간 건별 알림.

cron(5분마다 ainews.py collect 직후) 실행. DB에 새로 저장된 소식 중 주목할 것만
1건당 1메시지로 즉시 보낸다. 메시지 형식(사용자 지정):

    [AI 뉴스 알림]

    출처: {source}
    제목: {title}

    요약:
    {summary}

    원문 링크:
    {url}

  .venv/bin/python ainews/notify_telegram.py               # 신규분 발송
  .venv/bin/python ainews/notify_telegram.py --dry-run     # 전송 없이 메시지만 출력
  .venv/bin/python ainews/notify_telegram.py --test        # 최신 1건 테스트 발송(상태 유지)
  .venv/bin/python ainews/notify_telegram.py --min-level 3 # 임계값 임시 변경

설정(기본값은 .env 또는 셸 환경변수로 덮어쓴다):
  AINEWS_MIN_LEVEL=3     알림 임계값(alert_level). 4 = should_alert=1, 1 = 모든 새 글.
  AINEWS_MAX_PER_RUN=5   한 번(5분)에 건별로 보내는 최대 건수. 나머지는 한 줄 요약.
  AINEWS_OVERFLOW=1      한도 초과분을 한 줄("그 외 N건")로 알릴지 여부(0이면 조용히 생략).
  AINEWS_SUMMARY_LIMIT=450  요약 본문 최대 글자수.
  AINEWS_SKIP_SOURCES="HF Daily Papers"  실시간 알림에서 뺄 출처(쉼표 구분, DB 저장은 유지).

자격증명·chat_id는 저장소 루트 .env(.gitignore 등록). 발송 상태는 저장소 밖
(~/.ainews_notify_state.json)에 남긴다.
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHAT_ID=...
"""

import argparse
import html
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB_PATH = HERE / "db" / "aifield.db"
ENV_PATH = ROOT / ".env"
# 상태 파일은 저장소 밖에 둔다(공개 저장소에 딸려 들어가지 않게).
STATE_PATH = ROOT.parent / ".ainews_notify_state.json"

DEFAULTS = {
    "min_level": 3,      # alert_level >= 3 (레벨4+는 should_alert). 1이면 모든 새 글
    "max_per_run": 5,    # 5분당 건별 메시지 상한(알림 폭탄 방지)
    "overflow": 1,       # 한도 초과분을 한 줄로 알림
    "summary_limit": 450,
    "skip_sources": "HF Daily Papers",  # 학술 논문 일괄 묶음은 알림에서 뺌(DB 저장은 유지)
}
TELEGRAM_TEXT_LIMIT = 3900  # API 한도 4096자, 여유
OVERFLOW_TITLE_LIMIT = 48   # 초과분 한 줄에 넣을 제목 길이
# 목록·네비게이션 페이지에서 긁힌 제목("Features", "News" 등)은 알리지 않는다.
GENERIC_TITLES = {
    "features", "feature", "announcements", "announcement", "news", "blog",
    "press", "home", "about", "products", "product", "research", "index",
}


# ---------------------------------------------------------------- 환경변수
def load_env(path: Path) -> None:
    """.env 를 읽어 환경변수로 올린다. 이미 있는 값(실환경변수)이 우선."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def env_int(name: str, default: int) -> int:
    try:
        return int(str(os.getenv(name, "")).strip())
    except ValueError:
        return default


# ---------------------------------------------------------------- 상태 파일
def read_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_state(data: dict) -> None:
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATE_PATH)


# ---------------------------------------------------------------- DB 조회
def connect(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise SystemExit(f"DB가 없습니다: {path} (먼저 ainews.py collect 실행)")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def scalar(conn: sqlite3.Connection, sql: str, args: tuple = ()):
    row = conn.execute(sql, args).fetchone()
    return row[0] if row else None


def fetch_after(conn: sqlite3.Connection, after_id: int) -> list[dict]:
    return [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM news WHERE id > ? ORDER BY alert_level DESC, id ASC", (after_id,)
        ).fetchall()
    ]


# ---------------------------------------------------------------- 메시지
_META_LINE = re.compile(
    r"^(?:"
    r"points?\s*:?\s*[\d,]+\s*(?:\|\s*comments?\s*:?\s*[\d,]+)?"
    r"|comments?\s*:?\s*[\d,]+"
    r"|추천\s*[\d,]+"
    r"|votes?\s*:?\s*[\d,]+"
    r")\s*$",
    re.IGNORECASE,
)
_TAIL_NOISE = re.compile(r"(?:\s*\[\s*(?:…|\.\.\.|&#8230;)\s*\]|\s*\[\s*…\s*\])\s*$")


def _squeeze(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def clean_summary(raw: str, limit: int) -> str:
    """DB summary 정제 — 메타데이터 줄(Points/추천) 제거, 공백 정리, 길이 제한.

    원문에 없는 내용은 만들지 않는다. 쓸 만한 본문이 없으면 빈 문자열.
    """
    if not raw:
        return ""
    text = html.unescape(str(raw))
    lines = [ln.strip() for ln in text.splitlines()]
    while lines and (not lines[0] or _META_LINE.match(lines[0])):
        lines.pop(0)
    body = _squeeze(" ".join(lines))
    body = _TAIL_NOISE.sub("", body).strip()
    body = _squeeze(body)
    if len(body) < 25:          # "Points: 2" 같은 잔여 메타만 남은 경우
        return ""
    if len(body) > limit:
        cut = body[:limit]
        if " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        body = cut.rstrip(" ,;:·-—") + "…"
    return body


def is_generic(row: dict) -> bool:
    title = _squeeze(row.get("title")).lower()
    return title in GENERIC_TITLES


def item_message(row: dict, summary_limit: int) -> str:
    lines = [
        "[AI 뉴스 알림]",
        "",
        f"출처: {_squeeze(row.get('source')) or '출처 미상'}",
        f"제목: {_squeeze(row.get('title')) or '(제목 없음)'}",
    ]
    summary = clean_summary(row.get("summary") or "", summary_limit)
    if summary:
        lines += ["", "요약:", summary]
    url = (row.get("url") or "").strip()
    if url:
        lines += ["", "원문 링크:", url]
    return "\n".join(lines)


def overflow_message(rows: list[dict], total_new: int, min_level: int) -> str:
    parts = []
    for r in rows:
        title = _squeeze(r.get("title"))
        if len(title) > OVERFLOW_TITLE_LIMIT:
            title = title[: OVERFLOW_TITLE_LIMIT - 1].rstrip() + "…"
        src = _squeeze(r.get("source")) or "?"
        parts.append(f"· {title} ({src})")
    head = f"📎 그 외 신규 주목 소식 {len(rows)}건 (L{min_level}+, 메시지 한도 초과)"
    text = head + "\n" + "\n".join(parts)
    if len(text) > TELEGRAM_TEXT_LIMIT:
        text = text[: TELEGRAM_TEXT_LIMIT - 30].rstrip() + "\n… (이하 생략)"
    return text


# ---------------------------------------------------------------- 전송
def send(token: str, chat_id: str, text: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    ).encode("utf-8")
    last = None
    for attempt in range(1, 4):
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body)
            except ValueError:
                parsed = {}
            last = f"HTTP {exc.code}: {body[:300]}"
            retry_after = (parsed.get("parameters") or {}).get("retry_after")
            if exc.code == 429 and retry_after:
                time.sleep(min(int(retry_after), 60))
                continue
            if exc.code >= 500:
                time.sleep(3 * attempt)
                continue
            break
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(3 * attempt)
    raise RuntimeError(f"텔레그램 전송 실패: {last}")


def stamp() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")


def rotate_log(path: Path, limit: int = 5_000_000, keep: int = 2000) -> None:
    """5분 주기로 쌓이는 collect.log 가 커지면 뒤쪽 keep 줄만 남긴다.

    cron 이 `>>`(O_APPEND)로 쓰므로 잘라도 이어쓰기에 지장이 없다.
    """
    try:
        if path.stat().st_size <= limit:
            return
        tail = path.read_text(encoding="utf-8", errors="replace").splitlines()[-keep:]
        path.write_text("\n".join(tail) + "\n", encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------- 실행
def run(args, cfg, token, chat_id, conn) -> int:
    state = read_state()

    # ── 테스트: 최신 주목 1건을 상태 변화 없이 발송
    if args.test:
        level = args.min_level if args.min_level is not None else cfg["min_level"]
        row = conn.execute(
            "SELECT * FROM news WHERE alert_level >= ? ORDER BY id DESC LIMIT 1", (level,)
        ).fetchone()
        if not row:
            print(f"[{stamp()}] --test: alert_level >= {level} 인 소식이 없습니다")
            return 1
        text = item_message(dict(row), cfg["summary_limit"])
        print(f"[{stamp()}] TEST id={row['id']} L{row['alert_level']} {row['source']}")
        print("--- TEST MESSAGE ---")
        print(text)
        if args.dry_run:
            return 0
        result = send(token, chat_id, text)
        if not result.get("ok"):
            raise SystemExit(f"텔레그램 응답 실패: {json.dumps(result, ensure_ascii=False)[:300]}")
        msg = result.get("result") or {}
        print(f"전송 OK: ok=True message_id={msg.get('message_id')} chat={msg.get('chat', {}).get('username') or chat_id}")
        print("(상태 파일은 건드리지 않았습니다)")
        return 0

    # ── 기준선: 상태 파일에 last_id 가 없으면 지금까지 저장된 건은 보내지 않는다
    last_id = state.get("last_id")
    if not isinstance(last_id, int):
        last_id = int(scalar(conn, "SELECT COALESCE(MAX(id), 0) FROM news") or 0)
        state.update({
            "schema": 2,
            "last_id": last_id,
            "baseline_set_at": datetime.now(timezone.utc).isoformat(),
        })
        if not args.dry_run:
            write_state(state)
        print(f"[{stamp()}] 기준선 설정: last_id={last_id} (기존 저장분은 발송하지 않음)")
        return 0

    min_level = args.min_level if args.min_level is not None else cfg["min_level"]
    max_per_run = max(0, args.max_per_run if args.max_per_run is not None else cfg["max_per_run"])
    skip_sources = {
        s.strip().lower() for s in str(cfg.get("skip_sources") or "").split(",") if s.strip()
    }

    new_rows = fetch_after(conn, last_id)
    total_new = len(new_rows)
    if total_new == 0:
        print(f"[{stamp()}] 신규 0건 (last_id={last_id})")
        return 0

    new_max_id = max(r["id"] for r in new_rows)
    candidates = [
        r for r in new_rows
        if int(r.get("alert_level") or 0) >= min_level
        and _squeeze(r.get("source")).lower() not in skip_sources
        and not is_generic(r)
    ]

    print(
        f"[{stamp()}] 신규 {total_new}건 (id>{last_id}) · 기준 L{min_level}+ "
        f"{len(candidates)}건"
        + (f" · 제외 출처: {', '.join(sorted(skip_sources))}" if skip_sources else "")
    )

    if not candidates:
        write_state({
            "schema": 2,
            "last_id": new_max_id,
            "last_sent_at": datetime.now(timezone.utc).isoformat(),
            "last_new_count": total_new,
            "last_alert_count": 0,
        })
        return 0

    picked, skipped = candidates[:max_per_run], candidates[max_per_run:]

    sent = 0
    last_ok_id = last_id
    for row in picked:
        text = item_message(row, cfg["summary_limit"])
        if args.dry_run:
            print(f"--- {row['id']} L{row['alert_level']} ---")
            print(text)
            sent += 1
            last_ok_id = row["id"]
            continue
        try:
            result = send(token, chat_id, text)
        except RuntimeError as exc:
            print(f"  발송 실패 id={row['id']}: {exc}")
            break
        if not result.get("ok"):
            print(f"  발송 실패 id={row['id']}: {json.dumps(result, ensure_ascii=False)[:200]}")
            break
        msg = result.get("result") or {}
        print(
            f"  발송 OK id={row['id']} L{row['alert_level']} "
            f"message_id={msg.get('message_id')} · {_squeeze(row.get('title'))[:50]}"
        )
        sent += 1
        last_ok_id = row["id"]
        time.sleep(1)  # 같은 채팅에 연속 발송 — 텔레그램 rate limit 여유

    overflow_notified = 0
    all_sent = sent == len(picked)
    if all_sent:
        last_ok_id = new_max_id  # 필터·한도로 건너뛴 항목까지 처리 완료로 표시
        if skipped and cfg["overflow"]:
            text = overflow_message(skipped, total_new, min_level)
            if args.dry_run:
                print("--- OVERFLOW ---")
                print(text)
                overflow_notified = len(skipped)
            else:
                try:
                    result = send(token, chat_id, text)
                    if result.get("ok"):
                        overflow_notified = len(skipped)
                except RuntimeError as exc:
                    print(f"  초과분 요약 발송 실패: {exc}")

    if args.dry_run:
        print(f"[DRY RUN] {sent}건 / 초과 {len(skipped)}건 · 상태 파일 변경 없음")
        return 0

    state.update({
        "schema": 2,
        "last_id": last_ok_id,
        "last_sent_at": datetime.now(timezone.utc).isoformat(),
        "last_new_count": total_new,
        "last_alert_count": sent,
        "last_overflow": overflow_notified,
        "sent_total": int(state.get("sent_total") or 0) + sent,
    })
    write_state(state)
    print(
        f"[{stamp()}] 완료: 건별 {sent}건 · 초과 {len(skipped)}건"
        f"(한 줄 알림 {overflow_notified}건) · last_id={last_ok_id}"
    )
    return 0 if all_sent else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="ainews 신규 소식 실시간 텔레그램 알림")
    ap.add_argument("--dry-run", action="store_true", help="전송하지 않고 메시지만 출력")
    ap.add_argument("--test", action="store_true", help="최신 1건 테스트 발송(상태 유지)")
    ap.add_argument("--min-level", type=int, default=None, help="알림 임계값 alert_level")
    ap.add_argument("--max-per-run", type=int, default=None, help="5분당 건별 발송 상한")
    args = ap.parse_args()

    load_env(ENV_PATH)
    rotate_log(HERE / "collect.log")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise SystemExit(f"TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 가 없습니다 ({ENV_PATH})")

    cfg = {
        "min_level": env_int("AINEWS_MIN_LEVEL", DEFAULTS["min_level"]),
        "max_per_run": env_int("AINEWS_MAX_PER_RUN", DEFAULTS["max_per_run"]),
        "overflow": env_int("AINEWS_OVERFLOW", DEFAULTS["overflow"]),
        "summary_limit": env_int("AINEWS_SUMMARY_LIMIT", DEFAULTS["summary_limit"]),
        "skip_sources": os.getenv("AINEWS_SKIP_SOURCES", DEFAULTS["skip_sources"]),
    }

    conn = connect(DB_PATH)
    try:
        return run(args, cfg, token, chat_id, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
