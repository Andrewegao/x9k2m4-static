#!/usr/bin/env python3
"""Translate missing settlement records with boundary-safe requests.

This is a rate-limit-friendly baseline generator. Reviewed language-specific overrides
must still be applied before publication.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

from translate_settlements import (
    LANGUAGES,
    TRANSLATABLE_LISTS,
    TRANSLATABLE_SCALARS,
    restore,
    source_hash,
)

ROOT = Path(__file__).resolve().parents[1]


def request_translation(text: str, language: str) -> str:
    command = [
        "curl", "-fsS", "--get",
        "https://translate.googleapis.com/translate_a/single",
        "--data-urlencode", "client=gtx",
        "--data-urlencode", "sl=en",
        "--data-urlencode", f"tl={LANGUAGES[language]}",
        "--data-urlencode", "dt=t",
        "--data-urlencode", "format=html",
        "--data-urlencode", f"q={text}",
    ]
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            payload = json.loads(result.stdout)
            return "".join(segment[0] for segment in payload[0] if segment and segment[0])
        except Exception as error:
            last_error = error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"translation request failed: {last_error}")


def translate_record(record: dict, language: str, *, isolated: bool = False) -> dict:
    entries: list[tuple[str, int | None, str]] = []
    for field in TRANSLATABLE_SCALARS:
        value = record.get(field)
        if isinstance(value, str):
            entries.append((field, None, value))
    for field in TRANSLATABLE_LISTS:
        value = record.get(field)
        if isinstance(value, list):
            entries.extend((field, index, item) for index, item in enumerate(value))

    # A hard paragraph delimiter is more reliable than inline field markers here.
    # Inline markers can be moved into adjacent clauses by the translation service,
    # which previously corrupted dates and leaked marker text into the output.
    chunks = []
    for _, _, value in entries:
        # Translate each complete field naturally. Protecting every number/date with
        # inline HTML caused word-order corruption in inflected languages. Numeric
        # and monetary facts are checked against English by validate_localizations.py.
        chunks.append(value)
    if isolated:
        # A few unusually long legal descriptions cause every artificial delimiter
        # to be altered. Isolated requests ensure fields can never bleed together.
        values = [
            restore(request_translation(chunk, language), {})
            for chunk in chunks
        ]
    else:
        values = []
        for delimiter_token in ("⬛⬛⬛", "@@@", "• • •", "⟪⟫"):
            delimiter = f"\n{delimiter_token}\n"
            translated = request_translation(delimiter.join(chunks), language)
            values = [
                restore(value.strip(), {})
                for value in translated.split(delimiter_token)
            ]
            if len(values) == len(entries):
                break
        else:
            values = [
                restore(request_translation(chunk, language), {})
                for chunk in chunks
            ]

    output = dict(record)
    for field in TRANSLATABLE_LISTS:
        if isinstance(record.get(field), list):
            output[field] = list(record[field])
    for (field, index, _), value in zip(entries, values):
        if not value:
            raise ValueError(f"empty translated field {record['id']}/{field}")
        if index is None:
            output[field] = value
        else:
            output[field][index] = value
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", required=True, choices=LANGUAGES)
    parser.add_argument(
        "--refresh-date-added",
        help="Also regenerate records with this dateAdded value (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--isolated",
        action="store_true",
        help="Translate every field in a separate request for maximum boundary safety.",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=1,
        help="Resume at this one-based index within the selected records.",
    )
    args = parser.parse_args()

    source = json.loads((ROOT / "settlements.json").read_text())
    output_path = ROOT / f"settlements.{args.language}.json"
    manifest_path = ROOT / "localization" / f"manifest.{args.language}.json"
    existing = {record["id"]: record for record in json.loads(output_path.read_text())}
    manifest = json.loads(manifest_path.read_text())
    selected = [
        record for record in source
        if record["id"] not in existing
        or (args.refresh_date_added and record.get("dateAdded") == args.refresh_date_added)
    ]
    pending = selected[max(args.start_index - 1, 0):]
    print(
        f"{args.language}: localizing {len(pending)} of {len(selected)} selected records",
        flush=True,
    )

    translated_fields = (*TRANSLATABLE_SCALARS, *TRANSLATABLE_LISTS)

    def write_checkpoint() -> None:
        ordered = [
            {
                **record,
                **{
                    key: existing[record["id"]][key]
                    for key in translated_fields
                    if key in existing[record["id"]]
                },
            }
            for record in source
        ]
        output_path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n")
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )

    for index, record in enumerate(pending, 1):
        existing[record["id"]] = translate_record(
            record, args.language, isolated=args.isolated
        )
        manifest[record["id"]] = source_hash(record)
        write_checkpoint()
        if index % 5 == 0 or index == len(pending):
            print(f"  {index}/{len(pending)}", flush=True)

    write_checkpoint()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
