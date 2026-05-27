#!/usr/bin/env python3
"""
Local web UI for fleet config generation and baseline management.
Run Launch_Fleet_Config.bat or: python generator/fleet_app.py
"""

from __future__ import annotations

import re
import shutil
import webbrowser
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

from extract_inventory import baseline_filename, run_extract
from fleet_build import (
    ROOT,
    build_fleet_configs,
    fleet_output_dir,
    load_inventory,
    save_policy_history,
    write_fleet_manifest,
)

INVENTORY_PATH = ROOT / "inventory.csv"
BASELINES_DIR = ROOT / "baselines"
HOST = "127.0.0.1"
PORT = 8765

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AMR Fleet Config Builder</title>
  <style>
    :root { font-family: Segoe UI, system-ui, sans-serif; color: #1a1a1a; }
    body { max-width: 640px; margin: 2rem auto; padding: 0 1rem 3rem; }
    h1 { font-size: 1.35rem; font-weight: 600; margin-bottom: 0.25rem; }
    h2 { font-size: 1.1rem; font-weight: 600; margin-top: 2rem; padding-top: 1.5rem; border-top: 2px solid #eee; }
    p { line-height: 1.5; color: #444; }
    label { display: block; font-weight: 600; margin-top: 1rem; }
    input[type=file], input[type=text], input[type=number] {
      width: 100%; box-sizing: border-box; margin-top: 0.35rem;
      padding: 0.5rem; border: 1px solid #ccc; border-radius: 6px;
    }
    button {
      margin-top: 1.25rem; padding: 0.65rem 1.25rem; font-size: 1rem;
      background: #cc0000; color: #fff; border: none; border-radius: 6px;
      cursor: pointer;
    }
    button.secondary { background: #333; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .status { margin-top: 1rem; padding: 0.75rem; border-radius: 6px; display: none; }
    .status.ok { display: block; background: #e8f5e9; border: 1px solid #a5d6a7; }
    .status.err { display: block; background: #ffebee; border: 1px solid #ef9a9a; }
    .meta { font-size: 0.9rem; color: #666; margin-top: 0.5rem; }
    .hint { font-size: 0.85rem; color: #666; font-weight: 400; }
    ul.baseline-list { margin: 0.5rem 0 0; padding-left: 1.25rem; color: #444; font-size: 0.9rem; max-height: 120px; overflow-y: auto; }
    code { font-size: 0.88em; }
  </style>
</head>
<body>
  <h1>AMR Fleet Config Builder</h1>
  <p class="meta" id="inventoryMeta">Checking inventory…</p>

  <h2>Fleet build</h2>
  <p>Upload the <strong>updated policy</strong> .conf from any switch after site settings change.
     Each AMR file keeps its own MAC and IPs from <code>inventory.csv</code>.</p>
  <p class="hint">Fleet output goes to your <strong>Downloads</strong> folder. The uploaded policy is archived in <code>policy_history/</code> in the repo.</p>

  <form id="fleetForm">
    <label>Policy config file</label>
    <input type="file" name="config" accept=".conf" />

    <label>Or full path on this PC</label>
    <input type="text" name="config_path" placeholder="C:\\Users\\...\\updated.conf" />

    <button type="submit" id="fleetBtn">Build fleet folder</button>
  </form>
  <div id="fleetStatus" class="status"></div>

  <h2>Baselines</h2>
  <p>Add a switch export for a new AMR. Saved as
     <code>config_SCALANCE_S600_AMR_&lt;#&gt;.conf</code> in <code>baselines/</code>
     and <code>inventory.csv</code> is refreshed automatically.</p>

  <p class="meta" id="baselineMeta">Loading baselines…</p>

  <form id="baselineForm">
    <label>AMR number</label>
    <input type="number" name="amr_number" min="1" step="1" required placeholder="e.g. 51" />

    <label>Switch export (.conf)</label>
    <input type="file" name="baseline" accept=".conf" />

    <label>Or full path on this PC</label>
    <input type="text" name="baseline_path" placeholder="C:\\Users\\...\\export.conf" />

    <p class="hint">Provide a file upload <em>or</em> a path. AMR number is required.</p>

    <button type="submit" class="secondary" id="baselineBtn">Add to baselines</button>
  </form>
  <div id="baselineStatus" class="status"></div>

  <script>
    function showStatus(el, ok, htmlOrText) {
      el.style.display = 'block';
      el.className = 'status ' + (ok ? 'ok' : 'err');
      if (ok && htmlOrText.includes('<')) el.innerHTML = htmlOrText;
      else el.textContent = htmlOrText;
    }

    async function refreshMeta() {
      const inv = document.getElementById('inventoryMeta');
      const base = document.getElementById('baselineMeta');
      try {
        const r = await fetch('/api/status');
        const d = await r.json();
        if (d.ok) {
          inv.textContent = d.amr_count + ' AMR(s) in inventory.csv';
          if (d.baselines.length) {
            base.innerHTML = '<strong>' + d.baselines.length + '</strong> baseline file(s):<ul class="baseline-list">' +
              d.baselines.map(b => '<li>' + b + '</li>').join('') + '</ul>';
          } else {
            base.textContent = 'No baselines yet.';
          }
        } else {
          inv.textContent = d.error;
          base.textContent = '';
        }
      } catch (e) {
        inv.textContent = String(e);
      }
    }
    refreshMeta();

    document.getElementById('fleetForm').onsubmit = async (e) => {
      e.preventDefault();
      const btn = document.getElementById('fleetBtn');
      const status = document.getElementById('fleetStatus');
      const fd = new FormData(e.target);
      const policyFile = fd.get('config');
      const hasFile = policyFile && policyFile.size > 0;
      if (!hasFile && !fd.get('config_path')) {
        showStatus(status, false, 'Choose a policy file or enter a path.');
        return;
      }
      btn.disabled = true;
      showStatus(status, true, 'Building…');
      try {
        const res = await fetch('/api/build', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.ok) {
          let msg = 'Created <strong>' + data.count + '</strong> configs in Downloads:<br><code>' +
            data.folder + '</code>';
          if (data.policy_archive) {
            msg += '<br>Policy saved in repo:<br><code>' + data.policy_archive + '</code>';
          }
          showStatus(status, true, msg);
        } else {
          showStatus(status, false, data.error || 'Build failed');
        }
      } catch (err) {
        showStatus(status, false, String(err));
      }
      btn.disabled = false;
    };

    document.getElementById('baselineForm').onsubmit = async (e) => {
      e.preventDefault();
      const btn = document.getElementById('baselineBtn');
      const status = document.getElementById('baselineStatus');
      const fd = new FormData(e.target);
      const file = fd.get('baseline');
      const path = (fd.get('baseline_path') || '').trim();
      const hasBaselineFile = file && file.size > 0;
      if (!hasBaselineFile && !path) {
        showStatus(status, false, 'Choose a .conf file or enter a path.');
        return;
      }
      btn.disabled = true;
      showStatus(status, true, 'Saving baseline…');
      try {
        const res = await fetch('/api/baselines/add', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.ok) {
          let msg = 'Saved <code>' + data.filename + '</code>';
          if (data.overwritten) msg += ' (replaced existing file)';
          msg += '<br>inventory.csv updated — <strong>' + data.inventory_count + '</strong> AMR(s).';
          showStatus(status, true, msg);
          e.target.reset();
          refreshMeta();
        } else {
          showStatus(status, false, data.error || 'Failed');
        }
      } catch (err) {
        showStatus(status, false, String(err));
      }
      btn.disabled = false;
    };
  </script>
</body>
</html>
"""


def parse_amr_number(raw: str) -> int:
    digits = re.sub(r"\D", "", (raw or "").strip())
    if not digits:
        raise ValueError("AMR number is required")
    number = int(digits)
    if number < 1:
        raise ValueError("AMR number must be positive")
    return number


def list_baseline_files() -> list[str]:
    if not BASELINES_DIR.is_dir():
        return []
    return sorted(p.name for p in BASELINES_DIR.glob("*.conf"))


def refresh_inventory() -> tuple[int, list[str]]:
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    return run_extract(BASELINES_DIR, INVENTORY_PATH)


@app.get("/")
def index():
    return render_template_string(HTML)


@app.get("/api/status")
def status():
    baselines = list_baseline_files()
    if not INVENTORY_PATH.is_file():
        return jsonify(
            ok=bool(baselines),
            amr_count=0,
            baselines=baselines,
            error="inventory.csv missing — add a baseline or run extract_inventory.py",
        )
    try:
        rows = load_inventory(INVENTORY_PATH)
        return jsonify(ok=True, amr_count=len(rows), baselines=baselines)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc), baselines=baselines)


@app.post("/api/baselines/add")
def add_baseline():
    try:
        amr_number = parse_amr_number(request.form.get("amr_number", ""))
    except ValueError as exc:
        return jsonify(ok=False, error=str(exc))

    filename = baseline_filename(amr_number)
    dest = BASELINES_DIR / filename
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)

    upload = request.files.get("baseline")
    path_text = (request.form.get("baseline_path") or "").strip()
    overwritten = dest.is_file()

    try:
        if upload and upload.filename:
            content = upload.read()
            dest.write_bytes(content)
        elif path_text:
            src = Path(path_text)
            if not src.is_file():
                return jsonify(ok=False, error=f"File not found: {src}")
            shutil.copy2(src, dest)
        else:
            return jsonify(ok=False, error="Choose a .conf file or enter a path.")

        text = dest.read_text(encoding="utf-8", errors="replace")
        from conf_fields import extract_fields

        extract_fields(text)
        count, warnings = refresh_inventory()
    except Exception as exc:
        if dest.is_file() and not overwritten:
            dest.unlink(missing_ok=True)
        return jsonify(ok=False, error=str(exc))

    return jsonify(
        ok=True,
        filename=filename,
        amr_id=f"AMR {amr_number}",
        overwritten=overwritten,
        inventory_count=count,
        warnings=warnings,
    )


@app.post("/api/build")
def build():
    if not INVENTORY_PATH.is_file():
        return jsonify(
            ok=False,
            error="inventory.csv not found. Add baselines first.",
        )

    try:
        inventory = load_inventory(INVENTORY_PATH)
    except Exception as exc:
        return jsonify(ok=False, error=f"inventory.csv: {exc}")

    template_text: str | None = None
    source_name = "fleet_policy_source.conf"

    upload = request.files.get("config")
    path_text = (request.form.get("config_path") or "").strip()

    if upload and upload.filename:
        template_text = upload.read().decode("utf-8", errors="replace")
        source_name = Path(upload.filename).name
    elif path_text:
        path = Path(path_text)
        if not path.is_file():
            return jsonify(ok=False, error=f"File not found: {path}")
        template_text = path.read_text(encoding="utf-8", errors="replace")
        source_name = path.name
    else:
        return jsonify(ok=False, error="Choose a policy file or enter a path.")

    try:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        policy_archive = save_policy_history(template_text, source_name, stamp=stamp)
        out_dir = fleet_output_dir(stamp=stamp)
        names = build_fleet_configs(template_text, inventory, out_dir)
        shutil.copy2(INVENTORY_PATH, out_dir / "inventory_used.csv")
        shutil.copy2(policy_archive, out_dir / policy_archive.name)
        write_fleet_manifest(
            out_dir,
            policy_archive=policy_archive.relative_to(ROOT),
            amr_count=len(names),
        )
    except Exception as exc:
        return jsonify(ok=False, error=str(exc))

    return jsonify(
        ok=True,
        count=len(names),
        folder=str(out_dir),
        policy_archive=str(policy_archive),
        files=names,
    )


def main() -> None:
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    url = f"http://{HOST}:{PORT}/"
    print(f"Fleet builder: {url}")
    print("Close this window or press Ctrl+C to stop.")
    webbrowser.open(url)
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
