# xamidimura
Documentation and software for the Xamidimura telescopes


## Folders
configs - Contains configuration files for the filter wheels and focusers (currently only one filter wheel file present)  
logfiles - Where logfiles from the different scripts are stored. (currently only one empty logfile present)  

## Files
filter_wheel_control.py - contains basic serial port command functions for the filter wheels.  
focuser_control.py - basic serial port commands for the focusers.  
ifw_test.py - contains unitest for filter wheel control functions (All functions tested apart from initialisation function). In a terminal use "python ifw_test.py" to run.  
test_focuser_control.py - Unit tests for the focuser_control functions (only get_start_end_char tested so far).  
common.py - contains function that are useful to both focuser and filter wheel control.                
