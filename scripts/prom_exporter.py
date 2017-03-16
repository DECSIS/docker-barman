from prometheus_client import start_http_server, Gauge
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
import subprocess
import time
import random
import re
from  datetime import datetime

def barman_list_servers():
	p = subprocess.check_output(["barman", "list-server", "--minimal"])	
	servers = []
	for line in p.split('\n'):
		if line:
			servers.append(line)
	return servers

def barman_check():
	status = GaugeMetricFamily('barman_status', 'Status given by barman check', labels=['server_name'])
	for server in barman_list_servers():
		try:
			check_string = subprocess.check_output(["barman", "check", server, "--nagios"])
			status.add_metric([server], 1)
		except subprocess.CalledProcessError as e:
			status.add_metric([server], e.returncode)
	return status

def backup_metrics():
	database_size = GaugeMetricFamily('barman_database_size_bytes', 'Database size in bytes', labels=['server_name'])
	last_backup_age = GaugeMetricFamily('barman_last_backup_age_seconds', 'Last backup age', labels=['server_name'])
	last_backup_size = GaugeMetricFamily('barman_last_backup_size_bytes', 'Last backup size in bytes', labels=['server_name'])
	backup_window  = GaugeMetricFamily('barman_backup_window_seconds', 'Backup window covered by all existing backups', labels=['server_name'])
	redundancy_actual  = GaugeMetricFamily('barman_current_redundancy', 'Number of existing backups', labels=['server_name'])
	redundancy_expected  = GaugeMetricFamily('barman_expected_redundancy', 'Number of expected backups as defined in config', labels=['server_name'])	
	numbers_pattern = re.compile('\d+')
subprocess.check_output("barman show-backup postgreslab1 last | grep 'with WALs' | cut -d':' -f 2")
	for server in barman_list_servers():
		try:
			status_string = subprocess.check_output(["barman", "status", server])
			last_date = None
			first_date = None
			for line in status_string.split('\n'):
				if "Current data size:" in  line:
					database_size.add_metric([server],float(line.split(': ')[1].split()[0]) * 1024 *1024)
				if "available backups:" in  line:
					redundancy_actual.add_metric([server],float(line.split(': ')[1]))
				if "First available backup:" in  line:
					try:
						first_date = datetime.strptime( line.split(': ')[1], "%Y%m%dT%H%M%S" )
					except ValueError as e:
						True
				if "Last available backup:" in  line:
					try:
						last_date = datetime.strptime( line.split(': ')[1], "%Y%m%dT%H%M%S" )
						last_backup_age.add_metric([server],(datetime.utcnow()-last_date).total_seconds())
						backup_window.add_metric([server],(last_date-first_date).total_seconds())							
					except ValueError as e:												
						True
				if "Minimum redundancy requirements:" in  line:
					try:
						redundancy_expected.add_metric([server], float(numbers_pattern.findall(line)[1]))
					except:
						True
		except subprocess.CalledProcessError as e:
			print "Unable to read status"
	return [database_size,backup_window,last_backup_age,redundancy_actual,redundancy_expected]

class CustomCollector(object):
    def collect(self):        
        yield barman_check()
        for metric in backup_metrics():
        	yield metric

REGISTRY.register(CustomCollector())

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8000)
    # Generate some requests.
    while True:
        time.sleep(10000)