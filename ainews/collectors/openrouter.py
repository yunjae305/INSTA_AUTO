"""
OpenRouter 공개 모델 API 수집기 (인증 불필요).

https://openrouter.ai/api/v1/models 의 created(유닉스 시각)로
최근 N일 안에 새로 올라온 모델을 '신규 모델' 소식으로 만든다.
":batch" 같은 변형 id는 원래 모델과 겹치므로 뺀다.
"""

from datetime import datetime, timedelta, timezone

import aiohttp

from scorer import NewsItem

_URL = "https://openrouter.ai/api/v1/models"
_MAX_AGE_DAYS = 7
_HEADERS = {"User-Agent": "aiona-ainews/1.0 (AI news aggregator)"}


async def fetch() -> list[NewsItem]:
    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        async with session.get(_URL, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            resp.raise_for_status()
            models = (await resp.json())["data"]

    cutoff = (datetime.now(timezone.utc) - timedelta(days=_MAX_AGE_DAYS)).timestamp()
    items = []
    for m in models:
        if ":" in m["id"] or (m.get("created") or 0) < cutoff:
            continue
        ctx = m.get("context_length")
        price = (m.get("pricing") or {}).get("prompt")
        items.append(NewsItem(
            title=f"[신규 모델] {m.get('name') or m['id']}",
            source="OpenRouter",
            url=f"https://openrouter.ai/{m['id']}",
            summary=(f"{(m.get('description') or '')[:400]}\n"
                     f"context {ctx} tokens | prompt ${price}/token").strip(),
            is_official=False,
            is_rumor=False,
            reliability=4,
            singularity_impact=4,
        ))
    print(f"[openrouter] 신규 모델 {len(items)}건")
    return items
