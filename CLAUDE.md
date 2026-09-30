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

Sanity-check the artifact size: a correct Windows build is **~18MB**. If it comes out much
larger, an unwanted GUI backend was pulled in — pywebview uses EdgeChromium (pythonnet) on
Windows and Cocoa on macOS, but a Qt install in the build environment makes the hook bundle
all of PyQt5 (+31MB). The build scripts and spec exclude PyQt5/6, PySide2/6 and qtpy for this
reason; keep those excludes in sync across all three.

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

## Where things stand (resume here after a break)

Last verified 2026-09-30. Released through **v1.27.0** (tag `v1.27.0` → `10c9237`, asset
**`jm-mdv.exe`**, 18,024,426 bytes). `APP_VERSION` in `app.py` matches the released version, so a
fresh checkout needs no version bump before starting new work. Working tree clean at that commit.

Release assets no longer carry a version in the filename — always `jm-mdv.exe` / `jm-mdv.app`, which
gives a permanent download URL:
`https://github.com/wbslog/jm-markdowneditor/releases/latest/download/jm-mdv.exe`

Recent sessions, newest first:

- **v1.27.0** — the preview shows **the cursor's line and column in the *source* markdown**, on a
  dark chip at its bottom right. The preview holds no source line numbers, so the characters at the
  clicked point are located back in the original text: a normalized copy of the source (letters,
  digits, Hangul, CJK only) plus an index back to real offsets; up to 28 normalized characters are
  taken from the click point and matched, with the occurrence nearest the current scroll position
  winning. Because punctuation is dropped, markup that exists only in the source (`**bold**`,
  backtick code) is counted in the column. Verified 9/9 exact against hand-checked positions.
- **v1.26.0** — release filenames lost their version (see above), the full path moved out of the
  toolbar onto its own wide line under the tabs with an Open-folder button to its left (clicking the
  path text no longer opens the folder), the directory panel got text buttons (이전 / 새로고침), an
  absolute path on the line below them and a loading spinner. The v1.25.0 800ms poll was removed —
  the handing-over process now grants foreground rights (`AllowSetForegroundWindow`) and the receiver
  raises itself with user32, the frontend checks on focus, and a 1.5s fallback check **skips while a
  mouse button is held** (that constant bridge traffic was the prime suspect for the preview freezing
  mid drag-selection — removed, not proven).
- **v1.25.0** — fixed the two bugs the user hit after installing from a release.
  (a) **Updates left the old version wired up.** The updater saved each release under its versioned
  name, so Explorer's file association kept pointing at the previous exe — opening a `.md` launched
  the old build and re-offered the same update forever. `update_download_and_restart` now replaces
  the *running* file in place: a running exe cannot be deleted but can be renamed, so it is moved to
  `.old`, the new bytes take the same name, and `_cleanup_old_exe()` deletes `.old` on next start.
  If the rename fails it falls back to the old versioned-name behavior so the update still happens.
  (b) **Opening a file while running froze or killed the window.** `open_paths_from_other_instance()`
  now only appends to `pending_paths`; the frontend polls `take_pending_files()` every 800ms and does
  the opening. `focus_window()` no longer touches the pywebview window on Windows — it finds its own
  HWND via `EnumWindows` and calls user32 `ShowWindow`/`SetForegroundWindow`.
- **v1.24.0** — GitHub repo link banner at the top of Help → Version History, plus a delegated
  `document` click handler that routes `http(s)` links to `Api.open_external` (default browser).
  Before this the app had *no* link handling at all: clicking any link in the preview or help
  replaced the whole app window with that page, with no way back. In-document `#anchors` and
  `mailto:` deliberately keep native behavior. `closest('a[href]')` is load-bearing — the help
  search wraps matches in `<mark>` *inside* anchors, so `e.target` is often not the `<a>`.
- **v1.23.1** — fixed auto-update downloading but never relaunching. Two stacked causes: the child
  inherited PyInstaller's `_MEIPASS2`/`_PYI_*` (so the new onefile exe skipped unpacking and pointed
  at the parent's about-to-be-deleted temp dir), and the v1.23.0 single-instance IPC made the new
  process hand off to the still-dying old one and exit. Fixes live in
  `Api.update_download_and_restart`, `_clean_child_env()`, `_shutdown_ipc()` and the `UPDATED_ENV`
  check in `main()`.

### Open items

- **A real end-to-end auto-update has still never been exercised.** Every updater fix so far was
  verified by simulation (faked download, stubbed `Popen`) plus exe smoke tests — never against a
  live GitHub release, because a fix only takes effect once the *running* build already contains it.
  v1.25.0 does not settle it either: that release deliberately asks users to install manually, since
  their file association still points at an older exe. The first honest test is to install v1.25.0,
  publish the version after it, and press **⬇️ 다운로드 및 재시작**. Confirm that before
  telling anyone auto-update works.
- Anyone still on a versioned exe needs **one manual install** of `jm-mdv.exe` and one re-pointing of
  the file association. From v1.26.0 on the filename never changes, so this is the last time.
- **The preview freeze during drag-selection was never root-caused.** v1.26.0 removed the most likely
  contributor. If it recurs, that is the next clue — do not assume it is fixed.
- **Performance, measured 2026-09-18** (numbers, not guesses): onefile startup is **~7.8s** (18MB
  unpacked every launch) — the main "heavy" feeling; Python render is **~100ms for a 45KB document**
  and the debounce is only 100ms, so large files re-parse constantly. The frontend is not the problem
  (innerHTML 4ms, layout 21ms) and **backdrop-filter blur costs nothing measurable** (6.9ms frames
  either way) — that was a wrong guess, checked and discarded. Cheapest win: scale the render debounce
  with document size. Biggest win: `--onedir`, at the cost of single-file distribution. Neither done.
- Users still on v1.23.0 or earlier must install one build manually; their updater cannot relaunch.
- Carried over from earlier sessions: whether to return the Home key to OS default (asked, no answer
  yet); macOS `.app` has no `CFBundleDocumentTypes` so Finder double-click association does not work;
  onefile startup is slow (~18MB unpacked per launch) and `--onedir` would fix it at the cost of
  single-file distribution.

### Traps this repo has already sprung

- **Qt in the build environment.** PyQt5 installed into the system Python made the pywebview hook
  bundle all of it — 18MB → 49.6MB. Excluded in all three build files now; still check the size.
- **Chain release steps with `&&`.** A patch script failed with a syntax error, the next command ran
  anyway against the *unpatched* script, and it deleted and recreated the v1.23.1 release with the
  wrong body. The body was restored via `PATCH` (never delete/recreate to edit a release), but the
  published date and download count were lost permanently. Tags survive release deletion.
- **Heredocs here eat backslashes.** `\n` inside a `<<'PY'` heredoc reaches Python as a real
  newline, which silently breaks string literals. For anything with backslashes, write the file with
  `cat > file` first and run it, or build the characters with `chr(92)`.
- **Never name a scratch script after a stdlib module.** A `inspect.py` in `%TEMP%` shadowed the real
  one and broke `import webview` for every script run from that directory.
- Scratch scripts in `%TEMP%` are wiped between sessions — expect to recreate the release script.
- **pywebview window objects are GUI-thread-only, and the frozen build is stricter than source.**
  Touching `evaluate_js` / `restore()` / `show()` / `on_top` from any thread you created hangs or
  kills the process. Even the JS→Python API thread is not safe for them in a PyInstaller build,
  though it looks fine when run from source. Queue work for the frontend instead, and reach the
  window through the OS (user32 on the HWND) when you must. `python app.py` will not reproduce any
  of this — **every fix in this area has to be verified on the built exe, repeatedly**, since the
  failure is nondeterministic (it alternated between freeze and crash across runs).
- **Heredocs eat backslashes — write JS to a file instead.** Patching `ui/index.html` through a
  `<<'PY'` heredoc mangled `\n` into a real newline and broke the script twice in one session. For
  anything containing backslashes, `cat > file.js` the code verbatim, `node --check` it, then have a
  small Python script splice that file in. Same for probe scripts used in testing.
- **Editing a published release: `PATCH`, never delete-and-recreate.** A wrong release title was
  fixed in place with `PATCH`, keeping the asset and publish date. An earlier delete-and-recreate
  permanently lost the publish date and download count.
