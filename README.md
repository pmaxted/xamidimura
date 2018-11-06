# xamidimura
Documentation and software for the Xamidimura telescopes


## Folders
### configs -  
	Contains configuration files for the filter wheels and focusers (currently only one filter wheel file and one focuser present)  
	
### logfiles - 
	Where logfiles from the different scripts are stored. (logfiles currently overwritten each time scripts are run.)  


## Files
### filter_wheel_control.py -  
	contains basic serial port command functions for the filter wheels.  

### focuser_control.py -  
	basic serial port commands for the focusers.  
	
### common.py -  
	contains function that are useful to both focuser and filter wheel control.  
	  
### ifw_test.py -  
	contains unitest for filter wheel control functions (All functions tested apart from initialisation function). In a terminal use "python ifw_test.py" to run.  
	
### test_focuser_control.py -  
	Unit tests for the focuser_control functions.  
               
