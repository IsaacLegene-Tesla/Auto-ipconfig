# Optional: Tauri `.exe` (future)

Rust is available via rustup. The **pywebview viewer** (`Launch_Fleet_Viewer.bat`) is the supported desktop app today.

To package with Tauri later:

1. Install [WebView2](https://developer.microsoft.com/microsoft-edge/webview2/) (usually already on Windows 11)
2. From repo root, set env and build (scaffold Tauri app under `viewer/tauri/` first)
3. Ship `amr-fleet-viewer.exe` next to the repo; it must find Python + `generator/` on the machine

Tauri does not remove the Python dependency unless the config logic is rewritten in Rust.
