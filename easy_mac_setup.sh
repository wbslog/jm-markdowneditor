#!/bin/bash
# ============================================================
#  jm-mdv (Markdown Viewer) - macOS 원클릭 설치/업데이트 스크립트
#  비개발자용: 터미널에 아래 한 줄을 붙여넣고 Enter만 누르면 됩니다.
#
#    curl -fsSL https://raw.githubusercontent.com/wbslog/jm-markdowneditor/main/easy_mac_setup.sh | bash
#
#  - 처음 실행: 소스 다운로드 → 앱 빌드 → 응용 프로그램에 설치 → 실행
#  - 다시 실행: 최신 소스로 업데이트 → 재빌드 → 교체 (업데이트도 같은 한 줄!)
# ============================================================
set -e

REPO="https://github.com/wbslog/jm-markdowneditor.git"
SRC="$HOME/jm-mdv-src"

echo ""
echo "=============================================="
echo "  jm-mdv (Markdown Viewer) 설치/업데이트"
echo "=============================================="

# 0) 개발자 명령어 도구(git/python3 포함) 확인 — 없으면 설치 창이 뜸
if ! xcode-select -p >/dev/null 2>&1; then
  echo ""
  echo "▶ Apple 명령어 도구(Command Line Tools)가 필요합니다."
  echo "  잠시 후 뜨는 창에서 [설치] 를 눌러 주세요. (약 5~10분 소요)"
  xcode-select --install || true
  echo ""
  echo "  ⏳ 설치가 모두 끝난 뒤, 이 명령을 한 번 더 실행해 주세요."
  exit 0
fi

# 1) 소스 내려받기 / 업데이트
if [ -d "$SRC/.git" ]; then
  echo "▶ 기존 소스를 최신으로 업데이트합니다 (git pull)..."
  git -C "$SRC" fetch --depth 1 origin main
  git -C "$SRC" reset --hard origin/main
else
  echo "▶ 소스를 내려받습니다 (git clone)..."
  rm -rf "$SRC"
  git clone --depth 1 "$REPO" "$SRC"
fi
cd "$SRC"

# 2) 파이썬 가상환경 + 필요한 패키지 설치 (시스템에는 아무것도 설치하지 않음)
echo "▶ 파이썬 가상환경을 준비합니다..."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
echo "▶ 필요한 패키지를 설치합니다..."
python -m pip install -q -r requirements.txt

# 3) 앱 빌드
VER=$(python - <<'PY'
import re
print(re.search(r'APP_VERSION\s*=\s*"([^"]+)"', open('app.py', encoding='utf-8').read()).group(1))
PY
)
echo "▶ jm-mdv v$VER 앱을 빌드합니다... (1~3분 정도 걸립니다)"
python -m PyInstaller --noconfirm --clean --onedir --windowed --name "jm-mdv" \
  --add-data "ui:ui" \
  --collect-submodules markdown \
  --collect-submodules pymdownx \
  --collect-submodules pygments \
  --exclude-module numpy --exclude-module pygame --exclude-module PIL \
  --exclude-module matplotlib --exclude-module pandas --exclude-module scipy \
  --exclude-module tkinter \
  app.py >/dev/null
deactivate

# 4) 응용 프로그램 폴더로 복사 (권한이 없으면 사용자 Applications 폴더 사용)
APP_DIR="/Applications"
if [ ! -w "$APP_DIR" ]; then
  APP_DIR="$HOME/Applications"
  mkdir -p "$APP_DIR"
fi
APP="$APP_DIR/jm-mdv.app"
echo "▶ 응용 프로그램 폴더로 복사합니다: $APP"
rm -rf "$APP"
ditto "dist/jm-mdv.app" "$APP"

# 5) Gatekeeper 격리 속성 제거 후 실행
xattr -cr "$APP" 2>/dev/null || true
echo ""
echo "✅ 설치 완료!  jm-mdv v$VER  →  $APP"
echo "   (다음부터는 Launchpad/응용 프로그램에서 jm-mdv 를 실행하세요)"
echo "   업데이트가 필요하면 이 한 줄을 다시 실행하면 됩니다."
open "$APP"
