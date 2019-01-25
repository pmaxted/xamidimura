#!/usr/bin/env python

"""
Equivalent to the PHP executables, but now written in python
"""

import sys
sys.path.append('/home/observer/xamidimura/xamidimura')
import PLC_interaction_functions as plc

plc.plc_request_roof_control()
print('Roof control requested')
