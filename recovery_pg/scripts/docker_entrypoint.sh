#!/bin/bash

set -e

function stop_running_postgres() {
	kill -INT `head -1 /var/lib/postgresql/data/postmaster.pid` || true
}

function empty_pgdata() {
	rm -rf "$PGDATA/*"
}

function run_postgres() {
	/docker-entrypoint.sh postgres >> "/var/log/postgres.log" & #falta o stderror
}

function prepare_recover(){
	stop_running_postgres
	empty_pgdata
}

function adjust_pg_hba() {
	#remove ssl requirements
	sed -i  '/ssl/d' /var/lib/postgresql/data/pg_hba.conf
	#remove possible custom directories
	sed -i  '/dir/d' /var/lib/postgresql/data/postgresql.conf
}

function start_postgres() {
	adjust_pg_hba
	run_postgres
}

if [ "$1" = 'sshd' ]; then
	/usr/sbin/sshd -D >> /var/log/sshd.log &
	exec dockerize -stdout "/var/log/postgres.log" -stdout "/var/log/sshd.log"
fi
if [ "$1" = 'prepare_recover' ]; then
	prepare_recover
	exit 0
fi
if [ "$1" = 'start_postgres' ]; then
	start_postgres	
	exit 0
fi

exec $@