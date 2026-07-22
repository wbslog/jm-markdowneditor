# -*- coding: utf-8 -*-
"""Markdown View - 실시간 마크다운 에디터/뷰어 (Windows)"""
import base64
import datetime
import json
import os
import re
import shutil
import ssl
import string
import subprocess
import sys
import tempfile
import threading
import traceback
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

import markdown
import webview
from webview.dom import DOMEventHandler
from pygments.formatters import HtmlFormatter

APP_NAME = "jm-mdv(Markdown Viewer)"
APP_VERSION = "1.19.0"  # 버전 변경 시 여기와 ui/index.html의 VERSION_MD를 함께 갱신


def resource_path(rel):
    """PyInstaller 빌드/일반 실행 양쪽에서 리소스 경로 반환"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


MD_EXTENSIONS = [
    "pymdownx.superfences",
    "pymdownx.highlight",
    "pymdownx.inlinehilite",
    "pymdownx.tilde",
    "pymdownx.caret",
    "pymdownx.mark",
    "pymdownx.tasklist",
    "pymdownx.magiclink",
    "pymdownx.betterem",
    "tables",
    "admonition",
    "attr_list",
    "def_list",
    "footnotes",
    "abbr",
    "sane_lists",
    "md_in_html",
    "toc",
]
MD_CONFIGS = {
    "pymdownx.highlight": {"css_class": "highlight", "guess_lang": True},
    "pymdownx.tasklist": {"custom_checkbox": True},
    "toc": {"permalink": False},
}

PYGMENTS_CSS = HtmlFormatter(style="default").get_style_defs(".highlight")

GITHUB_REPO = "wbslog/jm-markdowneditor"  # 자동 업데이트 확인 대상 저장소
SESSION_FILE = os.path.join(os.path.expanduser("~"), ".jm-mdv-session.json")
UPDATE_STATE_FILE = os.path.join(os.path.expanduser("~"), ".jm-mdv-update.json")
CONFLUENCE_FILE = os.path.join(os.path.expanduser("~"), ".jm-mdv-confluence.json")
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".jm-mdv-settings.json")
# 편집 왕복(round-trip)을 위해 페이지에 원본 마크다운을 저장하는 content property 키
MD_PROP_KEY = "jmMdvMarkdown"

# 사내망 SSL 인터셉트(회사 프록시 인증서) 대응: 개발/사내 환경용 완화 컨텍스트.
# (운영 배포 시 사내 루트CA 신뢰로 대체 권장)
_CONF_SSL_CTX = ssl.create_default_context()
_CONF_SSL_CTX.check_hostname = False
_CONF_SSL_CTX.verify_mode = ssl.CERT_NONE


class Api:
    def __init__(self):
        self._window = None
        self.current_path = None
        self._md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=MD_CONFIGS)
        self._lock = threading.Lock()
        self._cloud_ids = {}  # host -> cloudId 캐시

    # ---------- 변환 ----------
    def render(self, text):
        with self._lock:
            self._md.reset()
            try:
                return {"html": self._md.convert(text or "")}
            except Exception as e:  # 파싱 실패 시에도 앱이 죽지 않도록
                return {"html": f"<pre>렌더링 오류: {e}</pre>"}

    # ---------- 파일 ----------
    def _read_file(self, path):
        for enc in ("utf-8-sig", "utf-8", "cp949"):
            try:
                with open(path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _set_title(self):
        name = os.path.basename(self.current_path) if self.current_path else "새 문서"
        self._window.set_title(f"{name} - {APP_NAME} v{APP_VERSION}")

    def open_file(self):
        result = self._window.create_file_dialog(
            webview.FileDialog.OPEN,
            file_types=("Markdown 파일 (*.md;*.markdown;*.mdown;*.txt)", "모든 파일 (*.*)"),
        )
        if not result:
            return None
        return self.open_path(result[0])

    def open_path(self, path):
        """탐색 패널 등에서 경로로 직접 파일 열기"""
        if not path or not os.path.isfile(path):
            return None
        content = self._read_file(path)
        self.current_path = path
        self._set_title()
        return {"path": path, "content": content}

    MD_FILE_EXTS = (".md", ".markdown", ".mdown", ".txt")

    @staticmethod
    def _drives():
        """드라이브(디스크) 목록 - Windows: C:\\ D:\\ ..., macOS: / 와 /Volumes/*"""
        if os.name == "nt":
            return [
                {"label": f"{c}:", "path": f"{c}:\\"}
                for c in string.ascii_uppercase
                if os.path.exists(f"{c}:\\")
            ]
        drives = [{"label": "/", "path": "/"}]
        if sys.platform == "darwin" and os.path.isdir("/Volumes"):
            try:
                for name in sorted(os.listdir("/Volumes")):
                    p = os.path.join("/Volumes", name)
                    if os.path.isdir(p):
                        drives.append({"label": name, "path": p})
            except OSError:
                pass
        drives.append({"label": "🏠", "path": os.path.expanduser("~")})
        return drives

    def list_dir(self, path=None):
        """폴더 탐색 패널용: 하위 폴더와 마크다운 파일 목록 반환 (drives는 항상 포함)"""
        drives = self._drives()
        if path == "::drives":
            return {
                "path": "::drives",
                "name": "내 PC",
                "parent": None,
                "drives": drives,
                "dirs": [{"name": d["label"], "path": d["path"]} for d in drives],
                "files": [],
            }

        if not path:
            if self.current_path:
                path = os.path.dirname(self.current_path)
            else:
                path = os.path.expanduser("~")
        path = os.path.normpath(path)
        if not os.path.isdir(path):
            path = os.path.expanduser("~")

        parent = os.path.dirname(path)
        if parent == path:  # 드라이브 루트
            parent = "::drives"

        dirs, files = [], []
        try:
            entries = sorted(os.scandir(path), key=lambda e: e.name.lower())
            for e in entries:
                # 숨김/시스템 항목도 표시 (단, 접근 시 오류나는 특수 항목만 제외)
                if e.name == "System Volume Information":
                    continue
                hidden = e.name.startswith(".") or self._is_hidden(e.path)
                md = e.name.lower().endswith(self.MD_FILE_EXTS)
                try:
                    if e.is_dir():
                        dirs.append({"name": e.name, "path": e.path, "hidden": hidden})
                    elif e.is_file():
                        # 마크다운뿐 아니라 모든 파일 표시
                        files.append({"name": e.name, "path": e.path, "hidden": hidden, "md": md})
                except OSError:
                    continue
        except (PermissionError, OSError):
            pass

        return {
            "path": path,
            "name": os.path.basename(path) or path,
            "parent": parent,
            "drives": drives,
            "dirs": dirs,
            "files": files,
        }

    @staticmethod
    def _is_hidden(path):
        """Windows 숨김 속성 파일 여부 (그 외 OS는 이름의 '.' 접두로 판단)"""
        if os.name == "nt":
            try:
                import ctypes

                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                if attrs == -1:
                    return False
                # FILE_ATTRIBUTE_HIDDEN(0x2) | FILE_ATTRIBUTE_SYSTEM(0x4)
                return bool(attrs & 0x2) or bool(attrs & 0x4)
            except Exception:
                return False
        return os.path.basename(path).startswith(".")

    def file_times(self, path):
        """파일의 최초 생성일/최근 수정일 (에디터 상단 표시용)"""
        if not path or not os.path.isfile(path):
            return None
        try:
            st = os.stat(path)
        except OSError:
            return None

        def fmt(t):
            return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")

        # Windows: st_ctime = 생성 시각 / macOS: st_birthtime 사용
        created = getattr(st, "st_birthtime", None) or st.st_ctime
        return {"created": fmt(created), "modified": fmt(st.st_mtime)}

    # ---------- 폴더 탐색 패널: 파일 관리 ----------
    INVALID_NAME_CHARS = '\\/:*?"<>|'

    def create_file(self, dir_path):
        """noname.md 로 새 파일 생성 (중복 시 noname_1.md, noname_2.md ...)"""
        if not dir_path or not os.path.isdir(dir_path):
            return {"error": "폴더를 찾을 수 없습니다"}
        base, ext = "noname", ".md"
        path = os.path.join(dir_path, base + ext)
        n = 1
        while os.path.exists(path):
            path = os.path.join(dir_path, f"{base}_{n}{ext}")
            n += 1
        try:
            with open(path, "x", encoding="utf-8") as f:
                f.write("")
        except OSError as e:
            return {"error": str(e)}
        return {"path": path, "name": os.path.basename(path)}

    def create_folder(self, dir_path):
        """noname 폴더 생성 (중복 시 noname_1, noname_2 ...)"""
        if not dir_path or not os.path.isdir(dir_path):
            return {"error": "폴더를 찾을 수 없습니다"}
        base = "noname"
        path = os.path.join(dir_path, base)
        n = 1
        while os.path.exists(path):
            path = os.path.join(dir_path, f"{base}_{n}")
            n += 1
        try:
            os.makedirs(path)
        except OSError as e:
            return {"error": str(e)}
        return {"path": path, "name": os.path.basename(path)}

    def rename_path(self, path, new_name):
        """파일/폴더 이름 변경 (같은 폴더 안에서)"""
        if not os.path.exists(path):
            return {"error": "파일/폴더를 찾을 수 없습니다"}
        new_name = (new_name or "").strip()
        if not new_name or any(c in new_name for c in self.INVALID_NAME_CHARS):
            return {"error": "올바르지 않은 파일 이름입니다"}
        new_path = os.path.join(os.path.dirname(path), new_name)
        if os.path.normcase(new_path) == os.path.normcase(path):
            return {"path": path, "name": os.path.basename(path)}
        if os.path.exists(new_path):
            return {"error": "같은 이름의 파일이 이미 있습니다"}
        try:
            os.rename(path, new_path)
        except OSError as e:
            return {"error": str(e)}
        if self.current_path == path:
            self.current_path = new_path
            self._set_title()
        return {"path": new_path, "name": new_name}

    def delete_path(self, path):
        """파일/폴더 삭제 (즉시 삭제, 휴지통 미사용). 폴더는 하위 포함 재귀 삭제"""
        if not path or not os.path.exists(path):
            return {"error": "파일/폴더를 찾을 수 없습니다"}
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError as e:
            return {"error": str(e)}
        return {"ok": True}

    def move_path(self, src, dst_dir):
        """파일/폴더를 다른 폴더로 이동 (드래그 앤 드롭용)"""
        if not os.path.exists(src):
            return {"error": "파일/폴더를 찾을 수 없습니다"}
        if not dst_dir or not os.path.isdir(dst_dir):
            return {"error": "대상 폴더를 찾을 수 없습니다"}
        src = os.path.normpath(src)
        dst_dir = os.path.normpath(dst_dir)
        if os.path.normcase(os.path.dirname(src)) == os.path.normcase(dst_dir):
            return {"error": "이미 같은 폴더에 있습니다"}
        if os.path.isdir(src):
            # 폴더를 자기 자신/하위 폴더로 이동하는 것 방지
            sp = os.path.normcase(src + os.sep)
            dp = os.path.normcase(dst_dir + os.sep)
            if dp.startswith(sp):
                return {"error": "자기 자신(하위 폴더)으로는 이동할 수 없습니다"}
        dst = os.path.join(dst_dir, os.path.basename(src))
        if os.path.exists(dst):
            return {"error": "대상 폴더에 같은 이름의 파일/폴더가 이미 있습니다"}
        try:
            shutil.move(src, dst)
        except OSError as e:
            return {"error": str(e)}
        if self.current_path == src:
            self.current_path = dst
            self._set_title()
        return {"path": dst, "name": os.path.basename(dst)}

    def new_file(self):
        self.current_path = None
        self._set_title()
        return {"ok": True}

    def save_file(self, content):
        path = self.current_path
        if not path:
            result = self._window.create_file_dialog(
                webview.FileDialog.SAVE,
                save_filename="untitled.md",
                file_types=("Markdown 파일 (*.md)", "모든 파일 (*.*)"),
            )
            if not result:
                return None
            path = result if isinstance(result, str) else result[0]
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        self.current_path = path
        self._set_title()
        backup = self._backup_file(path, content)
        return {"path": path, "backup": bool(backup)}

    def save_as_dialog(self, default_name="untitled.md"):
        """다른 이름으로 저장 대화상자 - 선택된 경로만 반환"""
        result = self._window.create_file_dialog(
            webview.FileDialog.SAVE,
            save_filename=default_name or "untitled.md",
            file_types=("Markdown 파일 (*.md)", "모든 파일 (*.*)"),
        )
        if not result:
            return None
        path = result if isinstance(result, str) else result[0]
        return {"path": path}

    def save_to(self, path, content):
        """지정 경로에 저장 (모두 저장/다른 이름 저장용, current_path 변경 없음)"""
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        backup = self._backup_file(path, content)
        return {"path": path, "backup": bool(backup)}

    def set_current(self, path):
        """활성 탭 변경 등으로 현재 파일 경로/창 제목 동기화"""
        self.current_path = path
        self._set_title()
        return {"ok": True}

    # ---------- 세션(열린 탭) 저장/복원 ----------
    def save_session(self, files, active):
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump({"files": files, "active": active}, f, ensure_ascii=False)
            return {"ok": True}
        except OSError:
            return None

    def load_session(self):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return {"files": [], "active": -1}
        files = [p for p in data.get("files", []) if isinstance(p, str) and os.path.isfile(p)]
        active = data.get("active", -1)
        return {"files": files, "active": active}

    # ---------- HTML 내보내기 ----------
    def export_html(self, content):
        if self.current_path:
            default = os.path.splitext(os.path.basename(self.current_path))[0] + ".html"
        else:
            default = "untitled.html"
        result = self._window.create_file_dialog(
            webview.FileDialog.SAVE,
            save_filename=default,
            file_types=("HTML 파일 (*.html)", "모든 파일 (*.*)"),
        )
        if not result:
            return None
        path = result if isinstance(result, str) else result[0]

        body = self.render(content)["html"]
        with open(resource_path(os.path.join("ui", "preview.css")), "r", encoding="utf-8") as f:
            preview_css = f.read()
        title = os.path.splitext(os.path.basename(path))[0]
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{preview_css}
{PYGMENTS_CSS}
body {{ margin: 0; background: #f0f2f5; }}
.page {{ max-width: 900px; margin: 0 auto; padding: 48px 24px; }}
.markdown-body {{ background: #ffffff; border-radius: 12px; box-shadow: 0 1px 8px rgba(0,0,0,.08); padding: 48px 56px; }}
@media (max-width: 700px) {{ .markdown-body {{ padding: 24px 20px; }} }}
</style>
</head>
<body>
<div class="page"><article class="markdown-body">
{body}
</article></div>
</body>
</html>
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return {"path": path}

    def get_pygments_css(self):
        return PYGMENTS_CSS

    # ================= 기본 설정 / 백업 =================
    def settings_load(self):
        """앱 기본 설정 반환 (백업 폴더 경로 등)"""
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except (OSError, ValueError):
            cfg = {}
        return {"backup_dir": cfg.get("backup_dir", "")}

    def settings_save(self, cfg):
        """앱 기본 설정 저장"""
        try:
            data = {"backup_dir": (cfg or {}).get("backup_dir", "").strip()}
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            return {"ok": True}
        except OSError as e:
            return {"error": str(e)}

    def choose_folder(self):
        """폴더 선택 대화상자 (백업 폴더 지정용)"""
        result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        if not result:
            return None
        path = result if isinstance(result, str) else result[0]
        return {"path": path}

    def _backup_file(self, path, content):
        """원본 저장과 별개로, 백업 폴더에 '파일명_년월일시분초' 백업 생성.
        백업 폴더가 미설정이면 아무것도 하지 않음.
        원본 경로 구조를 백업 폴더 아래에 그대로 재현한다."""
        try:
            bak = self.settings_load().get("backup_dir", "")
            if not bak or not os.path.isdir(bak):
                return None
            abspath = os.path.abspath(path)
            drive, rest = os.path.splitdrive(abspath)
            drive_folder = drive.replace(":", "").strip("\\/") or "root"
            rel_dir = os.path.dirname(rest).lstrip("\\/")
            target_dir = os.path.join(bak, drive_folder, rel_dir)
            os.makedirs(target_dir, exist_ok=True)
            name, ext = os.path.splitext(os.path.basename(abspath))
            ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            target = os.path.join(target_dir, f"{name}_{ts}{ext}")
            with open(target, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            return {"path": target}
        except OSError:
            return None

    # ================= Confluence 연동 (cloudId 게이트웨이) =================
    #  커스텀 도메인 뒤의 Confluence Cloud도 직접 /wiki/rest/api 대신
    #  https://api.atlassian.com/ex/confluence/{cloudId} 게이트웨이 + API 토큰 Basic 인증으로 호출한다.
    #  (이것이 "caller cannot access Confluence" 403의 근본 해결책)
    def conf_load_config(self):
        """저장된 Confluence 설정 반환 (없으면 빈 값)"""
        try:
            with open(CONFLUENCE_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except (OSError, ValueError):
            cfg = {}
        return {
            "email": cfg.get("email", ""),
            "token_name": cfg.get("token_name", ""),
            "token": cfg.get("token", ""),
            "work": cfg.get("work", ""),
            "cloud_id": cfg.get("cloud_id", ""),
            "verified": bool(cfg.get("verified", False)),
        }

    def conf_save_config(self, cfg):
        """Confluence 설정 저장 (토큰은 로컬 사용자 파일에만 저장)"""
        try:
            data = {
                "email": (cfg or {}).get("email", "").strip(),
                "token_name": (cfg or {}).get("token_name", "").strip(),
                "token": (cfg or {}).get("token", "").strip(),
                "work": (cfg or {}).get("work", "").strip(),
                "cloud_id": (cfg or {}).get("cloud_id", "").strip(),
                "verified": bool((cfg or {}).get("verified", False)),
            }
            with open(CONFLUENCE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            return {"ok": True}
        except OSError as e:
            return {"error": str(e)}

    @staticmethod
    def _conf_parse_work(work):
        """'접근할 폴더 링크'에서 host / space_key / folder_id / page_id 추출.
        - 폴더 링크: https://<site>/wiki/spaces/<KEY>/folder/<ID>?...
        - 페이지 링크: https://<site>/wiki/spaces/<KEY>/pages/<ID>/Title
        - 개인 스페이스 KEY는 '~'로 시작 가능(정규식 그대로 매칭)
        """
        work = (work or "").strip()
        host = space_key = folder_id = page_id = None
        hm = re.match(r"(https?://[^/]+)", work)
        if hm:
            host = hm.group(1)
        fm = re.search(r"/spaces/([^/?]+)/folder/(\d+)", work)
        if fm:
            space_key = urllib.parse.unquote(fm.group(1))
            folder_id = fm.group(2)
        else:
            sk = re.search(r"/spaces/([^/?]+)", work)
            if sk:
                space_key = urllib.parse.unquote(sk.group(1))
            pid = re.search(r"/pages/(\d+)", work)
            if pid:
                page_id = pid.group(1)
        if not host and work and not work.lower().startswith("http"):
            space_key = space_key or work  # URL이 아니면 스페이스 키로 간주
        return {"host": host, "space_key": space_key, "folder_id": folder_id, "page_id": page_id}

    def _conf_cloud_id(self, cfg):
        """cloudId 확보: 설정에 있으면 사용, 없으면 {host}/(wiki/)_edge/tenant_info 로 조회.
        SSO 게이트 등으로 비인증 조회가 막히면 Basic 인증을 붙여 재시도한다."""
        cfg = cfg or {}
        if (cfg.get("cloud_id") or "").strip():
            return cfg["cloud_id"].strip(), None
        host = self._conf_parse_work(cfg.get("work", "")).get("host")
        if not host:
            return None, "폴더 링크에 사이트 주소(https://...)가 필요합니다"
        if host in self._cloud_ids:
            return self._cloud_ids[host], None
        email = (cfg.get("email") or "").strip()
        token = (cfg.get("token") or "").strip()
        last = ""
        for use_auth in (False, True):
            for path in ("/wiki/_edge/tenant_info", "/_edge/tenant_info"):
                try:
                    req = urllib.request.Request(host + path, headers={"Accept": "application/json"})
                    if use_auth and email and token:
                        a = base64.b64encode(f"{email}:{token}".encode("utf-8")).decode("ascii")
                        req.add_header("Authorization", "Basic " + a)
                    with urllib.request.urlopen(req, timeout=15, context=_CONF_SSL_CTX) as r:
                        raw = r.read().decode("utf-8", "replace").strip()
                    try:
                        j = json.loads(raw)
                    except ValueError:
                        last = f"{path} 응답이 JSON 아님(로그인 게이트 가능): {raw[:60]}"
                        continue
                    cid = j.get("cloudId")
                    if cid:
                        self._cloud_ids[host] = cid
                        return cid, None
                    last = f"{path} 응답에 cloudId 없음"
                except urllib.error.HTTPError as e:
                    last = f"{path} HTTP {e.code}"
                except Exception as e:  # noqa: BLE001
                    last = f"{path}: {e}"
        return None, ("cloudId 자동 조회 실패(" + last + "). 설정의 cloudId 칸에 직접 입력해 주세요. "
                      "(브라우저에서 " + host + "/wiki/_edge/tenant_info 접속 시 보이는 cloudId 값)")

    def _conf_request(self, cfg, method, path, body=None):
        """cloudId 게이트웨이로 Confluence REST 호출 (basic auth: email + API token)."""
        cfg = cfg or self.conf_load_config()
        email = (cfg.get("email") or "").strip()
        token = (cfg.get("token") or "").strip()
        if not email or not token:
            return None, "계정(email)과 토큰 값을 입력하세요"
        cid, cerr = self._conf_cloud_id(cfg)
        if cerr:
            return None, cerr
        url = f"https://api.atlassian.com/ex/confluence/{cid}" + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        auth = base64.b64encode(f"{email}:{token}".encode("utf-8")).decode("ascii")
        req.add_header("Authorization", "Basic " + auth)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30, context=_CONF_SSL_CTX) as resp:
                raw = resp.read().decode("utf-8", "replace")
                return (json.loads(raw) if raw else {}), None
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            return None, f"HTTP {e.code} {e.reason} {detail}".strip()
        except urllib.error.URLError as e:
            return None, f"연결 실패: {e.reason}"
        except Exception as e:  # noqa: BLE001
            return None, str(e)

    def conf_test(self, cfg):
        """연동 테스트(접근 사전 점검): cloudId 조회 + 폴더/스페이스 접근 확인."""
        cfg = cfg or self.conf_load_config()
        cid, cerr = self._conf_cloud_id(cfg)
        if cerr:
            return {"error": cerr}
        info = self._conf_parse_work(cfg.get("work", ""))
        folder_id, space_key = info["folder_id"] or info["page_id"], info["space_key"]
        user = None
        ud, uerr = self._conf_request(cfg, "GET", "/rest/api/user/current")
        if uerr is None and ud:
            user = ud.get("displayName") or ud.get("publicName")
        if folder_id:
            fd, ferr = self._conf_request(cfg, "GET", f"/rest/api/content/{folder_id}")
            if ferr:
                return {"error": "폴더 접근 실패: " + ferr}
            return {"ok": True, "cloud_id": cid, "user": user,
                    "folder": fd.get("title", ""), "space": space_key}
        if space_key:
            sd, serr = self._conf_request(cfg, "GET", f"/rest/api/space/{urllib.parse.quote(space_key)}")
            if serr:
                return {"error": "스페이스 접근 실패: " + serr}
            return {"ok": True, "cloud_id": cid, "user": user, "space": space_key}
        return {"error": "폴더 링크에서 스페이스/폴더를 찾을 수 없습니다"}

    def conf_list(self, cfg=None):
        """폴더(또는 스페이스) 하위 페이지 목록."""
        cfg = cfg or self.conf_load_config()
        info = self._conf_parse_work(cfg.get("work", ""))
        folder_id = info["folder_id"] or info["page_id"]
        space_key = info["space_key"]
        if folder_id:
            data, err = self._conf_request(
                cfg, "GET", f"/rest/api/content/{folder_id}/child/page?limit=100&expand=version"
            )
        elif space_key:
            q = urllib.parse.urlencode(
                {"spaceKey": space_key, "type": "page", "limit": 100, "orderby": "title"}
            )
            data, err = self._conf_request(cfg, "GET", "/rest/api/content?" + q)
        else:
            return {"error": "작업 폴더/스페이스가 설정되지 않았습니다"}
        if err:
            return {"error": err}
        pages = [
            {"id": r["id"], "title": r["title"], "version": r.get("version", {}).get("number", 1)}
            for r in data.get("results", [])
        ]
        return {"pages": pages, "space": space_key, "folder_id": folder_id}

    @staticmethod
    def _sort_tree(nodes):
        """폴더 먼저, 그다음 제목순 (탐색기와 동일한 정렬)"""
        nodes.sort(key=lambda n: (n.get("kind") != "folder", n["title"].lower()))
        for n in nodes:
            Api._sort_tree(n["children"])

    def _conf_v2_children(self, cfg, node_id, kind):
        """v2 direct-children 조회 (폴더/페이지 공용, cursor 페이징 follow)"""
        paths = {
            "folder": f"/wiki/api/v2/folders/{node_id}/direct-children",
            "page": f"/wiki/api/v2/pages/{node_id}/direct-children",
        }
        base = paths.get(kind)
        if not base:
            return [], None
        out, cursor = [], None
        for _ in range(5):  # 안전장치: 최대 5페이지(500개)
            path = base + "?limit=100" + (("&cursor=" + urllib.parse.quote(cursor)) if cursor else "")
            data, err = self._conf_request(cfg, "GET", path)
            if err:
                return None, err
            out += data.get("results", [])
            nxt = (data.get("_links") or {}).get("next") or ""
            m = re.search(r"[?&]cursor=([^&]+)", nxt)
            cursor = urllib.parse.unquote(m.group(1)) if m else None
            if not cursor:
                break
        return out, None

    def _conf_tree_v2(self, cfg, root_id, root_kind, depth=0, budget=None):
        """v2 API로 폴더/페이지 계층을 재귀 조회 (하위 폴더 구조 그대로 보존)"""
        if budget is None:
            budget = {"n": 0}
        if depth > 6 or budget["n"] > 400:  # 깊이/개수 안전장치
            return [], None
        children, err = self._conf_v2_children(cfg, root_id, root_kind)
        if children is None:
            return None, err
        nodes = []
        for c in children:
            ctype = (c.get("type") or "").lower()
            kind = "folder" if ctype == "folder" else ("page" if ctype == "page" else ctype)
            node = {"id": str(c.get("id")), "title": c.get("title", ""), "kind": kind, "children": []}
            budget["n"] += 1
            if kind in ("folder", "page"):
                sub, _serr = self._conf_tree_v2(cfg, node["id"], kind, depth + 1, budget)
                if sub is not None:
                    node["children"] = sub
            nodes.append(node)
        return nodes, None

    @staticmethod
    def _fmt_date(iso):
        """ISO 날짜문자열(2026-07-09T06:11:40.973Z) → 'YYYY-MM-DD' (없으면 빈 문자열)"""
        if not iso or not isinstance(iso, str):
            return ""
        m = re.match(r"(\d{4}-\d{2}-\d{2})", iso)
        return m.group(1) if m else ""

    def conf_children(self, parent_id=None, kind=None, cfg=None):
        """직계 자식 '한 단계'만 조회 (지연 로딩용). 폴더/페이지 구성에 상관없이
        누락 없이 보이도록 여러 엔드포인트를 모두 조회해 합친다:
          A) v2 folders/{id}/direct-children  (폴더/페이지 혼합)
          B) v2 pages/{id}/direct-children    (페이지/폴더 혼합)
          C) v1 content/{id}/child/page       (등록일/수정일/하위존재 보강)
        """
        cfg = cfg or self.conf_load_config()
        if not parent_id:
            info = self._conf_parse_work(cfg.get("work", ""))
            parent_id = info["folder_id"] or info["page_id"]
            if not parent_id:
                r = self.conf_list(cfg)  # 폴더 링크가 없으면 스페이스 페이지 목록(플랫)
                if r.get("error"):
                    return r
                return {"children": [
                    {"id": p["id"], "title": p["title"], "kind": "page",
                     "version": p.get("version"), "created": "", "updated": "", "has_children": None}
                    for p in r.get("pages", [])
                ]}

        items, errs, any_ok = {}, [], False

        def add(cid, title, k, extra=None):
            cid = str(cid)
            n = items.get(cid) or {"id": cid, "title": title or "", "kind": k,
                                   "version": None, "created": "", "updated": "", "has_children": None}
            if title:
                n["title"] = title
            if k:
                n["kind"] = k
            if extra:
                for key, val in extra.items():
                    if val not in (None, ""):
                        n[key] = val
            items[cid] = n

        # A/B) v2 direct-children — 폴더/페이지 어느 쪽이든 자식 확보
        for ep in (
            f"/wiki/api/v2/folders/{parent_id}/direct-children?limit=100",
            f"/wiki/api/v2/pages/{parent_id}/direct-children?limit=100",
        ):
            data, err = self._conf_request(cfg, "GET", ep)
            if err is None and isinstance(data, dict):
                any_ok = True
                for c in data.get("results", []):
                    ct = (c.get("type") or "").lower()
                    add(c.get("id"), c.get("title", ""), "folder" if ct == "folder" else "page")
            else:
                errs.append(err)

        # C) v1 child/page — 날짜/하위존재 보강 (페이지)
        pdata, perr = self._conf_request(
            cfg, "GET",
            f"/rest/api/content/{parent_id}/child/page?limit=100&expand=version,history,childTypes.page",
        )
        if perr is None and isinstance(pdata, dict):
            any_ok = True
            for r in pdata.get("results", []):
                ctp = (r.get("childTypes") or {}).get("page")
                hc = bool(ctp.get("value")) if isinstance(ctp, dict) else None
                add(r.get("id"), r.get("title", ""), "page", {
                    "version": r.get("version", {}).get("number"),
                    "created": self._fmt_date((r.get("history") or {}).get("createdDate")),
                    "updated": self._fmt_date((r.get("version") or {}).get("when")),
                    "has_children": hc,
                })
        else:
            errs.append(perr)

        out = list(items.values())
        out.sort(key=lambda n: (n["kind"] != "folder", (n["title"] or "").lower()))
        if not out and not any_ok:
            return {"error": next((e for e in errs if e), "조회 실패")}
        return {"children": out}

    def conf_tree(self, cfg=None):
        """폴더 하위 문서를 하위 폴더 구조까지 포함한 '계층(트리)'로 반환.
        1순위: v2 direct-children 재귀(폴더 타입 보존) → 실패 시 CQL ancestor 폴백."""
        cfg = cfg or self.conf_load_config()
        info = self._conf_parse_work(cfg.get("work", ""))
        folder_id = info["folder_id"] or info["page_id"]
        space_key = info["space_key"]
        if not folder_id:
            return self.conf_list(cfg)  # 폴더가 없으면 스페이스 전체(플랫)

        root_kind = "folder" if info["folder_id"] else "page"
        tree, _err = self._conf_tree_v2(cfg, folder_id, root_kind)
        if tree is None and root_kind == "folder":
            tree, _err = self._conf_tree_v2(cfg, folder_id, "page")  # 폴더 ID가 실은 페이지인 경우
        if tree is not None:
            self._sort_tree(tree)
            return {"tree": tree, "space": space_key, "folder_id": folder_id}

        # ---- 폴백: CQL ancestor (페이지 + 폴더 함께 조회해 계층 복원) ----
        results = []
        for cql_type in ("page", "folder"):
            q = urllib.parse.urlencode(
                {"cql": f"ancestor={folder_id} and type={cql_type}", "limit": 200,
                 "expand": "ancestors,version"}
            )
            data, err = self._conf_request(cfg, "GET", "/rest/api/content/search?" + q)
            if err is None and isinstance(data, dict):
                results += data.get("results", [])
            elif cql_type == "page":
                return self.conf_list(cfg)  # 페이지 검색도 안 되면 직계 자식 폴백
        nodes = {}
        for r in results:
            nodes[str(r["id"])] = {
                "id": str(r["id"]), "title": r["title"],
                "kind": (r.get("type") or "page").lower(),
                "version": r.get("version", {}).get("number", 1), "children": [],
            }
        roots = []
        for r in results:
            anc = r.get("ancestors", []) or []
            pid = str(anc[-1]["id"]) if anc else None  # 직속 부모 = ancestors의 마지막
            if pid and pid != str(folder_id) and pid in nodes:
                nodes[pid]["children"].append(nodes[str(r["id"])])
            else:
                roots.append(nodes[str(r["id"])])
        self._sort_tree(roots)
        return {"tree": roots, "space": space_key, "folder_id": folder_id, "count": len(results)}

    # 스토리지 XHTML은 엄격 → void(빈) 요소를 반드시 self-close 해야 파싱 오류가 없음
    _VOID_TAGS = "area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr"

    def _conf_storage_body(self, markdown_text):
        """마크다운을 렌더링한 뒤 Confluence storage(XHTML) 규격에 맞게 정리."""
        html = self.render(markdown_text)["html"]
        html = re.sub(
            r"<(" + self._VOID_TAGS + r")((?:\s[^>]*?)?)\s*/?\s*>",
            r"<\1\2 />", html, flags=re.IGNORECASE,
        )
        return html

    def conf_get(self, page_id, cfg=None):
        """페이지 열기: 저장된 원본 마크다운(있으면) 또는 본문을 반환."""
        cfg = cfg or self.conf_load_config()
        data, err = self._conf_request(
            cfg, "GET", f"/rest/api/content/{page_id}?expand=body.storage,version,space"
        )
        if err:
            return {"error": err}
        version = data.get("version", {}).get("number", 1)
        title = data.get("title", "")
        prop, perr = self._conf_request(
            cfg, "GET", f"/rest/api/content/{page_id}/property/{MD_PROP_KEY}"
        )
        if perr is None and prop and isinstance(prop.get("value"), str):
            markdown_text = prop["value"]  # 원본 마크다운 우선(왕복 편집)
        else:
            markdown_text = data.get("body", {}).get("storage", {}).get("value", "")
        return {"id": page_id, "title": title, "markdown": markdown_text, "version": version}

    def conf_update(self, page_id, title, markdown_text, version=None, cfg=None):
        """기존 페이지 수정: 현재 version 재조회 후 +1 (낙관적 버전 충돌 방지)."""
        cfg = cfg or self.conf_load_config()
        cur, cerr = self._conf_request(cfg, "GET", f"/rest/api/content/{page_id}?expand=version")
        if cerr:
            return {"error": cerr}
        curver = cur.get("version", {}).get("number", int(version or 1))
        html = self._conf_storage_body(markdown_text)
        body = {
            "id": page_id, "type": "page", "title": title,
            "version": {"number": curver + 1},
            "body": {"storage": {"value": html, "representation": "storage"}},
        }
        data, err = self._conf_request(cfg, "PUT", f"/rest/api/content/{page_id}", body=body)
        if err:
            return {"error": err}
        self._conf_set_md_prop(cfg, page_id, markdown_text)
        return {"id": page_id, "version": data.get("version", {}).get("number", curver + 1)}

    def conf_create(self, title, markdown_text, parent_id=None, cfg=None):
        """새 페이지 생성: v1(선택 위치/폴더 하위 ancestors) 우선, 실패 시 v2 폴백.
        parent_id 를 주면 그 페이지 하위에, 없으면 폴더 최상위에 생성한다."""
        cfg = cfg or self.conf_load_config()
        info = self._conf_parse_work(cfg.get("work", ""))
        space_key = info["space_key"]
        folder_id = parent_id or info["folder_id"] or info["page_id"]
        if not space_key:
            return {"error": "작업 스페이스를 찾을 수 없습니다 (폴더 링크 확인)"}
        html = self._conf_storage_body(markdown_text)
        body = {
            "type": "page", "title": title, "space": {"key": space_key},
            "body": {"storage": {"value": html, "representation": "storage"}},
        }
        if folder_id:
            body["ancestors"] = [{"id": folder_id}]
        data, err = self._conf_request(cfg, "POST", "/rest/api/content", body=body)
        if err is None and data.get("id"):
            new_id = data["id"]
            self._conf_set_md_prop(cfg, new_id, markdown_text)
            return {"id": new_id, "title": title, "version": 1}
        # v2 폴백: spaceId 조회 후 /wiki/api/v2/pages
        sd, serr = self._conf_request(cfg, "GET", f"/rest/api/space/{urllib.parse.quote(space_key)}")
        space_id = str(sd.get("id", "")) if serr is None and sd else ""
        if space_id:
            b2 = {"spaceId": space_id, "status": "current", "title": title,
                  "body": {"representation": "storage", "value": html}}
            if folder_id:
                b2["parentId"] = folder_id
            d2, e2 = self._conf_request(cfg, "POST", "/wiki/api/v2/pages", body=b2)
            if e2 is None and d2.get("id"):
                new_id = d2["id"]
                self._conf_set_md_prop(cfg, new_id, markdown_text)
                return {"id": new_id, "title": title, "version": 1}
            return {"error": "생성 실패(v2): " + (e2 or "알 수 없음")}
        return {"error": "생성 실패: " + (err or "알 수 없음")}

    def conf_delete(self, page_id, cfg=None):
        """페이지 삭제(휴지통 이동, 복구 가능)."""
        cfg = cfg or self.conf_load_config()
        _, err = self._conf_request(cfg, "DELETE", f"/rest/api/content/{page_id}")
        if err:
            return {"error": err}
        return {"ok": True}

    def _conf_set_md_prop(self, cfg, page_id, markdown_text):
        """페이지에 원본 마크다운을 content property로 저장(왕복 편집용)."""
        cur, err = self._conf_request(
            cfg, "GET", f"/rest/api/content/{page_id}/property/{MD_PROP_KEY}"
        )
        if err is None and cur and "version" in cur:
            ver = cur["version"]["number"] + 1
            self._conf_request(
                cfg, "PUT", f"/rest/api/content/{page_id}/property/{MD_PROP_KEY}",
                body={"value": markdown_text, "version": {"number": ver}},
            )
        else:
            self._conf_request(
                cfg, "POST", f"/rest/api/content/{page_id}/property",
                body={"key": MD_PROP_KEY, "value": markdown_text},
            )

    # ================= 자동 업데이트 (GitHub Releases) =================
    def _github_json(self, path):
        """GitHub REST 호출 (인증 불필요한 공개 저장소)"""
        req = urllib.request.Request(
            "https://api.github.com" + path,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "jm-mdv-updater"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15, context=_CONF_SSL_CTX) as r:
                return json.loads(r.read().decode("utf-8", "replace")), None
        except Exception as e:  # noqa: BLE001
            return None, str(e)

    @staticmethod
    def _ver_tuple(v):
        nums = re.findall(r"\d+", v or "")
        return tuple(int(n) for n in (nums + ["0", "0", "0"])[:3])

    def update_check(self):
        """최신 릴리스 확인. 새 버전이면 버전/변경내용/OS별 다운로드 자산 반환."""
        data, err = self._github_json(f"/repos/{GITHUB_REPO}/releases/latest")
        if err or not isinstance(data, dict) or not data.get("tag_name"):
            return {"available": False, "error": err or "no release"}
        tag = data.get("tag_name") or ""
        if self._ver_tuple(tag) <= self._ver_tuple(APP_VERSION):
            return {"available": False, "latest": tag}
        assets = data.get("assets") or []
        asset = None
        if sys.platform == "darwin":
            # macOS: 'mac' 포함 zip 우선, 없으면 아무 zip
            for a in assets:
                n = (a.get("name") or "").lower()
                if "mac" in n and n.endswith(".zip"):
                    asset = a
                    break
            if not asset:
                for a in assets:
                    if (a.get("name") or "").lower().endswith(".zip"):
                        asset = a
                        break
        else:
            for a in assets:
                if (a.get("name") or "").lower().endswith(".exe"):
                    asset = a
                    break
        platform = "mac" if sys.platform == "darwin" else ("win" if os.name == "nt" else "other")
        return {
            "available": True,
            "current": APP_VERSION,
            "version": tag.lstrip("vV"),
            "notes": data.get("body") or "",
            "asset_name": asset.get("name") if asset else None,
            "asset_url": asset.get("browser_download_url") if asset else None,
            "page_url": data.get("html_url") or f"https://github.com/{GITHUB_REPO}/releases",
            "platform": platform,
            "repo_url": f"https://github.com/{GITHUB_REPO}",
            "releases_url": f"https://github.com/{GITHUB_REPO}/releases",
            "readme_url": f"https://github.com/{GITHUB_REPO}/blob/main/README.md",
        }

    def open_external(self, url):
        """기본 브라우저로 외부 URL 열기 (릴리스/빌드 안내 페이지용)"""
        if not url or not str(url).lower().startswith(("http://", "https://")):
            return {"error": "invalid url"}
        try:
            webbrowser.open(url)
        except Exception as e:
            return {"error": str(e)}
        return {"ok": True}

    def _notify_progress(self, done, total):
        """다운로드 진행률을 UI로 통지 (1% 단위 스로틀)"""
        try:
            pct = int(done * 100 / total) if total else -1
            if pct == getattr(self, "_last_pct", None) and pct >= 0:
                return
            self._last_pct = pct
            mb = round(done / 1048576, 1)
            self._window.evaluate_js(
                f"window.__updProgress && window.__updProgress({pct}, {mb})"
            )
        except Exception:
            pass

    def update_download_and_restart(self, asset_url, asset_name, version, notes=""):
        """릴리스 파일을 기존 프로그램 위치에 내려받고, 새 파일을 실행한 뒤 현재 앱 종료."""
        try:
            app_dir = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
                       else os.path.dirname(os.path.abspath(__file__)))
            target = os.path.join(app_dir, asset_name)
            tmp = target + ".part"
            req = urllib.request.Request(asset_url, headers={"User-Agent": "jm-mdv-updater"})
            self._last_pct = None
            with urllib.request.urlopen(req, timeout=300, context=_CONF_SSL_CTX) as r, open(tmp, "wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                done = 0
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    self._notify_progress(done, total)
            if os.path.exists(target):
                os.remove(target)
            os.rename(tmp, target)
            # 새 버전 첫 실행 때 보여줄 '추가/개선 내용'(릴리스 메시지) 보관
            try:
                st = self._update_state()
                st["pending_notes"] = {"version": str(version).lstrip("vV"), "notes": notes or ""}
                with open(UPDATE_STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(st, f, ensure_ascii=False)
            except OSError:
                pass
            # 새로 받은 파일 실행
            if sys.platform == "darwin" and asset_name.lower().endswith(".zip"):
                subprocess.run(["ditto", "-x", "-k", target, app_dir], check=False)
                bundle = None
                base = re.sub(r"\.zip$", "", asset_name, flags=re.I)
                cand = os.path.join(app_dir, base + ".app")
                if os.path.isdir(cand):
                    bundle = cand
                else:
                    for nme in sorted(os.listdir(app_dir)):
                        if nme.endswith(".app") and str(version).lstrip("vV") in nme:
                            bundle = os.path.join(app_dir, nme)
                            break
                subprocess.Popen(["open", bundle or app_dir])
            elif os.name == "nt":
                subprocess.Popen([target], cwd=app_dir, creationflags=0x00000008)  # DETACHED_PROCESS
            else:
                subprocess.Popen([target], cwd=app_dir)
            # 기존 프로그램 종료 (새 프로세스가 뜰 시간을 잠깐 준 뒤)
            threading.Timer(0.8, lambda: os._exit(0)).start()
            try:
                self._window.destroy()
            except Exception:
                pass
            return {"ok": True}
        except Exception as e:  # noqa: BLE001
            return {"error": str(e)}

    @staticmethod
    def _update_state():
        try:
            with open(UPDATE_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def onboarding_needed(self):
        """최초 실행 여부 반환 (온보딩 모달을 1회만 표시)."""
        return {"show": not self._update_state().get("onboarded", False)}

    def onboarding_done(self):
        """온보딩 완료 표시 (이후 다시 표시하지 않음).

        온보딩 직후 같은 버전의 '새 기능' 안내가 겹치지 않도록 현재 버전을
        '확인함'으로 함께 기록한다. 예전에는 프런트에서 onboarding_done()과
        update_mark_seen()을 각각(await 없이) 호출했는데, macOS의 pywebview는
        각 JS→Python 호출을 별도 스레드에서 처리하므로 두 호출이 같은 상태
        파일을 동시에 read-modify-write 하며 경쟁했다. 그 결과 update_mark_seen가
        onboarded=True 쓰기 직전 상태를 읽어 덮어써서 온보딩이 매번 다시 뜨는
        문제가 있었다. 이를 방지하기 위해 두 동작을 단일 쓰기로 합친다."""
        st = self._update_state()
        st["onboarded"] = True
        st["last_seen_version"] = APP_VERSION
        st.pop("pending_notes", None)
        try:
            with open(UPDATE_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(st, f, ensure_ascii=False)
            return {"ok": True}
        except OSError as e:
            return {"error": str(e)}

    def update_whatsnew(self):
        """새 버전 첫 실행 시 보여줄 '추가/개선 내용' 반환 (없으면 None).
        '다시 보지 않기' 체크 시 이후 버전에서도 표시하지 않음."""
        st = self._update_state()
        if st.get("dont_show"):
            return None
        if st.get("last_seen_version") == APP_VERSION:
            return None
        notes = None
        pn = st.get("pending_notes") or {}
        if str(pn.get("version", "")).lstrip("vV") == APP_VERSION and pn.get("notes"):
            notes = pn["notes"]
        else:
            data, err = self._github_json(f"/repos/{GITHUB_REPO}/releases/tags/v{APP_VERSION}")
            if err is None and isinstance(data, dict):
                notes = data.get("body") or None
        if not notes:
            self.update_mark_seen(False)  # 보여줄 내용이 없으면 재시도하지 않도록 처리
            return None
        return {"version": APP_VERSION, "notes": notes}

    def whatsnew_state(self):
        """이 버전의 변경내용을 보여줄지 여부. 새 버전(미확인) + '다시 보지 않기' 미체크면 표시.
        내용은 프런트의 로컬 버전 기록(VERSION_MD)에서 가져오므로 릴리스가 없어도 항상 표시됨."""
        st = self._update_state()
        show = (not st.get("dont_show")) and (st.get("last_seen_version") != APP_VERSION)
        return {"show": bool(show), "version": APP_VERSION}

    def update_mark_seen(self, dont_show=False):
        st = self._update_state()
        st["last_seen_version"] = APP_VERSION
        st["dont_show"] = bool(dont_show)
        st.pop("pending_notes", None)
        try:
            with open(UPDATE_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(st, f, ensure_ascii=False)
            return {"ok": True}
        except OSError as e:
            return {"error": str(e)}

    def on_files_dropped(self, event):
        """OS 탐색기/Finder에서 드롭한 파일들의 실제 경로로 편집기에서 열기.
        pywebview가 event.dataTransfer.files[i].pywebviewFullPath 에 원본 경로를 주입한다."""
        try:
            files = (event or {}).get("dataTransfer", {}).get("files", []) or []
        except AttributeError:
            files = []
        for f in files:
            path = f.get("pywebviewFullPath") if isinstance(f, dict) else None
            if not path or not os.path.isfile(path):
                continue
            try:
                self._window.evaluate_js("window.__openDroppedPath(" + json.dumps(path) + ")")
            except Exception:
                pass

    def show_in_explorer(self):
        """현재 열린 파일을 탐색기(Finder)에서 선택된 상태로 보여줌"""
        if not (self.current_path and os.path.exists(self.current_path)):
            return None
        path = os.path.normpath(self.current_path)
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", path])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path)])
        return {"ok": True}


def _setup_windowed_io():
    """--windowed(콘솔 없는) exe에서는 stdout/stderr가 None이라
    라이브러리가 출력을 시도하면 죽을 수 있음 → 로그 파일로 우회"""
    if sys.stdout is not None and sys.stderr is not None:
        return
    log_path = os.path.join(tempfile.gettempdir(), "JM-MDV.log")
    try:
        f = open(log_path, "a", encoding="utf-8", buffering=1)
    except OSError:
        f = open(os.devnull, "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = f
    if sys.stderr is None:
        sys.stderr = f


def main():
    _setup_windowed_io()
    api = Api()
    window = webview.create_window(
        f"{APP_NAME} v{APP_VERSION}",
        resource_path(os.path.join("ui", "index.html")),
        js_api=api,
        width=1440,
        height=900,
        min_size=(800, 500),
        text_select=True,  # 미리보기에서 마우스 드래그로 텍스트 선택/복사 허용
    )
    api._window = window

    # OS 파일 드롭 → 실제 경로로 열기 (DOM 로드 후 body에 drop 핸들러 등록)
    _dnd = {"done": False}

    def _register_dnd():
        if _dnd["done"]:
            return
        _dnd["done"] = True
        try:
            window.dom.body.on(
                "drop",
                DOMEventHandler(api.on_files_dropped, prevent_default=True, stop_propagation=True),
            )
        except Exception:
            pass

    window.events.loaded += _register_dnd
    webview.start()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        try:
            with open(os.path.join(tempfile.gettempdir(), "JM-MDV.log"), "a", encoding="utf-8") as _f:
                _f.write("\n=== 시작 실패 ===\n" + traceback.format_exc())
        except OSError:
            pass
        raise
