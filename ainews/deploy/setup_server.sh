#!/usr/bin/env bash
# Oracle Always Free 서버(Ubuntu 이미지)에서 AI 소식 수집을 매일 자동으로 돌린다.
# 여러 번 실행해도 안전하다 (서버가 회수돼 새로 만들었을 때도 이것만 다시 실행).
#   사용: bash setup_server.sh        (먼저 PC에서 .env를 scp로 올려 두면 Gemini·Reddit 키도 쓰인다)
set -euo pipefail

REPO=https://github.com/yunjae305/INSTA_AUTO.git
BRANCH=${BRANCH:-ccr-d57bbe8e-ikmxxg}
DIR=$HOME/INSTA_AUTO

sudo apt-get update -qq
sudo apt-get install -y -qq git python3-venv
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

# 매일 08:00, 20:00 수집. 기존 줄은 지우고 다시 넣는다
LINE="0 8,20 * * * cd $DIR && .venv/bin/python ainews/ainews.py collect >> $DIR/ainews/collect.log 2>&1"
( crontab -l 2>/dev/null | grep -v 'ainews.py collect' || true; echo "$LINE" ) | crontab -
echo "cron 등록:"; crontab -l | grep 'ainews.py collect'

echo "첫 수집 실행 중 (1분 정도)..."
cd "$DIR" && .venv/bin/python ainews/ainews.py collect 2>&1 | tail -5
