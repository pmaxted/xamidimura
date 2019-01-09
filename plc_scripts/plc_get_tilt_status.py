#!/usr/bin/env python

"""
Equivalent to the PHP executables, but now written in python. This is a new executable
 that has been created for the new telescope and is not in the PHP
"""

import sys
print(sys.path)
sys.path.append('/Users/Jessica/PostDoc/ScriptsNStuff/current_branch/xamidimura')
print(sys.path)
import PLC_interaction_functions as plc

plc.plc_get_telescope_tilt_status()