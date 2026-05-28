# UI options

## What you use today

**`Launch_Fleet_Viewer.bat`** → Python + **Flask** API + **pywebview** desktop window.

- Same HTML/CSS UI as during development
- No browser tab
- Requires Python 3.10+ on the PC (installed once per machine)

## If you want a single `.exe` later: **Tauri**

| | pywebview (now) | Tauri (future) |
|---|-----------------|----------------|
| Window | Desktop app | Desktop app |
| User install | Python + `.bat` | Possible standalone `.exe` |
| Backend | Keep Python fleet logic | Rust shell + Python, or rewrite |

See `docs/TAURI_BUILD.md` when that path is worth doing.

## Other options (not in use)

- **Flet** — Python UI framework; would replace the current HTML front end
- **Electron** — large install; usually not worth it here
