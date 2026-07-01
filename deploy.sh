#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
echo "==> Running scorer..."
python3 score_feeds.py
echo "==> Committing to GitHub..."
git add index.html
git commit -m "NewsFix update: $(date '+%Y-%m-%d %H:%M')"
git push origin main
echo "==> Done! Digest published."
