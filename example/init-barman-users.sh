#!/bin/bash
set -e
set -x


if ! grep -q streaming_barman /var/lib/postgresql/data/pg_hba.conf; then
	echo "hostssl replication streaming_barman all md5" >> /var/lib/postgresql/data/pg_hba.conf
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER barman SUPERUSER PASSWORD 'barman';
    CREATE USER streaming_barman REPLICATION PASSWORD 'barman';
EOSQL
