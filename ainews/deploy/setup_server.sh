#!/usr/bin/env bash
# Oracle Always Free 서버(Ubuntu 이미지)에서 AI 소식 수집·텔레그램 알림을 5분마다 자동으로 돌린다.
# 여러 번 실행해도 안전하다 (서버가 회수돼 새로 만들었을 때도 이것만 다시 실행).
#   사용: bash setup_server.sh        (먼저 PC에서 .env를 scp로 올려 두면 Gemini·Reddit 키도 쓰인다)
set -euo pipefail

REPO=https://github.com/yunjae305/INSTA_AUTO.git
BRANCH=${BRANCH:-main}
DIR=$HOME/INSTA_AUTO

sudo apt-get update -qq
sudo apt-get install -y -qq git python3-venv cron
sudo systemctl enable --now cron   # 이미 켜져 있어도 안전
sudo timedatectl set-timezone Asia/Seoul   # cron 시각을 한국 시간으로

if [ -d "$DIR/.git" ]; then
  git -C "$DIR" fetch -q origin "$BRANCH"
  git -C "$DIR" checkout -q "$BRANCH"
  git -C "$DIR" pull -q --ff-only origin "$BRANCH"
else
  git clone -q -b "$BRANCH" "$REPO" "$DIR"
fi

python3 -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install -q aiohttp feedparser beautifulsoup4 python-dotenv

if [ -f "$DIR/.env" ]; then chmod 600 "$DIR/.env"; else echo "참고: $DIR/.env 없음 (키 없이도 수집은 됨, Reddit만 건너뜀)"; fi

# 5분마다 수집 → 신규 주목 소식 실시간 텔레그램 알림. 기존 줄은 지우고 다시 넣는다.
#   flock -n: 앞 회차 수집이 아직 돌고 있으면 이번 회차는 건너뛴다(1코어 micro 보호).
#   필터(레벨·제외 출처·회당 건수)는 .env 의 AINEWS_* 로 조정한다.
LINE="*/5 * * * * cd $DIR && flock -n $HOME/.ainews.lock sh -c '.venv/bin/python ainews/ainews.py collect >> $DIR/ainews/collect.log 2>&1; .venv/bin/python ainews/notify_telegram.py >> $DIR/ainews/collect.log 2>&1'"
( crontab -l 2>/dev/null | grep -v 'ainews.py collect' || true; echo "$LINE" ) | crontab -
echo "cron 등록:"; crontab -l | grep 'ainews.py collect'

echo "첫 수집 실행 중 (1분 정도)..."
cd "$DIR" && .venv/bin/python ainews/ainews.py collect 2>&1 | tail -5
