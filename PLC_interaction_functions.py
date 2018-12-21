"""
PLC_interaction_functions.py


 Replaces all the individual PHP scripts to interact with the PLC box, to do things such as get the rain status
  or get the roof status.
  
 Have been written so they can be used individually in scripts from a command line, or imported into a larger
  script.

 When incorporating these functions into exsiting functions, it is probably worth checking to see if the function
  may exit when an error is thrown, then incoporate it in a try/except statement from where it is being 
  called. The request to exit is there so the program quits when called from the command line, but this probably is something you want when run in a large script. Also for these functions you will need to set exit_after to False. If set to True, the code will exit on succesful completion.
  
 <13/11/18> ** Note, most of the functions have not been properly tested, as they require the PLC to actually be connected. Also for the Xamidimura telescope need to add
	in the functions and code to work with the new tilt sensors.
	
	CURRENT FUNCTIONS:
	----------------------------------------------------------------------
	New Functions
	----------------------------------------------------------------------
	- sort_messages(message, print_messages = True, log_messages = True)
	
	- get_D100_D102_status()
	
	- split_up_response(response)
	
	- create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)
	----------------------------------------------------------------------
	OLD PHP Scripts
	----------------------------------------------------------------------
	- plc_close_roof(print_messages=True, log_messages=True, exit_after=True)
	
	- plc_get_plc_status(print_messages=True, log_messages=True)
	
	- plc_get_rain_status(print_messages=True, log_messages=True)
	
	- plc_get_roof_status(print_messages=True, log_messages=True)
	
	- plc_open_roof(print_messages=True, log_messages=True, exit_after=True)
	
	- plc_request_roof_control(print_messages=True, log_messages=True, exit_after=True)
	
	- plc_reset_watchdog(print_messages=True, log_messages=True, exit_after=True)
	
	- plc_select_battery(print_messages=True, log_messages=True, exit_after=True)
	
	- plc_select_mains(print_messages=True, log_messages=True, exit_after=True)
	
	- plc_set_comms_timeout(timeout, print_messages=True, log_messages=True, exit_after=True)
	
	- plc_set_power_timeout(timeout, print_messages=True, log_messages=True, exit_after=True)
	
	- plc_stop_roof(print_messages=True, log_messages=True, exit_after=True)
	----------------------------------------------------------------------
	NEW python functions
	----------------------------------------------------------------------
	- plc_is_roof_open(print_messages = True, log_messages = True)

"""

import serial
import roof_control_functions as rcf
import logging
import sys
import settings_and_error_codes as set_err_codes

logging.basicConfig(filename = '/Users/Jessica/PostDoc/ScriptsNStuff/current_branch/xamidimura/logfiles/plc.log',filemode='w',level=logging.INFO, format='%(asctime)s  %(levelname)s %(message)s')

class PLC_ERROR(Exception):
	"""
	User defined errir
	"""
	def __init__(self,message):
		self.message = message

	def __str__(self):
		return(repr(self.message))

def sort_messages(message, print_messages = True, log_messages = True,level = 'error'):
	"""
	Will decide if a message needs to be printed to the terminal and/or logging. Can do both, just one of them or neither.
	
	PARAMETERS:
		message -  the message that would be printed/logged
		
		print_messages - boolean, if True messages will be printed to the terminal
		
		log_messages - bool, if True, messages will be logged as an error
	"""

	if print_messages == True:
		print(message)
	if log_messages == True:
		if level == 'error':
			logging.error(message)
		else:
			logging.info(message)

def get_D100_D102_status():
	
	"""
	 Get the current status of the command buffer words D-100 to D-102. Will check the end code, and report
	  an error then exit if there was a problem getting the roof status. This function is equivalent to the 
	  following section of code taken from the orginial PHP scripts:
	 
	 -----------------------------------------------------------------------
	 # Get the current status of the command buffer words D-100 to D-102
	 $response = plc_command_response(PLC_Command_Status_Request);

	 if (plc_status_end_code($response)) {
		echo basename($argv[0]).": Error getting roof status from PLC: ";
		echo plc_data_error_message(plc_status_end_code($response))."\n";
		exit(1);
	 }
	 -----------------------------------------------------------------------
	  
	RETURN:
		
		response - If the response from the PLC pass the check, then it will be returned, otherwise Python will 
			raise a PLC_Error exception.
			
			
	"""

	# Get the current status of the command buffer words D-100 to D-102
	response = rcf.plc_command_response(rcf.PLC_Command_Status_Request)

	if rcf.plc_status_end_code(response):
		logging.error('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		raise PLC_ERROR('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))

	else:
		return response

def split_up_response(response, print_messages=True,log_messages=True):

	"""
	Takes a response message from the PLC and will split it up, and return the frame,
	 status_hex, power timeout hex, comm timeout hex and fcs_hex.
	 
	It will carry out a FCS check.
	
	This function is equivalent to the following section of code taken from the orginial PHP scripts:
	
	-----------------------------------------------------------------------
	$preg = '%^(@00RD00(....)(....)(....).*)(..)\*\r$%';
	if (preg_match($preg,$response,$matches)){
		$frame = $matches[1];
		$status_hex = $matches[2];
		$power_timeout_hex = $matches[2];
		$comms_timeout_hex = $matches[3];
		$fcs_hex = $matches[5];
		$x = ord("@");
		$i = 1;
		do {
			$x = $x ^ ord(substr($frame,$i,1));
		} while (($i++) < (strlen($frame)-1));

		if (hexdec("$fcs_hex") != $x) {
			echo basename($argv[0]).": roof status FCS check fail : ";
			echo $response."\n";
			exit(1);
		}
	} else {
		echo basename($argv[0]).": Got invalid roof status from PLC: ";
		echo $response."\n";
		exit(1);
	}
	-----------------------------------------------------------------------
	
	PARAMETER
	
	 response = The response to be split
	
	RETURN:
		frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex
	"""
	if response[-2:] == '*\r' and response[0] == '@' and response[:7] =='@00RD00':
		frame = response[:-4]
		status_hex = response[7:11]
		power_timeout_hex = response[11:15]
		comms_timeout_hex = response[15:19]
		fcs_hex = plc_string[-4:-2]

		x = ord('@')
		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])

		if int('fcs_hex' != x):
			logging.error('Roof status FCS check fail: '+str(response))
			raise PLC_ERROR('Roof status FCS check fail: '+str(response))
	else:
		logging.error('Got invalid roof status from PLC: '+str(response))
		raise PLC_ERROR('Got invalid roof status from PLC: '+str(response))

	return frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex

def create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex):
	"""
	This function will take the status, power timeout and comms timeout in hexadecimal format
	 and use them to form a command to send to the PLC. It will check that the command is ok,
	 if it is not then it will log an error message and exit.
	 
	This function is equivalent to the following section of code taken from the orginial PHP scripts:
	
	-----------------------------------------------------------------------
	$cmd = "@00WD0100".$status_hex.$power_timeout_hex.$comms_timeout_hex."00000000000000*\r";
	$cmd=  plc_insert_fcs($cmd);
	$response =  plc_command_response($cmd);
	if ($response != PLC_Roof_Command_Response_OK) {
		echo basename($argv[0]).": Command failed ".$cmd."\n";
		echo $response."\n";
		exit(1);
	}
	-----------------------------------------------------------------------
	
	"""
	cmd = "@00WD0100"+status_hex+power_timeout_hex+comms_timeout_hex+"00000000000000*\r"
	cmd = rcf.plc_insert_fcs(cmd)
	response = rcf.plc_command_response(cmd)
	if response != rcf.PLC_Roof_Command_Response_OK:
		logging.error('Command failed:'+str(response))
		raise PLC_ERROR('Command failed:'+str(response))


def plc_close_roof(print_messages = True, log_messages = True):

	"""
	Issue the commands to close the roof via the PLC box
	
	# Check the following conditions first.
	# - The Roof interface is set to Remote.
	# - The Motor Stop is not pressed.
	# - There is no power failure.
	
	*** DOES NOT CHECK IF THE TELESCOPE IS GOING TO BE HIT ****
	
	RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the code has completed
	
	"""

	#Get a status response from the PLC and check the response

	response = rcf.plc_command_response(rcf.PLC_Request_Roof_Status)
	if rcf.plc_status_end_code(response):
		logging.error('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		raise PLC_ERROR('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
	
	# Pickout the roof status part of the response
	roof_status = rcf.plc_status_status_code(response)
	# Check the roof is set for remote control
	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Remote_Control) == False:
		sort_messages('PLC is not under remote control.', print_messages=print_messages, log_messages=log_messages)
		raise PLC_ERROR('PLC is not under remote control.')

	# Check if the motor stop is pressed.
	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Motor_Stop_Pressed) == True:
		logging.error('PLC motor stop is pressed')
		raise PLC_ERROR('PLC motor stop is pressed')

	# Check to see if the AC motor is being used. If it is check for power failure
	#  or that the AC motor has tripped
	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_DC_Motor_In_Use) == False:
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Power_Failure) == True:
			logging.error('Power failure and AC motor selected')
			raise PLC_ERROR('Power failure and AC motor selected')

		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_AC_Motor_Tripped) == True:
			logging.error('AC motor has tripped.')
			raise PLC_ERROR('AC motor has tripped.')

	# Get the current status of the command buffer words D-100 to D-102
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	# Set the close roof command bit and unset the open roof command bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_CLOSE)
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_OPEN)

	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)

	return set_err_codes.PLC_CODE_OK


def plc_get_plc_status(log_messages = True):

	"""
	Issue the commands the get the status of the plc from the plc box
	
	PARAMETERS:
	
		log_messages = If True, messages will be logged in the file plc.log. Error messages will still be
			logged even if false.
		
	RETURN 
	
		plc_status_dict = Dictionary containing the current response code, status ans operating mode of the 
			plc box.
	"""

	response = rcf.plc_command_response(rcf.PLC_Status_Request)
	plc_status_dict = dict()

	plc_status_dict['PLC_Response_Code'] = response
	plc_status_dict['PLC_Status'] = rcf.plc_status_message(rcf.plc_status_request_response_plc(response))
	plc_status_dict['PLC_Operating_Mode'] = rcf.plc_mode(response)

	if log_messages == True:
		dict_keys_list = list(plc_status_dict.keys())
		for i in range(len(plc_status_dict.keys())):
			logging.info(dict_keys_list[i] +' = '+ plc_status_dict[dict_keys_list[i]])

	return plc_status_dict


def plc_get_rain_status(log_messages = True):
	"""
	Issue commands to get the rain status from the PLC box
	
	PARAMETERS:
	
		log_messages = If True, messages will be logged in the file plc.log. Error messages will still be
			logged even if false.
		
	RETURN:
	
		rain_status_dict =  A dictionary containing the response code, the rain status (either 'Check
		 Rain' or 'Ignore Rain') and the PC Comm and Power Failure timeouts.
	"""
	
	response = rcf.plc_command_response(rcf.PLC_Request_Roof_Status)
	rain_status_dict = dict()
	rain_status_dict['Response Code'] = response
	
	if rcf.plc_status_end_code(response):
		logging.error('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)),print_messages=print_messages, log_messages=log_messages)
		raise PLC_ERROR('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
	
	else:
		roof_status = rcf.plc_status_status_code(response)
		rain_status_dict = dict()
		if rcf.hex_bit_is_set(roof_status,rcf.PLC_CMD_BIT_RAIN) == True:
			rain_status_dict['Rain_status'] = 'Check Rain'
		else:
			rain_status_dict['Rain_status'] = 'Ignore Rain'

	rain_status_dict['PC_Communication_Timeout'] = rcf.plc_status_comms_timeout(response)
	rain_status_dict['Power_Failure_Timeout'] = rcf.plc_status_comms_timeout(response)

	if log_messages == True:
		dict_keys_list = list(rain_status_dict.keys())
		for i in range(len(rain_status_dict.keys())):
			logging.info(dict_keys_list[i] +' = '+ rain_status_dict[dict_keys_list[i]])

	return rain_status_dict


def plc_get_roof_status(log_messages=True):
	"""
	Sends the commands needed to get the roof status from the PLC box. Will also log the information

	PARAMETERS:
	
		log_messages = If true, the status of the various parameters will be logged. Error messages will still be
			logged even if false.
	
	RETURN
	
		roof_dict = A dictionary containing the status of all parameters relating to the roof.
		
	"""
	
	response = rcf.plc_command_response(rcf.PLC_Request_Roof_Status)
	roof_dict = dict()
	roof_dict['Response Code'] = response
	if rcf.plc_status_end_code(response):
		logging.error('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)), print_messages=print_messages, log_messages=log_messages)
		raise RunError('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))

	else:
		roof_status = rcf.plc_status_status_code(response)

		# Roof Closed?
		roof_dict['Roof_Closed'] = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Closed)

		# Roof open?
		roof_dict['Roof_Open'] = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Open)

		# Roof moving?
		roof_dict['Roof_Moving'] = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Moving)

		#Check Roof control Remote/Manual
		if rcf.int_bit_is_set(roof_status,rcf.PLC_Roof_Remote_Control):
			roof_dict['Roof_Control'] = 'Remote'
		else:
			roof_dict['Roof_Control'] = 'Manual'

		# Check rain status
		roof_dict['Roof_Raining'] = rcf.int_bit_is_set(roof_status,rcf.PLC_Roof_Raining)

		# Check for forced rain closure
		roof_dict['Roof_Forced_Close'] = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Forced_Rain_Closure)

		# Building Temp High:
		roof_dict['High_Building_Temp'] = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Building_Temp_High)

		# extractor fan
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Extractor_Fan_On):
			roof_dict['Extrator_Fan'] = 'On'
		else:
			roof_dict['Extrator_Fan'] = 'Off'

		# motor stop is pressed
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Motor_Stop_Pressed):
			roof_dict['Roof_Motor_Stop'] = 'Pressed'
		else:
			roof_dict['Roof_Motor_Stop'] = 'Not Pressed'

		# AC Motor has tripped
		roof_dict['Roof_AC_Motor_Tripped'] = rcf.int_bit_is_set(roof_status, PLC_Roof_AC_Motor_Tripped)

		# Using DC motor
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_DC_Motor_In_Use):
			roof_dict['Roof_Motor_Being_Used'] = 'DC'
		else:
			roof_dict['Roof_Motor_Being_Used'] = 'AC'


		#Close Proximity
		roof_dict['Roof_Close_Proximity'] = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Close_Proximity)

		#Power failure
		roof_dict['Roof_Power_Failure'] = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Power_Failure)

		#Force_Power_closure
		roof_dict['Roof_Forced_Power_Closure'] = rcf.int_bit_is_set(roof_status,rcf.PLC_Roof_Forced_Power_Closure)

		# Open proximity
		roof_dict['Roof_Open_Proximity'] = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Open_Proximity)

		#Door open
		roof_dict['Roof_Door_Open'] = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Door_Open)

	roof_dict['PC_Communication_Timeout'] = rcf.plc_status_comms_timeout(response)
	roof_dict['Power_Failure_Timeout'] = rcf.plc_status_comms_timeout(response)

	if log_messages == True:
		dict_keys_list = list(roof_dict.keys())
		for i in range(len(roof_dict.keys())):
			logging.info(dict_keys_list[i] +' = '+ str(roof_dict[dict_keys_list[i]]))

	return roof_dict


def plc_open_roof():
	"""
	Send the commands to open the roof. Will check the following:
	 - The roof interface is set to remote
	 - The motor Stop is not pressed
	 - The rain sensor is not triggered
	 - There is no power failure
	 
	 RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the code has completed
	 
	"""
	response = rcf.plc_command_response(rcf.PLC_Request_Roof_Status)
	if rcf.plc_status_end_code(response):
		logging.error('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		raise PLC_ERROR('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))

	roof_status = rcf.plc_status_status_code(response)

	if int_bit_is_set(roof_status, rcf.PLC_Roof_Remote_Control) == False:
		logging.error('PLC not under remote control')
		raise PLC_ERROR('PLC not under remote control')

	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Remote_Control):
		logging.error('PLC motor stop is pressed')
		raise PLC_ERROR('PLC motor stop is pressed')

	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Raining):
		logging.error("It's RAINING!!")
		raise PLC_ERROR("It's RAINING!!")

	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Power_Failure):
		logging.error('Power failure')
		raise PLC_ERROR('Power failure')

	# Get the current status of the command buffer words D-100 to D-102
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	# Set the close roof command bit and unset the open roof command bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_OPEN)
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_CLOSE)

	#Create new command, sent it and deal with response
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)

	return set_err_codes.PLC_CODE_OK

def plc_request_roof_control():
	"""
	Send the commands to request control of the roof
	
	RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the code has completed
		
	"""
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	#Set control request bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_REQ_CONTROL)
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)

	#Unset control request bit
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_REQ_CONTROL)
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)


	return set_err_codes.PLC_CODE_OK

def plc_reset_watchdog():
	"""
	Send the commands to reset the watchdog for the PLC box
	
	RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the code has completed
	
	"""
	
	# Get the current status of the command buffer words D-100 to D-102
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)
	
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)
	
	return set_err_codes.PLC_CODE_OK


def plc_select_battery():
	"""
	Send the commands to select the battery for the PLC box
	
	RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the code has completed
		
	"""
	
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)
	
	# Set main/battery bit to 0 = battery
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_MAINS)

	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)
	
	return set_err_codes.PLC_CODE_OK


def plc_select_mains():
	"""
	Send the commands to select the mains for the PLC box
	
	RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the code has completed
		
	"""
	
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)
	
	# Set main/battery bit to 0 = battery
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_MAINS)

	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)
	
	return set_err_codes.PLC_CODE_OK


def plc_set_comms_timeout(timeout):
	"""
	Send the commands to set the comms timeout for the PLC box
	
	PARAMETERS:
		
		timeout = timeout time in seconds, between 1 and 9999

	RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the code has completed

	"""
	
	if timeout < 1 or timeout >9999:
		logging.error('Invalid timeout value, 1 <= Timeout < 9999')
		raise ValueError('Invalid timeout value, 1 <= Timeout < 9999')

	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	# Set timeout value
	comms_timeout_hex = "{:04X}".format(timeout)
	
	# Set update timeout bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_SET_COMMS_DELAY)
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)

	#Unset timeout bit
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_SET_COMMS_DELAY)
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)

	return set_err_codes.PLC_CODE_OK

def plc_set_power_timeout(timeout):
	"""
	Send the commands to set the power timeout for the PLC box
	
	PARAMETERS:
		
		timeout = timeout time in seconds, between 1 and 9999
		
	RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the code has completed
	"""
	
	if timeout < 1 or timeout >9999:
		logging.error('Invalid timeout value, 1 <= Timeout < 9999')
		raise ValueError('Invalid timeout value, 1 <= Timeout < 9999')

			
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	# Set timeout value
	power_timeout_hex = "{:04X}".format(timeout)
	
	# Set update timeout bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_SET_POWER_DELAY)
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)

	#Unset timeout bit
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_SET_POWER_DELAY)
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)

	return set_err_codes.PLC_CODE_OK


def plc_stop_roof():

	"""
	Send the commands to stop the roof to the PLC box
	
	RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the code has completed
		
		
	"""
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	#Unset the close roof command bit and unset the open roof command bit
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_CLOSE)
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_OPEN)
	
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)

	return set_err_codes.PLC_CODE_OK



def plc_is_roof_open():
	"""
	Will just check if the open roof bit is set
	"""

	response = rcf.plc_command_response(rcf.PLC_Request_Roof_Status)
	if rcf.plc_status_end_code(response):
		logging.error('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		raise PLC_ERROR('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
	else:
		roof_open = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Open)

	return roof_open
