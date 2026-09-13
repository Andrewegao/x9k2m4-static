#!/usr/bin/env python3
"""Import the reviewed published Spanish feed and add current schema-only fields.

The published Spanish feed predates payoutDisplayType but contains the more polished
human-reviewed prose. Immutable English facts are verified before it can replace the
local file.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://raw.githubusercontent.com/Andrewegao/x9k2m4-static/main/settlements.es.json"
SCHEMA_ONLY_FIELDS = ("payoutDisplayType",)
PROTECTED_FIELDS = (
    "id", "company", "imageURL", "logoURL", "deadline", "category",
    "proofRequired", "claimURL", "sourceURL", "dateAdded", "status",
    "claimCount", "totalAmount",
)


def main() -> int:
    english = json.loads((ROOT / "settlements.json").read_text())
    with urllib.request.urlopen(URL, timeout=30) as response:
        spanish = json.load(response)
    spanish_by_id = {item["id"]: item for item in spanish}
    if len(spanish_by_id) != len(spanish) or set(spanish_by_id) != {item["id"] for item in english}:
        raise RuntimeError("published Spanish IDs differ from the English feed")
    ordered = []
    refreshed_facts = 0
    for source in english:
        target = spanish_by_id[source["id"]]
        for field in PROTECTED_FIELDS:
            if target.get(field) != source.get(field):
                refreshed_facts += 1
            target[field] = source[field]
        for field in SCHEMA_ONLY_FIELDS:
            target[field] = source[field]
        # Court names and docket identifiers are citations, not prose.
        target["caseInfo"] = source["caseInfo"]
        if set(target) != set(source):
            raise RuntimeError(f"{source['id']}: published schema differs after merge")
        ordered.append(target)
    (ROOT / "settlements.es.json").write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"Imported {len(ordered)} reviewed Spanish records; "
        f"refreshed {refreshed_facts} immutable facts from English"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
