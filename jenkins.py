#!/usr/bin/env python

import requests
import sys
import time


#TODO
#parallel request batch build

class Jenkins:
    def __init__(self, jenkins_user, jenkins_api, jenkins_host):
        self.jenkins_user = jenkins_user
        self.jenkins_api = jenkins_api
        self.jenkins_host = jenkins_host
        self.dev_path = "Dev_PATH/job/"
        self.cs_path = "CS_PATH/job/"

    def last_build(self, job, is_crumb=False):
        if is_crumb: 
            self.crumb_as_headers()
        job_url = "https://{0}:{1}@{2}/job/{3}/lastBuild/api/json?pretty=true".format(self.jenkins_user, self.jenkins_api, self.jenkins_host, job)
        return requests.get(job_url).json(),job_url


    def check_last_build(self,job):
        response, job_url = self.last_build(job)
        _build_id = response["actions"][0]["causes"][0]["upstreamBuild"] if 'rsync' in job_url else response["id"]
        console_build = response['url'] + "console"
        if response['building']:
            print("Building.. {0}".format(console_build))
            return 0, _build_id
        else:
            if response['result'] == "SUCCESS":
                if 'rsync' not in job_url:
                    print("SUCCESS JOB {0}".format(console_build))
                return 1, _build_id
            else:
                print("FAILED BUILD {0}".format(console_build))
                sys.exit()


    def crumb_as_headers(self):
        url = "https://{0}:{1}@{2}/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)". \
            format(self.jenkins_user, self.jenkins_api, self.jenkins_host)
        crumb = requests.get(url).content
        headers = dict()
        headers[crumb.split(":")[0]] = crumb.split(":")[1]
        return headers


    def queue_items(self):
        while True:
            queue_url = "https://{0}:{1}@{2}/queue/api/json?pretty=true".format(self.jenkins_user, self.jenkins_api, self.jenkins_host)
            queue_resp = requests.get(queue_url).json()
            if len(queue_resp["items"]) == 0:
                return True
            else:
                print("On queue.. {0}".format(queue_resp["items"][0]["task"]["name"]))
                time.sleep(5)
        return False


    def build(self, job): 
        if job.startswith('_RESTART_', 9):
            job_url = "https://{0}:{1}@{2}/job/{3}/buildWithParameters".format(self.jenkins_user, self.jenkins_api, self.jenkins_host, job)
            ip = "127.0.0.1" if "CS" in job else "127.0.0.2"
            param_data = {'ip_address': ip, 'project_name': self.headers['project_name']}
            return requests.post(job_url, headers=self.headers, params=param_data)
        else:
            job_url = "https://{0}:{1}@{2}/job/{3}/build".format(self.jenkins_user, self.jenkins_api, self.jenkins_host, job)
            return requests.post(job_url, headers=self.headers)


    def poll_status(self,build_url):
        is_success = False
        while True:
            status, id = self.check_last_build(build_url)
            if status == 1:
                is_success = True
                break
            elif status == 0:
                time.sleep(10)
            else:
                break
        return is_success, id


    def build_an_poll(self, build_job):
        build_resp = self.build(build_job)
        if build_resp.status_code == 201 and self.queue_items():
            if 'Dev_PATH' in build_job:
                return True
            return self.poll_status(build_job)[0]
        else:
            print("Unable to build {0}".format(build_resp.status_code))
        return False


    def dev_build(self):
        dev_build = self.dev_path + self.jenkins_job
        print("Building Dev Test {0}".format(dev_build))
        if self.build_an_poll(dev_build):
            build_id = self.poll_status(dev_build)[1]
            if 'core' not in self.jenkins_job:
                rsync_job = self.dev_path + 'rsync_' + self.jenkins_job
                while True:
                    rsync_status, rsyncId = self.poll_status(rsync_job)
                    if int(rsyncId) == int(build_id):
                        print("Job is sucess {0}".format(rsync_job))
                        break
                    else:
                        time.sleep(5)
                self.cs_build()    


    def cs_build(self):
        cs_build = self.cs_path + 'TEST_SYNC_' + self.jenkins_job.upper() + '_TEST'
        sync_restart_build = cs_build.replace("TEST_SYNC","SYNC_RESTART")
        print("Building CS Test {0}".format(cs_build))
        if self.build_an_poll(cs_build) and self.build_an_poll(sync_restart_build):
            print("Done")  

    def cs_restart(self):
        restart_build = self.cs_path+'_RESTART_CSTEST_TEST'
        print("Restarting CS TEST .. {0}".format(restart_build))
        self.headers['project_name'] = self.jenkins_job
        if self.build_an_poll(restart_build):
            print("Done")    
    
    def prod_restart(self):
        if "BT_PROJECT" in self.jenkins_job:
            prod_restart = self.cs_path + '_RESTART_BT_PROJECT_TEST'
            print("Restarting PROD BT_PROJECT .. {0}".format(prod_restart))
            self.headers['project_name'] = self.jenkins_job
            if self.build_an_poll(prod_restart):
                print("Done")
        else:
            print("No restart for this service")          


    def main(self):
        if len(sys.argv) < 3:
            print("Usage: Incomplete arguments")
            exit()
        self.headers = self.crumb_as_headers()
        action = sys.argv[2]
        jobs = sys.argv[1].split("~")
        for job in jobs:
            self.jenkins_job = job
            if action == 'build':
                self.dev_build()    
            elif action == 'test_sync':
                self.cs_build()
            elif action == 'cs_restart':
                self.cs_restart()
            elif action == 'prod_restart':
                self.prod_restart()
            else:
                 print("No action is suited for your request [build, test_sync, cs_restart, prod_restart]")


if __name__ == '__main__':
    sys.stdout.write("\x1b]2;%s\x07" % 'Jenkins ')
    Jenkins().main() #input user, host and token
