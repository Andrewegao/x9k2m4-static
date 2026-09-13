#!/usr/bin/env python3
"""Validate localized deal feeds against an arbitrary canonical deal catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from validate_localizations import numbers

TRANSLATABLE = {"title", "description", "features", "reviewSummary"}
ENGLISH_NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
}


def deal_numbers(value, language: str) -> Counter[str]:
    return numbers(value, language)


def deal_facts_match(source, target, language: str) -> bool:
    source_numbers = deal_numbers(source, "en")
    target_numbers = deal_numbers(target, language)
    # It is natural for a translator to render an English number word as a digit
    # ("one week" -> "1 tuần"). Accept only that bounded extra digit; all explicit
    # source digits, prices, percentages, and quantities still compare exactly.
    source_text = json.dumps(source, ensure_ascii=False).casefold()
    for word, normalized in ENGLISH_NUMBER_WORDS.items():
        allowance = len(re.findall(rf"\b{word}\b", source_text))
        extra = target_numbers[normalized] - source_numbers[normalized]
        if extra > 0:
            target_numbers[normalized] -= min(extra, allowance)
            if target_numbers[normalized] == 0:
                del target_numbers[normalized]
    return target_numbers == source_numbers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument(
        "--localized", action="append", required=True,
        help="language=path (repeat for each localized feed)",
    )
    args = parser.parse_args()
    source = json.loads(args.source.read_text())
    source_by_id = {item["id"]: item for item in source}
    errors: list[str] = []

    for value in args.localized:
        language, separator, raw_path = value.partition("=")
        if not separator:
            parser.error("--localized must be language=path")
        path = Path(raw_path)
        localized = json.loads(path.read_text())
        if [item.get("id") for item in localized] != [item["id"] for item in source]:
            errors.append(f"{language}: record IDs/order differ from source")
        for item in localized:
            deal_id = item.get("id")
            english = source_by_id.get(deal_id)
            if english is None:
                continue
            if set(item) != set(english):
                errors.append(f"{language}/{deal_id}: schema keys differ")
            for field in set(english) - TRANSLATABLE:
                if item.get(field) != english.get(field):
                    errors.append(f"{language}/{deal_id}/{field}: protected fact changed")
            for field in TRANSLATABLE:
                if not deal_facts_match(english.get(field), item.get(field), language):
                    errors.append(f"{language}/{deal_id}/{field}: numeric facts changed")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(source)} deals across {len(args.localized)} localized feeds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
