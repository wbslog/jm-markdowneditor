@echo off
rem jm-mdv(Markdown Viewer) - 무설치 단일 exe 빌드 스크립트
rem 결과물: dist\jm-mdv-<버전>.exe (이 파일 하나만 다른 PC에 복사해서 바로 실행)
rem  - onefile 방식: 실행 시 임시폴더에 풀리므로 첫 시작이 몇 초 걸림
cd /d "%~dp0"

rem app.py 의 APP_VERSION 을 읽어 파일명에 버전을 붙인다 (예: jm-mdv-1.4.0.exe)
for /f %%v in ('python -c "import re;print(re.search(r'APP_VERSION\s*=\s*\"([^\"]+)\"',open('app.py',encoding='utf-8').read()).group(1))"') do set VER=%%v
if "%VER%"=="" set VER=0.0.0

pyinstaller --noconfirm --clean --onefile --windowed --name jm-mdv-%VER% ^
  --add-data "ui;ui" ^
  --collect-submodules markdown ^
  --collect-submodules pymdownx ^
  --collect-submodules pygments ^
  --exclude-module numpy ^
  --exclude-module pygame ^
  --exclude-module PIL ^
  --exclude-module matplotlib ^
  --exclude-module pandas ^
  --exclude-module scipy ^
  --exclude-module tkinter ^
  --exclude-module cryptography ^
  --exclude-module unittest ^
  --exclude-module pydoc ^
  --exclude-module doctest ^
  --exclude-module lib2to3 ^
  --exclude-module xmlrpc ^
  app.py

echo.
echo ===== 빌드 완료: dist\jm-mdv-%VER%.exe =====
pause
