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

echo "$BARMAN_SERVER $BARMAN_BACKUP_ID start $(date +%s%N)" >> "/tmp/backups_$BARMAN_SERVER.log"