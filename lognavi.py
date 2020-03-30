#!/usr/bin/env python
import webbrowser, sys
import time
import bs4
import requests
from datetime import datetime
from bcolors import bcolors
from pymemcache.client import base
import ast

class LogNavi:
    def __init__(self, username, password, host):
        self.username = username
        self.password = password
        self.host = host

    def service_name(self):
        while True:
            project = raw_input("Enter service name : ")
            is_validated, projs = self.validate_service_name(project)
            if is_validated:
                break
        return project, projs

    def validate_service_name(self,project):
        mc = base.Client(('localhost', 11211))
        proj_cache = mc.get("proj_list_cached")
        if not proj_cache:
            projs = {} 
            res = requests.get(
                "http://{0}:{1}@{2}/lognavigator/logs/cstest-ag-ftp-sync-baibo-hkn117/list".format(self.username, self.password, self.host))
            res.raise_for_status()
            soup = bs4.BeautifulSoup(res.text, 'html.parser')
            for lab in soup.find_all("optgroup"):
                projs[lab['label']] = lab.text.split()
            mc.set("proj_list_cached", projs)
        else:
            projs = ast.literal_eval(proj_cache)
              
        if project in projs.keys():
            return True, projs
        else:
            for p in projs.keys():
                if project in p:
                    print(p)
        return False, projs


    def service_env(self):
        while True:
            env_input = raw_input("Enter environment [dev,cs,prod]: ")
            if self.validate_service_env(env_input):
                return env_input


    def validate_service_env(self,env_input):
        serv_env = {"devtest", "cstest", "production"}
        for i in serv_env:
            if env_input in i:
                return True
        return False


    def logs_time(self):
        while True:
            date_input = raw_input("Enter time using [YYYY-MM-DD-HH]: ")
            if self.validate_date(date_input):
                return date_input


    def validate_date(self,date_input):
        try:
            if not date_input:
                return True
            datetime.strptime(date_input, '%Y-%m-%d-%H')
            return True
        except ValueError:
            return False


    def check_logs_availability(self,current_proj, _url, current_time):
        list = "http://{0}:{1}@{2}/lognavigator/logs/{3}/list".format(self.username, self.password, self.host,  current_proj)
        res = requests.get(list)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        elem = soup.select('#resultsTable > tbody > tr > td:nth-of-type(1) > a')
        if not elem:
            print(bcolors.FAIL + "No Logs found : {0} - {1}".format(current_proj, current_time) + bcolors.ENDC)
        else:
            for a in elem:
                if current_time in a.text:
                    print(bcolors.OKBLUE + "Logs found : {0} - {1} ".format(current_proj, a.text) +bcolors.ENDC)
                    webbrowser.open(_url.replace("catalina.{0}.out".format(current_time), a.text))



    def catalina_list(self, current_proj):
        list = "http://{0}:{1}@{2}/lognavigator/logs/{3}/list".format(self.username, self.password, self.host, current_proj)
        res = requests.get(list)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        elem = soup.select('#resultsTable > tbody > tr > td:nth-of-type(1) > a')
        if not elem:
            print(bcolors.FAIL + "No Logs found : {0}".format(current_proj) + bcolors.ENDC)
            return {}
        else:
            return elem
                    

    def construct_url(self, current_proj, current_time, add_cmd):
        current_time = datetime.today().strftime('%Y-%m-%d-%H') if not current_time else current_time
        diff = datetime.today().hour - datetime.strptime(current_time, '%Y-%m-%d-%H').hour
        bzcat = '' if diff == 0 else '.bz2 | bzcat'
        add_cmd = "tail -1000" if not add_cmd else "grep '{0}'".format(add_cmd) 
        cmd = "command?cmd=curl -ksS catalina.{0}.out{1} | {2}".format(current_time, bzcat, add_cmd)
        return "http://{0}:{1}@{2}/lognavigator/logs/{3}/{4}".format(self.username, self.password, self.host, current_proj, cmd).replace(' ', '+'),current_time



    def main(self):
        while True:
            project, projs = self.service_name()
            env = self.service_env()
            time_str = self.logs_time().strip()
            grep = raw_input("Look for: ")
            for _proj in projs[project]:
                if env in _proj:
                    url, current_time = self.construct_url(_proj, time_str, grep)
                    if env == 'prod':
                        self.check_logs_availability(_proj, url, current_time)
                    else:
                        print("Logs found : {0}".format(_proj))
                        print(bcolors.OKBLUE + "Logs found : {0}".format(_proj) + bcolors.ENDC)
                        webbrowser.open(url)
            time.sleep(1)
    



    def global_search(self):
        while True:
            project, projs = self.service_name()
            env = self.service_env()
            grep = raw_input("Look for: ")
            for _proj in projs[project]:
                if env in _proj:
                    cat_list = self.catalina_list(_proj)
                    if not cat_list:
                        for c_list in reversed(cat_list):
                            if 'out' in c_list["href"]:
                                url_c = "http://{0}:{1}@{2}/lognavigator/logs/{2}/{3}".format(self.username, self.password, self.host, _proj, c_list["href"].replace("tail+-10000","grep '{0}'".format(grep)))
                                res = requests.get(url_c)
                                res.raise_for_status()
                                soup = bs4.BeautifulSoup(res.text, 'html.parser')
                                elem = soup.select('body > section.container-fluid > div > div > pre')
                                if elem[0].text:
                                    print("====Logs found at {0}===".format(url_c))
                                    break
                                else:
                                    print("No logs found at {0}".format(url_c))

                                                       


if __name__ == '__main__':
    sys.stdout.write("\x1b]2;%s\x07" % 'LogNavi ')
    LogNavi().main() #input username, password and host
        

