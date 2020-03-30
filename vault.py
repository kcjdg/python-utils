#!/usr/bin/env python

import requests
import pyperclip
import json
import sys
import webbrowser


def list_keys(path):
	resp = requests.get("https://{0}/v1/secret/{1}".format(path,domain), headers=headers, params=params).json()
	print(resp)
	for r in resp["data"]["keys"]:
		if inputd in r:
			print(r)
		

headers = dict()
headers["X-Vault-Token"]="s.7eX56ayfSGsJdGxjsOLVFKBr"
headers["Content-Type"]="application/json"
params ={"list":"true"}

domain = "127.0.0.1:8200"

if len(sys.argv) < 3:
    print("Usage: Incomplete arguments: Arguments example: application/ list or application val")
    exit()
inputd = sys.argv[1]
action = sys.argv[2]

if action == 'list':
	path="";
	if "/" in inputd:
		path = inputd
		inputd =""
		list_keys(path)
	else:
		list_keys(path)
elif action == 'val':
	resp = requests.get("https://{0}/v1/secret/{1}".format(domain, inputd), headers=headers).json()
	if "data" in resp.keys():
		json_resp = json.dumps(resp["data"],indent=2)
		pyperclip.copy(json_resp)
		print(json_resp)
		webbrowser.open("https://{0}/ui/vault/secrets/secret/show/{1}".format(domain,inputd))
	else:
		print("No vault path {}".format(inputd))	


