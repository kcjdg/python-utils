import requests
import sys
import time
import json

jenkins_host = "jenkins_host"
jenkins_user = "user_here"
jenkins_api = "api_key_here"
dev_path = "OLDJENKINS/job/" 
cs_path = "CPMS/job/" 


def check_last_build(jenkins_job):
		job_url = "http://{0}:{1}@{2}/job/{3}/lastBuild/api/json?pretty=true".format(jenkins_user, jenkins_api, jenkins_host, jenkins_job)
		response = requests.get(job_url).json()
		build_id = response["actions"][0]["causes"][0]["upstreamBuild"] if 'rsync' in job_url else response["id"]
		if response['building']:
			print("Building.. {0}".format(jenkins_job))
			return 0, build_id;
		else:
			if response['result'] == "SUCCESS":
				if 'rsync' not in job_url:
					print("Job is success {0}".format(jenkins_job))
				return 1, build_id;
			else: 
				print("Failed build {0}".format(jenkins_job))
				return 2, build_id;     

def crumb_as_headers():
	url = "http://{0}:{1}@{2}/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)".\
	format(jenkins_user,jenkins_api,jenkins_host)
	crumb = requests.get(url).content
	headers = dict()
	headers[crumb.split(":")[0]] = crumb.split(":")[1]
	return headers;



def queue_items():
	while True:
		queue_url = "http://{0}:{1}@{2}/queue/api/json?pretty=true".format(jenkins_user, jenkins_api, jenkins_host)
		queue_resp = requests.get(queue_url).json()
		if len(queue_resp["items"])==0:
			return True
		else:
			print("On queue.. {0}".format(queue_resp["items"][0]["task"]["name"])) 
			time.sleep(5)

	return False		


def build(job, headers):
	if '_RESTART_CSTEST_TEST' in job:
		job_url = "http://{0}:{1}@{2}/job/{3}/buildWithParameters".format(jenkins_user, jenkins_api, jenkins_host, job)
		param_data = {'ip_address':'10.167.12.117'}
		param_data['project_name'] = headers['project_name']
		return requests.post(job_url, headers=headers, params=param_data)
	else:
		job_url = "http://{0}:{1}@{2}/job/{3}/build".format(jenkins_user, jenkins_api, jenkins_host, job)
		return requests.post(job_url, headers=headers)



def poll_status(build_url):
	is_success = False
	while True:
		status, id = check_last_build(build_url)
		if status == 1:
			is_success = True
			break;
		elif status == 0:
			time.sleep(10)
		else:
			break;

	return is_success,id;


def build_an_poll(build_job, headers):
	build_resp = build(build_job,headers)
	if build_resp.status_code == 201 and queue_items():
		if 'OLDJENKINS' in build_job:
			return True
		return poll_status(build_job)[0];
	else:
		print("Unable to build {0}".format(build_resp.status_code))
	return False;




if len(sys.argv) < 3:
	print("Usage: Incomplete arguments")
	exit()
jenkins_job = sys.argv[1]
action = sys.argv[2]

headers = crumb_as_headers()
dev_build = dev_path + jenkins_job;
cs_build = cs_path + 'TEST_SYNC_' + jenkins_job.upper() + '_TEST'
sync_restart_build = cs_path + 'SYNC_RESTART_' + jenkins_job.upper() + '_TEST' 
restart_build = 'CPMS/job/_RESTART_CSTEST_TEST' 

if action is 'build':
	print("Building Dev Test - Cs Test {0}".format(dev_build))
	if build_an_poll(dev_build, headers):
		id = poll_status(dev_build)[1]
		rsync_job = dev_path+'rsync_'+jenkins_job
		while True:
			rsync_status, rsyncId =  poll_status(rsync_job)
			if int(rsyncId) == int(id):
				print("Job is sucess {0}".format(rsync_job))
				break;
			else:
				time.sleep(5);
		if build_an_poll(cs_build, headers) and build_an_poll(sync_restart_build, headers):
			print("Done")
elif action == 'sync_restart':
	print("Building CS TEST .. {0}".format(cs_build))
	if build_an_poll(cs_build, headers) and build_an_poll(sync_restart_build, headers):
		print("Done")
elif action =='cs_restart':
	print("Building RESTART CS TEST .. {0}".format(restart_build))
	headers['project_name'] = jenkins_job;
	if build_an_poll(restart_build, headers):
		print("Done")
