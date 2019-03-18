#!/usr/bin/env python

"""
Equivalent to the PHP executables, but now written in python
"""

import sys
import pathToSettings as set_err_codes
sys.path.append(set_err_codes.SOFTWARE_FOLDER_PATH)
import PLC_interaction_functions as plc

status_dict = plc.plc_get_rain_status()
for i in status_dict.keys():
	print(i, ' = ', status_dict[i])
