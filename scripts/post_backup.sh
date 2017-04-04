#!/bin/bash

# BARMAN_BACKUP_DIR: backup destination directory
# BARMAN_BACKUP_ID: ID of the backup
# BARMAN_CONFIGURATION: configuration file used by Barman
# BARMAN_ERROR: error message, if any (only for the post phase)
# BARMAN_PHASE: phase of the script, either pre or post
# BARMAN_PREVIOUS_ID: ID of the previous backup (if present)
# BARMAN_RETRY: 1 if it is a retry script, 0 if not
# BARMAN_SERVER: name of the server
# BARMAN_STATUS: status of the backup
# BARMAN_VERSION: version of Barman

set -e

BACKUP_LOG_FILE="${BARMAN_BARMAN_HOME}/prometheus_exporter_work/backups_$BARMAN_SERVER.log"

BACKUP_END_TIME=$(date +%s%N)
BACKUP_START_TIME=$(grep "$BARMAN_SERVER $BARMAN_BACKUP_ID start" "$BACKUP_LOG_FILE" | cut -d' ' -f4 | xargs)
BACKUP_DURATION_SECONDS=$(((BACKUP_END_TIME-BACKUP_START_TIME)/1000000000))

echo "$BARMAN_SERVER $BARMAN_BACKUP_ID end $BACKUP_END_TIME" >> "$BACKUP_LOG_FILE"
echo "$BARMAN_SERVER $BARMAN_BACKUP_ID duration $BACKUP_DURATION_SECONDS" >> "$BACKUP_LOG_FILE"