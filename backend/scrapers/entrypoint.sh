#!/bin/bash
set -e

echo "=== Scrapers Entrypoint ==="

# ── 1. Run seeding (idempotent — safe to re-run) ──────────────────
echo "=== Running initial taxonomy seeding ==="
python -m scrapers.seed_all
echo "=== Seeding complete ==="

# ── 2. Run scrapers ──────────────────────────────────────────────
echo "=== Running scrapers ==="
exec python -m scrapers.main
