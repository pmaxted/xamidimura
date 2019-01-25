#!/usr/bin/env python

"""
Equivalent to the PHP executables, but now written in python
"""

import sys
#print(sys.path)
sys.path.append('/home/observer/xamidimura/xamidimura')
#print(sys.path)
import PLC_interaction_functions as plc

status_dict = plc.plc_get_plc_status()
for i in status_dict.keys():
	print(i, ' = ', status_dict[i])
