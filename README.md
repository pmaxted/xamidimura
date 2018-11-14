# xamidimura
Documentation and software for the Xamidimura telescopes  


## Folders
* **configs** - Contains configuration files for the filter wheels and focusers (currently only one filter wheel file and one focuser present).  

* **database** - Contains the sqlite database 'xamidimura.db' which [so far] contains the observing log table 'obslog2'. Other tables could be added later, and the location is not set in stone.  

* **fits_file_tests** - A location to store the fits headers that are created. Again location can be moved later if necessary.  
	
* **logfiles** - Where logfiles from the different scripts are stored. (logfiles currently overwritten each time scripts are run.) Now contains weather.log as an example of how the weather information will be stored.  


## Files
* **common.py** - contains function that are useful to both focuser and filter wheel control.  

* **connect_database.py** - functions to connect to a sqlite database, and do useful thing like see what rows are in the database, convert it to a pandas dataframe (will be useful for manipulating). To be updated and adapted when extra functions are needed.  

* **filter_wheel_control.py** - contains basic serial port command functions for the filter wheels.  

* **focuser_control.py** - basic serial port commands for the focusers.  

* **observing.py** - Will contain the main function to carry out the observing, and other functions required by this main function. Currently can create fits file with only header information, store and observing record in the obslog2 table in the xamidimura database. No unit tests created yet.  


	



#### Unit test scripts	  
* **ifw_test.py** - contains unitest for filter wheel control functions (All functions tested apart from initialisation function). In a terminal use "python ifw_test.py" to run.  
	
* **test_focuser_control.py** - Unit tests for the focuser_control functions.  
               
