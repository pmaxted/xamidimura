#!/usr/bin/env python
"""
plc_status_request.py

 Will continually ask the PLC for its status...
"""

import roof_control_functions as rcf
import settings_and_error_codes as set_err_codes
import time
import logging
import mmap
import os
import struct
import ctypes
import subprocess

OPEN_ROOF_CHARACHTER = b'o'
CLOSE_ROOF_CHARACTER = b'c'
STOP_ROOF_CHARACTER = b's'

logger = logging.getLogger("plcd")
logger.setLevel(logging.INFO)
#fileHand = logging.FileHandler(filename = '/home/observer/xamidimura/xamidimur'\
#		'a/logfiles/plc_status.log', mode='w')
fileHand = logging.FileHandler(filename = set_err_codes.LOGFILES_DIRECTORY+'pl'\
	'c_status.log', mode='a')
fileHand.setLevel(logging.INFO)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s - '\
		'%(message)s','%Y-%m-%d_%H:%M:%S_UTC')
fileHand.setFormatter(formatter)
logger.addHandler(fileHand)

class PLC_ERROR(Exception):
	"""
	User defined error
	"""
	def __init__(self,message):
		self.message = message

def split_up_response(response):

	"""
	Takes a response message from the PLC and will split it up, and return the 
		frame, status_hex, power timeout hex, comm timeout hex and fcs_hex.
	 
	It will carry out a FCS check.
	
	This function is equivalent to the following section of code taken from the 
		orginial PHP scripts:
	
	PARAMETER
	
	 response = The response to be split
	
	RETURN:
		frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex
	"""
	if response[-2:] == '*\r' and response[:5] =='@00RD':
		frame = response[:-4]
		status_hex = response[7:11]
		power_timeout_hex = response[11:15]
		comms_timeout_hex = response[15:19]
		tilt_status_hex = response[19:23]
		fcs_hex = response[-4:-2]
		logger.debug('Frame: '+str(frame)+', fcs: '+fcs_hex+', status: '+str(
			status_hex))

		x = ord('@')
		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])
		logger.debug('x: '+ str(x)+ ', test: '+str(int(fcs_hex, 16) == x))
		if int(fcs_hex,16) != x:
			logger.error('Roof status FCS check fail: '+str(response))
			raise PLC_ERROR('Roof status FCS check fail: '+str(response))
	else:
		logger.error('Got invalid roof status from PLC: '+str(response))
		raise PLC_ERROR('Got invalid roof status from PLC: '+str(response))

	return frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex, \
		tilt_status_hex

def get_D100_D102_status(port):
	
	"""
	 Get the current status of the command buffer words D-100 to D-102. Will 
		check the end code, and report an error then exit if there was a problem
		getting the roof status.
	  
	RETURN:
		
		response - If the response from the PLC pass the check, then it will be 
			returned, otherwise Python will raise a PLC_Error exception.
			
			
	"""

	# Get the current status of the command buffer words D-100 to D-102
	#response = "@00RD000010232802580A0022*\r"
	
	response = rcf.plc_command_response_port_open(
		rcf.PLC_Command_Status_Request,port)
	#print(response)

	if rcf.plc_status_end_code(response):
		logger.error('Error getting command status from PLC: '+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		raise PLC_ERROR('Error getting command status from PLC : '+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))

	else:
		return response

def create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex,
		tilt_hex,port):
	"""
	This function will take the status, power timeout and comms timeout in 
	 hexadecimal format and use them to form a command to send to the PLC. 
	 It will check that the command is ok, if not then it will log an error 
	 message.
	 
	PARAMETERS:
	
		status_hex = The status of the roof as represented by 16 bits, converted
		to hex.
		
		power_timeout_hex = hex representation of the current power timeout
			setting
		
		comms_timeout_hex = hex representation of the current communtication 
			timeout setting
	
	"""
	#global plc_port
	cmd = "@00WD0100"+status_hex+power_timeout_hex+comms_timeout_hex+ \
			"00000000000000*\r"
	cmd = rcf.plc_insert_fcs(cmd)
	logger.debug('New command: '+cmd)
	response = rcf.plc_command_response_port_open(cmd, port)
	if response != rcf.PLC_Roof_Command_Response_OK:
		logger.error('Command failed:'+str(response))
		raise PLC_ERROR('Command failed:'+str(response))


def decode_tilt_status(tilt_status_hex):
	
	"""
	The tilt_status_hex should have come from the split up response function,
	 meaning the frame will have pass through an FCS check. Just need to convert 
	 straight to in and avoid using the function in the roof_control_functions
	 module.
	 
	PARAMETERS:
	
		tilt_status_hex = The tilt status of the telescope in hex representation
			and can be extracted stright from the plc roof response command.
			
	RETURN:
	
		tilt_dict = The decoded response represented as a dictionary
	"""
	tilt_dict = dict()
	tilt_dict['Tilt Response Code'] = tilt_status_hex
		
	tilt_status_int = int(tilt_status_hex, 16)

	tel_drive_control = rcf.int_bit_is_set(tilt_status_int,14)
	if tel_drive_control:
		tilt_status_int -= 16384
		tilt_dict['Tel_drive_control'] = 'Roof Controller'
	else:
		tilt_dict['Tel_drive_control'] = 'Normal - PC'

	valid_tilt_values = dict({	0:"1h East < x < 1h West",
		
							256:"1h East <= x < 6h East",
							1280:"6h East <= x < RA East limit", #two bits
							5376: "RA East limit", #3 bits
								
							512: "1h West <= x < 6h West",
							2560: "6h West <= x < RA West limit", #two bits
							10752: "RA West limit", #3 bits
							})
								
	try:
		message = valid_tilt_values[tilt_status_int]
	except KeyError:
		logger.error('Unexpected combination of tilt bits set')
		raise PLC_ERROR('Unexpected combination of tilt bits set')
				
	tilt_dict['Tilt_angle'] = message


	return tilt_dict

def request_remote_roof_control(port):

	response = get_D100_D102_status(port)
	#response = '@00RD00000A232802580A0052*\r'

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex,tilt_hex = split_up_response(response)
	logger.debug('Before WATCHDOG set status hex: '+str(status_hex))
	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	logger.debug('Before request: '+str(status_hex))
	#Set control request bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_REQ_CONTROL)
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex,
		tilt_hex,port)
	logger.debug('After request: '+str(status_hex))
	#Unset control request bit
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_REQ_CONTROL)
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex,
		tilt_hex,port)
	logger.debug('reset request: '+str(status_hex))


def request_telescope_drive_control(port):
	"""
	Send the commands to request control of the telescope drive. NEW FUNCTION...
	
	"""
	response = get_D100_D102_status(port)
	#response = '@00RD00000A232802580A0052*\r'

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex,tilt_hex = split_up_response(response)
	logger.debug('Before WATCHDOG set status hex: '+str(status_hex))
	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	logger.debug('Telescope_drive: Before request: '+str(status_hex))
	#Set control request bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_REQ_TELE_CONTROL)
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex,
		tilt_hex, port)
	logger.debug('After request: '+str(status_hex))
	#Unset control request bit
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_REQ_TELE_CONTROL)
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex,
		tilt_hex, port)
	logger.debug('reset request: '+str(status_hex))

def select_mains(port):

	response = get_D100_D102_status(port)
	#repsonse = '@00RD00000A232802580A0052*\r'

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex,tilt_hex = split_up_response(response)

	logger.debug('Select Main:Before request: '+str(status_hex))
	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)
	
	# Set main/battery bit to 0 = battery
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_MAINS)

	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex,
		tilt_hex,port)
	logger.debug('After request: '+str(status_hex))

def motor_stop_check(roof_status):
	"""
	 Check if the motor stop is pressed.
	
	"""
	motor_stop_pressed_bool = rcf.int_bit_is_set(roof_status,
		rcf.PLC_Roof_Motor_Stop_Pressed)
	if motor_stop_pressed_bool == True:
		logger.error('PLC motor stop is pressed')
	else:
		logger.info('Motor stop NOT pressed')

	return motor_stop_pressed_bool

def remote_control_check(roof_status, port):
	"""
	 Check the roof is set for remote control
	"""
	remote_control_bool = rcf.int_bit_is_set(roof_status,
		rcf.PLC_Roof_Remote_Control)
	
	if remote_control_bool == False:
	
		logger.warning('PLC is not under remote control. Attempting to '\
			'request control')
		try:
			request_remote_roof_control(port)
		
		except:
			logger.error('Cannot request remote roof control')

		else:
			response = rcf.plc_command_response_port_open(
				rcf.PLC_Request_Roof_Status, port)

		
			if rcf.plc_status_end_code(response):
				logger.error('Error getting roof status from PLC'\
				':'+ rcf.plc_status_error_message(rcf.plc_status_end_code(
					response)))
		
				raise PLC_ERROR('Error getting roof status from PLC'\
				':'+ rcf.plc_status_error_message(rcf.plc_status_end_code(
					response)))

			frame, roof_status_hex, power_hex, comms_hex, fcs_hex, tilt_hex = split_up_response(response)
			
			roof_status = int(roof_status_hex,16)
			remote_control_bool = rcf.int_bit_is_set(roof_status,
				rcf.PLC_Roof_Remote_Control)
	
			if remote_control_bool == True:
				logger.info('Remote control succesfully requested.')
			else:
				logger.error('Cannot request remote roof control')

	else:
		logger.info('Roof control set to remote')

	return remote_control_bool

def telescope_tilt_check(tilt_hex, port):

	# Take the tilt hex code and turn it into something that is a bit easier
	#  to work with
	tilt_status_dict = decode_tilt_status(tilt_hex)
	
	# Check to make sure the telescope is parked...
	telescope_parked_bool = \
		tilt_status_dict['Tilt_angle'] == "6h East <= x < RA East limit" or \
		tilt_status_dict['Tilt_angle'] == "6h West <= x < RA West limit" or \
		tilt_status_dict['Tilt_angle'] == "RA East limit" or \
		tilt_status_dict['Tilt_angle'] == "RA West limit"

	if telescope_parked_bool == False:
		print('TELESCOPE NOT PARKED! - Requesting move...')
		logger.warning('Telescopes NOT parked - Requesting move...')

		try:
			# Run the park command on the TCS, via ssh. If completed, will
			#  respond with random messages, with the exit code at the end
			#  exit code should be '0' id completed properly, otherwise
			#  assume can't park the telescopes
			output = subprocess.run(['ssh','wasp@tcs','park ; echo $?'],
				capture_output=True)
			exit_code = output.stdout.decode('utf-8').split('\n')[-2]
			
			if exit_code != '0':
				logger.error('Failed to park telescopes. Exit code:'+str(
					exit_code))
				raise PLC_ERROR('Failed to park telescopes. Exit code:'+str(
					exit_code))
				
		except:
			print('CANNOT CLOSE ROOF, TELESCOPES NOT PARKED AND'\
				' CANNOT BE MOVED')
			logger.critical('CANNOT CLOSE ROOF, TELESCOPES NOT PARKED AND'\
				' CANNOT BE MOVED')
				
		else:
			#Check tilt status again
			response = rcf.plc_command_response_port_open(
				rcf.PLC_Request_Roof_Status, port)

			if rcf.plc_status_end_code(response):
				logger.error('Error getting roof status from PLC'\
					':'+ rcf.plc_status_error_message(rcf.plc_status_end_code(
					response)))
		
				raise PLC_ERROR('Error getting roof status from PLC'\
				':'	+ rcf.plc_status_error_message(rcf.plc_status_end_code(
					response)))

			frame, roof_status_hex, power_hex, comms_hex, fcs_hex, tilt_hex = split_up_response(response)
				
			tilt_status_dict = decode_tilt_status(tilt_hex)
			telescope_parked_bool = \
			 tilt_status_dict['Tilt_angle'] == "6h East <= x < RA East limit" or\
			 tilt_status_dict['Tilt_angle'] == "6h West <= x < RA West limit" or\
			 tilt_status_dict['Tilt_angle'] == "RA East limit" or \
			 tilt_status_dict['Tilt_angle'] == "RA West limit"
		
			if telescope_parked_bool == False:
				logger.critical('CANNOT CLOSE ROOF, TELESCOPES NOT PARKED AND'\
				' CANNOT BE MOVED')
				print('CANNOT CLOSE ROOF, TELESCOPES NOT PARKED AND'\
				' CANNOT BE MOVED')
			else:
				logger.info('Telescopes now parked')
			
	else:
		logger.info('Telescopes ARE parked.')
	
	return telescope_parked_bool,tilt_status_dict

def stop_roof_instructions(port):

	# Th gets the current command status, which is required to create a new
	#  command that will set various bits on the PLC
	response = get_D100_D102_status(port)

	frame, status_hex,power_timeout_hex, comms_timeout_hex, fcs_hex, tilt_hex = split_up_response(response)

	logger.debug('Set comms:Before request: '+str(status_hex))
	# Reset the watchdog timer bit
	status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_WATCHDOG_RESET)

	#Unset the close roof command bit and unset the open roof command bit
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_CLOSE)
	status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_OPEN)
	
	create_and_send_new_command(status_hex,power_timeout_hex,comms_timeout_hex,
		tilt_hex, port)
	logger.debug('After request: '+str(status_hex))

	return set_err_codes.PLC_CODE_OK




def close_roof_instructions(port):

	"""
	Issue the commands to close the roof via the PLC box
	
	# Check the following conditions first.
	# - Is not already closed
	# - Where is the telescope pointing, needs to be parked. Will attempt to
			the telescopes if need be
	# - The Roof interface is set to Remote - can request to change it from 
			manual.
	# - The Motor Stop is not pressed - can't do anything if it is.
	
	# - If the telescopes need to be moved, request telescope drive control to
		move them. If close but just plc response, request telescope drive after
		to prevent drifting
		
	# - AC motor has not tripped - Not sure if this will be an issue with UPS 
		etc, but will keep it for now
		
		
	***  and check ups is alive
	
	RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the
			code has completed
	
	"""

	#Get a status response from the PLC and check the response

	response = rcf.plc_command_response_port_open(rcf.PLC_Request_Roof_Status,
		port)
		
	if rcf.plc_status_end_code(response):
		logger.error('Error getting roof status from PLC'\
		  ':'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		
		raise PLC_ERROR('Error getting roof status from PLC'\
		  ':'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))

	frame, roof_status_hex, power_hex, comms_hex, fcs_hex, \
				tilt_hex = split_up_response(response)

	logger.info('Roof close checks:')
	
	roof_status = int(roof_status_hex,16)
	# The roof status hex will have been through a fcs check when the plc
		#  response was split up, so can change it to an int and then use it
		
		
	# Is it already closed:
	roof_close_bool = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Closed)
	if roof_close_bool == True:
		logger.warning('Roof is already closed')
		return set_err_codes.PLC_CODE_OK
	
	else:
	
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		#  Tilt checks
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
		telescope_parked_bool,tilt_status_dict = telescope_tilt_check(
			tilt_hex,port)

		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		#  Roof status checks
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


		# Check the roof is set for remote control
		remote_control_bool = remote_control_check(roof_status, port)
				
		# Check if the motor stop is pressed.
		motor_stop_pressed_bool = motor_stop_check(roof_status)

		# Check to see if there is suitable power to close the roof, even if it
		#  is via UPS
	
		suitable_power_bool = True
		# Make sure the motor is set to AC motor, and that it has not tripped.
		#  The DC power bit should not get set with the new UPS stuff, but just
		#  in case check and ask to swap to AC if it is
		use_battery_bool = rcf.int_bit_is_set(roof_status,
			rcf.PLC_Roof_DC_Motor_In_Use)
		if use_battery_bool == True:
			suitable_power_bool = False
			logger.warning('DC motor bit is set, requesting use of AC motor..')
			try:
				select_mains(port)
			except:
				logger.error('Cannot request AC motor.')
			else:
				response = rcf.plc_command_response_port_open(
					rcf.PLC_Request_Roof_Status, port)

		
				if rcf.plc_status_end_code(response):
					logger.error('Error getting roof status from PLC'\
					':'+ rcf.plc_status_error_message(rcf.plc_status_end_code(
					response)))
		
					raise PLC_ERROR('Error getting roof status from PLC'\
					':'+ rcf.plc_status_error_message(rcf.plc_status_end_code(
						response)))

				frame, roof_status_hex, power_hex, comms_hex, fcs_hex, \
					tilt_hex = split_up_response(response)
			
				roof_status = int(roof_status_hex,16)
				
				
				use_battery_bool == rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_DC_Motor_In_Use)
				if use_battery_bool == False:
					logger.info('AC motor successfully requested')
					suitable_power_bool = True
				else:
					logger.error('Cannot request AC motor use')
					raise PLC_ERROR('Cannot request AC motor use')
		else:
			logger.info('Battery not in use')

		# If the roof is set to use the AC motor and there is a power cut, will
		#  need to make sure that it can use the UPS to close...

		power_failure_bool = rcf.int_bit_is_set(roof_status,
			rcf.PLC_Roof_Power_Failure)

		if use_battery_bool == False and power_failure_bool == True:
			suitable_power_bool = False
			print('Add code to check UPS is available')
			logger.error('Add code to check UPS is available')
			ups_available = True
			if ups_available == True:
				print('Power failure! but UPS available to close roof')
				suitable_power_bool = True
			else:
				print('Power failure and no UPS power')
				logger.critical('Power failure and no UPS power. NEED to close'\
					' roof')

		else:
			logger.info('No power failure, or still thinks battery in use.')


		# Check if the AC motor has tripped?
		motor_tripped_bool = rcf.int_bit_is_set(roof_status,
			rcf.PLC_Roof_AC_Motor_Tripped)

		if use_battery_bool == False and motor_tripped_bool == True:
			suitable_power_bool = False
			logger.error('AC motor has tripped.')
			raise PLC_ERROR('AC motor has tripped.')

		else:
			logger.info('No motor trip')


		# Telescope drive control
		if tilt_status_dict['Tel_drive_control'] == 'Roof Controller':
			try:
				request_telescope_drive_control(port)
			except:
				logger.error('Unable to request telescope drive control, teles'\
					'cope maybe drifting')
		else:
			logger.info('Telescope drive control is normal')

		# if the telescope is parked, under remote control, motor stop not
		#  pressed and suitable power, the roof can be closed. If not send
		#  critical cannot close roof message

		if telescope_parked_bool == True and remote_control_bool == True and motor_stop_pressed_bool == False and suitable_power_bool == True:
		
			logger.info('Going to attempt to close roof....')


			# Get the current status of the command buffer words D-100 to D-102
			response = get_D100_D102_status(port)

			frame, status_hex,power_hex, comms_hex, fcs_hex, tilt_hex = \
				split_up_response(response)

			logger.debug('Before WATCHDOG set status hex: '+str(status_hex))
			# Reset the watchdog timer bit
			status_hex = rcf.set_hex_bit(status_hex,
				rcf.PLC_CMD_BIT_WATCHDOG_RESET)

			logger.debug('Closed bit set status hex: '+str(status_hex))
			# Set the close roof command bit and unset the open roof command bit
			status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_OPEN)
			status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_CLOSE)
			logger.debug('Open bit unset status hex: '+ str(status_hex))

			create_and_send_new_command(status_hex,power_hex,
				comms_hex,tilt_hex, port)


			# Request telescope drive control to prevent grinding...
			try:
				request_telescope_drive_control(port)
			except:
				logger.error('Unable to request telescope drive control, teles'\
					'cope maybe drifting')
			else:
				logger.info('Roof closing....')

				# Wait to make sure the roof has started moving, then check the
				# status
				time.sleep(5)
				response = rcf.plc_command_response_port_open(
					rcf.PLC_Request_Roof_Status, port)
					
				roof_status = rcf.plc_status_status_code(response)
				roof_moving = rcf.int_bit_is_set(roof_status,
					rcf.PLC_Roof_Moving)
					
				# Keep check status until it have stopped moving
				while roof_moving == True:
	
					logger.info('Roof is still moving...')
					time.sleep(2)
					response = rcf.plc_command_response_port_open(
						rcf.PLC_Request_Roof_Status, port)
					
					roof_status = rcf.plc_status_status_code(response)
					roof_moving = rcf.int_bit_is_set(roof_status,
							rcf.PLC_Roof_Moving)

				else:
				
					logger.info('ROOF CLOSED')
					print('ROOF CLOSED')

			return set_err_codes.PLC_CODE_OK

		else:
			logger.critical('CANNOT CLOSE ROOF!!')

def open_roof_instructions(port):
	"""
	Send the commands to open the roof.
	
	# Check the following conditions first.
	# - Is not already open
	# - Where is the telescope pointing, needs to be parked - not safe to move
			if not.
	# - The Roof interface is set to Remote - can request it.
	# - The Motor Stop is not pressed - can't do anything if it is.
	# - check the weather, not raining and probably not really windy.
	# - Normal telescope drive control
	# - If theres a power cut, need to check with UPS first, Fo now not open
	
	 RETURN
	 
		PLC_CODE_OK, from the settings and errors codes script, to show that the
			code has completed
	 
	"""


	#Get a status response from the PLC and check the response

	response = rcf.plc_command_response_port_open(rcf.PLC_Request_Roof_Status,
		port)
		
	if rcf.plc_status_end_code(response):
		logger.error('Error getting roof status from PLC'\
		  ':'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))
		
		raise PLC_ERROR('Error getting roof status from PLC'\
		  ':'+ rcf.plc_status_error_message(rcf.plc_status_end_code(response)))

	frame, roof_status_hex, power_hex, comms_hex, fcs_hex, tilt_hex = \
		split_up_response(response)

	logger.info('Roof open checks:')
	
	roof_status = int(roof_status_hex,16)
	# The roof status hex will have been through a fcs check when the plc
		#  response was split up, so can change it to an int and then use it

	# Is it already open:
	roof_open_bool = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Open)

	if roof_open_bool == True:
		logger.warning('Roof is already open')
		return set_err_codes.PLC_CODE_OK
	
	else:
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		#  Weather checks
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		
		raining_bool = rcf.int_bit_is_set(roof_status, rcf.PLC_Roof_Raining)
		if raining_bool == True:
			logger.error("It's RAINING!!")
		else:
		
			#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
			#  Tilt checks
			#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
			# Take the tilt hex code and turn it into something that is a bit
			# easier to work with
			tilt_status_dict = decode_tilt_status(tilt_hex)

			# Check to make sure the telescope is parked...
			telescope_parked_bool = \
				tilt_status_dict['Tilt_angle']=="6h East <= x < RA East limit"\
				or tilt_status_dict['Tilt_angle']=="6h West <= x < RA West limit"\
				or tilt_status_dict['Tilt_angle'] == "RA East limit"\
				or tilt_status_dict['Tilt_angle'] == "RA West limit"

			if telescope_parked_bool == False:
				print('TELESCOPE NOT PARKED!')
				logger.warning('Telescopes NOT parked - Unsafe to move')
		
			else:
				logger.info('Telescopes ARE parked.')

			#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
			#  Roof status checks
			#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


			# Check the roof is set for remote control
			remote_control_bool = remote_control_check(roof_status,port)

			# Check if the motor stop is pressed.
			motor_stop_pressed_bool = motor_stop_check(roof_status)

			suitable_power_bool = False
			# Check for a power failure - eventually will check the UPS as well
			power_failure_bool = rcf.int_bit_is_set(roof_status,
				rcf.PLC_Roof_Power_Failure)

			if power_failure_bool == True:
				suitable_power_bool = False
				#put in UPS check
			else:
				suitable_power_bool = True


			# Telescope drive control
			if tilt_status_dict['Tel_drive_control']:
				try:
					request_telescope_drive_control(port)
				except:
					logger.error('Unable to request telescope drive control, '\
						'telescope maybe drifting')
			else:
				logger.info('Telescope drive control is normal')

			
		# if the telescope is parked, under remote control, motor stop not
		#  pressed and suitable power, it's not raining, the roof can be opened.
		
			if raining_bool == False and telescope_parked_bool == True and \
				remote_control_bool == True and \
				motor_stop_pressed_bool == False and \
				suitable_power_bool == True:
		
				logger.info('Going to attempt to open roof....')

				# Get the current status of the command buffer words D-100 to D-102
				response = get_D100_D102_status(port)
				logger.debug('D100 response: '+str(response))
				frame, status_hex,power_timeout_hex, comms_timeout_hex, \
					fcs_hex, tilt_hex = split_up_response(response)
	
				logger.debug('Before WATCHDOG set status hex: '+str(status_hex))
				# Reset the watchdog timer bit
				status_hex = rcf.set_hex_bit(status_hex,
					rcf.PLC_CMD_BIT_WATCHDOG_RESET)

				logger.debug('Closed bit set status hex: '+str(status_hex))
				# Set the close roof command bit and unset the open roof
				#  command bit
				status_hex = rcf.set_hex_bit(status_hex, rcf.PLC_CMD_BIT_OPEN)
				status_hex = rcf.unset_hex_bit(status_hex, rcf.PLC_CMD_BIT_CLOSE)
				logger.debug('Open bit set status hex: '+ str(status_hex))

				#Create new command, sent it and deal with response
				create_and_send_new_command(status_hex,power_timeout_hex,
					comms_timeout_hex, tilt_hex, port)

				logger.info('Roof opening....')


				# Wait to make sure the roof has started moving, then check the
				# status
				time.sleep(5)
				response = rcf.plc_command_response_port_open(
					rcf.PLC_Request_Roof_Status, port)
					
				roof_status = rcf.plc_status_status_code(response)
				roof_moving = rcf.int_bit_is_set(roof_status,
					rcf.PLC_Roof_Moving)

				# Keep check status until it have stopped moving
				while roof_moving == True:
					logger.info('Roof is still moving...')
					time.sleep(2)
					response = rcf.plc_command_response_port_open(
						rcf.PLC_Request_Roof_Status, port)
					
					roof_status = rcf.plc_status_status_code(response)
					roof_moving = rcf.int_bit_is_set(roof_status,
						rcf.PLC_Roof_Moving)
					

				else:
					logger.info('ROOF OPENED')
					print('ROOF OPENED')

				return set_err_codes.PLC_CODE_OK

			else:
				logger.error('Unable to OPEN roof.')


def main():
	
	# define a list of valid characters to use
	valid_chars =[OPEN_ROOF_CHARACHTER,CLOSE_ROOF_CHARACTER,STOP_ROOF_CHARACTER,
		None]
	
	#open the port to the plc
	plc_port = rcf.open_plc_port()
	
	# Open the file for reading
	fd = os.open(set_err_codes.PLC_MEMORY_MAP_FILE_LOC, os.O_CREAT | os.O_RDWR)
	
	# Memory map the file, it matter which way round these parameters are!
	#buf = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED)#, mmap.PROT_READ)
	try:
		buf = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED)
	except ValueError:
		# Zero out the file to insure it's the right size
		assert os.write(fd, b'\x00' * mmap.PAGESIZE) == mmap.PAGESIZE
		buf = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED)	
	
	
	old_char = None
	# On the first pass through, want to set the roof state to stop, before
	#  we try to get it to do anything.
	first_pass_through = True
	
	while 1:
		
		# Without this if the memory state is set to open(o) or close(c) the
		#  roof can move unexpectedly when this script is restarted. Set state
		# to stop(s) on the first time through the loop
		if first_pass_through ==True:
			s_type = ctypes.c_char * len('c')
			s = s_type.from_buffer(buf)
			s.raw = bytes('s', 'utf-8')
			first_pass_through = False
		
		# read in any new value in the memory map
		new_char, = struct.unpack('1s', buf[:1])
	
		# check that the value is a valid charachter before a trying to do
		#  anything with it.
		if new_char not in valid_chars:
			logger.warning('Invalid roof status character provided, use '\
					'"o" "c" or "s"')
			print('Invalid character provided.',
			old_char.decode('utf-8'))
			time.sleep(2)
			continue
	
		else:
			if new_char != old_char and old_char != None:
		
				logger.info('Detected status change request: '+
					new_char.decode('utf-8')+' from '+old_char.decode('utf-8'))
				print('Detected status change request: '+
                    new_char.decode('utf-8')+' from '+old_char.decode('utf-8'))
				if new_char == b's':
					#print('Do stuff to stop roof')
					ok_code = stop_roof_instructions(plc_port)
					if ok_code == 0:
						logger.info('Roof movement stopped')
						print('ROOF STOPPED')
					else:
						logger.critical('Unable to stop roof')
				
				elif new_char == b'c':
					#print('Do stuff to close roof')
					ok_code = close_roof_instructions(plc_port)
					if ok_code != set_err_codes.PLC_CODE_OK:
						logger.critical('Unable to CLOSE roof')
					else:
						print('ROOF stopped closing')
					
				elif new_char == b'o':
					#print('Do stuff to check roof can open')
					ok_code = open_roof_instructions(plc_port)
					if ok_code != set_err_codes.PLC_CODE_OK:
						logger.error('Unable to OPEN roof')
					else:
						print('ROOF stopped opening')
					
				else:
					logger.error('Invalid character received')
					print('Invalid character received')
					
				old_char = new_char
				time.sleep(2)
			
			
			elif new_char != old_char and old_char == None:
				logger.debug('update new char')
				print('Update')
				old_char = new_char
				time.sleep(2)
			
			else:
				print('Nothing')
				logger.debug('Nothing changed')
				time.sleep(2)
				continue


if __name__ == '__main__':
    main()
