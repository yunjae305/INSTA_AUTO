# HANDOFF

마지막 정리: 2026-11-24. 브랜치는 `main` 하나만 있다.

## 지금 되는 것

- AI 뉴스 수집 → 고르기 → Gemini 요약 → 카드 PNG·캡션까지 PC에서 동작한다. 사용법은 `ainews/README.md`.
- 2026-11-23에 카드 2세트를 만들었다: `aiona_cardnews/ai_news_20261123_2026/`, `aiona_cardnews/ai_news_20261123_2100/`.
- 노출 경고가 붙었던 옛 Gemini 키(`...DwQ8`)는 AI Studio에서 삭제했다.
- Oracle 서버(Ubuntu, Always Free)가 돌고 있다. 코드는 `2871f99`. cron이 5분마다 `collect` → `notify_telegram.py`를 실행하고, @pasuin_bot이 건별로 알린다. 서버에는 `GEMINI_API_KEY`가 없다(알림에 Gemini를 쓰지 않음).

## 로컬 환경 (2026-11-24, Windows PC의 WSL)

- 저장소: `/mnt/c/Users/winz/INSTA_AUTO`
- `.env`: 저장소 루트. `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, 알림 필터가 들어 있다. `.gitignore`로 제외.
- SSH 개인 키: `~/.ssh/oracle_ainews` (Oracle 콘솔에서 받은 `ssh-key-2026-11-23.key`). 접속은 `ssh -i ~/.ssh/oracle_ainews ubuntu@<서버IP>`. IP는 공개 저장소라 여기 적지 않는다.

## 해야 할 일

1. **코드 라이선스 (결정 필요)**
   - 원본은 `github.com/NoNamad5196/AIField`이고 LICENSE가 없다. 라이선스가 없으면 모든 권리를 저작권자가 가진다. 공개 저장소에 재배포하는 것은 허락 밖이다.
   - 그대로 복사한 파일(바이트 동일): `scorer.py`, `collectors/` 아래 `dcinside.py`, `arcalive.py`, `anthropic.py`, `huggingface.py`, `hacker_news.py`.
   - 고친 파일: `db/news_store.py`, `collectors/__init__.py`, `reddit.py`, `rss.py`.
   - 권고: 비공개로 전환 → 원저자에게 허락 요청 → 허락을 못 받으면 위 10개 파일을 다시 쓰고 히스토리(`815de6e` 이후)도 정리. 출처 표기만으로는 부족하다.
2. **11-23 카드 고친 뒤 올리기**
   - 숫자는 출처와 모두 맞다. 고칠 표현:
   - `ai_news_20261123_2026`: card_3 "동시 출시" → "새로 출시". Hydrogen 모델은 그 전 주, 플러그인은 11/17.
   - `ai_news_20261123_2100`:
     - card_3 제목 "[Gemini] 출시" → "[Hydrogen] 공개". 같은 카드의 "실시간"은 출처에 없다.
     - card_5 "ANT 종목명" → "티커 ANT", "83달러에 매각" → "공모가 83달러로 공모 마감".
     - 캡션 "정식 출시" → "API로 공개".
   - `cards.json`을 고친 뒤 `python3 ainews/ainews.py render <폴더>`로 다시 그린다.
3. **Reddit API 승인 대기**
   - 2026-11-23에 Reddit "Data Access Request"를 제출했다. 앱 직접 생성은 `Max clients have been reached`로 막혀 있다.
   - 승인 메일이 오면 `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`을 PC와 서버의 `.env`에 넣는다.

## 나중에 (선택)

- 카드뉴스를 릴스 영상으로: `docs/video_skills.md` 4절 순서. 영상 2 방식(프롬프트만)은 설치 없이 바로 시험할 수 있다.
- 직접 찍은 영상 편집: smartdaddy-video-edit 스킬은 설치됨. CapCut 설치와 준비물 설치(`doctor.py --fix`)가 남았다.
- Higgsfield 연결: claude.ai → Settings → Connectors에서 직접 로그인.
- 보류: 실제 사람처럼 보이는 YouTube 롱폼 영상.

## 주의

- Oracle은 7일간 사용률이 낮은 Always Free 서버를 회수할 수 있다. 회수되면 2~3번만 다시 하면 된다.
- 서버에는 ego lite가 없어서 페이지 읽기 출처(18곳)는 PC에서 `collect`를 돌려야 받는다.
- Gemini 모델은 `gemini-3.8-flash`를 먼저 쓰고, 막히면 `gemini-3.5-flash`로 넘어간다. `gemini-2.5-flash`는 새 키에서 404가 난다.
