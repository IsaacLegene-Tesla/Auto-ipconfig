# Desktop viewer

## Daily use

Double-click **`Launch_Fleet_Viewer.bat`** in the repo root.

- Opens a **standalone window** (not a browser tab)
- Starts the Flask server in the background
- Close the window when you are done

Uses **pywebview** (Python + Edge WebView2 on Windows). First run installs dependencies from `requirements.txt`.

## Optional future packaging

A Tauri `.exe` could wrap the same UI later. See `docs/UI_OPTIONS.md` and `docs/TAURI_BUILD.md` — not required for daily use.
