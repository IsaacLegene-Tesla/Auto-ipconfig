#!/usr/bin/env python3
"""CLI: build configs into output/ from REFRENCE.conf + inventory.csv."""

from __future__ import annotations

import argparse
from pathlib import Path

from fleet_build import ROOT, build_fleet_configs, load_inventory


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate per-AMR SCALANCE configs.")
    parser.add_argument("--template", type=Path, default=ROOT / "REFRENCE.conf")
    parser.add_argument("--inventory", type=Path, default=ROOT / "inventory.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "output")
    args = parser.parse_args()

    if not args.inventory.is_file():
        raise SystemExit(
            f"inventory not found: {args.inventory}\n"
            "Run: python generator/extract_inventory.py"
        )

    args.out.mkdir(parents=True, exist_ok=True)
    template_text = args.template.read_text(encoding="utf-8", errors="replace")
    inventory = load_inventory(args.inventory)
    names = build_fleet_configs(template_text, inventory, args.out, save_template_copy=None)
    print(f"done: {len(names)} file(s) in {args.out}")


if __name__ == "__main__":
    main()
