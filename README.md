# docker-barman
A pgbarman docker image with prometheus metrics

* Periodic recovery check (maybe another image?)
* Pass all global configuration parameters via ENV variables
* Have a volume for server configurations
* Have a volume for backup data
* Push metrics to a Prometheus Push Gateway
    - last backup size and date for each server
    - barman check status (0 or 1) for each server
    - backup times per server and type (full or wal)