#!/usr/bin/env python3
"""Validate localized settlement feeds against the canonical English facts."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("es", "zh-Hans", "vi", "fil")
PROTECTED_FIELDS = (
    "id", "company", "imageURL", "logoURL", "deadline", "category", "proofRequired",
    "claimURL", "sourceURL", "dateAdded", "status", "claimCount",
    "payoutDisplayType", "caseInfo",
)
TRANSLATABLE_FIELDS = (
    "title", "totalAmount", "individualPayout", "eligibility", "eligibilityBullets", "proofDetails",
    "summary", "scope", "estimatedClaimTime",
)
NUMBER_PATTERN = re.compile(r"\d[\d,.]*\s*%?")
RISK_WORDS = re.compile(r"\b(may|must|not|only|up to|before|after|between|proof|required)\b", re.I)
CORRUPTION_PATTERNS = {
    "es": (r"mMáximo", r"mmínimo", r"Est\.\$", r"[.!?](?=(?:Si|Los|Las|El|La)\b)"),
    "zh-Hans": (r"农民保险", r"结算", r"定居点"),
    "vi": (r"Nhóm Nhóm", r"[.!?](?=(?:Nếu|Các|Người|Những|Một|Bạn)\b)", r"\bb\s+ased\b"),
    "fil": (r"Est\.\$", r"m ang pinakamababa", r"[.!?](?=(?:Kung|Ang|Mga|Ito|Maaari|Kasama|Buksan)\b)", r"\bb\s+ased\b"),
}
MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "fil": ["Enero", "Pebrero", "Marso", "Abril", "Mayo", "Hunyo", "Hulyo", "Agosto", "Setyembre", "Oktubre", "Nobyembre", "Disyembre"],
}
MONTH_ALIASES = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep|Sept", "Oct", "Nov", "Dec"],
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"],
    "fil": ["Ene", "Peb", "Mar", "Abr", "May", "Hun", "Hul", "Ago", "Set", "Okt", "Nob", "Dis"],
}


def load_json_strict(path: Path):
    """Load JSON while rejecting duplicate object keys that json.loads hides by default."""
    def reject_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(path.read_text(), object_pairs_hook=reject_duplicate_keys)


def numbers(value, language: str) -> Counter[str]:
    text = json.dumps(value, ensure_ascii=False) if value is not None else ""
    month_tokens: list[str] = []
    word_language = language if language in MONTHS else "en"
    for index, month in enumerate(MONTHS[word_language], 1):
        # English "may" is overwhelmingly the legal modal in this dataset. Treat it as
        # the month only when followed by a calendar day.
        suffix = r"(?=\s+\d{1,2}(?![\d.]|\s*%))" if word_language == "en" and month == "May" else ""
        pattern = re.compile(rf"\b{re.escape(month)}\b{suffix}", re.I)
        # Full month names are unambiguous calendar facts. English "may" is the
        # exception because it is also a common legal modal, handled by `suffix`.
        matches = list(pattern.finditer(text))
        count = len(matches)
        if count:
            month_tokens.extend([f"month:{index}"] * count)
            for match in reversed(matches):
                text = text[:match.start()] + text[match.end():]
    for index, aliases in enumerate(MONTH_ALIASES.get(word_language, []), 1):
        # Abbreviations must introduce a day/year. This prevents a court-case suffix
        # such as "01335-SEP" from being interpreted as September.
        suffix = (
            r"(?=\s+(?:\d{4}|\d{1,2},?\s+\d{4})\b)"
            if word_language == "fil" and aliases == "May"
            else r"(?=\.?\s+\d{1,4}\b)"
        )
        pattern = re.compile(rf"\b(?:{aliases})\.?\b{suffix}", re.I)
        matches = list(pattern.finditer(text))
        count = len(matches)
        if count:
            month_tokens.extend([f"month:{index}"] * count)
            for match in reversed(matches):
                text = text[:match.start()] + text[match.end():]
    if language == "zh-Hans":
        chinese_months = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
            "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12,
        }
        def chinese_word_month(match: re.Match) -> str:
            month_tokens.append(f"month:{chinese_months[match.group(1)]}")
            return ""
        text = re.sub(
            r"(?<![一二三四五六七八九十])(十二|十一|十|[一二三四五六七八九])月份?",
            chinese_word_month,
            text,
        )
        def chinese_month(match: re.Match) -> str:
            month_tokens.append(f"month:{int(match.group(1))}")
            return ""
        text = re.sub(r"(?<!\d)(1[0-2]|[1-9])\s*月份?", chinese_month, text)
    elif language == "vi":
        vietnamese_months = {
            "một": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4, "năm": 5,
            "sáu": 6, "bảy": 7, "tám": 8, "chín": 9, "mười": 10,
            "mười một": 11, "mười hai": 12,
        }
        def vietnamese_word_month(match: re.Match) -> str:
            month_tokens.append(f"month:{vietnamese_months[match.group(1).casefold()]}")
            return ""
        text = re.sub(
            r"\btháng\s+(mười hai|mười một|mười|một|hai|ba|bốn|tư|năm|sáu|bảy|tám|chín)\b",
            vietnamese_word_month,
            text,
            flags=re.I,
        )
        def vietnamese_month(match: re.Match) -> str:
            month_tokens.append(f"month:{int(match.group(1))}")
            return ""
        text = re.sub(r"\btháng\s+(1[0-2]|[1-9])\b", vietnamese_month, text, flags=re.I)
    if language in {"en", "es", "vi", "fil"}:
        def slash_date(match: re.Match) -> str:
            first, second, year = match.groups()
            # Slash dates in the canonical U.S. legal feed are intentionally preserved
            # verbatim by the repair pass. Keep all three components as immutable facts;
            # inferring a locale-specific order here would make an unchanged 4/1/2019
            # look altered in Spanish or Vietnamese.
            return f" {first} {second} {year} "
        text = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", slash_date, text)
    # A translation may intentionally retain an English month name (common, natural
    # Taglish). Normalize those spellings as the same calendar fact.
    if language != "en":
        for index, month in enumerate(MONTHS["en"], 1):
            suffix = (
                r"(?=\s+(?:\d{4}|\d{1,2},?\s+\d{4})\b)"
                if language == "fil" and month == "May"
                else (r"(?=\s+\d{1,2}(?![\d.]|\s*%))" if month == "May" else "")
            )
            pattern = re.compile(rf"\b{month}\b{suffix}", re.I)
            count = len(pattern.findall(text))
            if count:
                month_tokens.extend([f"month:{index}"] * count)
                text = pattern.sub("", text)
    # Normalize explicit semantic zeroes before extracting values. Limit Vietnamese
    # `không` to balance/comparison phrases because the same word also means "not."
    if language == "en":
        text = re.sub(r"\bnon-?zero\b|\bzero(?=\s+(?:balance|payment|value|amount))", "0", text, flags=re.I)
    elif language == "es":
        text = re.sub(
            r"\bcero(?=\s+(?:saldo|pago|valor|cantidad))|(?<=saldo\s)cero\b|(?<=de\s)cero\b",
            "0", text, flags=re.I,
        )
    elif language == "vi":
        text = re.sub(r"\b(?:bằng|khác)\s+không\b", "0", text, flags=re.I)
    elif language == "fil":
        text = re.sub(
            r"\bzero(?=\s+(?:na\s+)?(?:balance|payment|value|amount|balanse|bayad|halaga))",
            "0", text, flags=re.I,
        )
    elif language == "zh-Hans":
        # `零` also appears in ordinary words such as 零售商 (retailer), so only
        # normalize explicit zero-value phrases.
        text = re.sub(r"非零|零(?=余额|付款|值)|(?<=为)零", "0", text)
    text = re.sub(r"(?<=\d)。(?=\d)", ".", text)
    # Normalize localized magnitude words/symbols before extracting values. Currency
    # placement and decimal punctuation may change naturally ($24 -> 24 美元,
    # $5.55M -> $5,55 millones), but the actual value must remain identical.
    units = {
        "en": {"million": Decimal(1_000_000), "billion": Decimal(1_000_000_000)},
        "es": {"mil": Decimal(1_000), "millón": Decimal(1_000_000), "millones": Decimal(1_000_000), "mil millones": Decimal(1_000_000_000)},
        "vi": {"nghìn": Decimal(1_000), "triệu": Decimal(1_000_000), "tỷ": Decimal(1_000_000_000)},
        "fil": {"libo": Decimal(1_000), "milyon": Decimal(1_000_000), "bilyon": Decimal(1_000_000_000)},
        "zh-Hans": {
            "千": Decimal(1_000), "万": Decimal(10_000), "百万": Decimal(1_000_000),
            "亿": Decimal(100_000_000), "十亿": Decimal(1_000_000_000),
        },
    }
    text = re.sub(r"(?<=\d)\s*[Kk]\b", " thousand", text)
    units["en"]["thousand"] = Decimal(1_000)
    all_units = sorted({unit for mapping in units.values() for unit in mapping}, key=len, reverse=True)
    text = re.sub(r"(?<=\d)M\b", " million", text)
    text = re.sub(r"(?<=\d)B\b", " billion", text)
    cjk_units = [unit for unit in all_units if re.search(r"[\u3400-\u9fff]", unit)]
    word_units = [unit for unit in all_units if unit not in cjk_units]
    # CJK unit glyphs are adjacent to currency words ("555万美元"), so an ASCII-
    # style trailing word boundary is valid only for alphabetic unit names.
    unit_pattern = "|".join(
        [rf"{re.escape(unit)}(?![A-Za-zÀ-ỹ])" for unit in word_units]
        + [re.escape(unit) for unit in cjk_units]
    )
    magnitude_pattern = re.compile(rf"(?<!\w)(\d[\d,.]*)\s*({unit_pattern})", re.I)
    magnitudes: list[str] = []

    def decimal_value(raw: str, magnitude: bool = False) -> Decimal:
        if language in {"es", "vi"}:
            if "," in raw and "." in raw:
                decimal_separator = "," if raw.rfind(",") > raw.rfind(".") else "."
                grouping_separator = "." if decimal_separator == "," else ","
                normalized = raw.replace(grouping_separator, "").replace(decimal_separator, ".")
            elif "," in raw:
                # A 1-2 digit suffix is decimal; 3+ digits is grouping/date separation.
                parts = raw.split(",")
                normalized = ".".join(parts) if len(parts) == 2 and (len(parts[1]) <= 2 or magnitude) else "".join(parts)
            elif "." in raw:
                parts = raw.split(".")
                normalized = raw if magnitude and len(parts) == 2 else (
                    "".join(parts) if len(parts) > 1 and all(len(part) == 3 for part in parts[1:]) else raw
                )
            else:
                normalized = raw
        else:
            normalized = raw.replace(",", "")
        try:
            return Decimal(normalized)
        except InvalidOperation:
            return Decimal(0)

    def replace_magnitude(match: re.Match) -> str:
        raw, unit = match.groups()
        mapping = units.get(language, units["en"])
        multiplier = next((scale for name, scale in mapping.items() if name.casefold() == unit.casefold()), None)
        if multiplier is None:
            # Retained English unit in otherwise localized prose.
            multiplier = next((scale for mapping in units.values() for name, scale in mapping.items() if name.casefold() == unit.casefold()), Decimal(1))
        value = decimal_value(raw, magnitude=True) * multiplier
        magnitudes.append(format(value.normalize(), "f"))
        return " "

    text = magnitude_pattern.sub(replace_magnitude, text)
    text = re.sub(r"(\d[\d,.]*)\s*[-–]\s*(\d[\d,.]*)\s*%", r"\1% - \2%", text)
    # Thin/non-breaking/ordinary spaces are all valid thousands separators in
    # localized output (for example "10 000").
    text = re.sub(r"(?<=\d)[\s\u00a0\u202f](?=\d{3}(?:\D|$))", "", text)
    found = []
    for token in NUMBER_PATTERN.findall(text):
        token = token.strip().rstrip(".,")
        is_percent = token.endswith("%")
        raw = token.rstrip("%").strip()
        # A comma immediately before a four-digit year can survive inline HTML
        # translation without whitespace; split it into the original two facts.
        joined_date = re.fullmatch(r"(\d{1,2}),(\d{4})", raw)
        if joined_date:
            found.extend(joined_date.groups())
            continue
        value = decimal_value(raw)
        found.append(("percent:" if is_percent else "") + format(value.normalize(), "f"))
    return Counter(found + magnitudes + sorted(set(month_tokens)))


def main() -> int:
    try:
        source = load_json_strict(ROOT / "settlements.json")
    except Exception as error:
        print(f"en: invalid JSON: {error}", file=sys.stderr)
        return 1
    source_by_id = {item["id"]: item for item in source}
    errors: list[str] = []
    report: dict[str, list[str]] = {}

    source_ids = [item.get("id") for item in source]
    if len(source_ids) != len(set(source_ids)):
        errors.append("en: duplicate record IDs")
    for item in source:
        record_id = item.get("id")
        if set(item) != set(source[0]):
            errors.append(f"en/{record_id}: schema keys differ")
        for field, expected in {
            "id": str, "title": str, "company": str, "imageURL": str,
            "totalAmount": str, "individualPayout": str, "category": str,
            "eligibility": str, "eligibilityBullets": list,
            "proofRequired": bool, "claimURL": str, "sourceURL": str,
            "summary": str, "scope": str, "dateAdded": str, "status": str,
            "logoURL": str, "estimatedClaimTime": str, "payoutDisplayType": str,
        }.items():
            if not isinstance(item.get(field), expected):
                errors.append(f"en/{record_id}/{field}: expected {expected.__name__}")
        for field in ("proofDetails", "caseInfo"):
            if item.get(field) is not None and not isinstance(item.get(field), str):
                errors.append(f"en/{record_id}/{field}: expected string or null")
        if item.get("deadline") is not None and not isinstance(item.get("deadline"), str):
            errors.append(f"en/{record_id}/deadline: expected string or null")
        if item.get("claimCount") is not None and not isinstance(item.get("claimCount"), int):
            errors.append(f"en/{record_id}/claimCount: expected integer or null")
        if isinstance(item.get("eligibilityBullets"), list) and not all(
            isinstance(value, str) and value.strip() for value in item["eligibilityBullets"]
        ):
            errors.append(f"en/{record_id}/eligibilityBullets: expected nonempty strings")
        for field in ("id", "title", "company", "imageURL", "totalAmount", "individualPayout",
                      "category", "eligibility", "claimURL", "sourceURL", "summary", "scope",
                      "dateAdded", "status", "estimatedClaimTime", "payoutDisplayType"):
            if isinstance(item.get(field), str) and not item[field].strip():
                errors.append(f"en/{record_id}/{field}: value is empty")
        for field in ("imageURL", "claimURL", "sourceURL", "logoURL"):
            value = item.get(field)
            if value and urlparse(value).scheme != "https":
                errors.append(f"en/{record_id}/{field}: URL must use https")
        for field in ("deadline", "dateAdded"):
            value = item.get(field)
            if value is not None:
                try:
                    date.fromisoformat(value)
                except (TypeError, ValueError):
                    errors.append(f"en/{record_id}/{field}: invalid ISO date")
        if item.get("category") not in {
            "Automotive", "Consumer", "Data Breach", "Employment", "Financial",
            "Healthcare", "Privacy", "Product", "Telemarketing",
        }:
            errors.append(f"en/{record_id}/category: invalid enum")
        if item.get("status") not in {"open", "closingSoon", "closed"}:
            errors.append(f"en/{record_id}/status: invalid enum")
        if item.get("payoutDisplayType") not in {"details", "exact", "tbd", "upTo"}:
            errors.append(f"en/{record_id}/payoutDisplayType: invalid enum")
        bullets = item.get("eligibilityBullets")
        if isinstance(bullets, list) and len(bullets) != len(set(bullets)):
            errors.append(f"en/{item.get('id')}/eligibilityBullets: duplicate entries")

    for language in LANGUAGES:
        path = ROOT / f"settlements.{language}.json"
        if not path.exists():
            errors.append(f"{language}: missing {path.name}")
            continue
        try:
            localized = load_json_strict(path)
        except Exception as error:
            errors.append(f"{language}: invalid JSON: {error}")
            continue
        ids = [item.get("id") for item in localized]
        if ids != source_ids:
            errors.append(f"{language}: record IDs/order differ from English")
        if len(ids) != len(set(ids)):
            errors.append(f"{language}: duplicate record IDs")
        high_risk: list[str] = []
        for item in localized:
            record_id = item.get("id")
            english = source_by_id.get(record_id)
            if english is None:
                continue
            if set(item) != set(english):
                errors.append(f"{language}/{record_id}: schema keys differ")
            bullets = item.get("eligibilityBullets")
            if isinstance(bullets, list) and len(bullets) != len(set(bullets)):
                errors.append(f"{language}/{record_id}/eligibilityBullets: duplicate entries")
            for field in PROTECTED_FIELDS:
                if item.get(field) != english.get(field):
                    errors.append(f"{language}/{record_id}/{field}: protected fact changed")
            for field in TRANSLATABLE_FIELDS:
                value = item.get(field)
                if isinstance(value, str) and english.get(field) and not value.strip():
                    errors.append(f"{language}/{record_id}/{field}: translation is empty")
                if isinstance(value, list) and len(value) != len(english.get(field) or []):
                    errors.append(f"{language}/{record_id}/{field}: list length changed")
                if (
                    field in {"totalAmount", "individualPayout"}
                    and isinstance(value, str)
                    and value == english.get(field)
                    and re.search(r"[A-Za-z]", value)
                    and not re.fullmatch(r"[\s$€£¥\d,.\-–+~%KkMmBb/()]+", value)
                ):
                    errors.append(f"{language}/{record_id}/{field}: untranslated display text")
                if numbers(value, language) != numbers(english.get(field), "en"):
                    errors.append(f"{language}/{record_id}/{field}: numeric facts changed")
                serialized = json.dumps(value, ensure_ascii=False)
                if language in {"es", "vi", "fil"} and (
                    re.search(r"\s+[,.;:!?]", serialized)
                    or re.search(r";(?=\S)", serialized)
                    or re.search(r"(?<!www)(?<!\b[A-Z])([.!?])(?=[A-ZÀ-ỸĐ])", serialized)
                    or re.search(r"\(\s+|\s+\)", serialized)
                ):
                    errors.append(f"{language}/{record_id}/{field}: invalid punctuation spacing")
                for pattern in CORRUPTION_PATTERNS.get(language, ()):
                    if re.search(pattern, serialized):
                        errors.append(f"{language}/{record_id}/{field}: known translation corruption")
            risk_text = " ".join(str(english.get(key) or "") for key in ("eligibility", "proofDetails", "individualPayout"))
            if RISK_WORDS.search(risk_text):
                high_risk.append(record_id)
        report[language] = high_risk

    deal_source = load_json_strict(ROOT / "deals.json")
    deal_source_by_id = {item["id"]: item for item in deal_source}
    deal_translatable = ("title", "description", "features", "reviewSummary")
    for language in LANGUAGES:
        path = ROOT / f"deals.{language}.json"
        if not path.exists():
            errors.append(f"{language}: missing {path.name}")
            continue
        try:
            localized_deals = load_json_strict(path)
        except Exception as error:
            errors.append(f"{language}: invalid deal JSON: {error}")
            continue
        if [item.get("id") for item in localized_deals] != [item["id"] for item in deal_source]:
            errors.append(f"{language}: deal record IDs/order differ from English")
        for item in localized_deals:
            deal_id = item.get("id")
            english = deal_source_by_id.get(deal_id)
            if english is None:
                continue
            if set(item) != set(english):
                errors.append(f"{language}/{deal_id}: deal schema keys differ")
            for field in set(english) - set(deal_translatable):
                if item.get(field) != english.get(field):
                    errors.append(f"{language}/{deal_id}/{field}: protected deal fact changed")
            for field in deal_translatable:
                if numbers(item.get(field), language) != numbers(english.get(field), "en"):
                    errors.append(f"{language}/{deal_id}/{field}: deal numeric facts changed")
                serialized = json.dumps(item.get(field), ensure_ascii=False)
                if language in {"es", "vi", "fil"} and (
                    re.search(r"\s+[,.;:!?]", serialized)
                    or re.search(r";(?=\S)", serialized)
                    or re.search(r"(?<!www)(?<!\b[A-Z])([.!?])(?=[A-ZÀ-ỸĐ])", serialized)
                    or re.search(r"\(\s+|\s+\)", serialized)
                    or "8 -in- 1" in serialized
                    or "8-in- 1" in serialized
                ):
                    errors.append(f"{language}/{deal_id}/{field}: invalid deal punctuation spacing")

    (ROOT / "localization" / "qa-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    if errors:
        print("\n".join(errors[:200]), file=sys.stderr)
        if len(errors) > 200:
            print(f"... and {len(errors) - 200} more", file=sys.stderr)
        return 1
    print(f"Validated {len(source)} records across {len(LANGUAGES)} localized feeds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
