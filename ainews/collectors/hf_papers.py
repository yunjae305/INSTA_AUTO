"""
Hugging Face Daily Papers API 수집기 (인증 불필요).

https://huggingface.co/api/daily_papers 는 사람이 고른 그날의 주목 논문이다.
추천(upvotes)이 기준 이상인 것만 소식으로 남긴다.
"""

import aiohttp

from scorer import NewsItem

_URL = "https://huggingface.co/api/daily_papers"
_MIN_UPVOTES = 20
_HEADERS = {"User-Agent": "aiona-ainews/1.0 (AI news aggregator)"}


async def fetch(limit: int = 100) -> list[NewsItem]:
    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        async with session.get(_URL, params={"limit": limit},
                               timeout=aiohttp.ClientTimeout(total=20)) as resp:
            resp.raise_for_status()
            papers = await resp.json()

    items = []
    for p in papers:
        paper = p.get("paper") or {}
        votes = paper.get("upvotes") or 0
        if votes < _MIN_UPVOTES or not paper.get("id"):
            continue
        items.append(NewsItem(
            title=f"[논문] {paper.get('title', '').strip()}",
            source="HF Daily Papers",
            url=f"https://huggingface.co/papers/{paper['id']}",
            summary=f"추천 {votes}\n{(paper.get('summary') or '')[:500]}",
            is_official=False,
            is_rumor=False,
            reliability=4,
        ))
    print(f"[hf_papers] 추천 {_MIN_UPVOTES}+ 논문 {len(items)}건")
    return items
