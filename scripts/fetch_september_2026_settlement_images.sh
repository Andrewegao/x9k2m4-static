#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE_DIR="$ROOT/images"
MANIFEST="$ROOT/images/september-2026-image-sources.tsv"
USED_IDS="$(mktemp)"
trap 'rm -f "$USED_IDS"' EXIT

printf 'filename\tunsplash_id\tphotographer\tsource\tquery\n' > "$MANIFEST"

while IFS='|' read -r filename query; do
  encoded_query="$(printf '%s' "$query" | jq -sRr @uri)"
  response="$(curl -LfsS --retry 3 "https://unsplash.com/napi/search/photos?query=${encoded_query}&per_page=20&page=1")"
  selected=''

  while IFS= read -r candidate; do
    photo_id="$(printf '%s' "$candidate" | jq -r '.id')"
    raw_url="$(printf '%s' "$candidate" | jq -r '.urls.raw')"
    if [[ "$raw_url" == https://images.unsplash.com/* ]] && ! grep -Fxq "$photo_id" "$USED_IDS"; then
      selected="$candidate"
      break
    fi
  done < <(printf '%s' "$response" | jq -c '.results[]')

  if [[ -z "$selected" ]]; then
    echo "No unique non-premium Unsplash result for: $query" >&2
    exit 1
  fi

  photo_id="$(printf '%s' "$selected" | jq -r '.id')"
  raw_url="$(printf '%s' "$selected" | jq -r '.urls.raw')"
  photographer="$(printf '%s' "$selected" | jq -r '.user.name')"
  source="$(printf '%s' "$selected" | jq -r '.links.html')"
  download_url="${raw_url}&w=1200&h=630&fit=crop&crop=entropy&fm=jpg&q=85"

  curl -LfsS --retry 3 "$download_url" -o "$IMAGE_DIR/$filename"
  printf '%s\n' "$photo_id" >> "$USED_IDS"
  printf '%s\t%s\t%s\t%s\t%s\n' "$filename" "$photo_id" "$photographer" "$source" "$query" >> "$MANIFEST"
  echo "Downloaded $filename ($photo_id)"
done <<'IMAGES'
mdi-tdi-wanhua-antitrust-2026.jpg|industrial chemical factory storage tanks
mdi-tdi-dow-huntsman-antitrust-2026.jpg|chemical plant pipes industrial
mdi-tdi-basf-covestro-antitrust-2026.jpg|chemistry laboratory scientist
cpap-medical-data-incident-2026.jpg|CPAP sleep apnea machine bedroom
nyc-doc-strip-search-2026.jpg|Foley Square courthouse New York
concora-credit-tcpa-2026.jpg|smartphone incoming phone call desk
fujifilm-diosynth-data-2026.jpg|biotechnology scientist laboratory
la-jolla-group-data-2026.jpg|surf shop clothing
schnucks-rewards-tax-2026.jpg|grocery store checkout rewards
vasindas-data-2026.jpg|home caregiver senior healthcare
autobell-data-2026.jpg|automatic car wash
carter-credit-union-data-2026.jpg|credit union bank counter
southern-graphics-data-2026.jpg|commercial packaging printing press
twist-bioscience-securities-2026.jpg|biotechnology stock market investing
covenant-transport-job-posting-2026.jpg|truck driver highway logistics
wayne-memorial-hospital-data-2026.jpg|community hospital exterior
highland-health-systems-data-2026.jpg|mental health counseling clinic
amn-healthcare-cipa-2026.jpg|medical interpreter video call
international-shoppes-data-2026.jpg|airport shopping
high5-games-washington-2026.jpg|mobile casino game smartphone
sugared-bronzed-tcpa-2026.jpg|beauty salon skincare treatment
levoit-air-purifier-2026.jpg|home air purifier device
wpm-salina-data-2026.jpg|pathology laboratory microscope
onetouchpoint-data-2026.jpg|printing press
peco-foods-data-2026.jpg|poultry farm chickens
regional-urology-data-2026.jpg|medical clinic doctor office
mental-health-association-data-2026.jpg|mental health therapy counseling
california-casualty-data-2026.jpg|car insurance documents vehicle
furniture-mart-usa-data-2026.jpg|furniture store showroom
summit-medical-data-2026.jpg|doctor medical team clinic
raging-waters-fee-2026.jpg|water park slides
mortgage-investors-group-data-2026.jpg|mortgage home loan signing
IMAGES
