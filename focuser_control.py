"""
focuser_control.py
Jessica A. Evans
22/10/18

 29/10/18 - Contains all the serial-port control functions for the focusers, currently excludes the commands that set various configuration settings. Need to decide if these will be needed...

"""
"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FOCUSER CONTROL FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import common
import serial
import logging

#def __main__():
	#**** Will need to be put somewhere better eventually
logging.basicConfig(filename = 'logfiles/focuser.log',filemode='w',level=logging.INFO, format='%(asctime)s  %(levelname)s %(message)s')

def check_config_port_values_for_focuser(config_dict):
	"""
		Check that the values specified in the config file match what is expected by the filter wheel manual,
	 includes checks for the baud rate, data bits, stop bits and parity
	 
	 PARAMETERS
	 
	 config_file = the config file wth the parameters to be tested
	 
		"""
	
	# BAUD RATE
	if 'baud_rate' in config_dict.keys():
		if config_dict['baud_rate'] != 115200:
			logging.critical('Unexpected baud rate for focuser, 115200 is expected')
			raise ValueError('Unexpected baud rate for focuser, 115200 is expected')
	else:
		logging.critical('No baud rate found in config file.')
		raise KeyError('No baud rate found in config file.')
	
	# DATA BITS
	if 'data_bits' in config_dict.keys():
		if config_dict['data_bits'] != 8:
			logging.critical('Unexpected number for data bits, 8 is expected')
			raise ValueError('Unexpected number for data bits, 8 is expected')
	else:
		logging.critical('No data bits number found in config file')
		raise KeyError('No data bits number found in config file')
	
	# STOP BITS
	if 'stop_bits' in config_dict.keys():
		if config_dict['stop_bits'] != 1:
			logging.critical('Unexpected number for stop bits, 1 is expected')
			raise ValueError('Unexpected number for stop bits, 1 is expected')
	else:
		logging.critical('No stop bits number found in config file')
		raise KeyError('No stop bits number found in config file')
	
	
	# PARITY
	if 'parity' in config_dict.keys():
		if config_dict['parity'] != 'N':
			logging.critical('Unexpected parity values, "N" is expected')
			raise ValueError('Unexpected parity values, "N" is expected')
	else:
		logging.critical('No parity values found in config file')
		raise KeyError('No parity values found in config file')


def get_start_end_char(command):
	"""
	The focuser requires a '<' at the begining and a '>' at the end of each command. This function will
	 add these to any string passed by 'command'.
	 
	PARAMETERS:
	
		command - the string command to which <> will be added.
		
	RETURN
	
		full_command - the full command
		
	"""

	full_command = '<'+str(command)+'>'
	return full_command

def check_focuser_no(x):
	
	"""
		Most of the commans for the focuser require the focuser number to be sent. This can either be
	 set to '1' or '2'. This function just makes sure that a valid number is sent.
	 
	 PARAMETERS:
	 
		x =  the focuser number to be checked.
		"""
	
	valid_focuser_number = [1,2]
	if x not in valid_focuser_number:
		logging.error(str(x) + ' is not a valid focuser number.')
		raise ValueError(str(x) + ' is not a valid focuser number.')
	else:
		return x

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
These assume two focusers connected to one controller, use 'x' parameter to select which one,
	1=South, 2=North
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def get_focuser_name(x, port):
	"""
	Will return the user defined nickname for focuser number 'x'.
	
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		
	RETURN:
		message = name for the focuser or a error message
	
	"""
	command = get_start_end_char('F'+str(check_focuser_no(x))+'HELLO')

	message = common.send_command_two_response(command, port)

	return message

def halt_focuser(x, port):
	"""
	Get focuser 'x' to stop its current motion. If Temperature Compensation was active, it becomes
	 deactived
	 
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
	
	"""

	command = get_start_end_char('F'+str(check_focuser_no(x))+'HALT')
	
	message = common.send_command_two_response(command, port)

	if message == 'HALTED':
		logging.info('Motion of Focuser '+str(x)+' HALTED')

def home_focuser(x, port):
	"""
	Ask focuser 'x' to begin homing routine. Controller will respond with 'H' to indicate it has 
	 started the homing proceedure.
	
	*** Should probably get something to check that it's stopped moving *****

	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
	
	"""
	command = get_start_end_char('F'+str(check_focuser_no(x))+'HOME')

	message = common.send_command_two_response(command, port)

	if message == 'H':
		logging.info('Focuser '+str(x)+ ' moving to home')


def center_focuser(x, port):

	"""
	Ask focuser 'x' to move to the center of it's travel. this is defined as being half the focusers max position. The max position is defined by the device type that is selected???. Controller will respond with 'M' to indicate it has started moving.
	
	*** Should probably get something to check that it's stopped moving *****
	
	PARAMETERS:
		
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		
	"""
	command = get_start_end_char('F'+str(check_focuser_no(x))+'CENTER')

	message = common.send_command_two_response(command, port)

	if message == 'M':
		logging.info('Focuser '+str(x)+ ' moving to center')


def move_to_position(pos, x, port):


	"""
	Ask focuser 'x' to move to the position specifiedby 'pos'. Must be between 0 and the focuser's maximum position (112000). The controller will respond with 'M' when it starts moving.
	
	This function will provide the necessary formating to the 'pos' parameter
	
	*** Should probably get something to check that it's stopped moving *****
	
	PARAMETERS:
	
	pos = integer in range 0 to focuser max position (112000), to which the focuser will move.
	x = 1 or 2 depending on the which focuser the command is for
	port = the open port for communicating with the focuser
	
	"""
	x = str(check_focuser_no(x))
	
	if pos > 112000 or pos < 0:
		logging.error(str(pos)+ ' is an invalid position for focuser ' + x)
		raise ValueError(str(pos)+ ' is an invalid position for focuser ' + x)
	

	format_pos = '{0:>06}'.format(pos)

	command = get_start_end_char('F'+ x +'MA'+format_pos)

	message = common.send_command_two_response(command, port)

	if message == 'M':
		logging.info('Focuser '+str(x)+ ' moving to position: '+ format_pos)

def move_focuser_in(x, port, move_speed=1):
	"""
	Ask focuser 'x' to move inwards (i.e. away from max position of 112000). Focuser will continue to move until a 'end_relative_move' command is received or it reaches the end of it's travel.
		
	*** Should probably get something to check that it's stopped moving *****
		
		PARAMETERS:
		
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		move_speed = 0 or 1, 0 for high speed, 1 for low speed
		
	"""
	valid_speeds = [0,1]
	if move_speed not in valid_speeds:
		logging.error(str(move_speed) + ' is not a valid move speed. 0 = High, 1 = low.')
		raise ValueError(str(move_speed) + ' is not a valid move speed. 0 = High, 1 = low.')
		
	else:
		x = str(check_focuser_no(x))
		command = get_start_end_char('F'+ x +'MIR'+str(move_speed))
		message = common.send_command_two_response(command, port)

		if message == 'M':
			logging.info('Focuser '+str(x)+ ' moving inwards')


def move_focuser_out(x, port, move_speed=1):
	"""
		Ask focuser 'x' to move outwards (i.e. towards the max position of 112000). Focuser will continue to move until a 'end_relative_move' command is received or it reaches the end of it's travel.
		
		*** Should probably get something to check that it's stopped moving *****
		
		PARAMETERS:
		
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		move_speed = 0 or 1, 0 for high speed, 1 for low speed
		
		"""
	valid_speeds = [0,1]
	if move_speed not in valid_speeds:
		logging.error(str(move_speed) + ' is not a valid move speed. 0 = High, 1 = low.')
		raise ValueError(str(move_speed) + ' is not a valid move speed. 0 = High, 1 = low.')

	else:
		x = str(check_focuser_no(x))
		command = get_start_end_char('F'+ x +'MOR'+str(move_speed))
		message = common.send_command_two_response(command, port)
		
		if message == 'M':
			logging.info('Focuser '+str(x)+ ' moving outwards')

def end_relative_move(x, port):

	"""
	Will get focuser 'x' to stop any relative motion. It should respond with 'STOPPED' when complete. 
	 If it was previously running, Temperature compensation will be resumed after the command is issued.
	 
	 PARAMETERS:
		
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
	
	"""
	x = str(check_focuser_no(x))
	command = get_start_end_char('F'+ x +'ERM')
	message = common.send_command_two_response(command, port)
		
	if message == 'STOPPED':
		logging.info('Focuser '+str(x)+ ' motion stopped.')

def get_focuser_status(x, port):
	"""
	***** NEEDS TESTING *****
	
	Will get focuser 'x' to display its current status. Should start with the line 'STATUSx' where x will be the focuser number, and finish with the line 'END'.
	
	
	
	INFO IN STATUS MESSAGE: (from manual)
	
	Temp(C): The current temperature in degrees Celisus
	
	Curr Pos: The current position of the specified focuser
	
	Target Pos: The absolute position that the device is currently moving to (if the device is moving)
	
	IsMoving: This flag is set to 1 if the device is moving and 0 if the device is stationary
	
	IsHoming: This flag is set 1 while the device is homing and zero otherwise.
	
	IsHomed: For focusers that support homing, this flag will be set to 0 if the focuser has not been homed and set to 1 when homed.
	
	FFDetect: Set to 1 when using an Optec FastFocus Focuser
	
	TmpProbe: This flag indicates the status of an attached temperature probe. A value of 1 means a probe is attached, 0 means no probe is detected.
	
	RemoteIO: This flag indicates the status of an attached In/Out remote. A value of 1 means a remote is attached, 0 means no remote is detected.
	
	Hnd Ctrlr: This flag indicates the status of an attached hand controller. A value of 1 means a hand controller is attached, 0 means no hand controller is detected.

	 
	PARAMETERS:
		
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		
	"""
	x = str(check_focuser_no(x))
	command = get_start_end_char('F'+ x +'GETSTATUS')
	message = common.send_command_two_response(command, port, expected_end='END\n')

	return message

def get_focuser_stored_config(x, port):
	"""
	***** NEEDS TESTING *****
	
	Will get the controller to report the configuation setting for focuser 'x'. Should start with the line 'CONFIGx' where x will be the focuser number, and finish with the line 'END'.
	
	INFO IN CONFIG MESSAGE: (from manual)
	
	Nickname: The user-defined nickname of the specified focuser
	
	MaxPos: The maximum absolute position that the selected focuser is capable of moving to. This setting is determined automatically based on the selected Device Type.
	
	Dev Typ: A two character designator of the currently set device type for the specified focuser. See the section entitled ppendix A – Device Types on page 17 for device type details.
	
	TComp ON: The current status of temperature compensation. 1 indicates the device is currently temperature compensating, 0 indicates temperature compensation is disabled.
	
	TemCo A-E: These items indicate the temperature coefficient for the respective temperature compensation mode. The units of the temperature coefficients are stepper motor steps per degree.
	
	TC Mode: Indicates the currently selected temperature compensation mode. When temperature compensation mode is turned on this value selected mode indicates which temperature coefficient will be used for compensation.
	
	BLC En: This flag indicates whether the internal backlash compensation is turned on or off. A value of 1 indicates that this feature is turned on, 0 indicates the feature is off.
	
	BLC Stps: This value indicates the number of steps that the focuser will travel past the target position before returning to the target position in order to compensate for mechanical backlash in the focusing device. A positive value indicates the compensation will occur when the focuser move to a greater absolute position. A negative value indicates the compensation will occur on moves to a lesser position. LED Brt: This value indicates the current setting for the brightness of the red power LED on the FocusLynx controller enclosure
	
	TC@Start: This value indicates if the Temperature Compensate at Start feature is turned on or off. A value of 1 indicate the feature is on, 0 indicates the feature is off. When this feature is enabled the device will automatically perform a temperature compensation move immediately following device power-up.
	
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
	
	"""
	
	x = str(check_focuser_no(x))
	command = get_start_end_char('F'+ x +'GETCONFIG')
	message = common.send_command_two_response(command, port, expected_end='END\n')
	
	return message


def set_device_name(x, port, device_name):
	"""
	Use to set a new nickname for focuser 'x'. Controller will respond with 'SET' once complete.
	
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		device_name = string with new name. Max 16 char
	
	"""

	# check the length of the new device nickname
	name_length = len(device_name)
	if name_length > 16 or name_length < 0:
		logging.error('Invalid device name given')
		raise ValueError('Invalid device name given')

	else:
		x = str(check_focuser_no)
		command = get_start_end_char('F'+ x +'SCNN'+str(device_name))
		message = common.send_command_two_response(command, port)

		if message == 'SET':
			logging.info('Name for Focuser '+str(x)+ ' set as: ' + str(device_name))

"""
	#Might be used for testing the status setup
	STATUS1\nTemp(C)  = +21.7\nCurr Pos = 108085\nTarg Pos = 000000\nIsMoving = 1\nIsHoming = 1\nIsHomed  = 0\nFFDetect = 0\nTmpProbe = 1\nRemoteIO = 0\nHnd Ctlr = 0\nEND
"""