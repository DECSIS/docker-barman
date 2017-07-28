#!/bin/bash
set -e

BARMAN_CONF="/etc/barman.conf"
TEMP_CONF="/tmp/barman.conf"

add_property() {
	echo $(echo "$1" | awk '{print tolower($0)}')'='${!1}
}

generate_configuration() {
	mkdir -p "BARMAN_LOG_FILE"
	> "$TEMP_CONF"
	echo "[barman]" >> "$TEMP_CONF"
	compgen -e | grep -e "^BARMAN_" | while read -r line ; do 
		add_property "$line" >> "$TEMP_CONF"
	done
	sed -e 's/^barman_//g' "$TEMP_CONF" > "$BARMAN_CONF"
}

generate_cron () {	
	touch /etc/crontab /etc/cron.*/* #fix https://github.com/DECSIS/docker-barman/issues/11
	/etc/init.d/cron start # deamon	
	cat <<- EOF > "/tmp/cron.jobs"
		MAILTO="" 
		$(env | grep -e "^BARMAN_")
		* * * * * /opt/barman/scripts/backup_scheduler.sh
	EOF
	cat "/tmp/cron.jobs"
	gosu barman bash -c "crontab /tmp/cron.jobs"	
}

ensure_permissions() {
	touch "$BARMAN_LOG_FILE"
	for path in \
		/etc/barman.conf \
		"$BARMAN_CONFIGURATION_FILES_DIRECTORY" \
		"$BARMAN_LOG_FILE" \
	; do
		chown -R barman:barman "$path"
	done	
}

prometheus_metrics_exporter_deamon(){
	python /opt/barman/scripts/prom_exporter.py >> "$PROM_EXPORTER_LOG_FILE" 2>&1 &	
}

if [ "$1" = 'barman' ]; then
	rm -rf /tmp/*	
	generate_configuration
	generate_cron	
	ensure_permissions
	prometheus_metrics_exporter_deamon	
	exec gosu barman dockerize -stdout "$BARMAN_LOG_FILE" -stderr "$BARMAN_LOG_FILE" -stdout "$PROM_EXPORTER_LOG_FILE"
fi

exec "$@"