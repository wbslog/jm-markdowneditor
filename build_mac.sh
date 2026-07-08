#!/bin/bash
# jm-mdv(Markdown Viewer) - macOS용 빌드 스크립트
# ⚠️ 반드시 맥(macOS)에서 실행해야 합니다. (PyInstaller는 크로스 컴파일 불가)
#
# 사용법:
#   1. 이 프로젝트 폴더를 맥으로 복사
#   2. 터미널에서:  chmod +x build_mac.sh && ./build_mac.sh
#   3. 결과물: dist/jm-mdv-<버전>.app  (응용 프로그램 폴더로 복사해서 사용)
set -e
cd "$(dirname "$0")"

python3 -m pip install --upgrade pywebview markdown pymdown-extensions pygments pyinstaller

# app.py 의 APP_VERSION 을 읽어 파일명에 버전을 붙인다 (예: jm-mdv-1.4.0.app)
VER=$(python3 -c "import re;print(re.search(r'APP_VERSION\s*=\s*\"([^\"]+)\"',open('app.py',encoding='utf-8').read()).group(1))")
[ -z "$VER" ] && VER="0.0.0"

# macOS는 --add-data 구분자가 ':' 입니다 (Windows는 ';')
# --onedir: 실행 시 압축해제가 없어 시작이 빠름 (.app 번들 생성)
python3 -m PyInstaller --noconfirm --clean --onedir --windowed --name "jm-mdv-$VER" \
  --add-data "ui:ui" \
  --collect-submodules markdown \
  --collect-submodules pymdownx \
  --collect-submodules pygments \
  --exclude-module numpy \
  --exclude-module pygame \
  --exclude-module PIL \
  --exclude-module matplotlib \
  --exclude-module pandas \
  --exclude-module scipy \
  --exclude-module tkinter \
  app.py

echo ""
echo "===== 빌드 완료: dist/jm-mdv-$VER.app ====="
echo "처음 실행 시 '확인되지 않은 개발자' 경고가 나오면:"
echo "  Finder에서 우클릭 → 열기, 또는: xattr -cr dist/jm-mdv-$VER.app"
