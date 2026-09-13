#!/usr/bin/env python3
"""Add locale-neutral payout display semantics to every settlement feed."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "settlements.json", "settlements.es.json", "settlements.zh-Hans.json",
    "settlements.vi.json", "settlements.fil.json",
]
DETAIL_TERMS = ("varies", "pro rata", "merchants only", "merchant", "reimbursement", "warranty")


def display_type(value: str) -> str:
    trimmed = value.strip()
    lower = trimmed.lower()
    if not trimmed or lower == "tbd":
        return "tbd"
    if any(term in lower for term in DETAIL_TERMS):
        return "details"
    amounts = re.findall(r"\$\s?[\d,.]+", trimmed)
    if not amounts:
        return "details"
    if lower.startswith("up to") or len(amounts) > 1 or len(trimmed) > len(amounts[0]) + 8:
        return "upTo"
    return "exact"


def main() -> int:
    english = json.loads((ROOT / FILES[0]).read_text())
    semantics = {item["id"]: display_type(item.get("individualPayout", "")) for item in english}
    for name in FILES:
        path = ROOT / name
        records = json.loads(path.read_text())
        for item in records:
            item["payoutDisplayType"] = semantics[item["id"]]
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
        print(f"updated {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
