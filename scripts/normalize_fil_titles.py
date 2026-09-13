#!/usr/bin/env python3
"""Apply FreeClaim's Filipino legal-domain glossary to settlement titles."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Longest/specific phrases first. Brand names, amounts, case identifiers, and dates
# remain untouched. These natural Filipino/Taglish terms match the UI glossary.
PHRASES = (
    ("Data Privacy", "Pagkapribado ng Data"),
    ("Data Breach", "Paglabag sa Data"),
    ("Job Posting", "Pag-post ng Trabaho"),
    ("False Advertising", "Maling Advertising"),
    ("Age Discrimination", "Diskriminasyon sa Edad"),
    ("Price Fixing", "Pag-aayos ng Presyo"),
    ("Merchant Interchange Fee", "Bayarin sa Merchant Interchange"),
    ("Merchant Fee", "Bayarin sa Merchant"),
    ("Subscription Fees", "Mga Bayarin sa Subscription"),
    ("Unwanted Texts/Calls", "Hindi Gustong Text/Call"),
    ("Safety Recall & Replacement", "Safety Recall at Pagpapalit"),
    ("Wire Harness Defect", "Depekto sa Wire Harness"),
    ("Class Action Settlement", "Kasunduan sa Class Action"),
    ("Pricing", "Pagpepresyo"),
    ("Mislabeling", "Maling Pag-label"),
    ("Settlement", "Kasunduan"),
    ("Restitution", "Restitusyon"),
)


def normalize(title: str) -> str:
    for source, target in PHRASES:
        title = re.sub(re.escape(source), target, title, flags=re.I)
    return title


def main() -> int:
    path = ROOT / "settlements.fil.json"
    settlements = json.loads(path.read_text())
    changed = 0
    for settlement in settlements:
        title = settlement.get("title", "")
        localized = normalize(title)
        if localized != title:
            settlement["title"] = localized
            changed += 1
    path.write_text(json.dumps(settlements, ensure_ascii=False, indent=2) + "\n")
    print(f"Normalized {changed} Filipino settlement titles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
