# AI 뉴스 카드뉴스 만들기

수집 → 고르기 → 요약 → 카드(PNG)·캡션. 모든 명령은 `~/INSTA_AUTO`에서 실행한다.

## 1. 수집 (매일 또는 카드 만들기 전)

```bash
python3 ainews/ainews.py collect
```

- 결과는 `ainews/db/aifield.db`에 쌓이고, 이미 있는 URL은 건너뛴다.
- RSS·공식 API는 최근 7일치를 받는다. ego 페이지 읽기는 사이트마다 최신 5건이다.
- ego 수집은 ego lite(Windows)가 켜져 있어야 동작한다. 꺼져 있으면 그 부분만 건너뛴다.

| 방식 | 출처 |
|---|---|
| 공식 API | Hacker News(Algolia), HuggingFace 모델·Daily Papers, OpenRouter 신규 모델, Reddit(키 있을 때) |
| RSS | `collectors/rss.py`의 `_FEEDS` (OpenAI, Google Gemini/AI/DeepMind/Developers, Mistral, Qwen, Meta, NVIDIA, 평가 기관, 언론 등) |
| 페이지 읽기 | `collectors/ego_pages.py`의 `_SITES` (Meta AI, xAI, DeepSeek, LMArena, Artificial Analysis 등), Anthropic, 디시 |

## 2. 고르기

```bash
python3 ainews/ainews.py list                    # 최근 7일, 레벨 3 이상
python3 ainews/ainews.py list --source gemini --min-level 1
```

앞의 숫자가 번호다. 카드 하나에 보통 4~5개를 고른다.

## 3. 카드 만들기

```bash
python3 ainews/ainews.py make 42,273,434,32
```

- 결과는 `aiona_cardnews/ai_news_<날짜_시각>/`에 생긴다. 고른 소식의 원문은 `sources.json`에 저장된다.
- `.env`에 `GEMINI_API_KEY`가 있으면 Gemini가 `cards.json`을 쓰고 카드 PNG와 `caption.txt`까지 만든다.
- 키가 없으면 `sources.json`까지만 만든다. 그 뒤 `cards.json`을 직접 쓰거나 Claude에게 맡기고, 4번처럼 렌더한다.

## 4. 손보고 다시 그리기

```bash
python3 ainews/ainews.py render aiona_cardnews/ai_news_<날짜_시각>
```

- `cards.json`의 문구를 고친 뒤 실행한다. 구조는 `cards.py` 맨 위 설명을 참고한다.
- 제목에서 `[ ]`로 감싼 부분은 분홍 형광펜으로 강조된다.
- `stat`(숫자 카드)은 원문에 숫자가 있을 때만 넣는다.

## 5. 올리기 전 확인

- `sources.txt`의 원문과 카드의 숫자·날짜·이름을 대조한다. AI 요약은 틀릴 수 있다.
- `card_1.png`부터 차례로 올리고, 본문에는 `caption.txt`를 붙인다.

## 서버에서 자동 수집 (Oracle Always Free)

서버(Ubuntu)는 매일 08:00·20:00에 `collect`만 돌린다. 고르기·카드 만들기는 PC에서 한다.

```bash
scp ~/INSTA_AUTO/.env ubuntu@<서버IP>:~/INSTA_AUTO.env          # 키 (선택)
ssh ubuntu@<서버IP> 'mkdir -p INSTA_AUTO && mv -f INSTA_AUTO.env INSTA_AUTO/.env; curl -fsSL https://raw.githubusercontent.com/yunjae305/INSTA_AUTO/main/ainews/deploy/setup_server.sh | bash'
scp ubuntu@<서버IP>:INSTA_AUTO/ainews/db/aifield.db ~/INSTA_AUTO/ainews/db/   # 카드 만들기 전에 PC로 받기
```

- 서버에는 ego lite가 없어서 ego 페이지 읽기(18곳)는 건너뛴다. 그 소식이 필요하면 PC에서 `collect`를 한 번 더 돌린다.
- Oracle은 7일간 CPU·네트워크 사용률이 20% 미만인 Always Free 서버를 회수할 수 있다. 회수되면 새로 만들고 위 명령만 다시 실행한다.

## .env (커밋 금지, `.gitignore`에 있음)

```
GEMINI_API_KEY=...
GEMINI_MODEL=...                   # 선택. 없으면 gemini-3.8-flash → 막히면 gemini-3.5-flash
REDDIT_CLIENT_ID=...               # Reddit API 승인 후
REDDIT_CLIENT_SECRET=...
REDDIT_USERNAME=...
```
