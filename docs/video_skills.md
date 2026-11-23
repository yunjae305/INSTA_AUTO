# 클로드 영상 자동화 영상 2편: 분석과 스킬 목록

작성일: 2026-11-23 (같은 날 로컬 PC에서 자막·설명란을 직접 받아 다시 씀)

## 0. 확인 범위

| 영상 | 제목 / 채널 | 확인한 자료 |
|---|---|---|
| [uTcTrFGiJ_g](https://youtu.be/uTcTrFGiJ_g) | 클로드로 영상 편집 완전 자동화하면 생기는 일 (설치 가이드 + 스킬 공유) / 스마트대디 | 설명란, 한국어 자동 자막 전체 |
| [5tbz_rxo5Qo](https://youtu.be/5tbz_rxo5Qo) | 이제 클로드만으로 영상을 만들 수 있습니다 / 데키랩 | 설명란, 한국어 자동 자막 전체 |

처음 버전은 클라우드에서 YouTube가 막혀 제목만 보고 추정했습니다. 이번 버전은 실제 자막 기준입니다.
처음 버전에 있던 Premiere MCP, Remotion, HyperFrames는 **두 영상 어디에도 나오지 않습니다.** 아래 6절에 참고로만 남깁니다.

## 1. 영상 1 분해 (스마트대디): "AI 편집팀" 8개 도구

흐름: 녹화 → Whisper 받아쓰기 → 클로드가 컷·자막·효과음·줌·모션 카드 → CapCut 프로젝트로 조립 → 사람이 CapCut에서 마지막 손질 → 피드백을 스킬 규칙으로 저장

| 역할 | 도구 | 비고 |
|---|---|---|
| 감독 | 사람 | 기획, 녹화, 재미 판단, 버릴 곳 결정 |
| 편집자 | Claude 데스크톱 앱 → Code 탭, Opus 5.5, 노력 높음/xhigh | 터미널보다 데스크톱 앱 추천 (영상·이미지 확인이 편함). $20 이상 요금제 |
| 받아쓰기 | Whisper (로컬, 무료) | 단어별 타임코드 → 반복·버벅임 찾기 |
| 최종 손질 | CapCut (무료) | 클로드가 만든 프로젝트를 열어 클립 끝만 늘리고 줄임 |
| 이미지·썸네일·캐릭터 | Higgsfield (MCP 커넥터), GPT 이미지 2.5 / 나노바나나 | 썸네일 글자는 따로 넣음 |
| 모션 그래픽 | 클로드가 코드(HTML)로 직접 | 템플릿으로 재사용 |
| 목소리 클론 | ElevenLabs | 가능하면 직접 녹음 |
| 광고풍 편집 | Higgsfield Katana | 레퍼런스 영상 스타일을 프레임 단위로 입힘. 기존 영상만 쓰면 크레딧 0 |

핵심 노하우: 피드백은 "몇 초에 뭐가 어떻다"로 구체적으로 주고, 끝나면 "오늘 고친 거 스킬에 저장해 줘"라고 해서 규칙을 쌓는다 (예: 반복한 말은 마지막 것만, 효과음 1분에 1~2개, 자막은 의미 단위).
결과: 12분 영상 초벌 1시간 23분, 사람 작업 30시간 → 8시간.

## 2. 영상 2 분해 (데키랩): 클로드만으로 영상 생성

설치하는 스킬은 없습니다. **Claude 데스크톱 앱의 일반 채팅(Opus 5.5)에 프롬프트만** 넣어 코드로 영상을 만듭니다.

- 예시: 크리스마스 도트 영상, 카톡 대화 밈 영상(알림음 포함), 홈페이지 홍보 영상(레퍼런스 영상 + 홈페이지 주소), 종이비행기 애니메이션(1분 30초, 배경음 포함), 스마트폰 속 줌 영상
- 노력 설정이 높을수록 결과가 좋고 크레딧을 더 씀
- 프롬프트 모음: [Prompt Motion](https://prompt-motion.com/), 영상별 프롬프트 복사 + Customize로 변수 바꾸기
- 레퍼런스(로고, 홈페이지, 참고 영상)를 같이 주면 브랜드 영상이 됨

## 3. 설치 / 기록 현황

| 항목 | 상태 | 위치 / 방법 |
|---|---|---|
| **smartdaddy-video-edit** 스킬 (영상 1 공유, [구글 드라이브](https://drive.google.com/file/d/1iD_kegs-DuGfOsF40hQulGD-5LkVmW9K/view)) | **설치함** (사용자 전역) | `~/.claude/skills/smartdaddy-video-edit/`. 스크립트를 읽어 확인: 외부 전송 없음 (렌더용 localhost 서버만). 라이선스가 없어 공개 저장소인 이 repo에는 넣지 않음 |
| 스킬 준비물: Python 패키지(faster-whisper, opencv, playwright 등), Chromium, ffmpeg | 미설치 | 처음 쓸 때 스킬이 `python scripts/doctor.py --fix`로 설치 (허락 후). Whisper large-v3 모델 약 3GB |
| CapCut | 미설치 | Windows/Mac 데스크톱 앱. 스킬은 CapCut 프로젝트 폴더에 씀 (WSL이면 Windows 쪽 경로) |
| Higgsfield MCP | 미연결 | claude.ai → Settings → Connectors → Higgsfield → 로그인 (계정 작업이라 직접) |
| ElevenLabs | 기록만 | 목소리 클론이 필요할 때만 |
| Prompt Motion | 기록만 | 사이트에서 프롬프트 복사 |

## 4. INSTA_AUTO에 적용할 우선순위

이 저장소는 인스타 카드뉴스(`aiona_cardnews/`)를 만듭니다.

1. **영상 2 방식 (프롬프트만)**: 카드 PNG와 문구를 주고 "이 카드뉴스를 9:16 릴스 모션 영상으로" 요청. 설치할 것이 없어 바로 시험 가능
2. **smartdaddy-video-edit**: 직접 찍은 녹화본을 릴스·쇼츠로 편집할 때 (CapCut 필요)
3. **Higgsfield**: 썸네일·캐릭터 이미지가 필요할 때

## 5. 출처

- 영상 설명란·자막 (yt-dlp로 받음, 2026-11-23)
- https://prompt-motion.com/
- https://dekilab.kr/class/?idx=3

## 6. 참고: 영상에는 안 나왔지만 같은 용도인 것

- Remotion 공식 스킬: `npx skills add remotion-dev/skills` (이 PC에는 ECC 플러그인의 `ecc:remotion-video-creation` 스킬이 이미 있음)
- HyperFrames: `npx skills add heygen-com/hyperframes --all`
- Premiere Pro MCP: [leancoderkavy/premiere-pro-mcp](https://github.com/leancoderkavy/premiere-pro-mcp) (Premiere 필요)
