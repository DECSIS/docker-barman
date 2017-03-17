#!/bin/bash
set -e
set -x

manage_backup_tasks() {
	for file in "$BARMAN_CONFIGURATION_FILES_DIRECTORY"/*.conf;
	do
		echo "Processing $file"
		CRON_EXP="$(grep "#:backup_cron" $file |cut -d'=' -f2 | xargs)"
		if [[ ! -z $CRON_EXP ]]; then
			SERVER_NAME=$(grep "\[.*\]" $file | sed -e 's/[]]\|[\[]//g')
			CRON_TASK="$CRON_EXP barman backup $SERVER_NAME"
			#echo "$CRON_TASK"
			crontab -l | grep -v -e "barman backup.*${SERVER_NAME}$" | { cat; echo "$CRON_TASK"; } | crontab -
		else
			crontab -l | grep -v -e "barman backup.*${SERVER_NAME}$" | crontab -
		fi
	done
}

manage_backup_tasks
