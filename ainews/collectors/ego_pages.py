"""
RSS가 없는 AI 기업·평가 기관 페이지 수집기 (ego-browser 사용).

ego lite(Windows 앱)가 떠 있어야 한다. WSL에서 ego-browser.exe를 불러
목록 페이지를 열고, 사이트별 경로 패턴에 맞는 기사 링크를 위에서부터 가져온다.
날짜가 없으므로 새 글 판단은 DB의 URL 중복 제거에 맡긴다.
ego-browser를 못 찾으면 빈 목록을 반환한다.
"""

import asyncio
import json
import os
from pathlib import Path

from scorer import NewsItem

# ego lite가 업데이트되면 이 링크가 새 버전 폴더를 가리킨다
_EGO = os.getenv("EGO_BROWSER") or "/mnt/c/Users/kyj31/.local/share/ego/active_version_dir/ego-browser.exe"
_PER_SITE = 5
_MARK = "@@EGO_PAGES@@"

# (이름, 목록 URL, 기사 경로 정규식(pathname+search), reliability)
# 2026-11-23 ego-browser로 각 페이지의 실제 링크를 보고 정함
_SITES: list[tuple[str, str, str, int]] = [
    ("Meta AI",             "https://ai.meta.com/blog/",                    r"^/blog/[^/]+/?$", 5),
    ("xAI",                 "https://x.ai/news",                            r"^/news/[^/]+$", 5),
    ("DeepSeek",            "https://api-docs.deepseek.com/news/news250120", r"^/news/news\d+/?$", 5),
    ("Cohere",              "https://cohere.com/blog",                      r"^/blog/(?!category/|page/)[^/]+$", 4),
    ("Microsoft AI",        "https://blogs.microsoft.com/ai/",              r"^/source/(\d{4}/\d{2}/\d{2}|features/ai)/[^/]+", 4),
    ("Perplexity",          "https://www.perplexity.ai/hub/blog",           r"^/hub/blog/[^/]+$", 4),
    ("AI21",                "https://www.ai21.com/blog/",                   r"^/blog/(?!category/)[^/]+/?$", 4),
    ("Runway",              "https://runwayml.com/news",                    r"^/(news|research)/[^/]+/[^/]+$", 4),
    ("Cursor",              "https://cursor.com/blog",                      r"^/(ko/)?blog/(?!topic/|page/)[^/]+$", 4),
    ("Replit",              "https://blog.replit.com/",                     r"^/blog/(?!category/)[^/]+$", 4),
    ("Upstage",             "https://www.upstage.ai/blog",                  r"^/blog/(en|ko)/[^/]+$", 4),
    ("LG AI Research",      "https://www.lgresearch.ai/news",               r"^/news/view\?", 4),
    ("Samsung Research",    "https://research.samsung.com/blog",            r"^/blog/[^/]+$", 4),
    ("Naver Clova",         "https://clova.ai/tech-blog",                   r"^/tech-blog/(?!tag/)[^/]+$", 4),
    # 모델 평가
    ("LMArena",             "https://news.lmarena.ai/",                     r"^/blog/[^/]+$", 4),
    ("Artificial Analysis", "https://artificialanalysis.ai/articles",       r"^/articles/[^/]+$", 4),
    ("Scale AI",            "https://scale.com/blog",                       r"^/blog/(?!category/)[^/]+$", 4),
    # 뉴스레터
    ("The Rundown AI",      "https://www.therundown.ai/",                   r"^/(articles|news)/[^/]+$", 3),
]

_SCRIPT = """
const SITES = %s, PER = %d;
const task = await taskSpace("AI news collect " + Date.now());
const page = task.page("p1");
const out = [];
for (const [name, url, pattern] of SITES) {
  try {
    await page.goto(url, { timeout: 25000 });
    await page.waitForTimeout(1500);
    const links = await page.evaluate(({ pattern, per }) => {
      const re = new RegExp(pattern), seen = new Set(), r = [];
      for (const a of document.querySelectorAll("a[href]")) {
        const u = new URL(a.href, location.href);
        const key = u.pathname + u.search;
        // 카드형 링크는 라벨·날짜가 섞이므로 안쪽 제목 태그를 우선 쓴다
        const h = a.querySelector("h1,h2,h3,h4");
        const text = ((h && h.innerText) || a.innerText || "").replace(/\\s+/g, " ").trim();
        if (u.host !== location.host || !re.test(key) || seen.has(key) || text.length < 12 || /^skip to/i.test(text)) continue;
        seen.add(key); r.push({ url: u.origin + key, title: text.slice(0, 160) });
        if (r.length >= per) break;
      }
      return r;
    }, { pattern, per: PER });
    out.push({ name, links });
  } catch (e) { out.push({ name, error: String(e.message).split("\\n")[0].slice(0, 120) }); }
}
await task.finish({ keep: [] });
console.log("%s" + JSON.stringify(out));
"""


async def fetch() -> list[NewsItem]:
    if not Path(_EGO).exists():
        print(f"[ego_pages] ego-browser 없음 ({_EGO}) — 건너뜀")
        return []

    sites = [[n, u, p] for n, u, p, _ in _SITES]
    script = _SCRIPT % (json.dumps(sites), _PER_SITE, _MARK)
    proc = await asyncio.create_subprocess_exec(
        _EGO, "nodejs", cwd="/mnt/c",  # Windows exe라 UNC 경로가 아닌 곳에서 실행
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(script.encode()), timeout=900)
    except asyncio.TimeoutError:
        proc.kill()
        print("[ego_pages] 시간 초과(15분) — 건너뜀")
        return []

    # ego-browser는 console.log를 stderr로 내보내기도 해서 둘 다 본다
    text = out.decode(errors="replace") + "\n" + err.decode(errors="replace")
    line = next((l for l in text.splitlines() if l.startswith(_MARK)), None)
    if line is None:
        print(f"[ego_pages] 결과 없음 (exit {proc.returncode}): {err.decode(errors='replace')[-300:]}")
        return []

    rel = {n: r for n, _, _, r in _SITES}
    items: list[NewsItem] = []
    for site in json.loads(line[len(_MARK):]):
        if "error" in site:
            print(f"[ego_pages] {site['name']} 실패: {site['error']}")
            continue
        for link in site["links"]:
            items.append(NewsItem(
                title=link["title"],
                source=site["name"],
                url=link["url"],
                is_official=rel[site["name"]] >= 4,
                is_rumor=False,
                reliability=rel[site["name"]],
            ))
    print(f"[ego_pages] {len(items)}건 수집")
    return items
