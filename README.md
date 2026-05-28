# AMR Fleet Config Builder

Update **every AMR’s SCALANCE switch config** from one policy file, without mixing up MAC addresses or IP addresses.

Each robot keeps its own hardware identity (MAC, SNMP IDs, switch/IPC/PLC IPs). When site-wide rules change (firewall, VLANs, SNMP, and so on), you upload the new policy once and the tool builds one ready-to-load `.conf` per AMR.

---

## Open the app

**Double-click:** `Launch_Fleet_Viewer.bat`

A desktop window opens (not a browser tab). Close the window when you are done.

**First run:** installs Python packages automatically (`flask`, `pywebview`). You need **Python 3.10+** installed (3.12 is typical on Windows).

---

## What you do in the app

### Deploy a policy change (most common)

1. Open the app → **Fleet build**
2. Choose your updated site policy `.conf`
3. Click **Deploy fleet configs**
4. Open your **Downloads** folder → `Fleet_config_YYYYMMDD_HHMMSS/`
5. Load each `config_AMR_XX.conf` on the switch that matches that AMR (use `inventory_used.csv` in the same folder to match MAC / IPs)

A copy of the policy you uploaded is also saved under `policy_history/` in this project folder.

### Add or update one AMR

1. Open the app → **Baselines**
2. Enter the AMR number (e.g. `37`)
3. Upload that switch’s full export: `config_SCALANCE_S600_AMR_37.conf`
4. The file is saved in `baselines/` and `inventory.csv` is refreshed automatically

**Alternative:** copy the `.conf` into `baselines/` yourself, then run:

```text
python generator/extract_inventory.py
```

---

## Important folders

| Folder | What it is |
|--------|------------|
| `baselines/` | One saved export per physical switch (source of truth for MAC + IPs) |
| `inventory.csv` | Table of AMR → MAC, switch IP, IPC IP, PLC IP (auto-built from baselines) |
| `policy_history/` | Archive of each policy file you deployed |
| **Downloads** `Fleet_config_*` | Output configs to load on hardware (not stored in this repo) |
| `IP.csv` | Optional reference IP plan only |

---

## Loading configs on switches

- Use the files in the **Downloads** fleet folder, not random copies from another AMR.
- Match each file to the correct switch using **MAC** (and IPs) in `inventory_used.csv`.
- Test **one** generated config on a lab switch before rolling out the full fleet.

---

## Optional: command line

Same logic as the app, without the UI:

```text
python generator/extract_inventory.py   # rebuild inventory.csv from baselines/
python generator/generate.py            # writes to output/ (advanced)
```

---

## Requirements

See `requirements.txt`: **flask**, **pywebview** (desktop window on Windows uses Edge WebView2).

---

## More detail

- `baselines/README.md` — naming and baseline rules  
- `viewer/README.md` — desktop launcher notes  
- `docs/UI_OPTIONS.md` — future packaging options (not needed for daily use)
