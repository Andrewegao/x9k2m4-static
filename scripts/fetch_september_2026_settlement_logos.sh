#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOGO_DIR="$ROOT/logos"
MANIFEST="$ROOT/logos/september-2026-logo-sources.tsv"

printf 'filename\tdomain\tsource\n' > "$MANIFEST"

while IFS='|' read -r filename domain; do
  source="https://www.google.com/s2/favicons?sz=128&domain=${domain}"
  curl -LfsS --retry 3 "$source" -o "$LOGO_DIR/$filename"
  printf '%s\t%s\t%s\n' "$filename" "$domain" "$source" >> "$MANIFEST"
  echo "Downloaded $filename from $domain"
done <<'LOGOS'
mdi-tdi-wanhua-antitrust-2026.png|en.whchem.com
mdi-tdi-dow-huntsman-antitrust-2026.png|dow.com
mdi-tdi-basf-covestro-antitrust-2026.png|basf.com
cpap-medical-data-incident-2026.png|cpapmedical.com
nyc-doc-strip-search-2026.png|nyc.gov
concora-credit-tcpa-2026.png|about.concoracredit.com
fujifilm-diosynth-data-2026.png|fujifilmdiosynth.com
la-jolla-group-data-2026.png|lajollagroup.com
schnucks-rewards-tax-2026.png|schnucks.com
vasindas-data-2026.png|bakersfieldcare.com
autobell-data-2026.png|autobell.com
carter-credit-union-data-2026.png|cartercu.org
southern-graphics-data-2026.png|sgxgraphics.com
twist-bioscience-securities-2026.png|twistbioscience.com
covenant-transport-job-posting-2026.png|covenantlogistics.com
wayne-memorial-hospital-data-2026.png|wmhweb.com
highland-health-systems-data-2026.png|highlandhealthsystems.org
amn-healthcare-cipa-2026.png|amnhealthcare.com
international-shoppes-data-2026.png|ishoppes.com
high5-games-washington-2026.png|high5games.com
sugared-bronzed-tcpa-2026.png|sugaredandbronzed.com
levoit-air-purifier-2026.png|levoit.com
wpm-salina-data-2026.png|wpmpath.com
onetouchpoint-data-2026.png|1touchpoint.com
peco-foods-data-2026.png|pecofoods.com
regional-urology-data-2026.png|ochsnerlsuhs.org
mental-health-association-data-2026.png|mhainc.org
california-casualty-data-2026.png|calcas.com
furniture-mart-usa-data-2026.png|furnituremartusa.com
summit-medical-data-2026.png|summitmedical.com
raging-waters-fee-2026.png|ragingwaters.com
mortgage-investors-group-data-2026.png|migonline.com
LOGOS
