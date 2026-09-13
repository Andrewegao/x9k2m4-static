#!/usr/bin/env python3
"""Apply source-verified settlement corrections and refresh publication status.

Run this after adding records and before generating localized feeds.  Status values
are a publication-time snapshot; the app independently filters by the ISO deadline.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERIC_SETTLEMENT_INDEX = "https://www.classaction.org/settlements"

FACT_CORRECTIONS = {
    "western-union-remission-phase3-2026": {
        "deadline": "2026-12-31",
        "eligibilityBullets": [
            "Sent money via Western Union between Jan 1, 2004 and Mar 9, 2020",
            "Lost the money to fraud (e.g., grandparent, lottery, or romance scam)",
            "Repayment is limited to the verified wire-transfer loss",
            "A 10-digit MTCN is required; supporting records may also be required",
        ],
        "proofDetails": (
            "Submit a Petition for Remission and any available supporting documentation. "
            "Each claimed transfer needs its 10-digit Money Transfer Control Number (MTCN); "
            "if an MTCN cannot be verified, the administrator will request supporting records "
            "such as a customer receipt. A Social Security number is required only for U.S. "
            "citizens; a non-U.S. citizen without an SSN or ITIN may check the form's "
            "\"I am not a U.S. Citizen\" option."
        ),
        "sourceURL": "https://www.westernunionremissionphase3.com/",
        "summary": (
            "Under a Department of Justice remission program, people who were defrauded "
            "through Western Union transfers between 2004 and 2020 can seek repayment of "
            "verified transfer losses. On August 5, 2026, the official administrator extended "
            "the Phase 3 petition deadline to December 31, 2026."
        ),
    },
    "delta-dental-wyssta-privacy-2026": {
        "proofDetails": (
            "A Class Member ID is required. Enter the ID from your email or postcard notice; "
            "if you did not receive a notice, call the Settlement Administrator at "
            "(833) 930-1183 to obtain an ID before filing. The form also requires an "
            "attestation that you held an eligible account."
        ),
    },
    "marlboro-chesterfield-breach-2026": {
        "proofDetails": (
            "Postcard-notice recipients may file online with their Notice ID and PIN. People "
            "who learned of the case through the Publication Notice may download the public "
            "Claim Form and mail it without those online credentials. Supporting records are "
            "required for the documented fraud or identity-theft tier; the $10 alternative is "
            "limited to class members whose Social Security number was compromised."
        ),
        "sourceURL": "https://m-cpsettlement.com/",
    },
    "ny-renaissance-faire-fees-2026": {
        "proofDetails": (
            "Online filing requires the Unique ID and PIN from the emailed notice. If you did "
            "not receive or cannot find the notice, contact the Settlement Administrator at "
            "(877) 239-7771 for assistance or download, sign, and mail the public Claim Form."
        ),
    },
    "playstation-psn-digital-games-2026": {
        "title": "PlayStation Digital Games Antitrust Settlement",
        "totalAmount": "$7.85 million",
        "individualPayout": "Automatic PSN wallet distribution; check for deactivated accounts",
        "eligibility": (
            "PlayStation Network account holders who, between April 1, 2019 and December 31, "
            "2023, bought at least one qualifying digital game through the PlayStation Store. "
            "A qualifying game must appear on the official eligible-games list and meet the "
            "settlement's retail game-specific voucher and price-increase criteria."
        ),
        "eligibilityBullets": [
            "Bought a game on the PlayStation Store between Apr 1, 2019 and Dec 31, 2023",
            "The game must be on the settlement's official eligible-games list",
            "Active qualifying accounts receive a PSN wallet distribution automatically",
            "Deactivated-account holders must request a check by Aug 27, 2026",
        ],
        "proofDetails": (
            "No claim is required for an active qualifying PSN account; its share is distributed "
            "to the PSN wallet automatically if the settlement becomes effective. A qualifying "
            "class member with a deactivated account must contact the administrator and provide "
            "qualifying purchase information plus a current mailing address by August 27, 2026 "
            "to request a check."
        ),
        "summary": (
            "Sony Interactive Entertainment agreed to a $7.85 million settlement over alleged "
            "anticompetitive conduct affecting certain qualifying PlayStation Store game "
            "purchases. Active qualifying accounts receive wallet distributions automatically; "
            "the August 27, 2026 deadline is for eligible deactivated-account holders to request "
            "a check."
        ),
        "caseInfo": (
            "Caccuri, et al. v. Sony Interactive Entertainment LLC, "
            "No. 21-cv-03361-AMO (N.D. Cal.)"
        ),
    },
    "bmw-shark-fin-antenna-2026": {
        "proofDetails": (
            "Reimbursement claims require the completed Claim Form and supporting documentation "
            "for eligible past repair expenses. The official site lists August 27, 2026 as the "
            "current claims deadline and advises class members to check for updates."
        ),
    },
    "aidvantage-tcpa-settlement-2026": {
        "proofDetails": (
            "Postcard recipients may file using the personalized claim form sent with their "
            "notice. A person who did not receive a postcard must request a claim form in "
            "writing and submit proof that an artificial or prerecorded-voice call or message "
            "from Aidvantage reached their cellular telephone during the class period."
        ),
    },
    "moodswings-ticket-fee-settlement-2026": {
        "proofDetails": (
            "Online filing requires the Class Member ID from the settlement notice. Cash is "
            "calculated from qualifying ticket purchases in the settlement records and requires "
            "a valid claim; doing nothing provides only the 25% discount code."
        ),
    },
}

BROKEN_LOGO_IDS = {
    "call-on-doc-pixel-2026",
    "hillcrest-convalescent-2026",
    "kyb-americas-breach-2026",
    "dohman-akerlund-eddy-breach-2026",
    "columbus-regional-privacy-2026",
    "pacific-bag-wa-jobs-2026",
    "hcf-management-breach-2026",
    "bradford-scott-data-breach-2026",
    "heritage-south-cu-breach-2026",
}


def status_for(deadline: str | None, as_of: date) -> str:
    if deadline is None:
        return "open"
    remaining = (date.fromisoformat(deadline) - as_of).days
    if remaining < 0:
        return "closed"
    if remaining <= 7:
        return "closingSoon"
    return "open"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--as-of",
        default=date.today().isoformat(),
        help="publication date used to refresh status values (YYYY-MM-DD)",
    )
    args = parser.parse_args()
    as_of = date.fromisoformat(args.as_of)

    path = ROOT / "settlements.json"
    records = json.loads(path.read_text())
    by_id = {record["id"]: record for record in records}
    missing = sorted(set(FACT_CORRECTIONS) - set(by_id))
    if missing:
        raise KeyError(f"missing correction targets: {missing}")

    source_replacements = 0
    for record in records:
        record.update(FACT_CORRECTIONS.get(record["id"], {}))
        if record.get("sourceURL") == GENERIC_SETTLEMENT_INDEX:
            record["sourceURL"] = record["claimURL"]
            source_replacements += 1
        if record["id"] in BROKEN_LOGO_IDS:
            record["logoURL"] = ""
        record["status"] = status_for(record.get("deadline"), as_of)

    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    counts = {name: sum(r["status"] == name for r in records) for name in ("open", "closingSoon", "closed")}
    print(f"Applied {len(FACT_CORRECTIONS)} verified record corrections")
    print(f"Replaced {source_replacements} generic source links with official claim links")
    print(f"Refreshed statuses as of {as_of}: {counts}")


if __name__ == "__main__":
    main()
