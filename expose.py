
import observing
import sys

"""
  
 INSTRUCTIONS FOR USE:
 
	- In a terminal, navigate to xamidimura directory will this code in.
	- Start Python
		> python
		
	- import the expose.py module using 
		>>> import expose
		
	Use 
		>>> expose.startup
	to start up the filterwheels, focusers and cameras etc.
	
	Use
		>>> expose.shutdown
	to shutdown the filterwheels, focusers and cameras.
	
	Use 
		>>> expose.expose
	to carry out an exposure. It will that the name of the target specified in
	 this script to load an observing recipe, and use the observing recipe to
	 decide what exposure number, lengths, filters to do.
	 
	Can use the expose function multiple times, but is does require the 
	filterwheels and focuser to have been set up previously.
	 
	Assumes that the telescope is already pointing in the correct direction.
	
	Each observing recipe is repeated once, each time expose.expose is called.
	
	Observing recipies are sorted in 
	"home/observer/xamidimura/xamidimura/obs_recipes/" 
	and are name as <target_name>.obs.
  
  
 Assume the observing recipe is called <target_name>.obs
 
 04/02/2019 - The observing.py is still very much work in progress, meaning
	that changes to that script could affect what works in this script. Will
	try to keep the observing.py file here in a working script, but there 
	could easily be bugs that creep in.
  
 
"""

target_name = 'test_target_single_Texp'
target_coords = ['10:46:04','-46:08:06']
target_type = 'TEST'

def startup():

	print('Starting up instruments and cameras')
	if obs.set_err_codes.run_camera_cooling == True:
		observing.tcs.camstart()
	observing.connect_to_instruments()

def expose():
	print('Exposing...')
	observing.basic_exposure(target_name,target_coords,target_type)

def shutdown():
	print('Shutting down instruments and cameras')
	observing.disconnect_database()
	observing.shutdown_instruments()
	if obs.set_err_codes.run_camera_cooling == True:
		observing.tcs.stopwasp()
