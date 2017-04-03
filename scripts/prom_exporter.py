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
			status.add_metric([server], 0)
		except subprocess.CalledProcessError as e:
			status.add_metric([server], e.returncode)
	return status

def add_metric_or_pass(metric,labels,value):	
	try:		
		if(float(value)):
			metric.add_metric(labels, float(value))
	except:
		pass


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

	try:
		for server,server_data in diagnose_data['servers'].iteritems():
			if not server_data['status']['connection_error']:
				if server_data['status']['current_size']:
					add_metric_or_pass(metrics['database_size'], [server], server_data['status']['current_size'])
				redundancy_actual = len(server_data['backups']) if len(server_data['backups']) else 0
				add_metric_or_pass(metrics['redundancy_actual'], [server], redundancy_actual)
				add_metric_or_pass(metrics['redundancy_expected'], [server], server_data['config']['minimum_redundancy'])				

				if len(server_data['backups']):
					backup_names = sorted(server_data['backups'].keys())
					done_backup_names = []
					for backup_name in backup_names:
						server_data['backups'][backup_name]['status'] != 'DONE'
						done_backup_names.append(backup_name)
					if len(done_backup_names):
						first_date = parse_date_from_backup_name( done_backup_names[0])
						last_date = parse_date_from_backup_name( done_backup_names[-1])
						last_backup_data = server_data['backups'][done_backup_names[-1]]						
						add_metric_or_pass(metrics['last_backup_size'],[server], last_backup_data['size'])
						add_metric_or_pass(metrics['last_backup_age'],[server], (datetime.utcnow()-last_date).total_seconds())
						add_metric_or_pass(metrics['backup_window'],[server], (last_date-first_date).total_seconds())

						if os.path.isfile("/tmp/backups_{}.log".format(server)):
							try:
								command = ["grep", "{} duration".format(done_backup_names[-1]), "/tmp/backups_{}.log".format(server)]
								grep_output = subprocess.check_output(command)
								add_metric_or_pass(metrics['backup_duration'],[server], grep_output.split()[3])								
							except subprocess.CalledProcessError as e:		
								print "{} | {} | {}".format(e.returncode,e.cmd,e.output)
								print 'Command failed: {}'.format(' '.join(command))
	except:
		print "ERROR: DIAGNOSE DATA -> {}".format(diagnose_data)
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
