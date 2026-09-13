#!/usr/bin/env python3
"""Repair only translated fields whose immutable numeric/date facts changed.

The normal translator is free to restructure prose. This conservative second pass
translates prose around every protected fact and rejoins each fact verbatim, making it
appropriate for the relatively small set of fields caught by the localization validator.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from translate_settlements import translate_text_segmented

ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "freeclaim_localization_validator", ROOT / "scripts" / "validate_localizations.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load localization validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    validator = load_validator()
    english = json.loads((ROOT / "settlements.json").read_text())
    source_by_id = {item["id"]: item for item in english}
    total = 0

    for language in validator.LANGUAGES:
        path = ROOT / f"settlements.{language}.json"
        localized = json.loads(path.read_text())
        repaired = 0
        for item in localized:
            source = source_by_id[item["id"]]
            company = source.get("company", "")
            for field in validator.TRANSLATABLE_FIELDS:
                source_value = source.get(field)
                target_value = item.get(field)
                if validator.numbers(target_value, language) == validator.numbers(source_value, "en"):
                    continue
                if isinstance(source_value, list):
                    result = list(target_value) if isinstance(target_value, list) else list(source_value)
                    for index, source_part in enumerate(source_value):
                        target_part = result[index] if index < len(result) else ""
                        if validator.numbers(target_part, language) != validator.numbers(source_part, "en"):
                            result[index] = translate_text_segmented(source_part, company, language)
                    item[field] = result
                elif isinstance(source_value, str):
                    item[field] = translate_text_segmented(source_value, company, language)
                repaired += 1
        path.write_text(json.dumps(localized, ensure_ascii=False, indent=2) + "\n")
        print(f"{language}: repaired {repaired} fields")
        total += repaired

    print(f"Repaired {total} localized fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
