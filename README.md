#ATTENTION WIP!

# docker-barman
A pgbarman docker image with prometheus metrics

## What does this image do

After properly configured this image runs a cron with the [cron](http://docs.pgbarman.org/release/2.1/index.html#cron) command every minute. That "executes WAL archiving operations concurrently on a server basis, and this also enforces retention policies on those servers that have:

* `retention_policy` not empty and valid;
* `retention_policy_mode` set to auto.

The cron command ensures that WAL streaming is started for those servers that have requested it, by transparently executing the receive-wal command."

## How to use this image

    $ docker run -v /path/to/db/configs:/etc/barman.d/ -v /path/to/backupdata/:/var/lib/barman/ decsis/pg-barman

### Configuring Barman

All `ENV` variables that starts with `BARMAN_` will be converted read and coverted to the correct format needed for `barman.conf` file. Example `BARMAN_MINIMUM_REDUNDANCY=1` will be inserted as `minimum_redundancy=1`. Full list of options at [pgbarman's manual](http://docs.pgbarman.org/release/2.1/barman.5.html#options).


Alternatively it is possible to mount a volume file in `$BARMAN_BARMAN_HOME/.barman.conf` thar will override the base config file.

### Configuring servers

For server configurations provide a file per server in `/etc/barman.d/` as stated in the conf filenkjsajkfjsadf.

Also the image runs a every minute script that mainstains a crontab blblablabbla

