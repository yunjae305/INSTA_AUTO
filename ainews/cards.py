"""AI 뉴스 카드뉴스 렌더러: cards.json → card_N.png (aiona_cardnews.pdf 1쪽 템플릿).

cards.json 구조:
{
  "cover": {"line1": "이번 주 AI 뉴스,", "line2": "4가지만 보면 끝"},
  "news": [{"short": "목록용 한 줄", "title": ["첫 줄", "[강조] 둘째 줄"],
            "points": ["요점", ...], "note": "날짜·출처 한 줄",
            "stat": null 또는 {"label": "...", "value": "-20%", "desc": "..."}}],
  "caption": "인스타 본문"
}
"""
import html
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cardnews.make_cardnews import render, inline, RED  # noqa: E402

CSS = f"""<style>
.top {{ position:absolute; top:60px; left:72px; right:72px; display:flex; justify-content:space-between;
  align-items:center; font-size:30px; font-weight:800; }}
.top .logo {{ display:flex; align-items:center; gap:12px; }}
.top .logo::before {{ content:''; width:30px; height:30px; border-radius:8px; background:{RED}; }}
.top .tag {{ color:#666; font-weight:700; }}
.ncover {{ height:100%; padding:190px 72px 0; display:flex; flex-direction:column; gap:72px; }}
.npanel {{ position:relative; background:#fff; border-radius:40px; padding:52px 44px; }}
.npanel .head {{ font-size:32px; font-weight:800; margin-bottom:22px; }}
.circle {{ position:absolute; top:-56px; right:-16px; width:190px; height:190px; border-radius:50%;
  background:{RED}; color:#fff; display:flex; align-items:center; justify-content:center; text-align:center;
  font-size:38px; font-weight:900; line-height:1.2; }}
.ncover h1 {{ font-size:92px; text-align:left; }}
.ncover h1 .red {{ color:{RED}; }}
ol {{ list-style:none; width:100%; display:flex; flex-direction:column; gap:22px; counter-reset:n; }}
ol li {{ background:#fff; border-radius:24px; padding:30px 36px 30px 110px; font-size:40px; font-weight:700;
  text-align:left; position:relative; counter-increment:n; }}
ol li::before {{ content:counter(n); position:absolute; left:36px; top:50%; width:50px; height:50px; margin-top:-25px;
  border-radius:50%; background:{RED}; color:#fff; font-size:28px; font-weight:800;
  display:flex; align-items:center; justify-content:center; }}
.npanel ol {{ gap:12px; }}
.npanel ol li {{ background:#F4F4F4; font-size:30px; padding:18px 24px 18px 84px; }}
.npanel ol li::before {{ left:24px; width:40px; height:40px; margin-top:-20px; font-size:22px; }}
.badge {{ background:{RED}; color:#fff; border-radius:999px; padding:10px 32px; font-size:32px; font-weight:800;
  letter-spacing:1px; }}
.label {{ font-size:48px; font-weight:700; color:#333; }}
.value {{ font-size:220px; font-weight:900; color:{RED}; line-height:1; letter-spacing:-6px; }}
.note {{ font-size:32px; color:#666; }}
</style>"""


def _e(s):
    return html.escape(s)


def cover(c, news):
    items = "".join(f"<li>{_e(n['short'])}</li>" for n in news)
    return (f'<div class="top"><span class="logo">AIONA</span><span class="tag">AI 뉴스</span></div>'
            f'<div class="ncover"><div class="npanel"><div class="circle">이번 주<br>TOP {len(news)}</div>'
            f'<div class="head">이번 주 AI 뉴스</div><ol>{items}</ol></div>'
            f'<h1>{inline(c["line1"])}<br><span class="red">{inline(c["line2"])}</span></h1></div>')


def overview(news):
    items = "".join(f"<li>{_e(n['short'])}</li>" for n in news)
    return f'<div class="card"><h1>이번 주 <mark>AI 뉴스</mark></h1><ol>{items}</ol></div>'


def headline(i, n):
    parts = [f'<span class="badge">NEWS {i:02d}</span>',
             f"<h1>{'<br>'.join(inline(t) for t in n['title'])}</h1>"]
    if n.get("points"):
        parts.append("<ul>" + "".join(f"<li>{inline(p)}</li>" for p in n["points"]) + "</ul>")
    if n.get("note"):
        parts.append(f'<p class="note">{_e(n["note"])}</p>')
    return f'<div class="card">{"".join(parts)}</div>'


def stat(i, s):
    return (f'<div class="card"><span class="badge">NEWS {i:02d}</span><div class="label">{_e(s["label"])}</div>'
            f'<div class="value">{_e(s["value"])}</div><p>{_e(s.get("desc", ""))}</p></div>')


def cta(handle):
    return (f'<div class="card"><h1>매주 AI 뉴스,<br><mark>AIONA</mark>에서 먼저</h1>'
            f'<div class="btn">저장하고 팔로우</div><div class="handle">{_e(handle)}</div></div>')


def validate(data):
    """LLM이 쓴 cards.json이 템플릿에 맞는지 확인한다. 틀리면 ValueError."""
    if not isinstance(data.get("cover"), dict) or not {"line1", "line2"} <= data["cover"].keys():
        raise ValueError("cover.line1 / cover.line2 필요")
    news = data.get("news")
    if not isinstance(news, list) or not 1 <= len(news) <= 6:
        raise ValueError("news는 1~6개 목록이어야 함")
    for i, n in enumerate(news, 1):
        if not isinstance(n.get("short"), str) or not isinstance(n.get("title"), list) or not n["title"]:
            raise ValueError(f"news[{i}]에 short(문자열)·title(목록) 필요")
        if n.get("stat") and not {"label", "value"} <= n["stat"].keys():
            raise ValueError(f"news[{i}].stat에 label·value 필요")


def pages(data, handle="@aiona_ai"):
    news = data["news"]
    out = [cover(data["cover"], news), overview(news)]
    for i, n in enumerate(news, 1):
        out.append(headline(i, n))
        if n.get("stat"):
            out.append(stat(i, n["stat"]))
    out.append(cta(handle))
    return out


def render_all(data, out_dir: Path):
    validate(data)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("card_*.png"):  # 다시 렌더할 때 장수가 줄면 옛 카드가 남지 않게
        old.unlink()
    ps = pages(data)
    with tempfile.TemporaryDirectory() as tmp:
        for i, p in enumerate(ps, 1):
            render(CSS + p, (out_dir / f"card_{i}.png").resolve(), tmp)
    return len(ps)
