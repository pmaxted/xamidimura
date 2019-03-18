#!/usr/bin/env python

"""
Equivalent to the PHP executables, but now written in python
"""

import sys
import pathToSettings as set_err_codes
sys.path.append(set_err_codes.SOFTWARE_FOLDER_PATH)
import PLC_interaction_functions as plc

plc.plc_select_mains()
print('MAINS selected')
