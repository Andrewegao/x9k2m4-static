# FreeClaim settlement localization

English (`settlements.json`) is the only source of truth. Localized feeds are generated
from it and must pass `scripts/validate_localizations.py` before publication.

Supported feeds:

- `settlements.es.json` — neutral U.S./Latin American Spanish
- `settlements.zh-Hans.json` — Simplified Chinese for U.S. users
- `settlements.vi.json` — Vietnamese for U.S. users
- `settlements.fil.json` — natural Filipino/Tagalog for U.S. users

## Translation rules

- Never infer or broaden eligibility.
- Preserve `may`, `must`, `not`, `only`, `up to`, residency limits, purchase periods,
  proof requirements, deadlines, company names, identifiers, URLs, dates, and amounts.
- Category and status values are machine-readable codes and remain in English.
- Currency is not converted.
- U.S. state and territory names remain recognizable legal jurisdiction labels.
- When the English is ambiguous, retain the cautious meaning rather than making a claim
  sound certain.

## Updating feeds

Run the generator for changed English content and then validate all outputs:

```sh
python3 scripts/translate_settlements.py --language es
python3 scripts/translate_settlements.py --language zh-Hans
python3 scripts/translate_settlements.py --language vi
python3 scripts/translate_settlements.py --language fil
python3 scripts/validate_localizations.py
```

The generator keeps a source hash per record, so unchanged translations stay stable.
The generated QA report lists records that need a semantic spot-check.
