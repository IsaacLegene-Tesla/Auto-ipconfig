#!/usr/bin/env python3
"""
Read baseline .conf exports (one per AMR) and write inventory.csv.

Baselines are the configs pulled from each physical switch — not generated files.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from conf_fields import amr_id_from_filename, extract_fields, normalize_amr_id

ROOT = Path(__file__).resolve().parent.parent

INVENTORY_COLUMNS = [
    "AMR ID",
    "Source File",
    "MAC",
    "Switch IP",
    "IPC IP",
    "PLC IP",
]


def collect_conf_files(folder: Path) -> list[Path]:
    return sorted(p for p in folder.glob("*.conf") if p.is_file())


def baseline_filename(amr_number: int) -> str:
    return f"config_SCALANCE_S600_AMR_{amr_number}.conf"


def run_extract(
    input_dir: Path | None = None,
    output_path: Path | None = None,
) -> tuple[int, list[str]]:
    """Scan baselines and write inventory.csv. Returns (row_count, warning messages)."""
    input_dir = input_dir or ROOT / "baselines"
    output_path = output_path or ROOT / "inventory.csv"
    warnings: list[str] = []

    if not input_dir.is_dir():
        raise FileNotFoundError(f"baseline folder not found: {input_dir}")

    files = collect_conf_files(input_dir)
    if not files:
        raise ValueError(f"no .conf files in {input_dir}")

    rows: list[dict[str, str]] = []
    for path in files:
        amr = amr_id_from_filename(path.name)
        if not amr:
            warnings.append(f"skip {path.name}: cannot detect AMR number in filename")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            fields = extract_fields(text)
        except RuntimeError as exc:
            warnings.append(f"skip {path.name}: {exc}")
            continue
        rows.append(
            {
                "AMR ID": amr,
                "Source File": path.name,
                "MAC": fields["mac"],
                "Switch IP": fields["switch_ip"],
                "IPC IP": fields["ipc_ip"],
                "PLC IP": fields["plc_ip"],
            }
        )

    if not rows:
        raise ValueError("no rows extracted from baselines")

    rows.sort(key=lambda r: int(r["AMR ID"].split()[-1]))
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=INVENTORY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows), warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract per-AMR MAC/IPs from baseline switch exports."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "baselines",
        help="folder containing one .conf per AMR (default: baselines/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "inventory.csv",
        help="inventory CSV to write (default: inventory.csv)",
    )
    args = parser.parse_args()

    try:
        count, warnings = run_extract(args.input, args.output)
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(exc) from exc

    for msg in warnings:
        print(msg)
    print(f"wrote {count} row(s) to {args.output}")


if __name__ == "__main__":
    main()
