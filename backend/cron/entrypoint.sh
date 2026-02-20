#!/bin/bash
set -e

echo "=== Cron Entrypoint ==="

#  1. Generate cron schedule from env var 
SCHEDULE="${SCRAPER_CRON_SCHEDULE:-0 */12 * * *}"
echo "Cron schedule: ${SCHEDULE}"

# Export all current environment variables so cron jobs inherit them
printenv | grep -v "no_proxy" >> /etc/environment

# Write crontab with the configured schedule
echo "${SCHEDULE} cd /app && python -m scrapers.main >> /var/log/cron.log 2>&1" > /etc/cron.d/scrapers
echo "" >> /etc/cron.d/scrapers   # crontab requires trailing newline
chmod 0644 /etc/cron.d/scrapers
crontab /etc/cron.d/scrapers

echo "Crontab installed:"
crontab -l

#  2. Run initial seeding (idempotent  safe to re-run) 
echo "=== Running initial taxonomy seeding ==="
python -m scrapers.seed_all
echo "=== Seeding complete ==="

#  3. Start cron in foreground 
echo "=== Starting cron daemon ==="
exec cron -f
