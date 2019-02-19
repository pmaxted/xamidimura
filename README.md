# xamidimura
Documentation and software for the Xamidimura telescopes  


## Folders
* **configs** - Contains configuration files for the filter wheels and focusers.
 Contains two for the focusers and two for the filter wheels. Each config file
 now contains the correct port for each device.  

* **database** - Contains the sqlite database 'xamidimura.db' which [so far] 
 contains the observing log table 'obslog2' (stores infomation about the types
 of images taken), 'target_info' (a table containing all the information on 
 the targets we could observe), and 'priority_table' contains all the info 
 related to the priority of each target. Other tables could be added later, 
 and the location is not set in stone.  

* **fits_file_tests** - A location to store the fits headers that are created. 
 Headers will be sorted in to folders based on the date at the start of the 
 night, and will have the format '20190129'.
 Again location can be moved later if necessary.  
	
* **logfiles** - Where logfiles from the different scripts are stored. (logfiles
 currently overwritten each time scripts are run.) Also contains a mock weather
 log file.  

* **obs_recipes** - Suggestion for where the observing recipes are kept.  

* **plc_scripts** - Contains scripts which will be equivalent to the PHP scripts
 currently on the Gateway machine. These scripts will open/close the roof, get
 the roof/rain/plc status, swap to/from main/battery power etc. They use the 
 roof_control_functions.py and PLC_interaction_function.py scripts.    

* **tests** - All the scripts for the different collections of unit tests.  

## Files
* **common.py** - contains function that are useful to both focuser and filter 
	wheel control. Most of it has been shown to work but not unit tests.  

* **connect_database.py** - functions to connect to a sqlite database, and do
 useful thing like see what rows are in the database, convert it to a pandas 
 dataframe (will be useful for manipulating). To be updated and adapted when 
 extra functions are needed.  
 
* **das_fits_file_handler.py** - Used to copy files from both das machines to 
 observer machine. Is desgined to running continuously in the background.  

* **expose.py** - A very basic observing script. It will start up the filter
 wheels and focusers, load in an observing recipe and take exposures as 
 specified by the observing script. It will not slew to a target, and details
 of the target, e.g. name, etc need to be filled in at the top of the script.
 Instructions on how to use are at the start of the script.  

* **filter_wheel_control.py** - contains basic serial port command functions 
 for the filter wheels. All tested.    

* **focuser_control.py** - basic serial port commands for the focusers. Tested.  

* **observing.py** - Will contain the main functions to carry out the observing,
 and other functions required by this main function. Currently can create fits
 file with only header information, store an observing record in the obslog2 
 table in the xamidimura database. No unit tests created yet.  
 
* **plcd.py** Eventually this script combined with the 'mya.py' script will be
 responsible for opening and closing the roof. Uses mempory mapping of a file, 
 which plcd continually monitors for changes. If a change is detected, the 
 appropriate action is taken. Contains appropriate tilt checks, will park the
 telescpe if needed and request remote control if needed.  

* **PLC_interaction_functions.py** - Contains functions that will open/close 
 the roof, get the roof/rain/plc status, swap to/from main/battery power etc. 
 Has been modified from the original version. Messages are now logged, and 
 errors (a user defined PLC_ERROR) are raised if a problem occurs instead of 
 exiting Python. Functions which check the status of something will return the 
 info as a dictionary and not just print the messages to screen. These functions
 also have the option to log the statu info or not. There is a function to get 
 the tilt status of the telescope. There is a function to request telescope 
 drive control. **CURRENTLY new tilt checks etc are NOT in place,
 i.e. before roof closes**.  

* **roof_control_functions.py** - Equivalent to the 'intelligent_roof_controller_functions'
 script written in PHP on the gateway machine. Responsible for the low level
 communication with the PLC box. Added a function to get the information
 containing the tilt bits, but not tested. Error codes are taken from
 dictionaries in the settings_and_error_code.py script.  

* **settings_and_error_codes.py** - Somewhere to keep all the error code 
 definitions, timeouts, etc so you don't need to go hunting through all the code
 to find them. Plus, if they are used multiple times, only have to change them 
 once. Can try to make error codes unique.  
 
* **specify_roof_state.py** - Use this to supply a new roof state
 to plcd. Can be either 'o' to open, 'c' to close or 's' to stop the roof.

* **tcs_control.py** - Contains the functions that interact with the TCS 
 machine. Uses the module subprocess.py to SSH directly to the TCS and pass the
 required commands.  


* **update_point_off.py** - Contains functions for handling moving the pointing 
 offsets between the reduction processes and the observing processes using a 
 memory mapped file. The ```read_offset_values function``` allow the currently 
 stored offsets to be read (returning zero if they cannot be read) and the 
 ```update_offset_values``` allows the values to be stored in the memory map.  


#### Unit test scripts

* **TO RUN TESTS** from the main xamidimura directory, use the following:
	
	- To run all tests scripts in the directory, use 
		```
		>python -m unittest discover .
		```
	- To run specific file of tests e.g. test_roof_control_functions.py
		```
		> python -m unittest tests.test_roof_control_functions
		```
	- To run a specific test class e.g. test_set_hex_bit
	```
	> python -m unittest tests.test_roof_control_functions.test_set_hex_bit
	```
	- To run one specific test in a test class e.g. test_set_bit_5
	```
	> python -m unittest tests.test_roof_control_functions.test_set_hex_bit.test_set_bit_5
	```

* **test_fits_file_handler.py** Contains the test for the script that copies
 files from the das machines. Currently not all functions are tested, but all
 the base functions are.  
	
* **test_focuser_control.py** - Unit tests for the focuser_control functions.  

* **test_ifw_control.py** Contains unitest for filter wheel control functions.  

* **test_observing.py** Only partly written... Will contain the test for the 
 main observing script.

* **test_plc_interaction_func.py** Contains the unit tests for the plc 
 interaction functions.  

* **test_plcd.py** Not yet complete. Tests all the function that are used by the
 main functions, but doesn't yet test the main function. Has been tested on the 
 roof and currently works  

* **test_roof_control_functions.py** Provides test for the functions contained 
 in the roof_control_functions.py script.
               

## Observing recipes

* So far one example 'test_target_single_Texp.obs', in the obs_recipes folder. 
 Eventually have one for each target.  
* Each file named with the target name.
* Perhaps have a 'standard' recipe, which will be used if no recipe is found for
 a particular target.  
* Some information still need to be sorted out e.g the IMG-RA/DEC values and how
 to store the comparison information.  

#### Observing recipe parameters
* **FILTERS** - A list of the filter names to be used in the observing pattern 
 for either telescope.  
* **EXPTIME** - A list of exposure times. The same exposure times will be used 
for simultaneous exposures on the North and South telescope. This list should 
be the same length as N_PATT and S_PATT
	
	```
	FILTERS RX, GX, BX  
	EXPTIME 1, 2, 3
	``` 
	 
 then the RX filter will have an exposure time of 1 seconds, the GX filter an 
 exposure time of 2 seconds and the BX filter an exposure time of 3 seconds.  
* **FOCUS_POS** - A list of ideal focus positions for each filter. (works same 
way as exposure times)  

* **N_PATT** - Use (array) element number to reference the pattern of filters 
 to be used for the north telescope. e.g. if

	```
	FILTERS RX, GX, BX
	N_PATT 0,0,0,1,1,1,2,2,2
	```  

	the observing pattern will be ```RX,RX,RX,GX,GX,GX,BX,BX,BX```. The focus 
	position will also do something similar.  For the exposure times a list such
	as ```1,1,1,2,2,2,3,3,3''' should be stated for the above observing 
	pattern, but this will be the same pattern used for the South telescope.
	
* **S_PATT** - Same as N_PATT but for south telescope.

* **DOFFIELD** - Y/N, whether or not to flat-field images during processing.

## Observing.py

As mentioned will contain the main functions to carry out the observing, and 
other functions required by this main function.

### Things it will currently do
- Currently can create fits file with only header information, store an 
 observing record in the obslog2 table in the xamidimura database. The next file
 number is obtained by looking for the last used number in the directory where 
 files are saved and adding 1. Files are sorted into folders based on the date
 at the start of the evening. Files stored under date of previous evening until
 9am UTC.  

- When the observing recipe is loaded, it takes the User defined patterns 
 (N_PATT, S_PATT) and populates it with the required filters, exposure times, 
 focus positions. Thought this would be the least effort for a user. A full list
 of exposure times to match the obseerving pattern is required as the same time 
 will for an exposure on both the North and South telescopes.  

- Image type is decided based on the first 4 letters of the target name e.g. 
 BIAS, FLAT, DARK, THER. If it doesn't match these three then it will assume it 
 is a object frame. This way can have multiple BIAS/FLAT/DARK/THERMAL targets in 
 the target info database and observing recipes. Requests for DARK frames will 
 be passed as THERMAL to the TCS. 

- The code will pair exposure requests for the North and South telescope. 
 Requests to change the filters are done asynchronously, so one telescope does 
 not need to wait for the other filter change to be complete. As the exposure
 time are the same for both telescopes, the code only refers to the exposure 
 pattern for the North telescope. The code will loop through the observing 
 pattern. A status flag will be obtained for each exposure, both North and 
 South. Need to workout how best to repeat the observing pattern.  

- **The code to change filter is not currently active**  

- The code waits for a response from the TCS after initially sending the 
 exposure command, and then waits for the require exposure time. Need to do it 
 this way, otherwise the function would time out for long exposures.  

- Timeout on TCS is currently 60 seconds.  

- Code to request TCS exposure is in place but needs to be tested. Need the 
 code to handle a weather interuption, etc.    

- Valid response code from TCS are: 
	``` 
	0 = message received, exposure started  
	1 = exposure started, but ccd temperature is greater than -20 degrees.
	-3 = message received by TCS but exposure not started
	```  
	   
- If no response is received from the TCS, status is set to -5

- Other status flags:  
	``` 
	-1 = Exposure interupted from weather alert
	-2 = Exposure interupted non weather reason
	-4 = Unexpected response from TCS
	-6 = Problem with filter wheel (code not active)
	```  
Status codes are defined in settings_and_error_codes.py.

The cooling on the cameras is started and stopped at the beginning/end of the 
 main function, if run_camera_cooling is set to True in settings_and_error_codes.py

The code for the interuptions needs to be written.  
	
- Exposure requests that are not completed (due to weather alert, TCS timeout 
 etc) are noted in the observing log table, by fits headers are not saved. 

- Started working on the code to load target information from the database, 
 not completed. 

- Some unit tests have been created for the telescope slewing and some of the 
 exposure functions, but not yet complete.  