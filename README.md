# xamidimura
Documentation and software for the Xamidimura telescopes  


## Folders
* **configs** - Contains configuration files for the filter wheels and focusers (currently only one filter wheel file and one focuser present).  

* **database** - Contains the sqlite database 'xamidimura.db' which [so far] contains the observing log table 'obslog2'. Other tables could be added later, and the location is not set in stone.  

* **fits_file_tests** - A location to store the fits headers that are created. Again location can be moved later if necessary.  
	
* **logfiles** - Where logfiles from the different scripts are stored. (logfiles currently overwritten each time scripts are run.) Now contains weather.log as an example of how the weather information will be stored.  

* **obs_recipes** - Suggestion for where the observing recipes are kept.  


## Files
* **common.py** - contains function that are useful to both focuser and filter wheel control.  

* **connect_database.py** - functions to connect to a sqlite database, and do useful thing like see what rows are in the database, convert it to a pandas dataframe (will be useful for manipulating). To be updated and adapted when extra functions are needed.  

* **filter_wheel_control.py** - contains basic serial port command functions for the filter wheels.  

* **focuser_control.py** - basic serial port commands for the focusers.  

* **observing.py** - Will contain the main functions to carry out the observing, and other functions required by this main function. Currently can create fits file with only header information, store an observing record in the obslog2 table in the xamidimura database. No unit tests created yet.  


	



#### Unit test scripts	  
* **ifw_test.py** - contains unitest for filter wheel control functions (All functions tested apart from initialisations function). In a terminal use "python ifw_test.py" to run.  
	
* **test_focuser_control.py** - Unit tests for the focuser_control functions.  
               

## Observing recipes

* So far one example 'test_target.obs', in the obs_recipes folder. Eventually have one for each target.  
* Each file named with the target name.
* Perhaps have a 'standard' recipe, which will be used if no recipe is found for a particular target.  
* Some information still need to be sorted out e.g the IMG-RA/DEC values and how to store the comparison information.  

#### Observing recipe parameters
* **FILTERS** - A list of the filter names to be used in the observing pattern for either telescope.  
* **EXPTIME** - A list of exposure times that correspond to each filter, e.g. if 
 ```FILTERS RX, GX, BX  
 EXPTIME 1, 2, 3```  
 then the RX filter will have an exposure time of 1 seconds, the GX filter an exposure time of 2 seconds and the BX filter an exposure time of 3 seconds.  
* **FOCUS_POS** - A list of ideal focus positions for each filter. (works same way as exposure times)  

* **N_PATT** - Use (array) element number to reference the pattern of filters to be used for the north telescope. e.g. if ```FILTERS RX, GX, BX  N_PATT 0,0,0,1,1,1,2,2,2```  
	the observing pattern will be ```RX,RX,RX,GX,GX,GX,BX,BX,BX```  
	
* **S_PATT** - Same as N_PATT but for south telescope.

* **DOFFIELD** - Y/N, whether or not to flat-field images during processing.

## Observing.py

As mentioned will contain the main functions to carry out the observing, and other functions required by this main function.

### Things it will currently do
- Currently can create fits file with only header information, store an observing record in the obslog2 table in the xamidimura database. The next file number is obtained by looking for the last used number in the directory where files are saved and adding 1.  

- When the observing recipe is loaded, it takes the User defined patterns (N_PATT, S_PATT) and populates it with the required filters, exposure times, focus positions. Thought this would be the least effort for a user.  

- Image type is decided based on the first 4 letters of the target name e.g. BIAS, FLAT, DARK. If it doesn't match these three then it will assume it is a science frame. This way can have multiple BIAS/FLAT/DARK targets in the target info database and observing recipes.  

- For one 'pattern' of exposures, i.e. one complete loop of N_PATT or S_PATT, the code will send request for an exposure to each telescope and get a status flag as a response. It uses asynchronous running to send the exposures, so one telescope does not need to wait for the other telescope to finish it's exposure before sending the new exposure request. During a pattern loop each telescope can take exposures independently. Need to workout how best to repeat the pattern.  

- **The code to change filter is not currently active + needs testing**  

- The code waits for a response from the TCS after initially sending the exposure command, and then waits for the require exposure time. Need to do it this way, otherwise the function would time out for long exposures.  

- Timeout on TCS is currently 60 seconds.  

- **Need to put in code to actually send TCS exposure request**  

- Valid response code from TCS are: 
	``` 
	0 = message received, exposure started  
	1 = exposure started, but ccd temperature is greater that -20 degrees.
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

The code for the interuptions need to be written.  
	
- Exposure requests that are not completed (due to weather alert, TCS timeout etc) are noted in the observing log table, by fits headers are not saved.  

- No unit tests created yet.  