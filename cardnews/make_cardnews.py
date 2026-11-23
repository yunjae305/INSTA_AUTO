"""주제·내용 텍스트 파일 하나로 인스타 카드뉴스(1080x1350 PNG)를 만든다.

사용법: python3 cardnews/make_cardnews.py <입력.txt> [출력폴더]
입력 형식은 cardnews/example.txt 참고.
"""
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

W, H = 1080, 1350
RED, BG, INK, PINK = "#EE1F4A", "#EFEFEF", "#1C1C1C", "rgba(236,110,140,.6)"

CSS = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ width:{W}px; height:{H}px; overflow:hidden; background:{BG}; color:{INK};
  font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif; word-break:keep-all; }}
.card {{ width:100%; height:100%; display:flex; flex-direction:column; justify-content:center;
  align-items:center; gap:48px; padding:0 72px; text-align:center; }}
h1 {{ font-size:80px; font-weight:900; line-height:1.3; letter-spacing:-1px; }}
mark {{ background:linear-gradient(transparent 55%, {PINK} 55%); color:inherit; }}
p {{ font-size:40px; font-weight:500; line-height:1.5; color:#444; }}
.img {{ width:936px; max-height:800px; border-radius:24px; object-fit:cover; background:#fff; }}
ul {{ list-style:none; width:936px; display:flex; flex-direction:column; gap:24px; }}
li {{ background:#fff; border-radius:28px; padding:36px 40px 36px 88px; font-size:44px;
  font-weight:700; text-align:left; position:relative; }}
li::before {{ content:''; position:absolute; left:40px; top:50%; width:22px; height:22px;
  margin-top:-11px; border-radius:50%; background:{RED}; }}
.cover {{ display:flex; flex-direction:column; height:100%; }}
.cover .pics {{ display:flex; gap:6px; height:704px; background:#fff; }}
.cover .pics img {{ flex:1; min-width:0; height:100%; object-fit:cover; }}
.cover .panel {{ flex:1; background:{RED}; color:#fff; display:flex; flex-direction:column;
  justify-content:center; gap:40px; padding:0 90px; }}
.cover h1 {{ font-size:96px; }}
.btn {{ background:{RED}; color:#fff; border-radius:999px; padding:36px 96px; font-size:48px; font-weight:900; }}
.handle {{ font-size:44px; font-weight:700; color:#777; }}
"""


def inline(text):
    """[강조] 표시를 형광펜 밑줄로 바꾼다."""
    return re.sub(r"\[(.+?)\]", r"<mark>\1</mark>", html.escape(text))


def parse(text, base):
    """첫 블록은 표지 정보(키: 값), 이후 '---'로 나눈 블록 하나가 카드 한 장."""
    blocks = [b.strip() for b in re.split(r"^---\s*$", text, flags=re.M) if b.strip()]
    meta = {}
    for line in blocks[0].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    if "제목" not in meta:
        raise ValueError("첫 블록에 '제목:' 줄이 필요합니다")
    cards = []
    for b in blocks[1:]:
        card = {"title": [], "items": [], "body": [], "image": None}
        for line in b.splitlines():
            line = line.strip()
            if line.startswith("#"):
                card["title"].append(line.lstrip("#").strip())
            elif line.startswith("- "):
                card["items"].append(line[2:].strip())
            elif line.startswith("이미지:"):
                card["image"] = resolve(line.split(":", 1)[1].strip(), base)
            elif line:
                card["body"].append(line)
        cards.append(card)
    pics = [resolve(p.strip(), base) for p in meta.get("표지이미지", "").split(",") if p.strip()]
    return meta, pics, cards


def resolve(path, base):
    p = (base / path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"이미지 없음: {p}")
    return p


def img(path, cls=""):
    return f'<img class="{cls}" src="{path.as_uri()}">'


def cover_html(meta, pics):
    top = f'<div class="pics">{"".join(img(p) for p in pics)}</div>' if pics else ""
    return f'<div class="cover">{top}<div class="panel"><h1>{inline(meta["제목"])}</h1></div></div>'


def body_html(c):
    parts = []
    if c["title"]:
        parts.append(f"<h1>{'<br>'.join(inline(t) for t in c['title'])}</h1>")
    if c["image"]:
        parts.append(img(c["image"], "img"))
    if c["items"]:
        parts.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in c["items"]) + "</ul>")
    if c["body"]:
        parts.append(f"<p>{'<br>'.join(inline(t) for t in c['body'])}</p>")
    return f'<div class="card">{"".join(parts)}</div>'


def cta_html(meta):
    kw = html.escape(meta.get("키워드", ""))
    btn = f"<div class='btn'>댓글에 '{kw}'</div>" if kw else ""
    handle = html.escape(meta.get("계정", "@aiona_ai"))
    return (f'<div class="card"><h1>지금 <mark>댓글</mark> 남기기</h1>{btn}'
            f'<p>저장해 두면 나중에 찾기 쉬워요</p><div class="handle">{handle}</div></div>')


def render(page_html, out_png, tmp):
    src = Path(tmp) / f"{out_png.stem}.html"
    src.write_text(f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>{page_html}", encoding="utf-8")
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--allow-file-access-from-files", "--force-device-scale-factor=1",
                    f"--window-size={W},{H}", f"--screenshot={out_png}", src.as_uri()],
                   check=True, capture_output=True)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]).resolve()
    meta, pics, cards = parse(src.read_text(encoding="utf-8"), src.parent)
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.parent / f"{src.stem}_cards"
    out.mkdir(parents=True, exist_ok=True)
    pages = [cover_html(meta, pics), *map(body_html, cards), cta_html(meta)]
    with tempfile.TemporaryDirectory() as tmp:
        for i, page in enumerate(pages, 1):
            render(page, (out / f"card_{i}.png").resolve(), tmp)
    print(f"{len(pages)}장 생성: {out}")


if __name__ == "__main__":
    main()
