#!/usr/bin/env python3
"""
Local web UI for fleet config generation and baseline management.
Started by viewer/launch_desktop.py (Launch_Fleet_Viewer.bat).
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from flask import Flask, jsonify, render_template, request

from extract_inventory import baseline_filename, run_extract
from fleet_build import (
    ROOT,
    build_fleet_configs,
    fleet_output_dir,
    load_inventory,
    save_policy_history,
    write_fleet_manifest,
)

GENERATOR_DIR = Path(__file__).resolve().parent
STATIC_DIR = GENERATOR_DIR / "static"
INVENTORY_PATH = ROOT / "inventory.csv"
BASELINES_DIR = ROOT / "baselines"
HOST = "127.0.0.1"
PORT = 8765

LOGO_FILENAME = "tesla symbol.png"

app = Flask(
    __name__,
    template_folder=str(GENERATOR_DIR / "templates"),
    static_folder=str(GENERATOR_DIR / "static"),
)


def parse_amr_number(raw: str) -> int:
    digits = re.sub(r"\D", "", (raw or "").strip())
    if not digits:
        raise ValueError("AMR number is required")
    number = int(digits)
    if number < 1:
        raise ValueError("AMR number must be positive")
    return number


def find_logo() -> str | None:
    path = STATIC_DIR / LOGO_FILENAME
    if path.is_file():
        return f"/static/{quote(LOGO_FILENAME)}"
    return None


def list_baseline_files() -> list[str]:
    if not BASELINES_DIR.is_dir():
        return []
    return sorted(p.name for p in BASELINES_DIR.glob("*.conf"))


def refresh_inventory() -> tuple[int, list[str]]:
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    return run_extract(BASELINES_DIR, INVENTORY_PATH)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/assets/<path:filename>")
def repo_assets(filename: str):
    from flask import send_from_directory

    return send_from_directory(ROOT, filename)


@app.get("/api/branding")
def branding():
    url = find_logo()
    return jsonify(logo_url=url, logo_invert=False, logo_banner=bool(url))


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
            dest.write_bytes(upload.read())
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

    upload = request.files.get("config")
    path_text = (request.form.get("config_path") or "").strip()
    source_name = "fleet_policy_source.conf"

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


def run_server() -> None:
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Fleet builder: http://{HOST}:{PORT}/", flush=True)
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def main() -> None:
    import sys

    try:
        run_server()
    except KeyboardInterrupt:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
