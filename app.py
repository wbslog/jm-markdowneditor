# -*- coding: utf-8 -*-
"""Markdown View - 실시간 마크다운 에디터/뷰어 (Windows)"""
import json
import os
import string
import subprocess
import sys
import tempfile
import threading
import traceback

import markdown
import webview
from pygments.formatters import HtmlFormatter

APP_NAME = "jm-mdv(Markdown Viewer)"


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

SESSION_FILE = os.path.join(os.path.expanduser("~"), ".jm-mdv-session.json")


class Api:
    def __init__(self):
        self._window = None
        self.current_path = None
        self._md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=MD_CONFIGS)
        self._lock = threading.Lock()

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
        self._window.set_title(f"{name} - {APP_NAME}")

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
                if e.name.startswith((".", "$")) or e.name == "System Volume Information":
                    continue
                try:
                    if e.is_dir():
                        dirs.append({"name": e.name, "path": e.path})
                    elif e.is_file() and e.name.lower().endswith(self.MD_FILE_EXTS):
                        files.append({"name": e.name, "path": e.path})
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
        return {"path": path}

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
        return {"path": path}

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
        APP_NAME,
        resource_path(os.path.join("ui", "index.html")),
        js_api=api,
        width=1440,
        height=900,
        min_size=(800, 500),
        text_select=True,  # 미리보기에서 마우스 드래그로 텍스트 선택/복사 허용
    )
    api._window = window
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
