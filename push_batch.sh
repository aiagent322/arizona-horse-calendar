#!/bin/bash
# push_batch.sh — Rebuild index.html from CSV, then commit and push both files.
# Usage: bash push_batch.sh "Your commit message here"

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

if [ -z "$1" ]; then
  echo "ERROR: Provide a commit message as argument."
  echo "Usage: bash push_batch.sh \"Add 4 flyer events...\""
  exit 1
fi

echo "→ Rebuilding index.html from CSV..."
python3 rebuild_index.py

echo "→ Exporting Bridle & Bit RTF..."
python3 export_bridle_bit.py

echo "→ Staging files..."
git add ArizonaHorseCalendar.csv index.html BridleBit_Events.rtf

echo "→ Committing..."
git commit -m "$1"

echo "→ Pushing..."
git push origin main

echo "✓ Done — CSV + index.html pushed."
