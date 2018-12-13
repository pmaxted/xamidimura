#!/usr/bin/env python

"""
Equivalent to the PHP executables, but now written in python
"""

import sys
print(sys.path)
sys.path.append('/Users/Jessica/PostDoc/ScriptsNStuff/current_branch/xamidimura')
print(sys.path)
import PLC_interaction_functions as plc

plc.plc_open_roof()