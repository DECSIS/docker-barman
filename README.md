# docker-barman
A pgbarman docker image with Prometheus metrics

## What does this image do

After properly configured this image runs a cron with the [cron](http://docs.pgbarman.org/release/2.1/index.html#cron) command every minute. That "executes WAL archiving operations concurrently on a server basis, and this also enforces retention policies on those servers that have:

* `retention_policy` not empty and valid;
* `retention_policy_mode` set to auto.

The cron command ensures that WAL streaming is started for those servers that have requested it, by transparently executing the receive-wal command."

The image currently is focused on streaming replication so no rsync streaming or now.

## How to use this image

    $ docker run -v /path/to/db/configs:/etc/barman.d/ -v /path/to/backupdata/:/var/lib/barman/ decsis/pg-barman

For an full overview of using this image with a server check the example configuration for in the [docker-compose.yml](). If you run this compose file you will obtain two PostgresSQL servers and a Barman scheduled to make full backups every hour for server1 and every 6 hours to server2. Also a Prometheus server will be available to gather metrics from the exporter included in the image.

    docker-compose up

After that Barman will complain in the log:

    barman_1        | 2017-03-17 11:54:02,239 [192] barman.server ERROR: replication slot 'barman' doesn't exist. Please execute 'barman receive-wal --create-slot postgreslab1'
    barman_1        | 2017-03-17 11:54:02,256 [193] barman.wal_archiver INFO: Synchronous WAL streaming for barman_receive_wal: False
    barman_1        | 2017-03-17 11:54:02,257 [193] barman.server ERROR: replication slot 'barman' doesn't exist. Please execute 'barman receive-wal --create-slot postgreslab2'

Just run:

    docker exec -u barman -it dockerbarman_barman_1 barman receive-wal --create-slot postgreslab1
    docker exec -u barman -it dockerbarman_barman_1 barman receive-wal --create-slot postgreslab2

Give it a minute or so to settle up and then execute the following to make PostgreSQL servers switch to another transaction log file and allows barman to be ready to do backups:

    docker exec -u barman -it dockerbarman_barman_1 barman switch-xlog --force all

Finally execute the backups:

    docker exec -u barman -it dockerbarman_barman_1 barman backup all

At any point you can view the status at http://localhost:8000

**IMPORTANT:** Take this just as a quick overview of the image funcionality. Please do read the [barman manual](http://docs.pgbarman.org/release/2.1/index.html) and the [PostgreSQL documentation](https://www.postgresql.org/docs/current/static/) to fully understand what is going on.

### Configuring Barman

All `ENV` variables that starts with `BARMAN_` will be converted read and converted to the correct format needed for `barman.conf` file. Example `BARMAN_MINIMUM_REDUNDANCY=1` will be inserted as `minimum_redundancy=1`. Full list of options at [pgbarman's manual](http://docs.pgbarman.org/release/2.1/barman.5.html#options).


Alternatively it is possible to mount a volume file in `$BARMAN_BARMAN_HOME/.barman.conf` that will override the base config file.

### Configuring servers

For server configurations provide a file per server in `/etc/barman.d/` as stated in the [barman manual](http://docs.pgbarman.org/release/2.1/index.html#configuration).

Additionaly you can pass a extra configuration in these files for scheduling backups:

    #:backup_cron = 0 10 * * *

The image runs a every minute script that maintains (insert, update and delete) the `crontab` gathering this preoperty from the available `*.conf` files. The resulting `crontab` for the previous example:

    MAILTO=""
    BARMAN_LOG_FILE=/var/log/barman.log
    BARMAN_PRE_BACKUP_SCRIPT=/opt/barman/scripts/pre_backup.sh
    BARMAN_POST_BACKUP_SCRIPT=/opt/barman/scripts/post_backup.sh
    BARMAN_BARMAN_HOME=/var/lib/barman
    BARMAN_CONFIGURATION_FILES_DIRECTORY=/etc/barman.d
    * * * * * barman cron
    * * * * * /opt/barman/scripts/backup_scheduler.sh
    0 10 * * * barman backup postgreslab3


**Important**: Please notice that this additional property is prefixed by `#:` to avoid barman complaining about an unknown property. The `:` is there to make clear this is not just a comment.

## Available metrics

The image ships with a Prometheus exporter in the form of a Python script. After the container starts the metrics should be available at http://localhost:8000.

It will generate the following metrics:

* *barman_status* Status as given by barman check command (0 is OK everything else is bad)
* *barman_last_backup_size_bytes* Last backup size in bytes
* *barman_expected_redundancy* Number of expected backups as defined in config minimum_redundancy
* *barman_database_size_bytes* Database size in bytes
* *barman_backup_duration_seconds* Backup duration in seconds
* *barman_recovery_duration_seconds* Recovery duration in seconds
* *barman_backup_window_seconds* Backup window covered by all existing backups
* *barman_last_backup_age_seconds* Last backup age
* *barman_current_redundancy* Number of existing backups

A sample scrape config is available in [example/prometheus_config.yml]()
