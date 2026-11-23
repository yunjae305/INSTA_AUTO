# 클로드 영상 자동화 영상 2편: 분석과 스킬 목록

작성일: 2026-11-23

## 0. 확인 범위 (먼저 읽어 주세요)

| 영상 | 제목 / 채널 | 확인된 내용 |
|---|---|---|
| [uTcTrFGiJ_g](https://youtu.be/uTcTrFGiJ_g) | **클로드로 영상 편집 완전 자동화하면 생기는 일 (설치 가이드 + 스킬 공유)** / 스마트대디_SmartDaddy (@SmartDaddyAI), 2026-10-21 업로드 | 제목·채널은 oEmbed로 확인. 검색 스니펫 기준 내용: **클로드가 프리미어 프로를 원격으로 조작해 내레이션 영상을 편집**하고, Claude Pro 요금제로 **약 15분 분량을 주 2회 정도** 만들 수 있다고 함 |
| [5tbz_rxo5Qo](https://youtu.be/5tbz_rxo5Qo) | **이제 클로드만으로 영상을 만들 수 있습니다** / 데키랩 (@dekilab) | 제목·채널만 확인. 데키랩은 "클로드 리모션 영상 제작" 영상과 클로드 모션그래픽 영상을 올리는 채널이고, 클로드 코드 콘텐츠 자동화 강의(블로그·카드뉴스·PPT·영상)를 운영함 |

이 클라우드 환경에서는 YouTube가 봇 확인으로 영상 페이지와 자막을 막았습니다. 그래서 **영상 본문, 더보기란 링크, 자막은 직접 보지 못했습니다.**
아래 목록은 영상 제목, 검색 스니펫, 같은 채널이 다루는 주제를 바탕으로 **추정**한 것입니다.
영상 설명란이나 자막을 붙여 넣어 주시면 실제 언급된 항목으로 맞춰 고치겠습니다.

## 1. 영상 1 분해 (스마트대디): 프리미어 원격 편집 자동화

추정되는 흐름: 내레이션 녹음 → 음성 인식(STT)으로 대본과 타임코드 생성 → 클로드가 컷 편집·자막·B롤 계획 → MCP로 프리미어 타임라인 조작 → 내보내기

| # | 구성 요소 | 후보 도구 | 설치 / 연결 | 상태 |
|---|---|---|---|---|
| 1 | 프리미어 원격 조작 (MCP) | [leancoderkavy/premiere-pro-mcp](https://github.com/leancoderkavy/premiere-pro-mcp): Premiere 2020–2026, CEP 브리지 패널 | 저장소 README 참고 (CEP 패널 설치 + MCP 등록) | 기록만 함. 로컬 PC에 Premiere 필요 |
| 2 | 프리미어 MCP (대안) | [ayushozha/AdobePremiereProMCP](https://github.com/ayushozha/AdobePremiereProMCP), [hetpatel-11/Adobe_Premiere_Pro_MCP](https://github.com/hetpatel-11/Adobe_Premiere_Pro_MCP) (Claude Desktop용 .mcpb) | README 참고 | 기록만 함 |
| 3 | Adobe 공식 연동 | Adobe for Claude 커넥터 (claude.ai 커넥터) | claude.ai → Settings → Connectors | 기록만 함 |
| 4 | 음성 인식 · 컷 편집 | FFmpeg + Whisper / WhisperX | `brew install ffmpeg` / `pip install whisperx` | 기록만 함 |
| 5 | 영상 편집 스킬 모음 (한국어) | [majung2/claude-video-editor](https://github.com/majung2/claude-video-editor): 릴스 자동 편집, 설치 스크립트 포함 | README의 설치 스크립트 | 기록만 함 |
| 6 | 편집 스킬 (FFmpeg + Whisper) | [6missedcalls/video-editing-skill](https://github.com/6missedcalls/video-editing-skill) (MIT): 자르기, 점프컷, 자막, 속도 조절 | `.claude/skills/`에 복사 | 기록만 함 |
| 7 | 풀 파이프라인 편집 스킬 | affaan-m/everything-claude-code `video-editing` | `npx skills add affaan-m/ecc --skill video-editing --agent claude-code` | 기록만 함 |

## 2. 영상 2 분해 (데키랩): 클로드만으로 영상 생성

추정되는 흐름: 프롬프트/대본 → 클로드가 코드(React/HTML)로 모션그래픽 작성 → Remotion 또는 HyperFrames로 MP4 렌더링 → (선택) TTS 내레이션 추가

| # | 구성 요소 | 도구 | 설치 명령 | 상태 |
|---|---|---|---|---|
| 1 | **Remotion 공식 스킬** | [remotion-dev/skills](https://github.com/remotion-dev/skills) | `npx skills add remotion-dev/skills` | 설치 시도했으나 막힘 → 기록 |
| 2 | **HyperFrames (HeyGen) 스킬** | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes): HTML → MP4 | `npx skills add heygen-com/hyperframes --all` 또는 플러그인: `claude plugin marketplace add heygen-com/hyperframes` → `claude plugin install hyperframes@hyperframes` | 기록만 함 |
| 3 | HyperFrames CLI | `npx hyperframes init my-video` → `npx hyperframes preview` | 사전 준비: Node.js 22+, FFmpeg | 기록만 함 |
| 4 | HyperFrames 호스팅 MCP | `npx add-mcp 'https://mcp.heygen.com/mcp/hyperframes/'` (HeyGen 계정 필요) | 기록만 함 |
| 5 | 영상 툴킷 | [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) (MIT): Remotion + ElevenLabs + FFmpeg + Playwright | README 참고 | 기록만 함 |
| 6 | 실사 영상 생성 (선택) | Higgsfield MCP 등 외부 영상 생성 모델 | 해당 서비스 문서 참고 | 기록만 함 |

## 3. INSTA_AUTO에 적용할 우선순위 (추천)

이 저장소는 인스타 카드뉴스(`aiona_cardnews/`)를 만듭니다. 카드뉴스를 **릴스로 확장**하는 기준으로 보면:

1. **HyperFrames**: 카드 PNG와 문구를 HTML 애니메이션으로 만들어 MP4 릴스로 렌더링. 기존 카드 이미지를 그대로 재사용할 수 있어 가장 잘 맞음
2. **Remotion 공식 스킬**: 같은 용도. React에 익숙하면 이쪽
3. **FFmpeg + Whisper 편집 스킬** (6missedcalls 또는 majung2): 직접 찍은 영상에 자막·컷 편집이 필요할 때
4. **Premiere MCP**: 본인 PC에 Premiere가 있고 긴 내레이션 영상을 만들 때만 (클라우드 세션에서는 불가)

## 4. 직접 설치하는 방법 (본인 PC 터미널, 저장소 루트에서)

```bash
# 사전 준비
node -v          # 22 이상
ffmpeg -version  # 없으면 brew install ffmpeg (Mac) / winget install ffmpeg (Windows)

# 1) Remotion 공식 스킬
npx skills add remotion-dev/skills

# 2) HyperFrames 스킬 (전체)
npx skills add heygen-com/hyperframes --all
```

설치하면 스킬이 `.claude/skills/`에 생기니, 커밋해 두면 클라우드 세션에서도 쓸 수 있습니다.
설치 전에 각 저장소의 `SKILL.md`를 한 번 훑어보세요. 모두 서드파티 코드입니다.

## 출처

- https://blog.heimdex.co/post/claude-code-video-editing-automation-guide-ko/
- https://wikidocs.net/335609 , https://wikidocs.net/335635
- https://github.com/majung2/claude-video-editor
- https://dekilab.kr/class/?idx=3
- https://hyperframes.heygen.com/quickstart
- https://claudeskills.info/skills/affaan-m/ecc/video-editing/
- https://vloggingpro.com/ai/mcp/premiere-pro/
- https://github.com/leancoderkavy/premiere-pro-mcp
