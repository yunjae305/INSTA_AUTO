"""
공식 AI 랩 블로그 RSS/Atom 수집기.

OpenAI, Anthropic, Google DeepMind, Meta AI, NVIDIA 공식 블로그의
최신 포스트를 피드로 수집한다. is_official=True / reliability=5 로 설정되므로
키워드 매칭 시 Level 4~5 즉시 알림으로 연결된다.
"""

import asyncio
import calendar
import re
import urllib.request
from datetime import datetime, timezone, timedelta

import aiohttp
import feedparser

from scorer import NewsItem

# (url, reliability)
# reliability=5: 순수 AI 랩 공식 블로그 → Level 5 즉시 알림 가능
# reliability=4: AI 관련 기술 블로그   → Level 4까지만 (Level 5 차단)
# reliability=3: 언론·뉴스레터·커뮤니티 → is_official=False
# 2026-11-23 ego-browser로 각 사이트에서 피드 링크를 찾고 feedparser로 읽히는 것만 넣음
_FEEDS: dict[str, tuple[str, int]] = {
    # AI 랩 공식
    "OpenAI Blog":      ("https://openai.com/news/rss.xml",                              5),
    "Google DeepMind":  ("https://deepmind.google/blog/rss.xml",                         5),
    "Google Gemini":    ("https://blog.google/products-and-platforms/products/gemini/rss/", 5),
    "Google AI":        ("https://blog.google/technology/ai/rss/",                       5),
    "Google Developers": ("https://developers.googleblog.com/rss/",                      5),
    "Google Research":  ("https://research.google/blog/rss/",                            4),
    "Mistral":          ("https://mistral.ai/news/rss",                                  5),
    "Qwen":             ("https://qwenlm.github.io/blog/index.xml",                      5),
    # AI 기업 공식
    "HuggingFace Blog": ("https://huggingface.co/blog/feed.xml",                         4),
    "NVIDIA AI Blog":   ("https://blogs.nvidia.com/feed/",                               4),  # deep-learning 카테고리 피드는 10월 이후 멈춤
    "Meta Engineering": ("https://engineering.fb.com/feed/",                             4),
    "Apple ML":         ("https://machinelearning.apple.com/rss.xml",                    4),
    "Amazon Science":   ("https://www.amazon.science/index.rss",                         4),
    "AWS ML Blog":      ("https://aws.amazon.com/blogs/machine-learning/feed/",          4),
    "Stability AI":     ("https://stability.ai/news-updates?format=rss",                 4),
    "Together AI":      ("https://www.together.ai/blog/rss.xml",                         4),
    "ElevenLabs":       ("https://elevenlabs.io/blog/rss.xml",                           4),
    "Databricks":       ("https://www.databricks.com/feed",                              4),
    "Ollama":           ("https://ollama.com/blog/rss.xml",                              4),
    "GitHub AI":        ("https://github.blog/ai-and-ml/feed/",                          4),
    "Kakao Tech":       ("https://tech.kakao.com/feed/",                                 4),
    "Naver D2":         ("https://d2.naver.com/d2.atom",                                 4),
    # 모델 평가·연구 기관
    "Epoch AI":         ("https://epoch.ai/atom.xml",                                    4),
    "METR":             ("https://metr.org/feed.xml",                                    4),
    "ARC Prize":        ("https://arcprize.org/feed.xml",                                4),
    "Aider Leaderboard": ("https://aider.chat/feed.xml",                                 4),
    # 언론·뉴스레터·커뮤니티
    "The Verge AI":     ("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", 3),
    "MIT Tech Review AI": ("https://www.technologyreview.com/topic/artificial-intelligence/feed", 3),
    "Ars Technica AI":  ("https://arstechnica.com/ai/feed/",                             3),
    "AI타임스":          ("https://www.aitimes.com/rss/allArticle.xml",                   3),
    "GeekNews":         ("https://news.hada.io/rss/news",                                3),
    "Simon Willison":   ("https://simonwillison.net/atom/everything/",                   3),
    "Import AI":        ("https://importai.substack.com/feed",                           3),
    "Latent Space":     ("https://latent.space/feeds/all.xml",                           3),
    "Interconnects":    ("https://www.interconnects.ai/feed",                            3),
    "Ben's Bites":      ("https://www.bensbites.com/feed",                               3),
    "TLDR AI":          ("https://tldr.tech/api/rss/ai",                                 3),
}
# RSS 없는 곳(Anthropic, Meta AI, xAI, LMArena, Artificial Analysis 등)은 anthropic.py / ego_pages.py

_MAX_AGE_HOURS = 24 * 7   # 카드뉴스는 주간 단위라 7일치 (중복은 DB가 막음)
_HEADERS = {"User-Agent": "AIField-Bot/1.0 (AI news aggregator)"}
_HTML_RE = re.compile(r"<[^>]+>")


def _entry_time(entry: dict) -> datetime | None:
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    if t is None:
        return None
    # feedparser의 *_parsed는 UTC 기준 — mktime(로컬)로 바꾸면 KST에서 9시간 어긋남
    return datetime.fromtimestamp(calendar.timegm(t), tz=timezone.utc)


def _urllib_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.read()


def _strip_html(text: str) -> str:
    return _HTML_RE.sub("", text).strip()


async def _fetch_one(
    session: aiohttp.ClientSession, name: str, url: str, reliability: int, cutoff: datetime
) -> list[NewsItem]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            status = resp.status
            raw = await resp.read() if status == 200 else b""
        if status == 403:
            # Substack(Import AI)은 같은 UA라도 aiohttp 요청만 403 — urllib으로 한 번 재시도
            raw = await asyncio.to_thread(_urllib_get, url)
        elif status != 200:
            print(f"[rss] {name} HTTP {status}")
            return []
    except Exception as e:
        print(f"[rss] {name} 요청 실패: {e}")
        return []

    feed = feedparser.parse(raw)
    items: list[NewsItem] = []

    for entry in feed.entries:
        pub = _entry_time(entry)
        if pub and pub < cutoff:
            continue

        title = _strip_html(entry.get("title") or "").strip()
        if not title:
            continue

        link = entry.get("link", "")

        # summary 추출 — summary → content → 없으면 빈 문자열
        raw_summary = entry.get("summary", "")
        if not raw_summary:
            content_list = entry.get("content", [])
            raw_summary = content_list[0].get("value", "") if content_list else ""
        summary = _strip_html(raw_summary)[:600]

        items.append(NewsItem(
            title=title,
            source=name,
            url=link,
            summary=summary,
            is_official=reliability >= 4,
            is_rumor=False,
            reliability=reliability,
        ))

    return items


async def fetch() -> list[NewsItem]:
    """등록된 모든 RSS 피드에서 최신 공식 포스트를 수집한다."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=_MAX_AGE_HOURS)

    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        tasks = [
            _fetch_one(session, name, url, rel, cutoff)
            for name, (url, rel) in _FEEDS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    items: list[NewsItem] = []
    for name, result in zip(_FEEDS.keys(), results):
        if isinstance(result, Exception):
            print(f"[rss] {name} 수집 실패: {result}")
            continue
        items.extend(result)

    return items
