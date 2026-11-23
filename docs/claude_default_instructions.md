# Karpathy 지침을 Claude 기본 지침으로 설정하기

원본: https://github.com/multica-ai/andrej-karpathy-skills (MIT)

## 1. Claude Code: 이 저장소 (완료)

저장소 루트의 `CLAUDE.md`에 지침을 넣어 두었습니다.
INSTA_AUTO에서 여는 Claude Code 세션(클라우드·로컬 모두)은 이 지침을 자동으로 읽습니다.

## 2. Claude Code: 내 PC 전체 (직접 한 번 실행)

둘 중 하나만 하면 됩니다.

**A. 전역 CLAUDE.md에 넣기 (추천)**

모든 프로젝트에서 항상 적용됩니다.

```bash
mkdir -p ~/.claude
curl -fsSL https://raw.githubusercontent.com/multica-ai/andrej-karpathy-skills/main/CLAUDE.md >> ~/.claude/CLAUDE.md
```

`>>`는 기존 내용 뒤에 덧붙이는 방식이라, 이미 써 둔 지침은 지워지지 않습니다.

**B. 플러그인으로 설치**

Claude Code 안에서 실행합니다. 이 방식은 스킬이라서, 관련 작업을 할 때만 불러옵니다.

```
/plugin marketplace add multica-ai/andrej-karpathy-skills
/plugin install andrej-karpathy-skills@karpathy-skills
```

## 3. Claude 채팅 (claude.ai / 앱)

claude.ai → **Settings → General(프로필)** → **"What personal preferences should Claude consider in responses?"** 칸에 아래 내용을 붙여 넣으세요.
코딩이 아닌 대화에도 맞도록 한국어로 줄인 버전입니다.

```
[작업 원칙 – Karpathy 지침]
1. 생각 먼저: 추측하지 말 것. 가정은 명시하고, 해석이 여러 개면 제시하고 고르게 할 것. 더 단순한 방법이 있으면 말하고, 불명확하면 멈추고 질문할 것.
2. 단순함 우선: 요청한 것만, 최소한으로. 요청 없는 기능·추상화·옵션 추가 금지. 200줄이 50줄로 되면 다시 쓸 것. "시니어가 보면 과하다고 할까?"를 자문할 것.
3. 외과적 수정: 고쳐 달라는 부분만 고칠 것. 주변 코드·문장·서식을 임의로 "개선"하거나 리팩터링하지 말 것. 기존 스타일을 따를 것. 관련 없는 문제는 언급만 하고 건드리지 말 것.
4. 목표 기반 실행: 작업을 검증 가능한 성공 기준으로 바꿀 것 (예: "버그 수정" → "재현 테스트 작성 후 통과"). 여러 단계 작업은 "단계 → 검증 방법" 형태로 짧은 계획을 먼저 제시할 것.
간단한 작업에는 상황에 맞게 판단할 것.
```

프로젝트별로만 적용하고 싶으면 claude.ai 프로젝트의 **Project instructions**에 같은 내용을 넣으면 됩니다.
