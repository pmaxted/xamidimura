"""
 roof_function_controls.py
 
 Low level functions for the communication with Pieter Fourie's PLC Intelligent Roof Controller system at the Xamidiura telescope (originally SuperWASP South).
  
 As translated from the php script originally written by Pierre Maxted, Sep 2015

 <13/11/18> ** Note, most of the functions have not been properly tested, as they require the PLC to actually be connected. Also for the Xamidimura telescope need to add
	in the functions and code to work with the new tilt sensors.
	
	- Also no stty settings are set when the port to the PLC is open. It may be possible
	 to use subprocess to set them if needed, however the Python functions don't really
	 interact with the terminal so I think there not needed - needs to be tested

"""

import serial

# Configuration parameters
PLC_COM_PORT = 'COM6'
PLC_BAUD_RATE = 9600
PLC_PARITY = 'E'#'PARITY_EVEN'
PLC_STOP_BITS = 2#'STOPBITS_TWO'
PLC_CHARACTER_LENGTH = 7#7
PLC_FLOW_CONTROL = 'none' # Not currently used
PLC_STTY_SETTINGS = 'time 5 crtscts ignbrk -icrnl -opost -onlcr -isig -icanon -iexten -echo -echoe -echok -echoctl -echoke'
"""
time 5 =
crtscts = enable RTS/CTS handshaking [Python - This is set when port is opened]
-ignbrk = ignore break charaters
-icrnl = translate carriage return to newline
-opost = postprocess output
-onlcr = translate newline to carriage return-newline
-isig = enable interrupt, quit, suspend special characters
-icanon = enable erase, kill, werase, and rprnt special characters
-iexten = enable non-POSIX special characters
-echo = echo input characters
-echoe=  same as [-]crterase
-echok = echo a newline after a kill character
-echoctl = same as [-]ctlecho
-echoke = same as [-]crtkill
"""

#Standard input/output
PLC_Status_Request = '@00MS5E*\r'
PLC_Status_Write  = '@00SC0252*\r'
PLC_Status_Write_Response = '@00SC0050*\r'
PLC_Request_Roof_Status = '@00RD0150000351*\r'
PLC_Roof_Command_Response_OK = '@00WD0053*\r'
# This is an undocumented command to get the current status of the command
# buffer (Data memory 100). See e-mail from Keegan Titus <keegan@saao.ac.za>
# to p.maxted@keele.ac.uk 29 Sep 2015.
PLC_Command_Status_Request = '@00RD0100000354*\r'

# Bits in D-memory location 100 for each command, updated for the new PLC controller
PLC_CMD_BIT_CLOSE = 0	# 1 = close
PLC_CMD_BIT_OPEN = 1	# 1 = open
PLC_CMD_BIT_MAINS = 2	# 1 = mains
PLC_CMD_BIT_RAIN = 4	# (on/off) 1 = Rain Det. on
PLC_CMD_BIT_REQ_CONTROL = 8 # Set to 1 briefly
PLC_CMD_BIT_SET_POWER_DELAY = 12
PLC_CMD_BIT_SET_COMMS_DELAY = 13
PLC_CMD_BIT_REQ_TELE_CONTROL = 14 # NEW!!!
PLC_CMD_BIT_WATCHDOG_RESET = 15

# Roof status bits
PLC_Roof_Closed = 0
PLC_Roof_Open = 1
PLC_Roof_Moving = 2
PLC_Roof_Remote_Control = 3 #remote control =1
PLC_Roof_Raining = 4 #1 = Raining
PLC_Roof_Forced_Rain_Closure = 5 # 1 = Forced closed due to rain
PLC_Roof_Building_Temp_High = 6 # 1 = Building temp is high
PLC_Roof_Extractor_Fan_On = 7 # 1 =  Extractor fan on
PLC_Roof_Motor_Stop_Pressed = 8 # 1 = stopped pressed
PLC_Roof_AC_Motor_Tripped = 9 # 0 = AC Motor OK 1 = AC motor tripped
PLC_Roof_DC_Motor_In_Use = 10 # 0 = AC motor in use 1 = Battery motor in use
PLC_Roof_Close_Proximity = 11 # 1 = Proximity triggered
PLC_Roof_Power_Failure = 12 # 1 = Mains Failure
PLC_Roof_Forced_Power_Closure = 13 #1 = Mains Failure Forced Closure
PLC_Roof_Open_Proximity = 14
PLC_Roof_Door_Open = 15

# NEW But no functions yet....
# Bits in D-memory 153
PLC_Tilt_1hour_East = 8
PLC_Tilt_1hour_West = 9
PLC_Tilt_6hours_East = 10
PLC_Tilt_6hours_West = 11
PLC_RA_Limit_East = 12
PLC_RA_Limit_West = 13
PLC_Telescope_Drive_Control = 14 # 0=Normal, 1=Roof controller

def plc_command_response(command=PLC_Status_Request):
	"""
	Sends a single PLC command, returns the response or FALSE if there is any problem.
	 PLC command must include terminating "*\r"
  
		PARAMETERS
	
			command = the command to send to the PLC. By default it is the status check command.
	
		RETURN
			response = The response from sending the command, if it was a vali command
			False = The command was not a valid command.
  
	"""
	if plc_string_is_valid(command):
	
	
		open_port = serial.Serial(port = PLC_COM_PORT, baudrate = PLC_BAUD_RATE, parity=PLC_PARITY, stopbits = PLC_STOP_BITS, bytesize = PLC_CHARACTER_LENGTH,rtscts = True)
		#???set stty settings?
		
		open_port.write(command.encode('utf-8'))
		response = open_port.read_until().decode('utf-8')
		open_port.close()

		return response


	else:
		raise ValueError("Request to send invalid PLC command")
		return False

def plc_string_is_valid(plc_string):
	"""
	 Return TRUE if:
		- plc_string has a leading "@"
		- and plc_string contains the correct node number (00)
		- and plc_contains a header code (validity of the code is not checked)
		- and plc_string has a trailing "*<CR>"
		- and The Frame Check Sequence (FCS) of $plc_string is correct
		else return false.
		
	PARAMETERS:
	
		plc_string = the string to be checked
	"""
	if plc_string[0] == '@' and plc_string[:3] == '@00' and plc_string[-2:] =='*\r' and len(plc_string[3:-2])!=0:
		frame = plc_string[:-4]
		fcs = plc_string[-4:-2]

		x = ord('@')
		
		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])


		return int(fcs, 16) == x

def plc_insert_fcs(plc_string):
	"""
	If
		- plc_string has a leading "@"
		- and plc_string contains the correct node number (00)
		- and plc_contains a header code (validity of the code is not checked)
		- and plc_string has a trailing "00*<CR>"
 	then
		- return original string but with the trailing "00" replaced with the
			correct Frame Check Sequence (FCS)
	else
		-  return false.
	"""
	if plc_string[0] == '@' and plc_string[:3] == '@00' and plc_string[-2:] =='*\r' and len(plc_string[3:-2])!=0:
		frame = plc_string[:-4]
		oldfcs = plc_string[-4:-2]
		terminator = plc_string[-2:]
		#print(frame,oldfcs,terminator)

		x = ord('@')
		
		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])

		return (str(frame)+hex(x)+str(terminator)).upper()

	else:
		return False

def plc_mode(plc_string):
	"""
	 If
		- plc_string is a valid PLC status, request response string
	then
		- return a string with the PLC operating mode
	else
		- return "Invalid PLC status request response string"
	
	*** Not tested **
	"""
	if plc_string[-2:] == '*\r' and plc_string[0] == '@' and plc_string[:8] =='@00MS000':
		frame = plc_string[:-4]
		fcs = plc_string[-4:-2]
		mode = plc_string[8] # This really needs to be checked
		x = ord("@")

		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])

		if int(fcs, 16) == x:
			if mode == int("0",16):
				return "Program mode"
			elif mode == int("2", 16):
				return "Run mode"
			elif mode == int("3", 16):
				return "Monitor Mode"
			else:
				return "Unknown mode: "+mode
		else:
			return "Invalid PLC status request response string"
	else:
		return "Invalid PLC status request response string"


def plc_status_request_response_plc(plc_string):
	"""
	If
		- plc_string is a valid PLC status request response string
	then
		- return the byte in the status data that contains the PLC status (16^3)
	else
		- return 15 (i.e., hex "F")
 
	For normal completion the end code is 0, so this function can be used 
	 in the following way.

	>>> if (plc_status_request_response_plc(plc_string))
	>>>     print("Problem with PLC: ")
	>>>     print(plc_status_message(plc_status_request_response_plc(plc_string))+"\n")

	PARAMETERS:
	
		plc_string = response string from the initial plc request
	
	RETURN
	
		The byte from the status data that contains the PLC status
		
		OR
		
		15 (hex "F")
		
	** Not Tested ***

	"""

	if plc_string[-2:] == '*\r' and plc_string[0] == '@' and plc_string[:7] =='@00MS00':
		frame = plc_string[:-4]
		fcs = plc_string[-4:-2]
		status = plc_string[7] # This really needs to be checked

		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])

		if int(fcs, 16) == x:
			return int(status, 16)
		else:
			return 15
	else:
		return 15

def plc_status_message(status):
	"""
	Return the error message corresponding to the byte status for a PLC status 
		request response string PLC status byte (or "Normal" if status is 0).
		If no such error message return "Unknown status code".
	
	PARAMETER:
	
		status - The status code to be compared
		
	RETURN
	
		message = The message corresponding to that status
	"""

	if status == int("0", 16):
		message = "Normal"
	
	elif status == int("1", 16):
		message = "Fatal error"

	elif status == int("8",16):
		message = "FALS error"

	else:
		message = "Unknown error code: "+str(status)

	return message


def plc_status_comms_timeout(plc_string):
	"""
	If
		plc_string is a valid PLC roof status string for normal completion
	then
		return the current power timeout as a decimal number
	else
		return 255
	
	PARAMETERs:
	
		plc_string = the response from the plc
		
	RETURN
	
		Either the current power timeout, or 255
		
	**NOT TESTED***
		
	"""

	if plc_string[-2:] == '*\r' and plc_string[0] == '@' and plc_string[:7] =='@00RD00':
		frame = plc_string[:-4]
		fcs = plc_string[-4:-2]
		timeout = plc_string[-7:-3] # This really needs to be checked

		x = ord('@')

		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])

		if int(fcs, 16) == x:
			return int(timeout, 16)
		else:
			return 255
	else:
		return 255

def plc_status_power_timeout(plc_string):
	"""
	If
		plc_string is a valid PLC roof status string for normal completion
	then
		return the current power timeout as a decimal number
	else
		return 255
	
	PARAMETERs:
	
		plc_string = the response from the plc
		
	RETURN
	
		Either the current power timeout, or 255
		
	**NOT TESTED***
		
	"""

	if plc_string[-2:] == '*\r' and plc_string[0] == '@' and plc_string[:7] =='@00RD00':
		frame = plc_string[:-4]
		fcs = plc_string[-4:-2]
		timeout = plc_string[11:15] # This really needs to be checked


		x = ord('@')
		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])

		if int(fcs, 16) == x:
			return int(timeout, 16)
		else:
			return 255
	else:
		return 255

def plc_status_status_code(plc_string):
	"""
	If
	 - plc_string is a valid PLC roof status string for normal completion
	then 
	 - return the status code as a decimal number
	else
	 - return 255
	 
	PARAMETERS:
	
		plc_string = the response string from plc.
	
	RETURN:
	
		Either:
		 - the status code as a decimal number
		 OR
		 - 255
	"""
	if plc_string[-2:] == '*\r' and plc_string[0] == '@' and plc_string[:7] =='@00RD00':
		frame = plc_string[:-4]
		fcs = plc_string[-4:-2]
		status = plc_string[-7:-3] # This really needs to be checked

		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])

		if int(fcs, 16) == x:
			return int(status, 16)
		else:
			return 255
	else:
		return 255

def plc_status_end_code(plc_string):
	"""
	If
	 - plc_string is a valid PLC roof status string
	then
	 - return the end code as a decimal number
	else
	 - return 255
 
	For normal completion the end code is 0, so this function can be used
	 in the following way.
 
	>>> if (plc_status_end_code(plc_string))
	>>>		print("Problem getting roof status from PLC: ")
	>>>		print(plc_error_message(plc_status_end_code(plc_string))+"\n")

	"""
	if plc_string[-2:] == '*\r' and plc_string[0] == '@' and plc_string[:5] =='@00RD':

		frame = plc_string[:-4]
		fcs = plc_string[-4:-2]
		endcode = plc_string[5:7] # This really needs to be checked


		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])

		if int(fcs, 16) == x:
			return int(endcode, 16)
		else:
			return 255
	else:
		return 255


def plc_status_write_response_end_code(plc_string):
	"""
	If
	 - plc_string is a valid PLC status write response string
	then
	 - return the end code as a decimal number
	else
	 - return 255
	 
	For normal completion the end code is 0, so this function can be used
	 in the following way.
	
	>>> if (plc_error_code(plc_string))
	>>>   print("Problem with PLC: ")
	>>>   print(plc_error_message(plc_error_code(plc_string))+"\n")

	"""

	if plc_string[-2:] == '*\r' and plc_string[0] == '@' and plc_string[:5] =='@00SC':

		frame = plc_string[:-4]
		fcs = plc_string[-4:-2]
		endcode = plc_string[5:7] # This really needs to be checked


		for i in range(1,len(frame)):
			x = x ^ ord(frame[i:i+1])

		if int(fcs, 16) == x:
			return int(endcode, 16)
		else:
			return 255
	else:
		return 255


def plc_status_write_error_message_(end_code):
	"""
	Return the error message corresponding to the End Code 'end_code' for a PLC
	 Status write response.
	(or 'Normal Completion' if the 'end_code' is 0)
	If no such error message return "Unknown error code
	"""

	if end_code == int("00",16):
		message = "Normal Completion"
	elif end_code == int("13",16):
		message = "FCS error"
	elif end_code == int("14",16):
		message = "Format error"
	elif end_code == int("15",16):
		message = "Entry number data error"
	elif end_code == int("18",16):
		message = "Frame length error"
	elif end_code == int("19",16):
		message = "Not executable"
	elif end_code == int("21",16):
		message = "Not executable due to CPU Unit CPU error"
	else:
		message = "Unknown error code: "+ str(end_code)

	return message


def plc_status_error_message(error_code):
	"""
	Return the error message corresponding to the End Code error_code
	 (or "Normal Completion" if error_code is 0)
	 If no such error message return "Unknown error code".
	"""
	if error_code == int("00",16):
		message = "Normal Completion"
	elif error_code == int("01",16):
		message = "Not executable in RUN mode"
	elif error_code == int("02",16):
		message = "Not executable in Monitor mode"
	elif error_code == int("04",16):
		message = "Address Over"
	elif error_code == int("08",16):
		message = "Not executable in Program mode"
	elif error_code == int("13",16):
		message = "FCS error"
	elif error_code == int("14",16):
		message = "Format error"
	elif error_code == int("15",16):
		message = "Entry number data error"
	elif error_code == int("18",16):
		message = "Frame length error"
	elif error_code == int("19",16):
		message = "Not executable"
	elif error_code == int("23",16):
		message = "Memory write protected"
	elif error_code == int("A3",16):
		message = "FCS Error in transmit data"
	elif error_code == int("A4",16):
		message = "Format Error in transmit data"
	elif error_code == int("A5",16):
		message = "Data Error in transmit data"
	elif error_code == int("A6",16):
		message = "Frame Length Error in transmit data"
	else:
		message = 'Unknown error code: '+str(error_code)+'.'

	return message

def plc_data_error_message(end_code):
	"""
	Return the error message corresponding to the End Code end_code from a PLC 
	 request data response (or "Normal Completion" if end_code is 00).
	 If no such error message return "Unknown error code".
	 
	"""
	if end_code == int("00",16):
		message = "Normal Completion"
	elif end_code == int("13",16):
		message = "FCS error"
	elif end_code == int("14",16):
		message = "Format error"
	elif end_code == int("15",16):
		message = "Entry number data error"
	elif end_code == int("18",16):
		message = "Frame length error"
	elif end_code == int("21",16):
		message = "Not executable due to CPU Unit CPU error"
	else:
		message = "Unknown error code: "+str(end_code)

	return message


def int_bit_is_set(int, offset):
	"""
	Uses bitwise operators '&' and '<<'
	"""
	ans = int & (1 <<offset)
	return ans

def set_hex_bit(hex, offset):
	"""
	Uses bitwise operators '|' and '~'
	"""
	fmt = ':0'+len(hex)+'X'
	ans = fmt.format(int(hex,16) | (1<<offset))
	return ans

def unset_hex_bit(hex, offset):
	"""
	Uses bitwise operators '&', '<<' and '~'
	"""
	fmt = ':0'+len(hex)+'X'
	ans = fmt.format(int(hex,16) & ~(1 << offset))
	return ans

def hex_bit_is_set(hex, offset):
	"""
	Uses bitwise operators '&' and '<<'
	"""
	ans = hex & (1 <<offset)
	return ans
