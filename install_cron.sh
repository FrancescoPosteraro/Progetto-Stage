#!/bin/bash

PROJECT_PATH="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="$PROJECT_PATH/.venv/bin/python"
RUN_SCRIPT="$PROJECT_PATH/run.py"
LOG_FILE="$PROJECT_PATH/cron.log"

CRON_JOB="0 3 * * 0 cd $PROJECT_PATH && $PYTHON_PATH $RUN_SCRIPT scraper >> $LOG_FILE 2>&1"

(crontab -l 2>/dev/null | grep -F "$CRON_JOB") || \
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job configurato correttamente."
echo "Esecuzione: ogni domenica alle 03:00"