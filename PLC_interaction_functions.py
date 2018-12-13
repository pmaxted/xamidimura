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


"""

import serial
import roof_control_functions as rcf
import logging
import sys

logging.basicConfig(filename = '/Users/Jessica/PostDoc/ScriptsNStuff/current_branch/xamidimura/logfiles/plc.log',filemode='w',level=logging.INFO, format='%(asctime)s  %(levelname)s %(message)s')

def sort_messages(message, print_messages = True, log_messages = True):
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
		logging.error(message)

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
			exit.
	"""

	# Get the current status of the command buffer words D-100 to D-102
	response = rcf.plc_command_response(rcf.PLC_Command_Status_Request)

	if rcf.plc_status_end_code(response):
		sort_messages('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		sys.exit(1)
	else:
		return response

def split_up_response(response):

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
			sort_messages('Roof status FCS check fail: '+response)
			sys.exit(1)
		else:
			sort_messages('Got invalid roof status from PLC: '+response)
			sys.exit(1)

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
		sort_messages('Command failed:'+response)
		sys.exit(1)

def plc_close_roof(print_messages = True, log_messages = True, exit_after = True):

	"""
	Issue the commands to close the roof via the PLC box
	
	# Check the following conditions first.
	# - The Roof interface is set to Remote.
	# - The Motor Stop is not pressed.
	# - There is no power failure.
	
	*** DOES NOT CHECK IF THE TELESCOPE IS GOING TO BE HIT ****
	
	Will used sys.exit(1) if there is an issue, otherwise sys.exit(0)
	
	PARAMETERS:
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
		
		exit_after = If True, will use sys.exit(0) to exit the script when successfully complete, but
			not if it is set to False. Again, useful if begin called from an executable script.
		
		messages can be both printed and logged.
	
	"""

	#Get a status response from the PLC and check the response

	response = rcf.plc_command_response(rcf.PLC_Request_Roof_Status)
	if rcf.plc_status_end_code(response):
		sort_messages('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		sys.exit(1)
	
	# Pickout the roof status part of the response
	roof_status = rcf.plc_status_status_code(response)
	# Check the roof is set for remote control
	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Remote_Control) == False:
		sort_messages('PLC is not under remote control.')
		sys.exit(1)

	# Check if the motor stop is pressed.
	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Motor_Stop_Pressed) == True:
		sort_messages('PLC motor stop is pressed')
		sys.exit(1)

	# Check to see if the AC motor is being used. If it is check for power failure
	#  or that the AC motor has tripped
	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_DC_Motor_In_Use) == False:
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Power_Failure) == True:
			sort_messages('Power failure and AC motor selected')
			sys.exit(1)

		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_AC_Motor_Tripped) == True:
			sort_messages('AC motor has tripped.')
			sys.exit(1)

	# Get the current status of the command buffer words D-100 to D-102
	response = hex(rcf.plc_command_response(rcf.PLC_Command_Status_Request))
	if rcf.plc_status_end_code(response):
		sort_messages('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		sys.exit(1)

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	# Set the close roof command bit and unset the open roof command bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_CLOSE)
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_OPEN)

	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)

	if exit_after == True:
		sys.exit(0)


def plc_get_plc_status(print_messages = True, log_messages = True):

	"""
	Issue the commands the get the status of the plc from the plc box
	
	PARAMETERS:
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
	"""

	response = rcf.plc_command_response(rcf.PLC_Status_Request)
	sort_messages('PLC response code:'+response)
	sort_messages('PLC status: '+rcf.plc_status_message(rcf.plc_status_request_response_plc(response)))
	sort_messages('PLC operating mode: '+rcf.plc_mode(response))


def plc_get_rain_status(print_messages = True, log_messages = True):
	"""
	Issue commands to get the rain status from the PLC box
	
	PARAMETERS:
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
	"""
	print(rcf.PLC_Request_Roof_Status)
	response = rcf.plc_command_response(rcf.PLC_Request_Roof_Status)
	sort_messages('PLC response code: '+str(response))
	if rcf.plc_status_end_code(response):
		sort_messages('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		sys.exit(1)
	else:
		roof_status = rcf.plc_status_status_code(response)
		sort_messages('Response: '+str(response))
		if rcf.hex_bit_is_set(roof_status,rcf.PLC_CMD_BIT_RAIN) == True:
			sort_messages('PLC_Check_Rain')
		else:
			sort_messages('PLC_Ignore_Rain')
	sort_messages('PLC PC communications timeout: '+rcf.plc_status_comms_timeout(response))
	sort_messages('PLC Power failure timeout: '+rcf.plc_status_power_timeout(response))




def plc_get_roof_status(print_messages = True, log_messages = True):
	"""
	Sends the commands needed to get the roof status from the PLC box

	PARAMETERS:
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
		
	"""

	response = rcf.plc_command_response(rcf.PLC_Request_Roof_Status)
	sort_messages('PLC response code: '+str(response))
	if rcf.plc_status_end_code(response):
		sort_messages('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		sys.exit(1)
	else:
		roof_status = rcf.plc_status_status_code(response)

		# Roof Closed?
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Closed):
			sort_messages('PLC_Roof_Closed')
		# Roof open?
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Open):
			sort_messages('PLC_Roof_Open')

		# Roof moving?
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Moving):
			sort_messages('PLC_Roof_Moving')

		#Check Roof control Remote/Manual
		if rcf.int_bit_is_set(roof_status,rcf.PLC_Roof_Remote_Control):
			sort_messages('PLC_Roof_Remote_Control')
		else:
			sort_messages('PLC_Roof_Manual_Control')

		# Check rain status
		if rcf.int_bit_is_set(roof_status,rcf.PLC_Roof_Raining):
			sort_messages('PLC_Roof_Raining')
		else:
			sort_messages('PLC_Roof_No_Rain')

		# Check for forced rain closure
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Forced_Rain_Closure):
			sort_messages('PLC_Roof_Forced_Rain_Closure')
		else:
			sort_messages('PLC_Roof_No_Forced_Rain_Closure')

		# Building Temp High:
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Building_Temp_High):
			sort.messages('PLC_Roof_Building_Temp_High')

		# extractor fan
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Extractor_Fan_On):
			sort.messages('PLC_Roof_Extractor_Fan_On')
		else:
			sort_messages('PLC_Roof_Extractor_Fan_Off')

		# motor stop is pressed
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Motor_Stop_Pressed):
			sort_messages('PLC_Roof_Motor_Stop_Pressed')
		else:
			sort_messages('PLC_Roof_Motor__Stop_Not_Pressed')

		# AC Motor has tripped
		if rcf.int_bit_is_set(roof_status, PLC_Roof_AC_Motor_Tripped):
			sort_messages('PLC_Roof_AC_Motor_Tripped')
		else:
			sort_messages('PLC_Roof_AC_Motor_OK_No_Trip')

		# Using DC motor
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_DC_Motor_In_Use):
			sort_messages('PLC_Roof_DC_Motor_In_Use')
		else:
			sort_messages('PLC_Roof_AC_Motor_In_Use')


		#Close Proximity
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Close_Proximity):
			sort_messages('PLC_Roof_Close_Proximity')

		#Power failure
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Power_Failure):
			sort_messages('PLC_Power_Failure')


		#Force_Power_closure
		if rcf.int_bit_is_set(roof_status,rcf.PLC_Roof_Forced_Power_Closure):
			sort_messages('PLC_Roof_Forced_Power_Closure')

		# Open proximity
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Open_Proximity):
			sort_messages('PLC_Roof_Open_Proximity')

		#Door open
		if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Door_Open):
			sort_messages('PLC_Roof_Door_Open')

	sort_messages('PLC PC communications timeout: '+rcf.plc_status_comms_timeout(response))
	sort_messages('PLC Power failure timeout: '+rcf.plc_status_power_timeout(response))



def plc_open_roof(print_messages = True, log_messages = True, exit_after=True):
	"""
	Send the commands to open the roof. Will check the following:
	 - The roof interface is set to remote
	 - The motor Stop is not pressed
	 - The rain sensor is not triggered
	 - There is no power failure
	 
	PARAMETERS:
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
		
		exit_after = If True, will use sys.exit(0) to exit the script when successfully complete, but
			not if it is set to False. Again, useful if begin called from an executable script.
		
		messages can be both printed and logged.
	 
	"""
	response = rcf.plc_command_response(rcf.PLC_Request_Roof_Status)
	if rcf.plc_status_end_code(response):
		sort_messages('Error getting roof status from PLC:'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		sys.exit(1)

	roof_status = rcf.plc_status_status_code(response)

	if int_bit_is_set(roof_status, rcf.PLC_Roof_Remote_Control) == False:
		sort_messages('PLC not under roemote control')
		sys.exit(1)

	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Remote_Control):
		sort_messages('PLC motor stop is pressed')
		sys.exit(1)

	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Raining):
		sort_messages("It's RAINING!!")
		sys.exit(1)

	if rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Power_Failure):
		sort_messages('Power failure')
		sys.exit(1)

	# Get the current status of the command buffer words D-100 to D-102
	response = get_D100_D102_status

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	# Set the close roof command bit and unset the open roof command bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_OPEN)
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_CLOSE)

	#Create new command, sent it and deal with response
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)

	if exit_after == True:
		sys.exit(0)

def plc_request_roof_control(print_messages = True, log_messages = True, exit_after=True):
	"""
	Send the commands to request control of the roof
	
	PARAMETERS:
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
		
		exit_after = If True, will use sys.exit(0) to exit the script when successfully complete, but
			not if it is set to False. Again, useful if begin called from an executable script.
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

	if exit_after == True:
		sys.exit(0)

def plc_reset_watchdog(print_messages = True, log_messages = True, exit_after=True):
	"""
	Send the commands to reset the watchdog for the PLC box
	
	PARAMETERS:
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
			
		exit_after = If True, will use sys.exit(0) to exit the script when successfully complete, but
			not if it is set to False. Again, useful if begin called from an executable script.
	
	"""
	
	# Get the current status of the command buffer words D-100 to D-102
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)
	
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)
	
	if exit_after == True:
		sys.exit(0)


def plc_select_battery(print_messages = True, log_messages = True, exit_after=True):
	"""
	Send the commands to select the battery for the PLC box
	
	PARAMETERS:
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
		
		exit_after = If True, will use sys.exit(0) to exit the script when successfully complete, but
			not if it is set to False. Again, useful if begin called from an executable script.
	"""
	
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)
	
	# Set main/battery bit to 0 = battery
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_MAINS)

	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)
	
	if exit_after == True:
		sys.exit(0)

def plc_select_mains(print_messages = True, log_messages = True, exit_after=True):
	"""
	Send the commands to select the mains for the PLC box
	
	PARAMETERS:
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
		
		exit_after = If True, will use sys.exit(0) to exit the script when successfully complete, but
			not if it is set to False. Again, useful if begin called from an executable script.
	"""
	
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)
	
	# Set main/battery bit to 0 = battery
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_MAINS)

	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)
	
	if exit_after == True:
		sys.exit(0)

def plc_set_comms_timeout(timeout, print_messages = True, log_messages = True, exit_after=True):
	"""
	Send the commands to set the comms timeout for the PLC box
	
	PARAMETERS:
		
		timeout = timeout time in seconds, between 1 and 9999
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
		
		exit_after = If True, will use sys.exit(0) to exit the script when successfully complete, but
			not if it is set to False. Again, useful if begin called from an executable script.
	"""
	
	if timeout < 1 or timeout >9999:
		sort_messages('Invalid timeout value, 1 <= Timeout < 9999')
		sys.exit(1)

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

	if exit_after == True:
		sys.exit(0)

def plc_set_power_timeout(timeout, print_messages = True, log_messages = True, exit_after=True):
	"""
	Send the commands to set the power timeout for the PLC box
	
	PARAMETERS:
		
		timeout = timeout time in seconds, between 1 and 9999
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
		
		exit_after = If True, will use sys.exit(0) to exit the script when successfully complete, but
			not if it is set to False. Again, useful if begin called from an executable script.
	"""
	
	if timeout < 1 or timeout >9999:
		sort_messages('Invalid timeout value, 1 <= Timeout < 9999')
		sys.exit(1)

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

	if exit_after == True:
		sys.exit(0)


def plc_stop_roof(print_messages = True, log_messages = True, exit_after=True):

	"""
	Send the commands to stop the roof to the PLC box
	
	PARAMETERS:
		
		print_messages = If True, messages will be printed to the terminal. Default is true, so that
							scripts called from terminal will display messages.
		log_messages = If True, messages will be logged in the file plc.log.
		
		exit_after = If True, will use sys.exit(0) to exit the script when successfully complete, but
			not if it is set to False. Again, useful if begin called from an executable script.
	"""
	response = get_D100_D102_status()

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex = split_up_response(response)

	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	#Unset the close roof command bit and unset the open roof command bit
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_CLOSE)
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_OPEN)
	
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex)


	if exit_after == True:
		sys.exit(0)

