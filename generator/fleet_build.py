"""Build per-AMR configs from any policy template + inventory.csv."""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path

from conf_fields import (
    apply_ips,
    apply_mac,
    normalize_amr_id,
    read_template_macs,
)

ROOT = Path(__file__).resolve().parent.parent
POLICY_HISTORY_DIR = ROOT / "policy_history"


def _field(row: dict[str, str], *names: str) -> str:
    for name in names:
        if name in row:
            return row[name].strip()
    normalized = {k.strip(): v for k, v in row.items()}
    for name in names:
        if name in normalized:
            return normalized[name].strip()
    raise KeyError(names[0])


def load_inventory(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return [
            {
                "amr_id": normalize_amr_id(_field(row, "AMR ID")),
                "mac": _field(row, "MAC"),
                "switch": _field(row, "Switch IP"),
                "ipc": _field(row, "IPC IP"),
                "plc": _field(row, "PLC IP"),
            }
            for row in csv.DictReader(f)
        ]


def amr_slug(amr_id: str) -> str:
    return amr_id.replace(" ", "_")


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def downloads_dir() -> Path:
    return Path.home() / "Downloads"


def fleet_output_dir(stamp: str | None = None) -> Path:
    """Fleet folder under the user's Downloads directory."""
    stamp = stamp or _timestamp()
    return downloads_dir() / f"Fleet_config_{stamp}"


def save_policy_history(template_text: str, source_name: str, stamp: str | None = None) -> Path:
    """Keep one .conf per fleet push in the repo for later reference."""
    POLICY_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = stamp or _timestamp()
    safe_name = re.sub(r"[^\w.\-]+", "_", source_name).strip("._") or "policy.conf"
    if not safe_name.lower().endswith(".conf"):
        safe_name += ".conf"
    dest = POLICY_HISTORY_DIR / f"fleet_push_{stamp}_{safe_name}"
    dest.write_text(template_text, encoding="utf-8")
    return dest


def write_fleet_manifest(
    out_dir: Path,
    *,
    policy_archive: Path,
    amr_count: int,
) -> None:
    manifest = out_dir / "README.txt"
    manifest.write_text(
        "\n".join(
            [
                "AMR Fleet config build",
                f"Generated: {datetime.now().isoformat(timespec='seconds')}",
                f"AMR count: {amr_count}",
                f"Policy archived in repo: {policy_archive}",
                "",
                "Load each config_AMR_XX.conf on the switch matching inventory_used.csv.",
            ]
        ),
        encoding="utf-8",
    )


def build_fleet_configs(
    template_text: str,
    inventory: list[dict[str, str]],
    out_dir: Path,
    *,
    save_template_copy: str | None = None,
) -> list[str]:
    """Apply each inventory row to template; write configs under out_dir."""
    template_header, template_engine = read_template_macs(template_text)
    out_dir.mkdir(parents=True, exist_ok=True)

    if save_template_copy:
        (out_dir / save_template_copy).write_text(template_text, encoding="utf-8")

    written: list[str] = []
    for row in inventory:
        text = template_text
        text = apply_ips(text, row["switch"], row["ipc"], row["plc"])
        text = apply_mac(text, template_header, template_engine, row["mac"])
        name = f"config_{amr_slug(row['amr_id'])}.conf"
        (out_dir / name).write_text(text, encoding="utf-8")
        written.append(name)
    return written


def build_fleet_from_paths(
    template_path: Path,
    inventory_path: Path,
    out_dir: Path | None = None,
) -> tuple[Path, list[str]]:
    inventory = load_inventory(inventory_path)
    if not inventory:
        raise ValueError("inventory.csv has no rows")
    template_text = template_path.read_text(encoding="utf-8", errors="replace")
    target = out_dir or fleet_output_dir()
    names = build_fleet_configs(template_text, inventory, target)
    return target, names
