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
| 파일 메뉴 | 상단 `📁 파일` 드롭다운에 열기/저장/다른 이름 저장/모두 저장/모두 닫기 그룹화 |
| 파일 열기 | `📁 파일 → 📂 열기` 또는 `Ctrl+O` (여러 파일 = 탭으로 열림) |
| 저장 (원본 md에 저장) | `📁 파일 → 💾 저장` 또는 `Ctrl+S` |
| 다른 이름으로 저장 | `📁 파일 → 📝 다른 이름 저장` 또는 `Ctrl+Shift+S` |
| 모두 저장 | `📁 파일 → 🗃️ 모두 저장` — 확인 후 열린 탭 전체 일괄 저장 |
| 모두 닫기 | `📁 파일 → 🚪 모두 닫기` — 확인 후 닫기(변경사항 있는 파일마다 저장 여부 확인) |
| 새 문서 | `📄 새 파일` 버튼 또는 `Ctrl+N` |
| 검색 | `🔍 검색` 버튼 또는 `Ctrl+F` — 에디터/미리보기 동시 하이라이트, 현재 위치 강조 |
| HTML 내보내기 | `🌐 HTML 내보내기` — 미리보기와 동일한 스타일의 단일 html 파일 생성 |
| 설정 | `⚙️ 설정` — 좌측 메뉴(기본 설정 / Confluence 연결). 기본 설정에서 백업 폴더 지정 |
| 자동 백업 | 백업 폴더 지정 시 저장할 때마다 `파일명_년월일시분초` 사본을 원본 경로 구조로 백업 |
| Confluence 연동 | 연동 완료 시 `🔗 Confluence` 메뉴 노출 — 문서 목록 조회·열기·편집·저장(업데이트), 새 페이지 생성 |
| 설명서 | `❓ 설명서` — 프로그램 사용법 / 마크다운 문법 30선 / 버전 기록 (모달, 검색 지원) |
| 언어 전환 | 우측 상단 `KOR / ENG` 버튼 — 메뉴·설명·안내 전체를 한/영으로 전환(설정 저장) |
| 파일 관리 | 디렉토리 패널에서 우클릭(이름 변경·삭제·새 파일), 드래그로 다른 폴더 이동 |
| 드래그 앤 드롭 | 탐색기(Windows)/Finder(macOS)에서 파일을 드롭하면 원본 경로로 열림(파일명·경로 표시, 저장 시 원본 업데이트+백업) |
| 파일 정보 | 에디터 상단에 현재 파일의 최초 생성일 / 최근 수정일 표시 |
| 동기 스크롤 | 좌/우 어느 쪽을 스크롤해도 반대편이 비율 기준으로 동기 이동 |
| 파일 탭 | 탭 클릭 = 전환(디스크 변경 시 재로딩 확인), 드래그 = 순서 변경, ◀▶ = 한 탭씩 이동, ✕ = 닫기 |
| 디렉토리 패널 | 폴더/`..` 한 번 클릭 = 이동, 파일 더블클릭 = 열기(숨김·모든 파일 표시), 경계선 드래그 = 너비 조절 |
| 맨 위로 | 에디터/미리보기 우측 하단의 ▲ 버튼 |
| 전체보기 | MARKDOWN/PREVIEW 라벨 옆 ⛶ 버튼으로 해당 영역만 전체 표시 |

> 🖥️ **단축키**: Windows/Linux는 `Ctrl`, **macOS는 `⌘(Command)`** 를 사용합니다. (예: 저장 = `Ctrl+S` / `⌘+S`)

지원 문법: 표, 펜스 코드블록(문법 하이라이트), 체크박스 목록, 취소선(`~~`),
하이라이트(`==텍스트==`), 각주, admonition(`!!! note`) 등.

파일 인코딩: UTF-8 / UTF-8(BOM) / CP949(EUC-KR) 자동 인식, 저장은 UTF-8.

## 💾 자동 백업

**⚙️ 설정 → 기본 설정 → 백업 파일 저장 경로**에서 백업 폴더를 지정하면, 파일을 저장할 때마다
원본은 원래 위치에 그대로 업데이트되고, **별도의 백업 사본**이 다음 규칙으로 생성됩니다.

- 파일명: `원본이름_YYYYMMDDHHMMSS.확장자` (예: `note_20260708153012.md`)
- 위치: 백업 폴더 아래에 **원본 경로 구조를 그대로 재현**하여 저장
  (예: 원본이 `X:\docs\note.md`, 백업 폴더가 `D:\bak` → `D:\bak\X\docs\note_...md`)
- 백업 폴더를 지정하지 않으면 백업 사본은 만들지 않습니다.

## 🔗 Confluence 연동

Confluence Cloud 문서(특정 **폴더** 하위)를 앱에서 바로 열고 편집·저장·삭제할 수 있습니다.
커스텀 도메인(사내 위키 등) 뒤의 Confluence Cloud도 **cloudId 게이트웨이**(`api.atlassian.com/ex/confluence/{cloudId}`)로 호출하여 동작합니다.

1. [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)에서 **Create API token**으로 토큰을 발급합니다. (스코프 없는 **클래식 토큰** 권장)
2. 앱 상단 **⚙️ 설정 → Confluence 연결**을 열고 아래 4개를 입력합니다.
   - **로그인 아이디(email)**: 토큰을 만든 Atlassian 계정 이메일
   - **토큰 이름**: 라벨(식별용, 인증엔 미사용)
   - **토큰 값**: 발급한 API 토큰
   - **접근할 폴더 링크**: 대상 폴더 URL
     (예: `https://사이트/wiki/spaces/KEY/folder/466190962`, 스페이스 링크도 가능)
3. **🔌 연동 테스트**로 폴더 접근을 확인한 뒤 **저장**합니다. (cloudId는 자동 조회·저장)
4. 연동이 완료되면 상단에 **🔗 Confluence** 메뉴가 나타납니다.
   - 폴더 하위 문서 목록을 조회하고, 클릭해 열어 편집한 뒤 `Ctrl+S`(macOS는 `⌘+S`)로 **업데이트**(버전 자동 +1)합니다.
   - 새 문서는 **"현재 내용을 새 페이지로 저장"**으로 제목을 입력해 생성(v1 우선·v2 폴백)합니다.
   - 목록의 🗑️ 버튼으로 페이지를 **삭제(휴지통 이동, 복구 가능)** 합니다.

> 편집 왕복(round-trip)을 위해 원본 마크다운을 페이지의 content property로 함께 보존합니다.
> 설정값(토큰 포함)은 사용자 홈의 `.jm-mdv-confluence.json`에 로컬 저장됩니다.
> 설정값은 사용자 홈의 `.jm-mdv-confluence.json`에 저장됩니다(토큰 포함, 로컬 저장).

## 🗒️ 버전 기록

앱 안의 **`❓ 설명서` → `버전 기록`** 탭에서도 확인할 수 있습니다.

| 버전 | 날짜 | 주요 내용 |
|------|------|-----------|
| **v1.6.2** | 2026-07-09 | Confluence **지연 로딩** — 직계 목록만 조회, 클릭 시점에 하위 로딩. 🔄 새로고침 텍스트 버튼(한/영) |
| **v1.6.1** | 2026-07-09 | Confluence **하위 폴더 계층 수정** — 폴더 타입 포함 재귀 조회로 문서가 최상단에 새는 문제 해결, 폴더 우선 정렬 |
| **v1.6.0** | 2026-07-08 | Confluence 목록 **제목 검색 필터**, 메뉴 열 때마다 **새로고침**, ☁️ 컨플 저장 위치를 **디렉토리 패널식 탐색 UI**로 변경 |
| **v1.5.0** | 2026-07-08 | Confluence **계층(트리) 조회**·창 확대, **저장 분기**(연 문서 직접 업데이트 / 로컬 문서는 ☁️ 컨플 저장으로 위치·제목 선택), 저장 XHTML 400 오류 수정, cloudId 직접 입력 |
| **v1.4.0** | 2026-07-08 | **🔗 Confluence 재구현**(cloudId 게이트웨이로 403 해결, 폴더 링크·CRUD·삭제), **⌨️ macOS 단축키(⌘)**, macOS 정상 동작 |
| **v1.3.0** | 2026-07-08 | 드래그 앤 드롭을 **원본 경로로 열기**로 개선(파일명·경로 표시, 저장 시 원본 업데이트+백업) |
| **v1.2.0** | 2026-07-08 | **🎨 글래스모피즘 테마**, **📁 파일 메뉴 그룹화**, **🔗 Confluence 연동**(설정·테스트·문서 열기/저장/생성), **💾 자동 백업**, 숨김·모든 파일 표시, OS 드래그 앤 드롭으로 열기 |
| **v1.1.0** | 2026-07-08 | 한국어/영어 **언어 전환**(KOR/ENG) 추가 — 메뉴·설명·안내·설명서 전체 |
| **v1.0.0** | 2026-07-07 | 첫 정식 버전 — 검색, 설명서 모달, 파일 관리, 파일 정보, 동기 스크롤, HTML 내보내기 |

---

## 📥 다운로드 후 실행 (릴리스 사용자용)

[GitHub Releases](../../releases)에서 자신의 OS에 맞는 파일을 받아 실행합니다.
직접 빌드하지 않고 바로 쓰고 싶은 분은 이 방법을 사용하세요.

### 🪟 Windows

1. 릴리스에서 **`jm-mdv.exe`** (또는 `jm-mdv-win.zip`)를 받습니다. zip이면 압축을 풉니다.
2. `jm-mdv.exe`를 더블클릭해 실행합니다.
3. **"Windows의 PC 보호"(SmartScreen)** 경고가 뜨면 → **추가 정보** → **실행**을 누릅니다.
   (서명이 없는 앱이라 나오는 정상 경고이며, 최초 1회만 확인하면 됩니다.)

### 🍎 macOS

> ⚠️ macOS 앱(`.app`)은 **폴더 번들**이라 압축 방식이 중요합니다. 반드시 아래처럼 풀어야
> 내부 링크가 보존되어 정상 실행됩니다. (잘못 풀면 "이 Mac에서 실행할 수 없습니다" 오류)

1. 릴리스에서 자신의 칩에 맞는 zip을 받습니다.
   - Apple Silicon(M1/M2/M3): `jm-mdv-mac-arm64.zip`
   - Intel: `jm-mdv-mac-x86_64.zip`
   - (본인 칩 확인: 터미널에서 `uname -m` → `arm64` 또는 `x86_64`)
2. **압축 풀기** — Finder에서 zip을 **더블클릭**하거나, 터미널에서:
   ```bash
   ditto -x -k jm-mdv-mac-arm64.zip ./
   ```
3. **격리 표식 제거 후 실행** (다운로드한 앱은 이 과정이 필요합니다):
   ```bash
   xattr -cr jm-mdv.app     # 앱이 있는 위치에서 실행
   open jm-mdv.app
   ```
   또는 Finder에서 앱 **우클릭 → 열기 → (대화상자에서) 열기** (최초 1회).

> **실행이 안 될 때 원인 빠르게 확인** — 터미널에서 직접 실행하면 실제 오류가 표시됩니다:
> ```bash
> ./jm-mdv.app/Contents/MacOS/jm-mdv
> ```
> - `bad CPU type` → 칩에 맞지 않는 파일(다른 아키텍처 zip을 받은 경우)
> - `Library not loaded / image not found` → 압축을 잘못 풀어 번들이 깨짐 → 2번을 `ditto`로 다시
> - `developer cannot be verified` → 3번의 `xattr -cr` 로 해결

---

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

### 가상환경(.venv) 사용 — 권장

시스템 Python을 더럽히지 않고 이 프로젝트 전용으로 라이브러리를 격리하려면 가상환경을 사용하세요.
특히 macOS는 시스템 Python 보호(`externally-managed-environment` 오류) 때문에 가상환경이 사실상 필요합니다.

**Windows (cmd / PowerShell)**

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

> - 활성화되면 프롬프트 앞에 `(.venv)` 가 표시됩니다. 이후 `pip`/`python`은 모두 이 가상환경을 가리킵니다.
> - 아래 **빌드**도 이 활성화 상태에서 실행하면 격리된 환경으로 깔끔하게 빌드됩니다.
> - 작업이 끝나면 `deactivate` 로 빠져나옵니다.
> - `.venv/` 폴더는 `.gitignore`에 포함되어 git에 커밋되지 않습니다.
>
> ⚠️ **가상환경은 개발/빌드하는 사람에게만 해당합니다.** 빌드 결과물(exe/.app)은 Python과
> 모든 라이브러리를 번들에 포함하므로, **배포받은 최종 사용자는 Python도 가상환경도 필요 없습니다.**

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

### 방법 B — 명령어로 직접 빌드 (가상환경 사용, 권장)

시스템 Python을 건드리지 않도록 **가상환경 안에서** 의존성을 설치하고 빌드합니다.

```bat
REM 1) 가상환경 생성 및 활성화 (프로젝트 폴더에서)
python -m venv .venv
.venv\Scripts\activate

REM 2) 의존성 설치 (이 가상환경에만 설치됨)
pip install -r requirements.txt

REM 3) PyInstaller로 빌드
pyinstaller --noconfirm --clean --onefile --windowed --name jm-mdv ^
  --add-data "ui;ui" ^
  --collect-submodules markdown ^
  --collect-submodules pymdownx ^
  --collect-submodules pygments ^
  --exclude-module numpy --exclude-module pandas --exclude-module scipy ^
  --exclude-module matplotlib --exclude-module PIL --exclude-module tkinter ^
  app.py

REM 4) 빌드가 끝나면 가상환경 빠져나오기
deactivate
```

> 가상환경 없이 곧바로 빌드하려면 위에서 1·4번(venv 생성/deactivate)을 빼고,
> 2번을 `pip install -r requirements.txt`로 실행한 뒤 3번 명령만 그대로 쓰면 됩니다.
> (PowerShell에서 활성화가 막히면 `Set-ExecutionPolicy -Scope Process RemoteSigned` 후 `.venv\Scripts\Activate.ps1`)

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

### 빌드 (가상환경 사용, 권장)

macOS는 시스템 Python 보호 정책 때문에 **가상환경 사용을 강력히 권장**합니다.
아래 흐름에서 3번은 **스크립트(3.1)** 또는 **수동 명령(3.2)** 중 하나만 선택해 실행하면 됩니다.

```bash
# 1) 가상환경 생성 및 활성화 (프로젝트 폴더에서)
python3 -m venv .venv
source .venv/bin/activate

# 2) 의존성 설치 (이 가상환경에만 설치됨)
pip install -r requirements.txt

# 3.1) 스크립트로 빌드 (의존성 설치 + 빌드를 한 번에 처리)
chmod +x build_mac.sh   # 최초 1회 실행 권한 부여
./build_mac.sh

# 또는 아래와 같이 수동으로 빌드하세요.

# 3.2) PyInstaller로 직접 빌드
python -m PyInstaller --noconfirm --clean --onedir --windowed --name jm-mdv \
  --add-data "ui:ui" \
  --collect-submodules markdown \
  --collect-submodules pymdownx \
  --collect-submodules pygments \
  --exclude-module numpy --exclude-module pandas --exclude-module scipy \
  --exclude-module matplotlib --exclude-module PIL --exclude-module tkinter \
  app.py

# 4) 빌드가 끝나면 가상환경 빠져나오기
deactivate
```

> 가상환경 없이 빌드하려면 1·4번을 빼고, 2번을
> `python3 -m pip install --upgrade pywebview markdown pymdown-extensions pygments pyinstaller`로
> 바꾼 뒤 3.2번을 `python3 -m PyInstaller ...`로 실행하면 됩니다.

> **Windows와의 차이점**
> - `--add-data "ui:ui"` : **macOS는 구분자가 콜론(`:`)** (Windows의 세미콜론과 다름)
> - `--onedir` : 맥에서는 `.app` 번들을 만들며, 압축해제가 없어 시작이 빠름
> - pywebview가 macOS에서는 내장 **WebKit**을 사용 (Windows의 WebView2와 대응)

### 결과물 및 배포

- 결과: **`dist/jm-mdv.app`** — 응용 프로그램 폴더로 복사해서 사용합니다.
- 코드는 크로스 플랫폼이라 Finder에서 보기, `/Volumes` 드라이브 목록, 🏠 홈 버튼이 자동 지원됩니다.

### GitHub 릴리스에 올리기 (중요)

`.app`은 **폴더 번들**이라 그냥 올리면 안 되고, **심볼릭 링크·실행 권한을 보존하는 방식으로 압축**해야 합니다.
Finder "압축"도 되지만, 확실하게 하려면 **`ditto`** 로 만드세요:

```bash
# 배포용 zip 생성 (심링크·권한·리소스 보존)
ditto -c -k --sequesterRsrc --keepParent dist/jm-mdv.app jm-mdv-mac-arm64.zip
#                                                          └ Intel 빌드면 -x86_64 로
```

그런 다음 GitHub 저장소 → **Releases → Draft a new release** → 태그 지정(예: `v1.1.0`)
→ 위 zip을 **드래그해서 첨부** → **Publish**.

> ⚠️ **아키텍처 주의**: PyInstaller는 **빌드한 맥의 칩으로만** 만듭니다.
> Apple Silicon에서 빌드한 앱은 Intel 맥에서 실행되지 않습니다(그 반대는 Rosetta로 실행 가능).
> 두 칩 모두 지원하려면 각 칩에서 빌드해 **arm64 / x86_64 두 개의 zip**을 올리거나,
> Rosetta로 x86_64 하나만 빌드해 올리면 됩니다. (`arch -x86_64 python3 -m venv ...` 로 x86_64 환경 구성)

### "확인되지 않은 개발자" / "손상됨" 경고

서명/공증(notarize)이 없는 앱이라 Gatekeeper가 실행을 막을 수 있습니다. 무료 대응:

- Finder에서 앱 **우클릭 → 열기** → 대화상자에서 다시 **"열기"** (최초 1회만)
- 또는 터미널에서 격리 속성 제거:
  ```bash
  xattr -cr jm-mdv.app
  ```

### 자주 겪는 문제

| 증상 | 해결 |
|------|------|
| `python3: command not found` | `brew install python` 또는 python.org에서 설치 |
| `command not found: pyinstaller` | `python3 -m PyInstaller ...` 형태로 모듈 실행 |
| "이 Mac에서 실행할 수 없습니다" (다른 칩) | 대상 칩에 맞게 빌드. Apple Silicon→Intel은 실행 불가 → x86_64로 빌드 |
| "이 Mac에서 실행할 수 없습니다" (**같은 칩인데도**) | zip이 번들을 깨뜨린 것 → `ditto`로 압축/해제. `./jm-mdv.app/Contents/MacOS/jm-mdv` 직접 실행해 원인 확인 |
| 앱이 "손상됨"이라며 안 열림 | `xattr -cr jm-mdv.app` 실행 후 재시도 |
| 아키텍처 확인 | `lipo -archs jm-mdv.app/Contents/MacOS/jm-mdv` (arm64 / x86_64 / 둘 다) |

## 파일 구조

```
app.py           # 메인 (pywebview 창 + 파일/변환 API)
ui/index.html    # UI (툴바, 에디터, 미리보기, 동기 스크롤 로직)
ui/preview.css   # 미리보기 스타일 (HTML 내보내기에도 동일 적용)
build_exe.bat    # Windows exe 빌드 스크립트
build_mac.sh     # macOS .app 빌드 스크립트 (맥에서 실행)
requirements.txt
```
