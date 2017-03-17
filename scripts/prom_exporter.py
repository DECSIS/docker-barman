from prometheus_client import start_http_server, Gauge
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
import subprocess
import time
import random
import re
import json
import os.path
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
	metrics = {}
	metrics['database_size'] = GaugeMetricFamily('barman_database_size_bytes', 'Database size in bytes', labels=['server_name'])
	metrics['last_backup_age'] = GaugeMetricFamily('barman_last_backup_age_seconds', 'Last backup age', labels=['server_name'])
	metrics['last_backup_size'] = GaugeMetricFamily('barman_last_backup_size_bytes', 'Last backup size in bytes', labels=['server_name'])
	metrics['backup_duration'] = GaugeMetricFamily('barman_backup_duration_seconds', 'Backups duration in seconds', labels=['server_name'])
	metrics['backup_window']  = GaugeMetricFamily('barman_backup_window_seconds', 'Backup window covered by all existing backups', labels=['server_name'])
	metrics['redundancy_actual']  = GaugeMetricFamily('barman_current_redundancy', 'Number of existing backups', labels=['server_name'])
	metrics['redundancy_expected']  = GaugeMetricFamily('barman_expected_redundancy', 'Number of expected backups as defined in config', labels=['server_name'])	


	diagnose_data = json.loads(subprocess.check_output(["barman","diagnose"]))	
	
	for server,server_data in diagnose_data['servers'].iteritems():				
		metrics['database_size'].add_metric([server],server_data['status']['current_size'])
		metrics['redundancy_actual'].add_metric([server],len(server_data['backups']))
		metrics['redundancy_expected'].add_metric([server], server_data['config']['minimum_redundancy'] )
	
		if len(server_data['backups']):
			backup_names = sorted(server_data['backups'].keys())
			first_date = parse_date_from_backup_name( backup_names[0])
			last_date = parse_date_from_backup_name( backup_names[-1])
			metrics['last_backup_size'].add_metric([server], server_data['backups'][backup_names[-1]]['size'])
			metrics['last_backup_age'].add_metric([server],(datetime.utcnow()-last_date).total_seconds())
			metrics['backup_window'].add_metric([server],(last_date-first_date).total_seconds())							
			if os.path.isfile("/tmp/backups_{}.log".format(server)):
				metrics['backup_duration'].add_metric([server],float(subprocess.check_output(["tail", "-n", "1", "/tmp/backups_{}.log".format(server)]).split()[3]))
		
	return metrics.values()

def parse_date_from_backup_name(backup_name):
	try:		
		return datetime.strptime(backup_name, "%Y%m%dT%H%M%S" )
	except ValueError:
		return None

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