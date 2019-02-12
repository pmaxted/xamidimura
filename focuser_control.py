"""
focuser_control.py
Jessica A. Evans
22/10/18

 02/01/19 - Contains all the serial-port control functions for the focusers, and
  the startup/shutdown functions


	CURRENT FUNCTIONS:
	----------------------------------------------------------------------
	Focuser Control
	----------------------------------------------------------------------
	- check_config_port_values_for_focuser(config_dict)
	
	- get_start_end_chars(command)
	
	- check_focuser_no(x)
	
	- get_focuser_name(x, port)
	
	- halt_focuser(x, port)
	
	- home_focuser(x, port)
	
	- center_focuser(x, port)
	
	- move_to_position(pos, x, port)
	
	- move_focuser_in(x, port, move_speed=1)
	
	- move_focuser_out(x, port, move_speed=1)
	
	- end_relative_move(x, port)

	----------------------------------------------------------------------
	Focuser Configuration/Status Functions
	----------------------------------------------------------------------

	- get_focuser_status(x, port)
	
	- get_focuser_stored_config(x, port)
	
	- set_device_name(x, port, device_name)
	
	- set_device_type(x, port, device_type = 'OB')
	
	- set_temp_comp(x, port, temp_comp=False)
	
	- set_temp_comp_mode(x, port, mode='A')
	
	- set_temp_comp_coeff(x, port, mode, temp_coeff_val)
	
	- set_temp_comp_start_state(x, port, temp_comp_start = False)
	
	- set_backlash_comp(x, port, backlash_comp = False)
	
	- set_backlash_steps(x, port, backlash_steps = 10)
	
	- set_LED_brightness(brightness, port)
	
	----------------------------------------------------------------------
	Group Observing Functions
	----------------------------------------------------------------------
	
	- focuser_initial_configuration(config_file_name, config_file_loc = 
		'configs/')
	
	- startup_focuser(config_file_name, config_file_loc = 'configs/')
	
"""
"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FOCUSER CONTROL FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import common
import serial
import logging
import time
import PLC_interaction_functions as plc
import settings_and_error_codes as set_err_codes

focus_logger = logging.getLogger(__name__)
focus_logger.setLevel(logging.INFO)
focusHand = logging.FileHandler(filename = set_err_codes.LOGFILES_DIRECTORY+\
						'focuser.log', mode = 'a')
focusHand.setLevel(logging.INFO)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s - '\
		'%(message)s','%Y-%m-%d_%H:%M:%S_UTC')
focusHand.setFormatter(formatter)
focus_logger.addHandler(focusHand)


def check_config_port_values_for_focuser(config_dict):
	"""
	Check that the values specified in the config file match what is expected 
	 by the filter wheel manual, includes checks for the baud rate, data bits, 
	 stop bits and parity
	 
	 PARAMETERS
	 
	 config_file = the config file wth the parameters to be tested
	 
	"""
	
	# BAUD RATE
	if 'baud_rate' in config_dict.keys():
		if config_dict['baud_rate'] != 115200:
			focus_logger.critical('Unexpected baud rate for focuser, 115200 is'\
				' expected')
			raise ValueError('Unexpected baud rate for focuser, 115200 is '\
				'expected')
	else:
		focus_logger.critical('No baud rate found in config file.')
		raise KeyError('No baud rate found in config file.')
	
	# DATA BITS
	if 'data_bits' in config_dict.keys():
		if config_dict['data_bits'] != 8:
			focus_logger.critical('Unexpected number for data bits, 8 is'\
				' expected')
			raise ValueError('Unexpected number for data bits, 8 is expected')
	else:
		focus_logger.critical('No data bits number found in config file')
		raise KeyError('No data bits number found in config file')
	
	# STOP BITS
	if 'stop_bits' in config_dict.keys():
		if config_dict['stop_bits'] != 1:
			focus_logger.critical('Unexpected number for stop bits, 1 is '\
				'expected')
			raise ValueError('Unexpected number for stop bits, 1 is expected')
	else:
		focus_logger.critical('No stop bits number found in config file')
		raise KeyError('No stop bits number found in config file')
	
	
	# PARITY
	if 'parity' in config_dict.keys():
		if config_dict['parity'] != 'N':
			focus_logger.critical('Unexpected parity values, "N" is expected')
			raise ValueError('Unexpected parity values, "N" is expected')
	else:
		focus_logger.critical('No parity values found in config file')
		raise KeyError('No parity values found in config file')


def get_start_end_char(command):
	"""
	The focuser requires a '<' at the begining and a '>' at the end of each 
	 command. This function will add these to any string passed by 'command'.
	 
	PARAMETERS:
	
		command - the string command to which <> will be added.
		
	RETURN
	
		full_command - the full command
		
	"""

	full_command = '<'+str(command)+'>'
	return full_command

def check_focuser_no(x):
	
	"""
	Most of the commans for the focuser require the focuser number to be
	 sent. This can either be set to '1' or '2'. This function just makes sure 
	 that a valid number is sent.
	 
	 PARAMETERS:
	 
		x =  the focuser number to be checked.
		"""
	
	valid_focuser_number = [1,2]
	if x not in valid_focuser_number:
		focus_logger.error(str(x) + ' is not a valid focuser number.')
		raise ValueError(str(x) + ' is not a valid focuser number.')
	else:
		return x

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
These assume two focusers connected to one controller, use 'x' parameter to 
	select which one, 1=South, 2=North
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def get_focuser_name(port, x=1):
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

def halt_focuser(port, x=1):
	"""
	Get focuser 'x' to stop its current motion. If Temperature Compensation was 
	 active, it becomes deactived
	 
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
	
	"""

	command = get_start_end_char('F'+str(check_focuser_no(x))+'HALT')
	
	message = common.send_command_two_response(command, port)

	if message == 'HALTED':
		focus_logger.info('Motion of Focuser '+str(x)+' HALTED')
	else:
		focus_logger.error('Response:'+message)

def home_focuser(port,x=1):
	"""
	Ask focuser 'x' to begin homing routine. Controller will respond with 'H' to
	 indicate it has started the homing proceedure.
	
	Need to first check that the telescope is stowed before homing...

	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
	
	"""
	
	#Need to check to make sure the telescope it stowed before homing the
	#  focusers. Focusers don't like trying to lift all the camera weight.
	
	tilt_stat = plc.plc_get_telescope_tilt_status()
	if tilt_stat['Tilt_angle'] == "6h East <= x < RA East limit" or \
		tilt_stat['Tilt_angle'] == "6h West <= x < RA West limit":
	
		command = get_start_end_char('F'+str(check_focuser_no(x))+'HOME')

		message = common.send_command_two_response(command, port)

		if message == 'H':
			focus_logger.info('Focuser '+str(x)+ ' moving to home')
		else:
			focus_logger.error('Response:'+message)
	else:
		focus_logger.error('Cannot home focuser, telescope is not parked')
		print('Cannot home focuser, telescope is not parked')

def center_focuser(port, x=1):

	"""
	Ask focuser 'x' to move to the center of it's travel. this is defined as 
	 being half the focusers max position. The max position is defined by the 
	 device type that is selected???. Controller will respond with 'M' to 
	 indicate it has started moving.
	
	*** Should probably get something to check that it's stopped moving *****
	
	PARAMETERS:
		
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		
	"""
	command = get_start_end_char('F'+str(check_focuser_no(x))+'CENTER')

	message = common.send_command_two_response(command, port)

	if message == 'M':
		focus_logger.info('Focuser '+str(x)+ ' moving to center')
	else:
		focus_logger.error('Response:'+message)

def move_to_position(pos, port, x=1):


	"""
	Ask focuser 'x' to move to the position specifiedby 'pos'. Must be between 
	 0 and the focuser's maximum position (112000). The controller will respond 
	 with 'M' when it starts moving.
	
	This function will provide the necessary formating to the 'pos' parameter
	
	*** Should probably get something to check that it's stopped moving *****
	
	PARAMETERS:
	
	pos = integer in range 0 to focuser max position (112000), to which the 
	focuser will move.
	x = 1 or 2 depending on the which focuser the command is for
	port = the open port for communicating with the focuser
	
	"""
	x = str(check_focuser_no(x))
	
	if pos > 112000 or pos < 0:
		focus_logger.error(str(pos)+ ' is an invalid position for focuser ' + x)
		raise ValueError(str(pos)+ ' is an invalid position for focuser ' + x)
	

	format_pos = '{0:>06}'.format(pos)

	command = get_start_end_char('F'+ x +'MA'+format_pos)

	message = common.send_command_two_response(command, port)

	if message == 'M':
		focus_logger.info('Focuser '+str(x)+ ' moving to position: '+ format_pos)
	else:
		focus_logger.error('Response:'+message)

def move_focuser_in(port, x=1, move_speed=1):
	"""
	Ask focuser 'x' to move inwards (i.e. away from max position of 112000). 
	 Focuser will continue to move until a 'end_relative_move' command is 
	 received or it reaches the end of it's travel.
		
	*** Should probably get something to check that it's stopped moving *****
		
		PARAMETERS:
		
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		move_speed = 0 or 1, 0 for high speed, 1 for low speed
		
	"""
	valid_speeds = [0,1]
	if move_speed not in valid_speeds:
		focus_logger.error(str(move_speed) + ' is not a valid move speed. 0 = '\
			'High, 1 = low.')
		raise ValueError(str(move_speed) + ' is not a valid move speed. 0 = '\
			'High, 1 = low.')
		
	else:
		x = str(check_focuser_no(x))
		command = get_start_end_char('F'+ x +'MIR'+str(move_speed))
		message = common.send_command_two_response(command, port)

		if message == 'M':
			focus_logger.info('Focuser '+str(x)+ ' moving inwards')
		else:
			focus_logger.error('Response:'+message)

def move_focuser_out(port, x=1, move_speed=1):
	"""
		Ask focuser 'x' to move outwards (i.e. towards the max position of 
		 112000). Focuser will continue to move until a 'end_relative_move' 
		 command is received or it reaches the end of it's travel.
		
		*** Should probably get something to check that it's stopped moving ****
		
		PARAMETERS:
		
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		move_speed = 0 or 1, 0 for high speed, 1 for low speed
		
		"""
	valid_speeds = [0,1]
	if move_speed not in valid_speeds:
		focus_logger.error(str(move_speed) + ' is not a valid move speed. 0 = '\
			'High, 1 = low.')
		raise ValueError(str(move_speed) + ' is not a valid move speed. 0 = '\
			'High, 1 = low.')

	else:
		x = str(check_focuser_no(x))
		command = get_start_end_char('F'+ x +'MOR'+str(move_speed))
		message = common.send_command_two_response(command, port)
		
		if message == 'M':
			focus_logger.info('Focuser '+str(x)+ ' moving outwards')

		else:
			focus_logger.error('Response:'+message)

def end_relative_move(port, x=1):

	"""
	Will get focuser 'x' to stop any relative motion. It should respond with 
	 'STOPPED' when complete. If it was previously running, Temperature 
	 compensation will be resumed after the command is issued.
	 
	 PARAMETERS:
		
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
	
	"""
	x = str(check_focuser_no(x))
	command = get_start_end_char('F'+ x +'ERM')
	message = common.send_command_two_response(command, port)
		
	if message == 'STOPPED':
		focus_logger.info('Focuser '+str(x)+ ' motion stopped.')

	else:
		focus_logger.error('Response:'+message)

def get_focuser_status(port, x=1, return_dict=False):
	"""
	Will get focuser 'x' to display its current status. Should start with the 
	 line 'STATUSx' where x will be the focuser number, and finish with the 
	 line 'END'.
	
	
	INFO IN STATUS MESSAGE: (from manual)
	
	Temp(C): The current temperature in degrees Celisus
	
	Curr Pos: The current position of the specified focuser
	
	Target Pos: The absolute position that the device is currently moving to 
		(if the device is moving)
	
	IsMoving: This flag is set to 1 if the device is moving and 0 if the device 
		is stationary
	
	IsHoming: This flag is set 1 while the device is homing and zero otherwise.
	
	IsHomed: For focusers that support homing, this flag will be set to 0 if the
		focuser has not been homed and set to 1 when homed.
	
	FFDetect: Set to 1 when using an Optec FastFocus Focuser
	
	TmpProbe: This flag indicates the status of an attached temperature probe. 
		A value of 1 means a probe is attached, 0 means no probe is detected.
	
	RemoteIO: This flag indicates the status of an attached In/Out remote. A 
		value of 1 means a remote is attached, 0 means no remote is detected.
	
	Hnd Ctrlr: This flag indicates the status of an attached hand controller. A 
		value of 1 means a hand controller is attached, 0 means no hand 
		controller is detected.

	 
	PARAMETERS:
		
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		return_dict = True/False, set to true to get the config values returned 
			as a dictionary
		
	
	RETURN
	
		message = The configuration message returned as a long string.
		message_dict = if return_dict is True, the message will be turned into a
			python dictionary so parameters can be called to return values.
		
	"""
	x = str(check_focuser_no(x))
	command = get_start_end_char('F'+ x +'GETSTATUS')
	message = common.send_command_two_response(command, port,
		expected_end='END\n')

	if return_dict == False:
		return message
	else:
		#Convert string to python dictionary, as this will be easier to work
		#  with in other parts of the code.

		#cut of the config + end bits, split into rows, and then split at equals
		message_dict = dict(row.split('=') for row in message[8:-4].split('\n'))
		
		#Need to put the keys into a list, otherwise not all keys are looped
		#  because the keys change during the loop. Was only doing half the
		#  keys.
		dict_key_list = list(message_dict.keys())
		# as it is there lots of spaces at the start/end of name and values,
		#  this will remove them
		for name in dict_key_list:
			message_dict[name] = message_dict[name].strip()
			message_dict[name.strip()] = message_dict.pop(name)

		return message_dict

def get_focuser_stored_config(port, x = 1, return_dict = False):
	"""
	
	Will get the controller to report the configuation setting for focuser 'x'. 
	 Should start with the line 'CONFIGx' where x will be the focuser number, 
	 and finish with the line 'END'.
	
	INFO IN CONFIG MESSAGE: (from manual)
	
	Nickname: The user-defined nickname of the specified focuser
	
	MaxPos: The maximum absolute position that the selected focuser is capable 
	 of moving to. This setting is determined automatically based on the
	 selected Device Type.
	
	Dev Typ: A two character designator of the currently set device type for the
	 specified focuser. See the section entitled ppendix A – Device Types on 
	 page 17 for device type details.
	
	TComp ON: The current status of temperature compensation. 1 indicates the 
	 device is currently temperature compensating, 0 indicates temperature 
	 compensation is disabled.
	
	TemCo A-E: These items indicate the temperature coefficient for the 
	 respective temperature compensation mode. The units of the temperature 
	 coefficients are stepper motor steps per degree.
	
	TC Mode: Indicates the currently selected temperature compensation mode. 
	 When temperature compensation mode is turned on this value selected mode 
	 indicates which temperature coefficient will be used for compensation.
	
	BLC En: This flag indicates whether the internal backlash compensation is 
	 turned on or off. A value of 1 indicates that this feature is turned on, 
	 0 indicates the feature is off.
	
	BLC Stps: This value indicates the number of steps that the focuser will 
	 travel past the target position before returning to the target position 
	 in order to compensate for mechanical backlash in the focusing device. A 
	 positive value indicates the compensation will occur when the focuser move 
	 to a greater absolute position. A negative value indicates the compensation
	will occur on moves to a lesser position. LED Brt: This value indicates the 
	current setting for the brightness of the red power LED on the FocusLynx 
	controller enclosure
	
	TC@Start: This value indicates if the Temperature Compensate at Start 
	 feature is turned on or off. A value of 1 indicate the feature is on, 0 
	indicates the feature is off. When this feature is enabled the device will 
	automatically perform a temperature compensation move immediately following 
	device power-up.
	
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		return_dict = True/False, set to true to get the config values returned 
		as a dictionary
		
	
	RETURN
	
		message = The configuration message returned as a long string.
		message_dict = if return_dict is True, the message will be turned into 
		a python dictionary so parameters can be called to return values.
		
	
	"""
	
	x = str(check_focuser_no(x))
	command = get_start_end_char('F'+ x +'GETCONFIG')
	message = common.send_command_two_response(command, port,
		expected_end='END\n')
	
	if return_dict == False:
		return message
	else:
		#Convert string to python dictionary, as this will be easier to work
		# with in other parts of the code.
		#cut of the config + end bits, split into rows, and then split at equals
		message_dict = dict(row.split('=') for row in message[8:-4].split('\n'))
		
		#Need to put the keys into a list, otherwise not all keys are looped
		#  because the keys change during the loop. Was only doing half the
		#  keys.
		dict_key_list = list(message_dict.keys())
		# as it is there lots of spaces at the start/end of name and values,
		#  this will remove them
		for name in dict_key_list:
			message_dict[name] = message_dict[name].strip()
			message_dict[name.strip()] = message_dict.pop(name)


		return message_dict


def set_device_name(port, device_name, x=1):
	"""
	Use to set a new nickname for focuser 'x'. Controller will respond with 
	'SET' once complete.
	
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		device_name = string with new name. Max 16 char
	
	"""
	# check the length of the new device nickname
	name_length = len(device_name)
	if name_length > 16 or name_length <= 0:
		focus_logger.error('Invalid device name given')
		raise ValueError('Invalid device name given')

	else:
		x = str(check_focuser_no(x))
		command = get_start_end_char('F'+ x +'SCNN'+str(device_name))
		message = common.send_command_two_response(command, port)

		if message == 'SET':
			focus_logger.info('Name for Focuser '+str(x)+ ' set as: ' + str(
				device_name))

		else:
			focus_logger.error('Response:'+message)


def set_device_type(port, x = 1, device_type = 'OI'):

	"""
	Use this to specify the type of focuser attached. The controller uses this 
	information to determine the correct speed and motor power to use. An 
	incorrect value could damage a focuser. Valid settings are shown in 
	Appendix A of the user manual, and are also listed here. The controller will
	 respond with 'SET' once complete.
	
	
	Available Types:
	
		OA: Optec TCF-Lynx 2”
		OB: Optec TCF-Lynx 3”
		OC: Optec TCF-Lynx 2” with Extended Travel
		OD: Optec Fast Focus Secondary Focuser
		OE: Optec TCF-S Classic converted (original unipolar motor)
		OF: Optec TCF-S3 Classic converted (original unipolar motor)
		OG: Optec Gemini (reserved for future use)
		OI: what it was initial set as
		FA: FocusLynx QuickSync FT Hi-Torque
		FB: FocusLynx QuickSync FT Hi-Speed
	
	*** 2/11/18 ***
	I think the focuser are TCF-S 3" so device type OB, but need to check.
	
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		
		port = the open port for communicating with the focuser
		
		device_type = string, 2 characters in length to set what type of focuser
		 is connected to the control box. Valid options: OA, OB, OC, OD, OE, OF,
		 OG, FA, and FB. See Appendix A of controller manual for more info.

	
	"""

	valid_device_types = ['OA', 'OB', 'OC', 'OD', 'OE',
							'OF', 'OG', 'FA', 'FB', 'OI']

	if device_type not in valid_device_types:

		focus_logger.error(str(device_type) + ' is not a valid device type.')
		raise ValueError(str(device_type) + ' is not a valid device type.')

	else:
		x = str(check_focuser_no(x))
		command = get_start_end_char('F'+ x +'SCDT'+str(device_type))
		message = common.send_command_two_response(command, port)

		if message == 'SET':
			focus_logger.info('Device Type for Focuser '+str(x)+ ' set '\
				'as: ' + str(device_type))

		else:
			focus_logger.error('Response:'+message)



def set_temp_comp(port, x =1, temp_comp = False):
	"""
	Use to enabled/disable the temperature compensation feature for focuser 'x'.
	 Controller will respond with 'SET' once complete.
	
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		temp_comp = True/False. True will enabled the temperature compensation 
			feature, False will disable


	"""
	if temp_comp == True:
		tc_state = 'ENABLED'
		setno = str(1)
	
	elif temp_comp == False:
		tc_state = 'DISABLED'
		setno = str(0)
	else:
		#print(temp_comp)
		#print(type(temp_comp))
		focus_logger.error('Invalid input for temperature compensation control'\
			'. True=Enable, False=Disable')
		raise ValueError('Invalid input for temperature compensation control.'\
			' True=Enable, False=Disable')

	x = str(check_focuser_no(x))
	#print(temp_comp)
	command = get_start_end_char('F'+ x +'SCTE'+str(setno))
	message = common.send_command_two_response(command, port)

	if message == 'SET':
		focus_logger.info('Temperature compensation ' + tc_state + ' for'\
			' focuser '+str(x))

	else:
		focus_logger.error('Response:'+message)

def set_temp_comp_mode(port, x=1, mode='A'):

	"""
	Use this to set the mode used when the temperature compensation mode is set.
	 For example, selecting mode 'C' will mean that temperature coefficient 
	 'C' will be used. The controller will respond with 'SET' once complete.
		
		PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		mode = Mode to be selected for the temperature compensation. 
		Suitable values are: A, B, C, D or E.
	
	"""

	valid_modes = ['A','B','C','D','E']
	if mode not in valid_modes:
		focus_logger.error(str(mode)+ ' is not a valid mode for the '\
			'temperature compensation.')
		raise ValueError(str(mode) + ' is not a valid mode for the '\
			'temperature compensation.')

	else:
		x = str(check_focuser_no(x))
		command = get_start_end_char('F'+ x +'SCTM'+str(mode))
		message = common.send_command_two_response(command, port)

		if message == 'SET':
			focus_logger.info('Temperature compensation mode ' + str(
				mode) + ' set for focuser '+str(x))

		else:
			focus_logger.error('Response:'+message)

def set_temp_comp_coeff(port,mode,temp_coeff_val, x=1):

	"""
	Use this function to set the temperature coefficients for each of the 
		modes, for each focuser.
	
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		mode = Mode to be selected for the temperature compensation. Suitable 
			values are: A, B, C, D or E.
		temp_coeff_val = integer (in steps per degree) to be used for the 
			coefficient. Between -9999 and 9999.
	
	"""

	valid_modes = ['A','B','C','D','E']
	if mode not in valid_modes:
		focus_logger.error(str(mode)+ ' is not a valid mode for the '\
			'temperature compensation.')
		raise ValueError(str(mode) + ' is not a valid mode for the '\
			'temperature compensation.')


	if isinstance(temp_coeff_val, int) == False:
		focus_logger.error('Temperature compensation coefficient must be '\
			'an integer')
	else:

		if temp_coeff_val < -9999 or temp_coeff_val > 9999:
			focus_logger.error('Invalid value enter for the temperature '\
				'compensation coefficient')

		else:

			x = str(check_focuser_no(x))
			formatted_coeff = '{0:=+05}'.format(temp_coeff_val)
			command = get_start_end_char('F'+ x +'SCTC'+str(
				mode)+formatted_coeff)
			
			message = common.send_command_two_response(command, port)

			if message == 'SET':
				focus_logger.info('Temperature compensation coefficient'\
					'set as ' + formatted_coeff +
				' for mode: '+ str(mode) + ' and for focuser '+str(x))

			else:
				focus_logger.error('Response:'+message)


def set_temp_comp_start_state(port, x=1, temp_comp_start = False):

	"""
	Enable or disable the 'Temperature Compensation at Start' feature on the 
	 controller. When enabled, the controller will perform a temperature 
	 compensation move when the device is first switched on, using the 
	 temperature recorded last time the compensation feature was switched on. 
	 Controller will respond with 'SET' once complete.
	
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		temp_comp_start = True/False. True will enabled the 'temperature 
			compensation at start' feature, False will disable it.
	
	"""
	if temp_comp_start == False:
		tcs_state = 'DISABLED'
		set_no = 0
	elif temp_comp_start == True:
		tcs_state = 'ENABLED'
		set_no =1
	else:
		focus_logger.error('Invalid input for "temperature compensation at '\
			'start" control. True=Enable, False=Disable')
		raise ValueError('Invalid input for "temperature compensation at '\
			'start" control. True=Enable, False=Disable')


	x = str(check_focuser_no(x))
	command = get_start_end_char('F'+ x +'SCTS'+str(set_no))
	message = common.send_command_two_response(command, port)

	if message == 'SET':
		focus_logger.info('"Temperature compensation at start" state set '\
			'to ' + tcs_state + ' for focuser '+str(x))

	else:
		focus_logger.error('Response:'+message)


def set_backlash_comp(port,x=1, backlash_comp = False):

	"""
	Enable or disable the 'Backlash Compensation as Start' feature on the 
	 controller. When enabled, the controller will move the focus pass the 
	 target position (by a number of steps that is set using the 
	 set_backlash_steps() function) and then return to the target position. 
	 This is so the focuser always approaches the target postition to try to 
	 avoid mechanical backlash. Backlash compensation is caried out on all 
	 outward moves (never on inward moves) Controller will respond with 'SET' 
	 once complete.
	
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		backlash_comp = True/False. True will enabled the backlash compensation
		 feature, False will disable it.
	
	"""
	if backlash_comp == False:
		bl_state = 'DISABLED'
		set_no = 0
	elif backlash_comp == True:
		bl_state = 'ENABLED'
		set_no =1
	else:
		focus_logger.error('Invalid input for backlash compensation control.'\
			' True=Enable, False=Disable')
		raise ValueError('Invalid input for backlash compensation control. '\
			'True=Enable, False=Disable')


	x = str(check_focuser_no(x))
	command = get_start_end_char('F'+ x +'SCBE'+str(set_no))
	message = common.send_command_two_response(command, port)

	if message == 'SET':
		focus_logger.info('Backlash compensation state set to ' + bl_state +
			' for focuser '+str(x))

	else:
		focus_logger.error('Response:'+message)

def set_backlash_steps(port,x=1, backlash_steps = 10):

	"""
	Use to set the number of steps the focuser will move past the target 
	 position whilst carrying out a backlash compensation move. Backlash 
	 compensation is caried out on all outward moves (never on inward moves) 
	 Controller will respond with 'SET' once complete.
		
	PARAMETERS:
	
		x = 1 or 2 depending on the which focuser the command is for
		port = the open port for communicating with the focuser
		backlash_steps = Integer between 0-99, for the number of steps past the 
			target point the focuser will move.
	
	"""
	#make sure value is an integer
	if isinstance(backlash_steps, int) == False:
		focus_logger.error('Backlash steps value must be an integer.')
		
	else:
		if backlash_steps<=0 or backlash_steps >99:
			focus_logger.error('Backlash steps must be between 0 and 99')

		else:
			x = str(check_focuser_no(x))
			formatted_steps = '{0:>02}'.format(backlash_steps)
			command = get_start_end_char('F'+ x +'SCBS'+str(formatted_steps))
			message = common.send_command_two_response(command, port)

			if message == 'SET':
				focus_logger.info('Backlash steps set to ' + formatted_steps +
					' for focuser '+str(x))

			else:
				focus_logger.error('Response:'+message)

def set_LED_brightness(brightness, port):

	"""
	Use 'brightness' to change the brightness of the LED on the controller 
	 enclosure. 0 will turn off the LED. Controller will respond with 'SET' 
	 once complete.
	
	PARAMETERS:
	
	brightness = An integer between 0 and 100. 0 will turn off the LED.
	port = the open port for communicating with the focuser
	
	"""
	

	if isinstance(brightness, int):
	
		if brightness > 100 or brightness < 0:
			focus_logger.error(str(brightness)+ ' is an invalid value for '\
				'brightness setting.')
		else:
			format_bright = '{0:>03}'.format(brightness)

			command = get_start_end_char('FHSCLB'+format_bright)

			message = common.send_command_two_response(command, port)

			if message == 'SET':
				focus_logger.info('LED brightness set to: ' + str(
					format_bright))
			else:
				focus_logger.error('Response:'+message)

	else:
	
		focus_logger.error('Check value entered for brightness setting.')


"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Group OBSERVING FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

def focuser_initial_configuration(config_file_name,
			config_file_loc = 'configs/'):
	"""
	
	This function will set all the settings needed to run a focuser. The 
	 settings will be loaded from a configuration file, and passed to the
	 relavent control functions.
	 
	 Don't think this will need to be done everytime the focuser is run, just 
	 when first setup unless you'd like to change the settings.
	  
	  General description of function:
	   - Load configuration file and check serial port connection settings.
	   - Open a serial port connection to the focuser
	   - Set the device name and type in the onboard focuser configuration.
	   - Set the LED brightness.
	   - Set everything required for the temperature compensation, even if it is
			not used
	   - Set everything for the backlash compensation, even if it is not used.
	   - Close the port.
	  
	  PARAMETERS:
	  
	  config_file_name = name of the file containing configuration setting for 
		the focuser
	  config_file_loc = directory to find the configuration file
	  
	"""

	config_dict = common.load_config(config_file_name, path = config_file_loc)
	check_config_port_values_for_focuser(config_dict)
	open_p = common.open_port_from_config_param(config_dict)

	focuser_no = config_dict['focuser_no']
	#start loading the settings
	set_device_name(open_p, device_name = config_dict['focuser_name'],
		x=focuser_no)
	set_device_type(open_p, device_type= config_dict['device_type'],
		x=focuser_no)
	set_LED_brightness(config_dict['LED_brightness'], open_p)

	#set temperature compensation setings:
	set_temp_comp(open_p, temp_comp = config_dict['temp_compen'], x=focuser_no)
	set_temp_comp_start_state(open_p,
		temp_comp_start = config_dict['temp_compen_at_start'], x= focuser_no)
	set_temp_comp_coeff(open_p, mode= 'A',
		temp_coeff_val=config_dict['temp_coeffA'], x= focuser_no)
	set_temp_comp_coeff(open_p, mode='B',
		temp_coeff_val=config_dict['temp_coeffB'], x= focuser_no)
	set_temp_comp_coeff(open_p, mode='C',
		temp_coeff_val= config_dict['temp_coeffC'], x= focuser_no)
	set_temp_comp_coeff(open_p, mode='D',
		temp_coeff_val=config_dict['temp_coeffD'], x= focuser_no)
	set_temp_comp_coeff(open_p, mode='E',
		temp_coeff_val=config_dict['temp_coeffE'], x= focuser_no)
	set_temp_comp_mode(open_p, mode = config_dict['temp_compen_mode'],
		x= focuser_no)

	#Set backlash settings:
	set_backlash_comp(open_p, backlash_comp = config_dict['backlash_compen'],
		x= focuser_no)
	set_backlash_steps(open_p, backlash_steps = config_dict['backlash_steps'],
		x= focuser_no )
	
	get_focuser_stored_config(open_p, x= focuser_no)

	#close the port
	common.close_port(open_p)

def startup_focuser(config_file_name, config_file_loc = 'configs/'):
	"""
	
	This function will perform any startup operations, to make it so the
	 focuser is ready to work. Return the open port ready for sending further 
	 instructions.
	 
	PARAMETERS:
	  
	  config_file_name = name of the file containing configuration setting for 
		the focuser
	  config_file_loc = directory to find the configuration file
	  
	RETURN
	
		focuser_no = Number of the focuser that has been started up
		open_p = the serial port that has been opened for future communication.
	  
	"""
	config_dict = common.load_config(config_file_name, path = config_file_loc)
	check_config_port_values_for_focuser(config_dict)
	open_p = common.open_port_from_config_param(config_dict)
	focuser_no = config_dict['focuser_no']

	#home_focuser(open_p, x = focuser_no)
	
	
	current_config=get_focuser_stored_config(open_p, x = focuser_no,
		return_dict=True)
	if current_config['TComp ON'] == 1:
		focus_logger.info('Focuser '+str(focuser_no)+': Temperature '\
			'compensation - ON')
	else:
		focus_logger.info('Focuser '+str(focuser_no)+': Temperature '\
			'compensation - OFF')
	if current_config['BLC En'] == 1:
		focus_logger.info('Focuser '+str(focuser_no)+': Backlash compensation'\
			' - ON')
	else:
		focus_logger.info('Focuser '+str(focuser_no)+': Backlash compensation '\
			'- OFF')

	focus_logger.info('Startup for Focuser '+str(focuser_no)+' complete.')

	return focuser_no, open_p

def shutdown_focuser(open_p, x=1):
	"""
	
	This function will perform any shutdown operations at the end of the night 
		or during shutdown. Then close the serial port connection

	PARAMETERS:
		
		open_p = an open serial port connection to the focuser
		x = focuser number
	
	"""

	#center_focuser(open_p)
	open_p.close()

	focus_logger.info('Serial port connection to focuser has been closed')

"""
	#Might be used for testing the status setup
	STATUS1\nTemp(C)  = +21.7\nCurr Pos = 108085\nTarg Pos = 000000\nIsMoving 
		= 1\nIsHoming = 1\nIsHomed  = 0\nFFDetect = 0\nTmpProbe = 1\nRemoteIO 
		= 0\nHnd Ctlr = 0\nEND
	
	CONFIG\nNickname = FocusLynx Foc2\nMax Pos = 125440\nDevTyp =OE\nTComp ON 
		= 0\nTempCo A = +0086\nTempCo B = +0086\nTempCo C = +0086\nTempCo D = 
		+0000\nTempCo E = +0000\nTCMode =A\nBLC En =0\nBLC Stps = +40\nLED Brt 
		= 075\nTC@Start = 0\nEND
"""