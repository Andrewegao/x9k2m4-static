#!/usr/bin/env python3
"""Repair changed numeric facts in localized deal feeds conservatively."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from translate_settlements import translate_text_segmented
from validate_deal_localizations import deal_facts_match


def repair_value(source, target, language: str, brand: str):
    if isinstance(source, str):
        if deal_facts_match(source, target, language):
            return target, False
        return translate_text_segmented(source, brand, language), True
    if isinstance(source, list):
        result = list(target) if isinstance(target, list) else list(source)
        changed = False
        for index, source_part in enumerate(source):
            target_part = result[index] if index < len(result) else ""
            result[index], repaired = repair_value(source_part, target_part, language, brand)
            changed |= repaired
        return result, changed
    if isinstance(source, dict):
        result = dict(target) if isinstance(target, dict) else dict(source)
        changed = False
        for key, source_part in source.items():
            result[key], repaired = repair_value(source_part, result.get(key), language, brand)
            changed |= repaired
        return result, changed
    return target, False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--language", required=True)
    parser.add_argument("--localized", required=True, type=Path)
    args = parser.parse_args()
    source = json.loads(args.source.read_text())
    source_by_id = {item["id"]: item for item in source}
    localized = json.loads(args.localized.read_text())
    repaired = 0
    for item in localized:
        english = source_by_id[item["id"]]
        brand = english.get("brand", "")
        for field in ("title", "description", "features", "reviewSummary"):
            item[field], changed = repair_value(
                english.get(field), item.get(field), args.language, brand
            )
            repaired += int(changed)
    args.localized.write_text(json.dumps(localized, ensure_ascii=False, indent=2) + "\n")
    print(f"{args.language}: repaired {repaired} deal fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
