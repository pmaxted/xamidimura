#!/usr/bin/env python

"""
Equivalent to the PHP executables, but now written in python. This is a new executable
 that has been created for the new telescope and is not in the PHP
"""

import sys
import pathToSettings as set_err_codes
sys.path.append(set_err_codes.SOFTWARE_FOLDER_PATH)
import PLC_interaction_functions as plc

status_dict = plc.plc_get_telescope_tilt_status()
for i in status_dict.keys():
	print(i, ' = ', status_dict[i])
