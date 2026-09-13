#!/usr/bin/env bash
# Fetch the primary Michigan legal sources this project verifies against.
#
#   ./fetch-sources.sh [output-dir]        # default: ./primary
#
# Requires: curl, and pdftotext (poppler) for the text extractions.
#   Debian/Ubuntu : sudo apt-get update && sudo apt-get install -y poppler-utils
#   macOS         : brew install poppler
#   Windows       : winget install oschwartz10612.Poppler   (or use WSL)

set -euo pipefail
OUT="${1:-./primary}"
mkdir -p "$OUT"

# courts.michigan.gov returns HTTP 503 to requests without a browser User-Agent.
# That is the whole reason earlier research passes fell back to search snippets.
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'

# ---------------------------------------------------------------------------
# 1. Court rules and evidence rules (official SCAO consolidated PDFs)
# ---------------------------------------------------------------------------
# The hex path segment is CMS-generated and HAS changed before. If one 404s,
# search courts.michigan.gov for the document title -- it was not withdrawn.

declare -a DOCS=(
  "michigan-court-rules.pdf|https://www.courts.michigan.gov/48ec32/siteassets/rules-instructions-administrative-orders/michigan-court-rules/michigan-court-rules.pdf"
  "michigan-rules-of-evidence.pdf|https://www.courts.michigan.gov/498acb/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf"
  "local-court-rules-circuit-court.pdf|https://www.courts.michigan.gov/492c71/siteassets/rules-instructions-administrative-orders/local-court-rules/local-court-rules-circuit-court.pdf"
  "2025-michigan-child-support-formula.pdf|https://www.courts.michigan.gov/4a7a53/siteassets/court-administration/standardsguidelines/foc/2025mcsf.pdf"
  "mji-evidence-benchbook.pdf|https://www.courts.michigan.gov/49dfe1/siteassets/publications/benchbooks/evidence/evidbb.pdf"
  "mji-domestic-violence-benchbook.pdf|https://www.courts.michigan.gov/499b2f/siteassets/publications/benchbooks/dvbb/dvbb.pdf"
)

for entry in "${DOCS[@]}"; do
  name="${entry%%|*}"; url="${entry#*|}"
  printf '%-46s ' "$name"
  code=$(curl -sS -L --max-time 300 -A "$UA" -o "$OUT/$name" -w '%{http_code}' "$url" || echo 000)
  if [ "$code" = "200" ] && [ -s "$OUT/$name" ] && head -c4 "$OUT/$name" | grep -q '%PDF'; then
    echo "OK ($(du -h "$OUT/$name" | cut -f1))"
    # Prefer structured markdown (pymupdf4llm); fall back to layout text (poppler).
    # The plugin already ships the .md extractions, so this is only to refresh them.
    if python3 -c 'import pymupdf4llm' 2>/dev/null; then
      python3 -c "import pymupdf4llm,sys; open(sys.argv[2],'w').write(pymupdf4llm.to_markdown(sys.argv[1]))" \
        "$OUT/$name" "$OUT/${name%.pdf}.md"
    elif command -v pdftotext >/dev/null; then
      pdftotext -layout "$OUT/$name" "$OUT/${name%.pdf}.txt"
    fi
  else
    echo "FAILED (HTTP $code) -- search courts.michigan.gov for the title"
    rm -f "$OUT/$name"
  fi
done

# ---------------------------------------------------------------------------
# 2. Statutes (MCL)
# ---------------------------------------------------------------------------
# NOTE: inside the Claude Code sandbox this step fails with
#   CERTIFICATE_VERIFY_FAILED -- unable to get local issuer certificate
# because the session's egress proxy re-terminates TLS and legislature.mi.gov
# does not serve a complete chain. On an ordinary machine it normally works.
# If you hit the same error locally, your OpenSSL is missing an intermediate --
# update your CA store (`sudo update-ca-certificates`, or `brew install
# ca-certificates`). Do NOT use `curl -k`.
#
# ?objectName= returns the HTML page; /Home/Document?objectName= returns the
# document file, which is the better archive target.

SECTIONS=(
  722-23 722-26a 722-27 722-27a 722-31          # Child Custody Act
  552-505a 552-507                               # Friend of the Court Act
  552-605b 552-605c                              # support
  552-641 552-642 552-644                        # SPTEA enforcement
  400-1501 600-2950                              # domestic violence, PPO
  600-2591                                       # frivolous filings
  750-411h 750-539c 750-539d 750-350a            # stalking, eavesdropping, kidnapping
)

mkdir -p "$OUT/mcl"
for s in "${SECTIONS[@]}"; do
  printf '%-46s ' "MCL ${s//-/.}"
  code=$(curl -sS -L --max-time 60 -A "$UA" \
    -o "$OUT/mcl/mcl-$s.html" -w '%{http_code}' \
    "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-$s" || echo 000)
  [ "$code" = "200" ] && echo "OK" || { echo "FAILED (HTTP $code)"; rm -f "$OUT/mcl/mcl-$s.html"; }
  sleep 1   # be polite
done

# ---------------------------------------------------------------------------
# 3. Fix the record
# ---------------------------------------------------------------------------
( cd "$OUT" && sha256sum ./*.pdf > SHA256SUMS 2>/dev/null || shasum -a 256 ./*.pdf > SHA256SUMS )
echo
echo "Done. Fix the retrieval date in your notes -- these documents carry their own"
echo "'updated' stamps on the face, and local Genesee facts are not in this set."
