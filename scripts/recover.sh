#!/bin/bash

set -ex

DB_TO_RESTORE=$1
BACKUP_ID=$2
RECOVERY_SSH_CMD=$3


function prepare_recover() {
	echo "Preparing recovery of $DB_TO_RESTORE / $BACKUP_ID"
	$RECOVERY_SSH_CMD 'cd / && /docker_entrypoint_rec.sh prepare_recover'
}

function recover(){
	echo "Recovering $DB_TO_RESTORE / $BACKUP_ID"
	barman recover --remote-ssh-command "$RECOVERY_SSH_CMD" $DB_TO_RESTORE $BACKUP_ID "/var/lib/postgresql/data/"
}

function start_postgres(){
	echo "Starting postgresql with $DB_TO_RESTORE / $BACKUP_ID"
	$RECOVERY_SSH_CMD 'cd / && /docker_entrypoint_rec.sh start_postgres'
}

prepare_recover
recover
start_postgres