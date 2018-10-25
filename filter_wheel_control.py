
"""
filter_wheel_control.py
Jessica A. Evans
15/10/18

	Numerous function to control the operations of the filter wheels. 
	
	22/10/18 - So far has all the commands that are laid out in the manual for the ifw filter wheel.
			 - Some functions need checking
			 - Want to integrate some form of logging into the functions, currently just print to screen
			 - Need to create some test to make sure it all works
			 - Make sure that it's raising suitable errors/logging them - I think sometimes its just printing
				to screen
"""
"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FILTER WHEEL CONTROL FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import common
import serial
import logging


logging.basicConfig(filename = 'logfiles/filter_wheel.log',filemode='w',level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def check_config_port_values_for_ifw(config_dict):
	"""
	Check that the values specified in the config file match what is expected by the filter wheel manual,
	 includes checks for the baud rate, data bits, stop bits and parity
	 
	 PARAMETERS
	 
	 config_file = the config file wth the parameters to be tested
	 
	"""
	
	# BAUD RATE
	if 'baud_rate' in config_dict.keys():
		if config_dict['baud_rate'] != 19200:
			raise ValueError('Unexpected baud rate for ifw filter wheels, 19200 is expected')
	else:
		raise KeyError('No baud rate found in config file')
	
	# DATA BITS
	if 'data_bits' in config_dict.keys():
		if config_dict['data_bits'] != 8:
			raise ValueError('Unexpected number for data bits, 8 is expected')
	else:
		raise KeyError('No data bits number found in config file')
	
	# STOP BITS
	if 'stop_bits' in config_dict.keys():
		if config_dict['stop_bits'] != 1:
			raise ValueError('Unexpected number for stop bits, 1 is expected')
	else:
		raise KeyError('No stop bits number found in config file')
	
	
	# PARITY
	if 'parity' in config_dict.keys():
		if config_dict['parity'] != 'N':
			raise ValueError('Unexpected parity values, "N" is expected')
	else:
		raise KeyError('No parity values found in config file')

def initialise_ifw_serial_connection(config_dict):
	"""
	*** Not tested and probably not complete (18/10/18) ***
		
	The ifw filter wheels require initialisaton before they will accept any further commands. The initialise
	 requires the command 'WSMODE' to be sent and a '!' to be received.
	 
	 This function should carry out the require initialisation.
	 
	 PARAMETERS
	 
		config_dict = dictionary containing the configuration files for a filter wheel, so that a port
		can be opened using correct details.
		
	 RETURN
		
		initial_port = the port that is opened and initialised. Can be used later to send other commands
		to the filter wheel. Will need to be closed when all communication is finished with the ???
		function
		
	"""
	initialise_command = b'WSMODE'
	expected_return = '!\r\n'
	
	# Open a port
	initial_port = common.open_port_from_config_param(config_dict)
	#Send initialising command 'WSMODE' in bytes (indicated by the 'b')
	initial_port.write(initialise_command)#.encode('utf-8'))
	
	# Expecting a '!' followed by a CR/LF if succesfully received
	read_bytes = initial_port.read(size=3)
	no_of_attempts = 1
	
	# The controller can timeut if only a partial command is received, so try upto
	#  3 times if it failed the first time
	while read_bytes != expected_return:
		initial_port.write(initialise_command)#.encode('utf-8'))
		read_bytes = initial_port.read(size=3)
		no_of_attempts +=1
		if no_of_attempts == 3:
			raise Exception('Failed to initialise after 3 attempts..')
			break

	if read_bytes == expected_return:
		print('Filter wheel initialisation complete')
	
	return initial_port

def form_filter_names_string_from_config_dict(config_dict):
	"""
	Takes the names that are assigned to the filter IDs (A,B,C,D,E) in the config file and combines them
	 to produce a 40 char string that can be passed to the filter wheel's EEPROM.
	 
	 A limited number of characters are permitted and are shown below
		
		0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ=.#/-% and a space
		
	All names must be less than 8 charachers long. The function will check the name length and
		
	PARAMETERS
		
		config_dict = contains the names associated with the 5 filters IDs.
		
	RETURN
		
		final_string =  A string of 40 characters that will be used to program the EEPROM. Each group
		of 8 chars will be used as a filter name.
		
	"""
	valid_chars = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D',
				   'E','F','G','H','I','J','K','L','M','N','O','P','Q','R',
				   'S','T','U','V','W','X','Y','Z','=','.','#','/','-','%', ' ']
		
	#So far this creates a tuple of names assign to each ID from the config file.
	extracted_names = [config_dict['A'], config_dict['B'],config_dict['C'], config_dict['D'], config_dict['E']]
				   
	final_string = str()
				   
	# Check each name contains valid characters
	all_valid_bool = True
	for name in extracted_names:
		for letter in name:
			valid_letter_bool = letter in valid_chars
			if valid_letter_bool == False:
				all_valid_bool = False
				raise ValueError(letter+' in the name '+ name + ' is not a valid character. Please only use "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ=.#/-% or a space"')
		if len(name) > 8 or len(name) <=0:
			all_valid_bool = False
			raise ValueError('One of the names is too long or too short. Must be  <8 but >0')
			
		final_string += '{: <8}'.format(name)

	return final_string



def pass_filter_names(str_of_40chars, initialised_port, wheel_ID = 'A'):
	"""
		****************************
		**** NEEDS TO BE TESTED ****
		****************************
		
	Pass a formatted string of 40 characters (which contains the names for the filters) to the EEPROM
	 on board the filter wheel.
	 
	 Must wait at least 10 ms for the names to be stored before another command can be sent, that will
	 be handle by this function. A '!' character is return if the names are successfully received
	 and stored.
	 
	 If ER=3 is returned, it means an invalid wheel ID was received. (Valid options: 'A','B','C','D','E')
	 
	 PARAMETERS
	 
		str_of_40chars = A string of 40 chars containing the 5 filter names, in groups of 8 chars.
		wheel_ID = **NOT TOO SURE** Indicates what position the names will be applied from. Is 'A'
		by default because of how the from_filter_names_string_from_config_dict() function extracts
		the names
		
		
		"""
	valid_wheel_ID = ['A','B','C','D','E']
	if wheel_ID not in valid_wheel_ID:
		raise ValueError('Invalid wheel ID. Please select A,B,C,D or E')
	else:
		
		issue_command = 'WLOAD'+wheel_ID+'*'+str_of_40chars
		expected_return = '!'
		#print(issue_command)
		#print(expected_return)
		
		message = common.send_command_get_response(issue_command, initialised_port)
		
		if message == expected_return:
			print('Filter names successfully stored')
		elif message == 'ER=3':
			raise ValueError('ER=3: Improper value received for wheel ID. Please see manual for more info.')
		else:
			raise Exception(message)


def get_stored_filter_names(initialise_port, formatted_dict = True):
	
	"""
		****************************
		**** NEEDS TO BE TESTED ****
		****************************
		
	Will read the 40 character string containing the filter names from the filter wheel, and either returned
		as a dictionary with the names assign to the keys A,B,C,D,E or return as the 40 char string
		
	PARAMETERS
		
		initialised_port = the opened initialised port to the filter wheel.
	
		formatted_dict = If true, the names will be returned as a dictionary, otherwise just a string of 40
			characters
		
	REUTRN
		
		new_dict or name_string depending on 'formatted_dict' parameter
				will be 40 char string if formatted_dict is False
				and a dictionary if it's se to True
		
	"""
	
	issue_command = 'WREAD'
	name_string = common.send_command_get_response(issue_command, initialised_port)
	
	if formatted_dict == True:
		name_list = [name_string[i:i+8].strip() for i in range(0,len(name_string), 8)]
		key_letters = ['A','B','C','D','E']
		new_dict = {}
		for n in range(0,key_letters):
			new_dict[key_letters[n]] = name_list[n]
		
		return new_dict
	
	else:
		return name_string


def get_current_position(initialised_port):
	"""
		****************************
		**** NEEDS TO BE TESTED ****
		****************************
	Will return the current position of the filter wheel (i.e. 1,2,3,4,5)
		
	PARAMETERS
		
		initialised_port = an open initialised serial port to the filter wheel
		
	RETURN
		
		filter_pos = Integer in the range 1...5.
	"""
	
	pos_command = 'WFILTR'
	pos = int(common.send_command_get_response(pos_command,initialised_port))
	
	return pos

def get_current_ID(initialised_port):
	"""
		****************************
		**** NEEDS TO BE TESTED ****
		****************************
	Will return the current filter ID (i.e A,B,C,D,E)
		
	PARAMETER
		
		initialised_port = an open initialised port to the filter wheel.
		
	RETURN
		
		filter_id = A,B,C,D or E as appropriate.
		
	"""
	id_command = 'WIDENT'
	id = common.send_command_get_response(id_command,initialised_port)
	
	return id

def get_current_filter_position_and_name(initialised_port):
	"""
	Use this to return the current position of the filter wheel (1,2,3,4,5) and the identity of the
	 filter wheel (A,B,C,D,E)
	 
	 PARAMETERS
		initialised_port = A serial port to the filter wheel that has been opened and initialised.
		
	RETURN
		[identity, position] = list containing the filter-ID (A,B,C,D, or E) and filter position
	
	"""
	identity = get_current_ID(initialised_port)
	position = get_current_position(initialised_port)
	
	return [identity,position]


def goto_home_position(initialised_port, return_home_id = False):
	
	"""
		****************************
		**** NEEDS TO BE TESTED ****
		****************************
		
	Will make the wheel find position 1 and identify the filter wheels. Will load filter names from EEPROM
	 Can take up to 20 secs to complete the HOME function.
	 
	 PARAMETER
	 
		initialised_port = an open initialised port to the filter wheel
		
	"""
	valid_wheel_ID = ['A','B','C','D','E']
	
	home_command = 'WHOME'
	return_message = common.send_command_get_response(home_command,initialised_port) #will need to check this is waiting a good amount of time.
	
	# There are tw possible error messages according to the manual: ER=1, and ER=3. Just in case will check
	#  the code has returned a valid ID to identify the home position. If not assume that it's an error and
	#  raise an exception...
	if return_message == 'ER=1':
		print('ER=1. WARNING! Number of steps to find position 1 > 2600. See manual for details.')
	elif return_message == 'ER=3':
		print('ER=3. Filter ID not found successfully.')
	elif return_message in valid_wheel_ID:
		print('Filter ID: ' +return_message+' set as home position, at position 1')
	else:
		raise Exception(return_message)
	
	if return_home_id == True:
		return return_message


def goto_filter_position(new_position, initialised_port):
	
	"""
		****************************
		**** NEEDS TO BE TESTED ****
		****************************
		
	Will move to the filter position 'new_position'.
		
	PARAMETERS:
		
		new_position = the position to move to. An integer from the list [1,2,3,4,5]
		
		initialised_port = an open initialised port to the filter wheel
		
		
	"""
	
	move_command = 'WGOTO'+str(new_position)
	expected_return = '*'
	valid_positions = [1,2,3,4,5]
	
	if new_position not in valid_positions:
		raise ValueError(new_position+' is not a valid position number')
	else:
		return_message = common.send_command_get_response(move_command,initialised_port)
		
		if return_message == expected_return:
			print('Filter change successful. Current position: '+new_position)
		elif return_message == 'ER=4':
			print('ER=4. WARNING! wheel stuck in position, or moving slowly.')
		elif return_message == 'ER=5':
			raise ValueError('ER=5. Invalid position supplied')
		elif return_message == 'ER=6':
			print('ER=6. WARNING! wheel slipping and taking too many step to next position')
		else:
			raise Exception(return_message)

def end_serial_communication_close_port(initialised_port):
	"""
	executes the command to stop the communication with the filter wheel and then close the serial port.
	
	PARAMETERS:
	
		initialised_port = an open initialised port to the filter wheel.
	
	"""
	exit_command = 'WEXITS'
	expected_return	= 'END'

	return_message = common.send_command_get_response(exit_command, initialised_port)
	if return_message == expected_return:
		print('Communication with filter wheel: Closed')
		initialised_port.close()
	else:
		print('Warning! communication not closed')



"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Group OBSERVING FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""