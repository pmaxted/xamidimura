#!/usr/bin/env python

"""
Equivalent to the PHP executables, but now written in python
"""

import sys
import pathToSettings as set_err_codes
sys.path.append(set_err_codes.SOFTWARE_FOLDER_PATH)
import PLC_interaction_functions as plc

try:
	time = int(sys.argv[1])
except:
	raise ValueError('Problem with input time. Should be integer '\
		'between 0 and 9999')


plc.plc_set_power_timeout(time)
print('Power failure timeout set to '+str(time))
