"""AI 소식 수집 → 선택 → 카드뉴스 CLI.

  python3 ainews/ainews.py collect               # 전체 수집 → ainews/db/aifield.db (중복은 건너뜀)
  python3 ainews/ainews.py list [--days 7] [--min-level 3] [--source 이름]
  python3 ainews/ainews.py make 12,34,56,78      # 고른 소식 → 원문 수집 → (Gemini) cards.json → PNG·캡션
  python3 ainews/ainews.py render <폴더>          # cards.json 손본 뒤 다시 그리기
"""
import argparse
import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # 수집기가 import 시점에 키를 읽으므로 먼저

from collectors import fetch_all  # noqa: E402
from db.news_store import NewsStore  # noqa: E402
import cards  # noqa: E402

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "aiona-ainews/1.0 (AI news aggregator)"}
# gemini-2.5-flash는 2026-11 기준 신규 키에 404 ("no longer available to new users").
# 앞 모델이 503(수요 폭주)·429·시간 초과면 다음 모델로 넘어간다.
GEMINI_MODELS = [m for m in [os.getenv("GEMINI_MODEL"), "gemini-3.8-flash", "gemini-3.5-flash"] if m]
CAPTION_FOOTER = "\n\n📌  저장해 두면 나중에 다시 보기 편해요 :)\n👉  AI 소식 놓치지 않으려면? @aiona_ai 팔로우"

PROMPT = """너는 인스타그램 카드뉴스 'AIONA AI 뉴스'의 에디터다. 아래 기사 원문만 근거로 카드 문구를 쓴다.
규칙:
- 원문에 없는 사실·숫자·날짜는 절대 쓰지 않는다. 불확실하면 뺀다.
- 한국어. 고유명사(모델명·회사명)는 원문 표기 그대로.
- 소식 순서는 입력 순서 그대로, 개수도 그대로.
- 날짜는 그 소식 자체가 일어난 날만 쓴다 (글 작성일과 발표일이 다르면 무엇의 날짜인지 밝힌다).
- 여러 금액을 합친 숫자는 무엇을 합쳤는지 함께 쓴다 (예: '사모 포함').
- caption은 처음부터 끝까지 해요체(~했어요)로 통일한다.
JSON 하나만 출력한다:
{
 "cover": {"line1": "이번 주 AI 뉴스,", "line2": "N가지만 보면 끝"},
 "news": [{
   "short": "목록용 한 줄, 18자 이내 명사형 (예: GPT-6.2 Astra 공개)",
   "title": ["1~2줄, 줄당 12자 이내", "핵심어 하나만 [대괄호]로 감싼다"],
   "points": ["2~3개, 각 24자 이내, 명사형으로 끝"],
   "note": "원문에 날짜가 있을 때만 '11월 17일 공개'처럼 30자 이내, 없으면 빈 문자열",
   "stat": "원문에 있는 가장 눈에 띄는 숫자 하나: {\\"label\\": 15자 이내, \\"value\\": 7자 이내(예: -20%, 450/450, +17%), \\"desc\\": 40자 이내}. 없으면 null"
 }],
 "caption": "첫 줄 '\\"이번 주 AI 뉴스, N가지만 보면 끝\\" 📰', 빈 줄, 도입 한 문장, 소식마다 1~2문장 문단(해요체), 마지막 줄 '카드뉴스를 넘겨 자세한 내용을 확인해보세요.'"
}"""


def collect(store):
    items = asyncio.run(fetch_all())
    new = [it for it in items if store.save(it)]
    print(f"\n수집 {len(items)}건 / 새로 저장 {len(new)}건")
    for src, n in Counter(it.source for it in new).most_common():
        print(f"  {n:3}  {src}")


def show(store, days, min_level, source):
    rows = store.list_recent(days=days, min_level=min_level, limit=1000)
    if source:
        rows = [r for r in rows if source.lower() in (r["source"] or "").lower()]
    for r in rows:
        at = datetime.fromisoformat(r["created_at"]).astimezone(KST).strftime("%m-%d %H:%M")
        print(f"{r['id']:5}  L{r['alert_level']}  {at}  {(r['source'] or '')[:18]:18}  {r['title'][:80]}")
    print(f"\n{len(rows)}건 (최근 {days}일, 레벨 {min_level} 이상)")


def article_text(url, limit=4000):
    """기사 본문 텍스트. 못 읽으면 빈 문자열 (JS로만 그리는 페이지 등)."""
    from bs4 import BeautifulSoup
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15).read()
    except Exception as e:
        print(f"  원문 못 읽음: {url} ({str(e)[:60]})")
        return ""
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    body = soup.find("article") or soup.find("main") or soup.body or soup
    return " ".join(body.get_text(" ").split())[:limit]


def gemini(sources):
    """sources를 Gemini에 보내 cards.json용 dict를 받는다."""
    key = os.environ["GEMINI_API_KEY"]
    req = {
        "systemInstruction": {"parts": [{"text": PROMPT}]},
        "contents": [{"parts": [{"text": json.dumps(sources, ensure_ascii=False)}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4},
    }
    for model in dict.fromkeys(GEMINI_MODELS):
        r = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=json.dumps(req).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
        for wait in (20, None):
            try:
                print(f"  Gemini 요약 중: {model}")
                resp = json.loads(urllib.request.urlopen(r, timeout=300).read())
                return json.loads(resp["candidates"][0]["content"]["parts"][0]["text"])
            except (urllib.error.HTTPError, TimeoutError) as e:
                code = getattr(e, "code", "시간 초과")
                if code not in (429, 503, "시간 초과"):
                    raise
                print(f"  {model}: {code}" + (f" — {wait}초 뒤 다시 시도" if wait else " — 다음 모델로"))
                if wait:
                    time.sleep(wait)
    raise RuntimeError(f"모든 Gemini 모델 실패: {GEMINI_MODELS}")


def make(store, ids):
    rows = store.get_by_ids(ids)
    out = ROOT / "aiona_cardnews" / f"ai_news_{datetime.now(KST):%Y%m%d_%H%M}"
    out.mkdir(parents=True, exist_ok=True)
    sources = []
    for r in rows:
        print(f"원문 읽는 중: [{r['id']}] {r['title'][:60]}")
        sources.append({"id": r["id"], "title": r["title"], "source": r["source"], "url": r["url"],
                        "summary": r["summary"] or "", "text": article_text(r["url"]) if r["url"] else ""})
    (out / "sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=1), encoding="utf-8")

    if not os.getenv("GEMINI_API_KEY"):
        print(f"\nGEMINI_API_KEY 없음 → {out}/sources.json 을 보고 cards.json 을 쓴 뒤:\n"
              f"  python3 ainews/ainews.py render {out}")
        return
    data = gemini(sources)
    (out / "cards.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    render_dir(out)


def render_dir(out):
    out = Path(out)
    data = json.loads((out / "cards.json").read_text(encoding="utf-8"))
    n = cards.render_all(data, out)
    (out / "caption.txt").write_text(data.get("caption", "").rstrip() + CAPTION_FOOTER, encoding="utf-8")
    srcs = out / "sources.json"
    if srcs.exists():  # 출처 표기·사실 확인용
        links = [f"{s['source']}: {s['url']}" for s in json.loads(srcs.read_text(encoding="utf-8"))]
        (out / "sources.txt").write_text("\n".join(links) + "\n", encoding="utf-8")
    print(f"카드 {n}장 + caption.txt 생성: {out}")
    print(f"게시 전 sources.txt의 원문과 숫자·날짜를 꼭 대조하세요 (AI 요약은 틀릴 수 있음).")


def main():
    p = argparse.ArgumentParser(description="AI 소식 수집 → 카드뉴스")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("collect", help="모든 소스에서 수집해 DB에 저장")
    ls = sub.add_parser("list", help="저장된 소식 목록")
    ls.add_argument("--days", type=int, default=7)
    ls.add_argument("--min-level", type=int, default=3)
    ls.add_argument("--source", help="출처 이름 일부 (예: gemini)")
    mk = sub.add_parser("make", help="고른 소식 번호(쉼표 구분)로 카드뉴스 만들기")
    mk.add_argument("ids", help="예: 12,34,56,78")
    rd = sub.add_parser("render", help="cards.json으로 카드 다시 그리기")
    rd.add_argument("dir")
    a = p.parse_args()

    store = NewsStore()
    if a.cmd == "collect":
        collect(store)
    elif a.cmd == "list":
        show(store, a.days, a.min_level, a.source)
    elif a.cmd == "make":
        ids = [int(x) for x in a.ids.split(",") if x.strip()]
        if not 1 <= len(ids) <= 6:
            p.error("소식은 1~6개 (보통 4~5개)")
        make(store, ids)
    else:
        render_dir(a.dir)


if __name__ == "__main__":
    main()
