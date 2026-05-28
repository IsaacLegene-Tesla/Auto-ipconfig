# Auto-ipconfig

Generate per-AMR SCALANCE switch configs from one policy file + fleet inventory.

## Quick start

1. **New AMR:** run **`Launch_Fleet_Config.bat`** → **Baselines** section → enter AMR #, upload export → saved as `config_SCALANCE_S600_AMR_<#>.conf`.
2. Or drop files in `baselines/` manually, then `python generator/extract_inventory.py`
3. **Fleet policy change:** same launcher → **Fleet build** → upload updated policy `.conf` → all AMR configs in **Downloads** (`Fleet_config_YYYYMMDD_HHMMSS/`), policy copy in `policy_history/`

## Folders

| Folder | Purpose |
|--------|---------|
| `baselines/` | One `.conf` per physical switch (committed to repo) |
| `inventory.csv` | MAC + Switch / IPC / PLC per AMR (auto-generated) |
| `IP.csv` | Reference IP plan (optional) |
| `policy_history/` | One archived policy `.conf` per fleet push (in repo) |
| Downloads `Fleet_config_*` | Per-AMR configs to load on switches |
| `output/` | Optional CLI output (`python generator/generate.py`) |

## Commands

```text
python generator/extract_inventory.py
python generator/generate.py
```

`Launch_Fleet_Config.bat` runs the browser UI (installs Flask on first run).

## Load on hardware

Each `config_AMR_XX.conf` goes on the switch whose MAC matches that row in `inventory_used.csv` inside the fleet folder.

## Requirements

Python 3.10+ — see `requirements.txt`.
