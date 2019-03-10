#!/usr/bin/env python

"""
Equivalent to the PHP executables, but now written in python

input argument: An integer time between 0 and 9999

"""

import sys
import pathToSettings as set_err_codes
sys.path.append(set_err_codes.SOFTWARE_FOLDER_PATH)
import PLC_interaction_functions as plc

try:
	time = int(sys.argv[1])
except:
	raise ValueError('Problem with input time. Should be integer between 0 and 9999')

plc.plc_set_comms_timeout(time)
print('PC communication timeout set to '+str(time))
