# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

jm-mdv(Markdown Viewer) — a desktop Markdown editor/viewer built on **pywebview**: a Python backend
(`app.py`) hosting a single-page frontend (`ui/index.html`). Ships as a no-install single `.exe`
(Windows, onefile) or `.app` bundle (macOS, onedir), built with PyInstaller.

UI text is bilingual (Korean/English). Korean is the primary language for user-facing strings,
comments, README, and commit messages.

## Commands

```bash
pip install -r requirements.txt
python app.py            # run from source (macOS: python3)
```

Build (reads `APP_VERSION` from `app.py` and names the output `jm-mdv-<version>`):

```bat
build_exe.bat            REM Windows -> dist\jm-mdv-<ver>.exe   (has `pause`; call pyinstaller directly when non-interactive)
```
```bash
./build_mac.sh           # macOS -> dist/jm-mdv-<ver>.app  (must build on a Mac; no cross-compile)
```

There is no test suite and no linter. The only mechanical check that exists — and it is **mandatory
before any build or release after touching `ui/index.html`** — is a JS syntax check of the inline
`<script>` block:

```python
import re, subprocess, os
b = re.findall(r'<script[^>]*>(.*?)</script>', open('ui/index.html', encoding='utf-8').read(), re.S)[0]
f = os.path.join(os.environ['TEMP'], 'chk.js'); open(f, 'w', encoding='utf-8').write(b)
print(subprocess.run(['node', '--check', f], capture_output=True).returncode)  # 0 = OK
```

Why it matters: an unescaped backtick inside the `VERSION_MD_KO` / `VERSION_MD_EN` template literals
once terminated the string early, breaking the *entire* script — every button dead, no session
restore (v1.18.2/1.18.3, fixed in 1.18.4). `python app.py` does not catch this. Escape inline code
inside those template literals as ``\` ``.

## Architecture

**Two files hold nearly everything.** `app.py` (~1400 lines) is one `Api` class exposed to JS as
`window.pywebview.api.*`; `ui/index.html` (~7600 lines) is markup + one inline `<style>` + one inline
`<script>` holding all frontend state and logic. `ui/preview.css` styles rendered preview output and
is also inlined into exported HTML.

- **Rendering**: Markdown → HTML happens in Python (`Api.render`) via `markdown` +
  `pymdown-extensions`, with Pygments CSS cached in `_PYGMENTS_CSS`. The frontend calls `render()` on
  keystroke-idle and drops in the HTML.
- **Frontend state**: `tabs = [{path, name, content, dirty}]` (path `null` = new document) plus the
  active tab id. Tab switching, dirty tracking, and duplicate-open prevention (path compared
  case- and separator-insensitively; Confluence pages by string page id) all live here.
- **i18n**: `I18N` table + `lang` global + `applyLang()`, which re-labels the DOM. Every user-visible
  string needs both `ko` and `en` entries. Help/version-history content lives in paired
  `*_KO`/`*_EN` template literals.
- **Persistence** — plain JSON files in the user's home, all defined at the top of `app.py`:
  `.jm-mdv-session.json` (open tabs), `.jm-mdv-settings.json` (backup dir), `.jm-mdv-confluence.json`
  (Confluence creds incl. token), `.jm-mdv-update.json` (what's-new seen state), `.jm-mdv-ipc.json`
  (IPC port). **Do not write shared state concurrently** — on macOS each JS→Python call runs on its
  own thread and two save paths racing corrupted the onboarding flag (v1.18.2).
- **Single instance / IPC**: `main()` first calls `_send_to_running_instance()`; if a live
  `127.0.0.1` port is recorded in `.jm-mdv-ipc.json` the file paths are handed to the existing window
  and this process exits. Otherwise `_start_ipc_server()` claims a port. Paths from `argv` are stashed
  as `api.startup_paths` and pulled by the frontend via `startup_files()` *after* session restore, so
  restoration doesn't clobber them.
- **Confluence**: Cloud REST via the cloudId gateway (`api.atlassian.com/ex/confluence/{cloudId}`) to
  survive custom domains. Original Markdown is round-tripped in a page content property
  (`MD_PROP_KEY`), since Confluence stores XHTML.
- **Auto-update**: checks GitHub Releases of `GITHUB_REPO`. Windows downloads the `.exe` next to the
  running binary and restarts; macOS only shows instructions (no signing/notarization).
- **Windowed builds have no stdout** — `_setup_windowed_io()` redirects to `%TEMP%\JM-MDV.log`, which
  is where startup crashes are recorded.

## Per-task conventions

- Bump `APP_VERSION` in `app.py` when behavior changes; the comment there is accurate — the version
  also appears in `ui/index.html`'s version-history blocks.
- After **every** development task, update all three in sync: the README version table, `VERSION_MD_KO`,
  and `VERSION_MD_EN`, with detailed notes (not one-liners), plus any user-facing README sections.
- The dedication line near the top of `README.md` is marked never to modify or translate — leave it.
- `jm-mdv-*.spec` files are gitignored build residue; ignore them. `untitled.md` / `untitled.html`
  are sample fixtures.
- No `gh` CLI in this environment. Releases are published via the GitHub REST API using a token from
  `git credential fill` (tag `v<version>`, `.exe` asset attached; macOS gets the one-line
  `easy_mac_setup.sh` install instructions instead of a binary).
