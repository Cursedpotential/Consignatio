#!/usr/bin/env bash
# R2 casebible-sorted -> v2 structure (owner-approved plan 2026-07-11).
# Byline: Claude Code · Fable 5 · 2026-07-11
# Server-side moves within the bucket (zero egress). Ledger = pre-move recursive
# listings per prefix (old_path derivable -> new prefix). NOTHING deleted:
# rclone move relocates objects; source prefixes end at 0 objects.
set -euo pipefail
R=r2:casebible-sorted
LEDGER_DIR="D:/casebible/casebible-coordination/specs/sorted-restructure-v2-ledger"
mkdir -p "$LEDGER_DIR"
FLAGS=(--transfers 32 --checkers 32 --stats-one-line --stats 30s)

snap() { # snap <label> <prefix>
  rclone lsf -R --files-only "$R/$2" > "$LEDGER_DIR/$1.before.txt" 2>/dev/null || true
  wc -l < "$LEDGER_DIR/$1.before.txt" | tr -d ' '
}

mv_prefix() { # mv_prefix <label> <src-prefix> <dst-prefix>
  local n; n=$(snap "$1" "$2")
  echo "== $1: $n objects  '$2' -> '$3'"
  [ "$n" = "0" ] && { echo "   (empty, skip)"; return; }
  rclone move "$R/$2" "$R/$3" "${FLAGS[@]}"
  local left; left=$(rclone lsf -R --files-only "$R/$2" 2>/dev/null | wc -l | tr -d ' ')
  local dst; dst=$(rclone lsf -R --files-only "$R/$3" 2>/dev/null | wc -l | tr -d ' ')
  echo "   done: src-left=$left dst-now=$dst"
}

echo "=== v2 restructure start $(date) ==="
mv_prefix platform            "Platform"           "Code/_intake/legacy-platform"
mv_prefix tools-and-platform  "Tools & Platform"   "Code"
mv_prefix legal               "Legal"              "CaseManagement/_intake/legal"
mv_prefix case-management     "Case Management"    "CaseManagement"
mv_prefix documents           "Documents"          "Triage/documents"
mv_prefix exports-bundles     "Exports & Bundles"  "Triage/exports-bundles"
mv_prefix inbox               "Inbox"              "Triage"
mv_prefix kb-legal            "Knowledge/legal-reference" "KnowledgeBase/legal"
mv_prefix knowledge           "Knowledge"          "KnowledgeBase"
mv_prefix legacy              "Legacy"             "Recovered"

echo "=== creating skeleton markers ==="
tmp=$(mktemp); echo "vault skeleton marker (v2 2026-07-11)" > "$tmp"
for p in \
  "Recovered/.keep" \
  "EvidenceVault/_intake/.keep" "EvidenceVault/_recovered/.keep" \
  "EvidenceVault/exports/google-takeout/.keep" "EvidenceVault/exports/facebook/.keep" "EvidenceVault/exports/snapchat/.keep" \
  "Entities/_intake/.keep" "Entities/_recovered/.keep" \
  "CaseManagement/_intake/.keep" "CaseManagement/_recovered/.keep" \
  "CaseManagement/filings/.keep" "CaseManagement/received/.keep" "CaseManagement/orders/.keep" \
  "CaseManagement/drafts/.keep" "CaseManagement/motions/.keep" "CaseManagement/discovery/.keep" \
  "CaseManagement/correspondence/.keep" "CaseManagement/hearings/.keep" "CaseManagement/calendar/.keep" \
  "CaseManagement/exhibits/.keep" "CaseManagement/financials/.keep" "CaseManagement/parenting-time/.keep" \
  "CaseManagement/work-product/.keep" \
  "KnowledgeBase/_intake/.keep" "KnowledgeBase/_recovered/.keep" \
  "KnowledgeBase/legal/.keep" "KnowledgeBase/personal-history/.keep" "KnowledgeBase/ai-chats/_derived/.keep" \
  "Code/_intake/.keep" "Code/_recovered/.keep" \
  "Triage/documents/.keep" "Triage/exports-bundles/.keep"
do rclone copyto "$tmp" "$R/$p" -q; done
rm -f "$tmp"

echo "=== final top-level ==="
rclone lsf -R --files-only "$R" | awk -F/ '{print $1}' | sort | uniq -c | sort -rn
echo "=== v2 restructure done $(date) ==="
