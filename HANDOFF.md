# HANDOFF

마지막 정리: 2026-11-24. 브랜치는 `main` 하나만 있다.

## 지금 되는 것

- AI 뉴스 수집 → 고르기 → Gemini 요약 → 카드 PNG·캡션까지 PC에서 동작한다. 사용법은 `ainews/README.md`.
- 2026-11-23에 카드 2세트를 만들었다: `aiona_cardnews/ai_news_20261123_2026/`, `aiona_cardnews/ai_news_20261123_2100/`.
- API 키는 `~/INSTA_AUTO/.env`에만 있다(권한 600, `.gitignore`로 제외). 저장소 기록에 키는 없다.
- 노출 경고가 붙었던 옛 Gemini 키(`...DwQ8`)는 AI Studio에서 삭제했다.

## 해야 할 일 (순서대로)

1. **Oracle Cloud 가입** (사용자가 직접)
   - 이메일 인증, 카드, 전화, 캡챠, 약관 동의는 사용자 몫이다.
   - 홈 리전은 나중에 바꿀 수 없다. 권장: South Korea Central (Seoul). 계정 유형: 개인.
2. **서버 만들기**
   - 이미지 Ubuntu, 모양 `VM.Standard.E2.1.Micro` (Always Free). 수집기에는 이 사양이면 충분하다.
   - SSH 공개 키: `~/.ssh/oracle_ainews.pub` (같은 파일을 Windows 다운로드 폴더에도 복사해 뒀다). 개인 키는 `~/.ssh/oracle_ainews`.
   - SSH 접속은 내 IP에서만 허용한다.
3. **서버 설치**
   - `ainews/README.md`의 "서버에서 자동 수집" 명령을 그대로 실행한다(`.env` 복사 → `setup_server.sh`).
   - 확인: 첫 수집 출력이 나오는지, `crontab -l`에 `ainews.py collect` 줄이 있는지.
4. **Reddit API 승인 대기**
   - 2026-11-23에 Reddit "Data Access Request"를 제출했다. 앱 직접 생성은 `Max clients have been reached`로 막혀 있다.
   - 승인 메일이 오면 `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`을 PC와 서버의 `.env`에 넣는다.
5. **11-23 카드 올리기 전 확인**
   - README 5단계대로 `sources.txt`와 카드의 숫자·날짜·이름을 대조한다. 올렸는지는 기록이 없다.
6. **코드 라이선스 확인**
   - `ainews/` 일부는 받은 AIField 봇 코드를 바탕으로 했다. 라이선스를 확인하지 않았는데 이 저장소는 공개다.
   - 확인이 안 되면 저장소를 비공개로 돌리거나 해당 부분을 다시 쓴다.

## 나중에 (선택)

- 카드뉴스를 릴스 영상으로: `docs/video_skills.md` 4절 순서. 영상 2 방식(프롬프트만)은 설치 없이 바로 시험할 수 있다.
- 직접 찍은 영상 편집: smartdaddy-video-edit 스킬은 설치됨. CapCut 설치와 준비물 설치(`doctor.py --fix`)가 남았다.
- Higgsfield 연결: claude.ai → Settings → Connectors에서 직접 로그인.
- 보류: 실제 사람처럼 보이는 YouTube 롱폼 영상.

## 주의

- Oracle은 7일간 사용률이 낮은 Always Free 서버를 회수할 수 있다. 회수되면 2~3번만 다시 하면 된다.
- 서버에는 ego lite가 없어서 페이지 읽기 출처(18곳)는 PC에서 `collect`를 돌려야 받는다.
- Gemini 모델은 `gemini-3.8-flash`를 먼저 쓰고, 막히면 `gemini-3.5-flash`로 넘어간다. `gemini-2.5-flash`는 새 키에서 404가 난다.
