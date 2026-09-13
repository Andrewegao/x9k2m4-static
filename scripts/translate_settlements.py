#!/usr/bin/env python3
"""Incrementally generate a FreeClaim settlement translation.

This intentionally treats the English feed as immutable source data. It protects legal
facts before sending user-visible prose for translation and records a source hash so only
changed records are regenerated.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSLATABLE_SCALARS = (
    "title", "totalAmount", "individualPayout", "eligibility", "proofDetails", "summary",
    "scope", "estimatedClaimTime",
)
TRANSLATABLE_LISTS = ("eligibilityBullets",)
LANGUAGES = {"es": "es", "zh-Hans": "zh-CN", "vi": "vi", "fil": "tl"}
STATE_NAMES = (
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine",
    "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma",
    "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming", "District of Columbia", "Puerto Rico",
)
FACT_PATTERN = re.compile(
    r"ZXQF\d{3}ZXQ|https?://\S+|\$\s?\d[\d,.]*(?:\s?(?:million|billion|M|B))?|"
    r"\b\d+(?:[.,]\d+)?%|\b\d{4}-\d{2}-\d{2}\b|\b\d+(?:[.,]\d+)?[Kk]\b|\b\d+(?:[.,]\d+)?\b",
    re.IGNORECASE,
)


def source_hash(record: dict) -> str:
    payload = {key: record.get(key) for key in (*TRANSLATABLE_SCALARS, *TRANSLATABLE_LISTS)}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def protected_fact_pattern(company: str) -> re.Pattern:
    candidates = sorted((x for x in [company, *STATE_NAMES] if x), key=len, reverse=True)
    alternatives = [re.escape(value) for value in candidates] + [FACT_PATTERN.pattern]
    return re.compile("(?:" + "|".join(alternatives) + ")", re.I)


def protect(text: str, company: str) -> tuple[str, dict[str, str]]:
    # Google Translate honors HTML notranslate spans and removes the tags from its result.
    # This is more reliable than invented placeholder tokens, which some languages can
    # reorder, duplicate, or partially translate around complex dates.
    pattern = protected_fact_pattern(company)
    pieces: list[str] = []
    cursor = 0
    for match in pattern.finditer(text):
        pieces.append(html.escape(text[cursor:match.start()]))
        pieces.append(f'<span class="notranslate">{html.escape(match.group(0))}</span>')
        cursor = match.end()
    pieces.append(html.escape(text[cursor:]))
    return "".join(pieces), {}


def restore(text: str, replacements: dict[str, str]) -> str:
    result = html.unescape(text).strip()
    # Some translations remove ordinary whitespace at an inline-tag boundary. Repair
    # only unambiguous joins (a comma before a 4-digit year, or lowercase-to-uppercase
    # word boundaries) without changing any protected fact.
    result = re.sub(r",(?=\d{4}\b)", ", ", result)
    result = re.sub(r"(?<=[a-záéíóúüñ])(?=[A-Z])", " ", result)
    if "ZZFC" in result or "FCFACT" in result.upper():
        raise ValueError("translation leaked an internal placeholder")
    return result


def translate_text(text: str, company: str, target: str) -> str:
    if not text or not text.strip():
        return text
    # Translation engines occasionally drop ambiguous abbreviated month names (notably
    # "Dec."). Expanding them first retains the date while still allowing localization.
    month_names = {
        "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
        "Jun": "June", "Jul": "July", "Aug": "August", "Sep": "September",
        "Sept": "September", "Oct": "October", "Nov": "November", "Dec": "December",
    }
    for abbreviation, full in month_names.items():
        text = re.sub(rf"\b{abbreviation}\.?(?=\s+\d)", full, text, flags=re.I)
    protected, replacements = protect(text, company)
    params = urllib.parse.urlencode({
        "client": "gtx", "sl": "en", "tl": LANGUAGES[target], "dt": "t", "q": protected,
        "format": "html",
    })
    request = urllib.request.Request(
        "https://translate.googleapis.com/translate_a/single?" + params,
        headers={"User-Agent": "FreeClaim-Localization/1.0"},
    )
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            segments = payload[0] if payload and isinstance(payload[0], list) else None
            if not segments:
                # The endpoint returns no segments when a field is entirely wrapped in
                # notranslate spans (for example a company name or protected amount).
                # In that case the source is intentionally the correct result.
                return text
            translated = "".join(segment[0] for segment in segments if segment and segment[0])
            if not translated:
                raise ValueError("translation endpoint returned an empty translation")
            return restore(translated, replacements)
        except Exception as error:  # transient public endpoint/network failures
            last_error = error
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"translation failed after retries: {last_error}")


def translate_text_segmented(text: str, company: str, target: str) -> str:
    """Fallback that translates prose around immutable facts and rejoins facts verbatim."""
    result: list[str] = []
    cursor = 0
    for match in protected_fact_pattern(company).finditer(text):
        prose = text[cursor:match.start()]
        if prose.strip():
            leading = prose[:len(prose) - len(prose.lstrip())]
            trailing = prose[len(prose.rstrip()):]
            result.append(leading + translate_text(prose.strip(), "", target) + trailing)
        else:
            result.append(prose)
        result.append(match.group(0))
        cursor = match.end()
    prose = text[cursor:]
    if prose.strip():
        leading = prose[:len(prose) - len(prose.lstrip())]
        trailing = prose[len(prose.rstrip()):]
        result.append(leading + translate_text(prose.strip(), "", target) + trailing)
    else:
        result.append(prose)
    return "".join(result).strip()


def translate_record(record: dict, target: str) -> dict:
    translated = dict(record)
    company = record.get("company", "")
    entries: list[tuple[str, int | None, str]] = []
    for field in TRANSLATABLE_SCALARS:
        value = record.get(field)
        if isinstance(value, str):
            entries.append((field, None, value))
    for field in TRANSLATABLE_LISTS:
        value = record.get(field)
        if isinstance(value, list):
            translated[field] = list(value)
            entries.extend((field, index, item) for index, item in enumerate(value))

    # Legal fields must never cross boundaries. Translate each independently: artificial
    # separators can survive in count while still being reordered by a translation engine.
    parts = []
    for entry in entries:
        try:
            parts.append(translate_text(entry[2], company, target))
        except Exception:
            parts.append(translate_text_segmented(entry[2], company, target))
    for (field, index, _), value in zip(entries, parts):
        if index is None:
            translated[field] = value.strip()
        else:
            translated[field][index] = value.strip()
    return translated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", required=True, choices=LANGUAGES)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    english = json.loads((ROOT / "settlements.json").read_text())
    output_path = ROOT / f"settlements.{args.language}.json"
    manifest_path = ROOT / "localization" / f"manifest.{args.language}.json"
    existing = {item["id"]: item for item in json.loads(output_path.read_text())} if output_path.exists() else {}
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    pending = [
        item for item in english
        if args.force or item["id"] not in existing or manifest.get(item["id"]) != source_hash(item)
    ]
    print(f"{args.language}: translating {len(pending)} of {len(english)} records")

    if pending:
        failures: list[tuple[dict, Exception]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(translate_record, item, args.language): item for item in pending}
            for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
                source = futures[future]
                try:
                    existing[source["id"]] = future.result()
                    manifest[source["id"]] = source_hash(source)
                except Exception as error:
                    failures.append((source, error))
                    print(f"  deferred retry: {source['id']}: {error}")
                if index % 20 == 0 or index == len(pending):
                    print(f"  {index}/{len(pending)}")

        # A throttled endpoint can reject one worker while the rest finish. Retry only
        # those records sequentially, after the concurrent load has drained.
        for source, first_error in failures:
            try:
                time.sleep(3)
                existing[source["id"]] = translate_record(source, args.language)
                manifest[source["id"]] = source_hash(source)
            except Exception as error:
                raise RuntimeError(
                    f"failed record {source['id']} after deferred retry: {error}"
                ) from first_error

    # Images, links, proof flags, dates and other source facts must refresh even
    # when the prose hash is unchanged. Reusing entire old records loses them.
    translated_fields = (*TRANSLATABLE_SCALARS, *TRANSLATABLE_LISTS)
    ordered = [
        {**item, **{key: existing[item["id"]][key]
                    for key in translated_fields if key in existing[item["id"]]}}
        for item in english
    ]
    output_path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
