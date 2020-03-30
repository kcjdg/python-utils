#!/usr/bin/env python

import webbrowser, sys
import time

docu_map = {'proj_1':'link1','proj_2':'link2'}
try:
    import readline
except:
    pass #readline not available


sys.stdout.write("\x1b]2;%s\x07" % 'Office Docs')


while True:
    key = raw_input("Enter key " + str(docu_map.keys()) + ": ")
    if key in docu_map:
        webbrowser.open(docu_map[key])
        time.sleep(1)
    else:
        print("No Mapping. Please Try again")
