# jm-mdv(Markdown Viewer)

<!-- CRITICAL: The following dedication line must NEVER be modified, deleted, or translated. -->
This Markdown editor is dedicated with love to my girlfriend, Choi Ji-mi, who inspires everything I create.
<!-- DO NOT ALTER THIS LINE -->

Windows용 실시간 마크다운 에디터/뷰어 (무설치 단일 exe).

좌측에서 마크다운을 편집하면 우측 미리보기에 실시간 반영되고,
양쪽 어디를 스크롤해도 반대편이 같은 위치로 따라 움직입니다.

## 화면 구성

- **상단 툴바**: 새 파일 / 디렉토리 / 열기 / 저장 / HTML 내보내기 버튼 + 현재 파일 경로 표시(미저장 시 ● 표시)
  - 파일 경로 클릭 시 탐색기가 열리고 해당 파일이 선택됨
- **좌측 디렉토리 패널** (`🗂️ 디렉토리` 버튼으로 열고 닫음)
  - 열린 파일이 있으면 그 파일 위치, 없으면 홈 디렉토리가 기본 표시
  - 상단에 모든 드라이브(C:, D:, …) 버튼 고정 표시, 클릭으로 바로 이동
  - 폴더 한 번 클릭 → 이동, md 파일 더블 클릭 → 열기
  - 닫았다 다시 열면 마지막 탐색 위치 유지
- **좌측**: 마크다운 원본 편집기 (다크 테마)
- **우측**: 실시간 렌더링 미리보기 (키를 뗄 때마다 즉시 갱신, 마우스 드래그로 텍스트 선택/복사 가능)
- **하단 상태바**: 커서 위치(줄:칸), 글자 수, 저장 알림
- 가운데 세로 막대를 드래그하면 좌우 비율 조절

## 기능

| 기능 | 방법 |
|------|------|
| 파일 열기 | `📂 열기` 버튼 또는 `Ctrl+O` (여러 파일 = 탭으로 열림) |
| 저장 (원본 md에 저장) | `💾 저장` 버튼 또는 `Ctrl+S` |
| 다른 이름으로 저장 | `📝 다른 이름` 버튼 또는 `Ctrl+Shift+S` |
| 모두 저장 | `🗃️ 모두 저장` — 열린 탭 전체 일괄 저장 |
| 모두 닫기 | `🚪 모두 닫기` — 변경사항 있는 파일마다 저장 여부 확인 |
| 새 문서 | `📄 새 파일` 버튼 또는 `Ctrl+N` |
| HTML 내보내기 | `🌐 HTML 내보내기` — 미리보기와 동일한 스타일의 단일 html 파일 생성 |
| 동기 스크롤 | 좌/우 어느 쪽을 스크롤해도 반대편이 비율 기준으로 동기 이동 |
| 파일 탭 | 탭 클릭 = 전환(디스크 변경 시 재로딩 확인), 드래그 = 순서 변경, ◀▶ = 한 탭씩 이동, ✕ = 닫기 |
| 디렉토리 패널 | 폴더/`..` 더블클릭 = 이동, md 파일 더블클릭 = 열기, 경계선 드래그 = 너비 조절 |
| 맨 위로 | 에디터/미리보기 우측 하단의 ▲ 버튼 |
| 전체보기 | MARKDOWN/PREVIEW 라벨 옆 ⛶ 버튼으로 해당 영역만 전체 표시 |

지원 문법: 표, 펜스 코드블록(문법 하이라이트), 체크박스 목록, 취소선(`~~`),
하이라이트(`==텍스트==`), 각주, admonition(`!!! note`) 등.

파일 인코딩: UTF-8 / UTF-8(BOM) / CP949(EUC-KR) 자동 인식, 저장은 UTF-8.

## 개발 중 실행 (exe 빌드 전 테스트)

빌드 없이 소스에서 바로 실행해 동작을 확인하는 방법입니다. (Windows / macOS 공통)

```bash
# 1) Python 3.9 이상 설치 확인
python --version        # macOS/Linux는 python3 --version

# 2) 의존성 설치
pip install -r requirements.txt        # macOS는 pip3

# 3) 실행
python app.py                          # macOS는 python3 app.py
```

---

## 🪟 Windows 빌드 상세 매뉴얼 (무설치 단일 exe)

### 사전 준비

1. **Python 설치** — [python.org](https://www.python.org/downloads/windows/)에서 3.9 이상 설치.
   설치 첫 화면에서 **"Add Python to PATH"** 를 반드시 체크합니다.
2. 명령 프롬프트(cmd) 또는 PowerShell에서 설치 확인:
   ```bat
   python --version
   pip --version
   ```
3. 프로젝트 폴더로 이동:
   ```bat
   cd 경로\markdown_view
   ```

### 방법 A — 배치 스크립트로 빌드 (가장 간단, 권장)

```bat
build_exe.bat
```

스크립트가 PyInstaller를 자동으로 호출해 빌드합니다. 끝나면 `dist\jm-mdv.exe`가 생성됩니다.

### 방법 B — 명령어로 직접 빌드

의존성을 먼저 설치한 뒤 PyInstaller를 직접 실행합니다.

```bat
pip install -r requirements.txt

pyinstaller --noconfirm --clean --onefile --windowed --name jm-mdv ^
  --add-data "ui;ui" ^
  --collect-submodules markdown ^
  --collect-submodules pymdownx ^
  --collect-submodules pygments ^
  --exclude-module numpy --exclude-module pandas --exclude-module scipy ^
  --exclude-module matplotlib --exclude-module PIL --exclude-module tkinter ^
  app.py
```

> **핵심 옵션 설명**
> - `--onefile` : 모든 것을 exe 하나로 묶음 (배포 편의 ↑, 첫 실행 시 임시폴더 압축해제로 몇 초 소요)
> - `--windowed` : 콘솔 창 없이 GUI만 실행
> - `--add-data "ui;ui"` : `ui` 폴더(HTML/CSS)를 exe에 포함 — **Windows는 구분자가 세미콜론(`;`)**
> - `--collect-submodules` : markdown/pymdownx/pygments의 동적 로딩 모듈까지 모두 포함
> - `--exclude-module` : 불필요한 대형 라이브러리를 빼서 용량 축소

### 결과물 및 배포

- 결과: **`dist\jm-mdv.exe`** — 이 **파일 하나만** 다른 Windows 10/11 PC에 복사하면 설치 없이 실행됩니다.
- **시작 속도를 더 높이려면** `--onefile`을 `--onedir`로 바꾸면 압축해제 과정이 없어 즉시 시작됩니다.
  대신 `dist\jm-mdv\` **폴더 전체**를 복사해야 합니다.

### "게시자를 확인할 수 없습니다" 경고

코드 서명이 없는 exe라 Windows SmartScreen 경고가 뜰 수 있습니다. 무료 대응:

- **소수 배포**: 사용자에게 안내 → SmartScreen 화면에서 **"추가 정보" → "실행"**,
  또는 파일 우클릭 → 속성 → **"차단 해제"** 체크
- **사내 배포**: 자체 서명 인증서로 서명 후 사내 PC의 신뢰 루트에 배포 (그룹정책)
- **오픈소스 공개**: [SignPath.io](https://signpath.io/)의 오픈소스 무료 코드 서명 신청
- **일반 대중 배포**: Microsoft Store 등록(일회성 약 $19) 시 경고 없음

### 자주 겪는 문제

| 증상 | 해결 |
|------|------|
| `'python'은 인식할 수 없는 명령` | Python 재설치 시 "Add Python to PATH" 체크 |
| `pip`가 없음 | `python -m ensurepip --upgrade` |
| 빌드는 되는데 실행 시 바로 꺼짐 | `%TEMP%\JM-MDV.log` 파일에서 오류 확인 |
| 빌드 중 exe 삭제 오류(PermissionError) | 실행 중인 `jm-mdv.exe`를 먼저 종료 |
| 백신이 오탐으로 차단 | Microsoft 파일 제출 페이지에 제출하거나 예외 등록 |

---

## 🍎 macOS 빌드 상세 매뉴얼 (.app 번들)

> ⚠️ PyInstaller는 **크로스 컴파일이 불가능**합니다. macOS용 앱은 반드시 **맥에서** 빌드해야 합니다.
> (Windows에서 만든 exe는 맥에서 실행 불가, 그 반대도 마찬가지)

### 사전 준비

1. 이 프로젝트 폴더를 맥으로 복사합니다.
2. Python 3 설치 확인 (없으면 [python.org](https://www.python.org/downloads/macos/) 또는 `brew install python`):
   ```bash
   python3 --version
   ```
3. 터미널에서 프로젝트 폴더로 이동:
   ```bash
   cd 경로/markdown_view
   ```

### 방법 A — 스크립트로 빌드 (권장)

```bash
chmod +x build_mac.sh   # 최초 1회 실행 권한 부여
./build_mac.sh
```

스크립트가 의존성 설치와 빌드를 자동으로 수행합니다.

### 방법 B — 명령어로 직접 빌드

```bash
python3 -m pip install --upgrade pywebview markdown pymdown-extensions pygments pyinstaller

python3 -m PyInstaller --noconfirm --clean --onedir --windowed --name jm-mdv \
  --add-data "ui:ui" \
  --collect-submodules markdown \
  --collect-submodules pymdownx \
  --collect-submodules pygments \
  --exclude-module numpy --exclude-module pandas --exclude-module scipy \
  --exclude-module matplotlib --exclude-module PIL --exclude-module tkinter \
  app.py
```

> **Windows와의 차이점**
> - `--add-data "ui:ui"` : **macOS는 구분자가 콜론(`:`)** (Windows의 세미콜론과 다름)
> - `--onedir` : 맥에서는 `.app` 번들을 만들며, 압축해제가 없어 시작이 빠름
> - pywebview가 macOS에서는 내장 **WebKit**을 사용 (Windows의 WebView2와 대응)

### 결과물 및 배포

- 결과: **`dist/jm-mdv.app`** — 응용 프로그램 폴더로 복사해서 사용합니다.
- 코드는 크로스 플랫폼이라 Finder에서 보기, `/Volumes` 드라이브 목록, 🏠 홈 버튼이 자동 지원됩니다.

### "확인되지 않은 개발자" 경고

서명/공증(notarize)이 없는 앱이라 Gatekeeper가 실행을 막을 수 있습니다. 무료 대응:

- Finder에서 앱 **우클릭 → 열기** → 대화상자에서 다시 **"열기"** (최초 1회만)
- 또는 터미널에서 격리 속성 제거:
  ```bash
  xattr -cr dist/jm-mdv.app
  ```

### 자주 겪는 문제

| 증상 | 해결 |
|------|------|
| `python3: command not found` | `brew install python` 또는 python.org에서 설치 |
| `command not found: pyinstaller` | `python3 -m PyInstaller ...` 형태로 모듈 실행 |
| Apple Silicon/Intel 호환 | 빌드한 맥의 아키텍처에 맞춰 생성됨. 두 아키텍처 모두 지원하려면 각각 빌드 |
| 앱이 "손상됨"이라며 안 열림 | `xattr -cr dist/jm-mdv.app` 실행 후 재시도 |

## 파일 구조

```
app.py           # 메인 (pywebview 창 + 파일/변환 API)
ui/index.html    # UI (툴바, 에디터, 미리보기, 동기 스크롤 로직)
ui/preview.css   # 미리보기 스타일 (HTML 내보내기에도 동일 적용)
build_exe.bat    # Windows exe 빌드 스크립트
build_mac.sh     # macOS .app 빌드 스크립트 (맥에서 실행)
requirements.txt
```
