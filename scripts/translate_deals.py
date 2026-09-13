#!/usr/bin/env python3
"""Generate localized deal feeds while preserving prices, URLs, and identifiers."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path

from translate_settlements import LANGUAGES, translate_text

ROOT = Path(__file__).resolve().parents[1]
SCALAR_FIELDS = ("title", "description")
LIST_FIELDS = ("features",)


def translate_deal(deal: dict, language: str) -> dict:
    result = dict(deal)
    brand = deal.get("brand", "")
    for field in SCALAR_FIELDS:
        result[field] = translate_text(deal[field], brand, language)
    for field in LIST_FIELDS:
        result[field] = [translate_text(value, brand, language) for value in deal.get(field, [])]
    summary = deal.get("reviewSummary")
    if summary:
        result["reviewSummary"] = {
            "pros": [translate_text(value, brand, language) for value in summary.get("pros", [])],
            "cons": [translate_text(value, brand, language) for value in summary.get("cons", [])],
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", required=True, choices=LANGUAGES)
    parser.add_argument("--source", type=Path, default=ROOT / "deals.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    source = json.loads(args.source.read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        localized = list(pool.map(lambda deal: translate_deal(deal, args.language), source))
    output = args.output or ROOT / f"deals.{args.language}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(localized, ensure_ascii=False, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
