#!/bin/bash
set -e

BARMAN_CONFIGURATION_FILES_DIRECTORY="/tmp/confsbackups"

for file in "$BARMAN_CONFIGURATION_FILES_DIRECTORY"/*.conf;
do
	echo "Processing $file"
	CRON_EXP="$(grep backup_cron $file |cut -d'=' -f2 | xargs)"
	SERVER_NAME=$(grep "\[.*\]" $file | sed -e 's/[]]\|[\[]//g')
	CRON_TASK="$CRON_EXP barman backup $SERVER_NAME"	
	echo "$CRON_TASK"
	crontab -l | grep -v -e "barman backup.*${SERVER_NAME}$" | { cat; echo "$CRON_TASK"; } | crontab -		
done