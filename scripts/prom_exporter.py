from prometheus_client import start_http_server, Gauge
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
import subprocess
import time
import random
import re
import json
import os
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

def add_metric_or_pass(metric,labels,value,default_value=None):	
	try:		
		if(float(value) is not None):
			metric.add_metric(labels, float(value))
	except:
		if default_value:
			metric.add_metric(labels, float(default_value))
		else:
			pass

def backup_metrics():
	metrics = setup_metrics()
	diagnose_data = json.loads(subprocess.check_output(["barman","diagnose"]))
	try:
		for server,server_data in diagnose_data['servers'].iteritems():
			process_server(server,server_data,metrics)
	except Exception as e:
		print e
		print "ERROR: DIAGNOSE DATA -> {}".format(diagnose_data)
	return metrics.values()

def setup_metrics():
	metrics = {}
	metrics['database_size'] = GaugeMetricFamily('barman_database_size_bytes', 'Database size in bytes', labels=['server_name'])
	metrics['last_backup_age'] = GaugeMetricFamily('barman_last_backup_age_seconds', 'Last backup age', labels=['server_name'])
	metrics['last_backup_size'] = GaugeMetricFamily('barman_last_backup_size_bytes', 'Last backup size in bytes', labels=['server_name'])
	metrics['backup_duration'] = GaugeMetricFamily('barman_backup_duration_seconds', 'Backups duration in seconds', labels=['server_name'])
	metrics['recovery_duration'] = GaugeMetricFamily('barman_recovery_duration_seconds', 'Recovery duration in seconds', labels=['server_name'])
	metrics['recovery_status'] = GaugeMetricFamily('barman_recovery_status', 'Last recovery attempt status', labels=['server_name'])	
	metrics['backup_window']  = GaugeMetricFamily('barman_backup_window_seconds', 'Backup window covered by all existing backups', labels=['server_name'])
	metrics['redundancy_actual']  = GaugeMetricFamily('barman_current_redundancy', 'Number of existing backups', labels=['server_name'])
	metrics['redundancy_expected']  = GaugeMetricFamily('barman_expected_redundancy', 'Number of expected backups as defined in config', labels=['server_name'])
	return metrics

def process_server(server,server_data,metrics):
	# check 'connection_error' with 'get' to avoid a KeyError if key is missing (as in barman v1.6)
	if not server_data['status'].get('connection_error'):
		add_metric_or_pass(metrics['database_size'], [server], server_data['status']['current_size'])
		add_metric_or_pass(metrics['redundancy_expected'], [server], server_data['config']['minimum_redundancy'])				
		done_backup_names = get_done_backups(server_data)
		add_metric_or_pass(metrics['redundancy_actual'], [server], len(done_backup_names))		
		if done_backup_names:						
			first_backup_name = done_backup_names[0] 
			last_backup_name = done_backup_names[-1]
			first_date = parse_date_from_backup_name( first_backup_name )
			last_date = parse_date_from_backup_name( last_backup_name )			
			add_metric_or_pass(metrics['last_backup_size'],[server], server_data['backups'][last_backup_name]['size'])
			add_metric_or_pass(metrics['last_backup_age'],[server], (datetime.utcnow()-last_date).total_seconds())
			add_metric_or_pass(metrics['backup_window'],[server], (last_date-first_date).total_seconds())
			add_metric_or_pass(metrics['backup_duration'],[server], backup_duration(server,last_backup_name))														
			add_metric_or_pass(metrics['recovery_duration'],[server], recovery_duration(server,last_backup_name))
			add_metric_or_pass(metrics['recovery_status'],[server], recovery_status(server,last_backup_name))		

def server_has_backups(server_data):
	len(server_data['backups']) > 0

def get_done_backups(server_data):
	done_backup_names = []
	backup_names = sorted(server_data['backups'].keys())
	for backup_name in backup_names:
		if server_data['backups'][backup_name]['status'] == 'DONE':
			done_backup_names.append(backup_name)
	return done_backup_names

def backup_duration(server,backup_name):
	return fetch_metric_from_log_file('duration',server,backup_name)

def recovery_duration(server,backup_name):
	return fetch_metric_from_log_file('recovery',server,backup_name)

def recovery_status(server,backup_name):
	return fetch_metric_from_log_file('rec_status',server,backup_name)

def fetch_metric_from_log_file(duration_type,server,backup_name):
	backup_log_file = get_backup_log_file(server)
	if os.path.isfile(backup_log_file):
		try:
			command = ["grep", "{} {}".format(backup_name,duration_type), backup_log_file]
			grep_output = subprocess.check_output(command)			
			return grep_output.split()[3]
		except subprocess.CalledProcessError as e:					
			#print 'Command failed: {}'.format(' '.join(command))
			#print "{} | {} | {}".format(e.returncode,e.cmd,e.output)
			return None

def get_backup_log_file(server):
	return "{}/prometheus_exporter_work/backups_{}.log".format(os.environ["BARMAN_BARMAN_HOME"],server)

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
