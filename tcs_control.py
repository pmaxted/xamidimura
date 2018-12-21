""" 

tcs_control.py

	This script will contain the functions that will interact with the TCS computer. This includes connecting
	 to the TCS via ssh, logging off at the end, and sending commands to take images.

"""
from pexpect import pxssh
import pexpect
import getpass
import logging
import settings_and_error_codes as set_err_code
import timeout_decorator

logging.basicConfig(filename= 'testlog.log', filemode = 'w', level=logging.INFO, 
	format='%(asctime)s %(levelname)s %(message)s')
""" 
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  TCS connection functions
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def open_gateway_ssh_connection(gate_timeout=set_err_code.tcs_coms_timeout):
	""" 
	Setup an ssh connection to the gateway/observer machine. Again this won't be necessary when the script
	 is actually on the machine.
	 
	 RETURN
	 
	 s = the opened connection
	 
	"""

	s = pexpect.pxssh.pxssh(timeout=gate_timeout)
	host = 'superwasp.saao.ac.za'
	user = 'wasp'
	password = getpass.getpass('Gateway Password: ')
	print('Logging into gateway machine...')
	logging.info('Logging into gateway machine...')
	s.login(host, user,password)
	s.expect('P*')
	s.prompt()
	print('Connected to gateway')
	logging.info('Connected to gateway')

	return s


def open_TCS_ssh_connection(connect_to_gateway_first = False, timeout=set_err_code.tcs_coms_timeout):

	""" 
	
	Set up an ssh connection to the TCS pc using the 'ssh TCS' command that is currently in place on the 
	 gateway machine. In addition to logging, this function will also run the 'telshow' command, in order
	 to display the telescopes current status on the screen.
	 
	There is the option to connect to the gateway machine first (at least while working remotely - won't be
	needed once the script is on the 'observer' machine.) Note that connecting to the gateway machine will 
	only work is run from a Keele PC, and it will require the password to be entered. Can change this at a 
	later date if need be.
	
	PARAMETERS:
	
		connect_to_gateway_first = True/False, if true a connection to the wasp gateway machine
			at wasp superwasp.saao.ac.za will be made first, and then the connection to the TCS
			machine will be made using 'ssh tcs'
			
		timeout = timeout waiting to establish a connection to the gateway and tcs.
			
	RETURN:
	
		s = the opened ssh connection to the TCS. Will need to close the connection to the TCS before
			the gateway, when finiched with the connection.

	"""
	connectedBool = False
	tcsPrompt = '[wasp@tcs ~]$'

	if connect_to_gateway_first == True:
		
		try:
			s = open_gateway_ssh_connection(gate_timeout=timeout)
		except pexpect.pxssh.ExceptionPxssh as ex:
			logging.error('Failed to login to gateway:', ex)
			print('Failed to login to gateway:', ex) 

		else:
		
			print('Attempting to connect to TCS')
			logging.info('Attempting to connect to TCS')
			s.sendline('ssh tcs')
			s.prompt()
			s.expect_exact(tcsPrompt)
			print('Getting telescope status')
			logging.info('Getting telescope status')
			s.sendline('telshow')
			s.expect_exact(tcsPrompt) #expect_exact searches for a string not re expression
			info = s.before.decode('utf-8').split('\r\r\n')[1].strip()
			print('TCS connected, current status: ')
			logging.info('TCS connected, current status:\n'+ info)
			print(info)
			
			connectedBool = True

	else:
		""" 
		**** Not TESTED ****
		This has not been tested, and can only really be used once on the gateway/observer machine. Currently 
		 (29/11/18) the python version is too old to test it
		"""
		try:
			s = pexpect.spawn('ssh tcs')
		except:
			print('Failed to connect to TCS machine...')
			logging.error('Failed to connect to TCS machine...')
						
		else:
			s.prompt()
			s.sendline('telshow')
			s.expect_exact(tcsPrompt) #expect_exact searches for a string not re expression
			info = s.before.decode('utf-8')
			print('TCS connected, current status: ')
			print(info)
			logging.info('TCS connected, current status:\n'+info)
			connectedBool = True
	
	if connectedBool == True:	
		return s
	else:
		print('Not connected!')
		logging.critical('Not connected!')

def close_both_connections(open_conn):

	""" 	
	Close the connection to the TCS pc and if there is a connection to the gateway machine logout of that
	 ssh connection.
	 
	The connection to the TCS will be stopped using the "exit" command sent to the terminal. The connection 
	 to the gateway machine will be closed using the logout function which is part of the 'pexpect' module. 
	 
	
	"""

	#close the ssh session with the TCS
	close_TCS_connection(open_conn)
	
	try:
	
		close_gateway_ssh(open_conn)

	except:
	
		open_conn.prompt()
		print(open_conn.before)

def close_TCS_connection(open_conn):
	""" 
	Send the commands to exit the ssh connection to the TCS machine
	
	PARAMETERS:
	
		open_conn - the pxssh connection that was previously opened
	"""
	
	print('Closing connection to TCS...')
	logging.info('Closing connection to TCS...')
	open_conn.sendline('exit')
	open_conn.prompt()
	logging.info('Connection to tcs closed.')
	print('Connection to tcs closed.')

def close_gateway_ssh(open_conn):
	"""
	Send the commands to logout from the ssh connection to the gateway/observer machine. This will not be
	 needed once the script is actually on the observer machine.
	
	PARAMETERS:
	
		open_conn - the pxssh connection that was previously opened
	"""
	print('Logging out of gateway...')
	logging.info('Logging out of gateway...')
	open_conn.logout()
	print('Gateway connection closed')
	logging.info('Gateway connection closed')

""" 
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Commands to interact with telescope on TCS over ssh
 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
@timeout_decorator(set_err_code.tcs_coms_timeout, use_signals=False)
def send_command(command, open_conn, expected_prompt = '[wasp@tcs ~]$'):
	""" 
	Send a 'command' to the TCS computer over the 'open_conn' ssh connection.
	It will take any repsonse, remove the echoed command and return just the message
	
	PARAMETERS:
	
		command = A command that will be accepted by the command line interface (cli). Although
		 other general command-line commands will work as well
		
		open_conn = the parameter containing a previously open ssh connection to the TCS
		
		expected_prompt = After sending a command, the function will read the response until this 
			'prompt' is found. The prompt is used to indicate the end of the response, and another
			command can be sent.
			
	RETURN:
	
		response = A string containing the message that is returned in response the command.
	
	"""
	open_conn.sendline(command)
	open_conn.expect_exact(expected_prompt)
	
	#get rid of repeated command
	response = open_conn.before.decode('utf-8').split('\r\r\n')[1].strip()
	logging.info('FROM TCS: '+response)
	return response


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Functions to check the status of various things
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def split_ra_dec_alt_az(response_string):
	""" 
	Takes a string with the format [hh mm ss hh mm ss hh mm ss hh mm ss hh mm ss status]
	 and splits it into ra, dec, ha, alt, az and telscope status
	 
	 PARAMETERS
	 
	 	response_string = the string to be split up
	 
	 RETURN
	 
	 	[ra,dec,ha, alt, az, status] as a list
	"""
	splitup = response_string.split()
	ra = ' '.join(splitup[:3])
	dec = ' '.join(splitup[3:6])
	ha = ' '.join(splitup[6:9])
	alt = ' '.join(splitup[9:12])
	az = ' '.join(splitup[12:15])
	stat = splitup[-1]

	return [ra, dec, ha, alt, az, stat]

def get_tel_target(open_conn):
	""" 
	Send 'getstatus teltarget' to tcs and processes response
	
	 Response to the 'getstatus teltarget' command is a string showing the telescopes target
	 RA, Dec, Ha, Alt, Az in sexagesimal format, using 3 components separated by spaces
	 (i.e. hh mm ss), followed by telescope status. If telescope is moving/slewing will 
	 report target position.
	
	PARAMETERS
	
		open_conn = parameter holding the open ssh connection to the tcs
		
	RETURN
	
		split_ans = List containing the RA, Dec, Ha, Altitude, azimuth and status of telescope,
			and show the target coordinates it is moving/slewing.
	
	"""
	target = send_command('getstatus teltarget', open_conn)
	split_ans = split_ra_dec_alt_az(target)
	
	return split_ans

def get_tel_pointing(open_conn):
	""" 
	Sends 'getstatus tel' to the tcs and processes the response

	Response to the 'getstatus tel' command is a string showing the telescopes target
	 RA, Dec, Ha, Alt, Az in sexagesimal format, using 3 components separated by spaces
	 (i.e. hh mm ss), followed by telescope status. 
	 
	Valid status messages are as follows:
		- STOPPED (telescope is stopped)
		- SLEWING (slewing rapidly)
		- HUNTING (slewing slowly)
		- TRACKING (tracking the given position)
		- HOMING (finding the home position)
		- LIMITING (finding the limit switches)
	
	PARAMETERS
	
		open_conn = parameter holding the open ssh connection to the tcs
		
	RETURN
	
		split_ans = List containing the RA, Dec, Ha, Altitude, azimuth and status of telescope,
			and show the target coordinates it is moving/slewing.
	
	"""
	target = send_command('getstatus tel', open_conn)
	split_ans = split_ra_dec_alt_az(target)
	
	return split_ans
	
def get_homed_status(open_conn):
	""" 
	Sends the 'getstatus home' command to the tcs and processes the repsonse
	
	Will return the hommed status of the following in this order
	 HA DEC, rotator, focus, filterwheel
	Will show 'ABSENT' (if not present) or 'NOTHOMED'/'HOMED' 
	
		PARAMETERS:
	
			open_conn = parameter holding the open ssh connection to the TCS
			
		RETURN:
		
			split_ans = List with the homed status for the HA axism DEC axis, rotator, focus and 
				filterwheel in that order
	"""
	target = send_command('getstatus home', open_conn)
	split_ans = target.split()
	
	return split_ans

def get_camera_status(open_conn):

	""" 
	 Send the 'getstatus cam' to the tcs and processes it's repsonse.
	
	
	This will report the overall combine camera status of the all the CCDs.
	Possible states are:
		- IDLE
		- EXPOSING
		- READING
	Will also show the status of the cooler status (see below) and then the current 
	 and target temperatures.
	 Cooler status values:
	 	- AtTemp (at target temp)
	 	- UnderTemp (under target temperature)
	 	- 0verTemp (over target temperature)
	 	- CoolerOff (cooler is switched off)
	 	- RampDown (ramping temperture down)
	 	- RampUp (ramping temperature up)
	 	- Stuck (temperature stuck, can't reach target)
	 	- AtMax (temperature can't go any higher)
	 	- CoolerIdle (cooler is idle, temperature is ambient)
	 
	PARAMETERS
	
		open_conn = parameter holding the open ssh connection to the TCS
	
	RETURN
	
		split_ans = List containing the camera state, cooler state, current temperature
			 and target temperature, in that order
	"""

	target = send_command('getstatus cam', open_conn)
	split_ans = target.split()
	
	return split_ans

def get_roof_status_from_tcs(open_conn):
	""" 
	Send the 'getstatus dome' command to the TCS. This will get the TCS to respond with the
	 roof's current status.
	 
	Possible states:
	 - ABSENT (no shutter present or shutter disabled)
	 - IDLE (stopped but not at open or closed limit)
	 - OPENING (currently opening)
	 - CLOSING (currently closing)
	 - OPEN (open)
	 - CLOSED (closed)
	 
	 Also returns an integer which indicates wheter the alarm has been trigger (will be 1 if triggered)
	 
	 PARAMETERS:
	 
	 	open_conn = the parameter storing the open ssh connection to the TCS
	 	
	 RETURN:
	 
	 	split_ans = List containing the roof status and alarm status, in that order
	"""
	
	target = send_command('getstatus dome', open_conn)
	split_ans = target.split()
	
	return split_ans


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Functions to send commands to telescope
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def stop_telescope_move(open_conn):
	""" 
	Sends the 'stoptel' command to the TCS computer. This will stop an motion of the
		telescope mount.

	 PARAMETERS:
	 
	 	open_conn = the parameter storing the open ssh connection to the TCS
	
	"""
	target = send_command('stoptel', open_conn)
		
def startTel(open_conn, startAll = False):
	""" 
	*** NOT TESTED ***
	
	Send the 'startTel' command to the TCS machine. This will start a basic set of OCAAS processes
	 including 'telescoped' and 'xobs' [Check what these are]. If startAll is set to True then it 
	 will add the '-all' argument to the command, which will also start the camerad,shm,camera, 
	 xephem and telsched processes
	
	 PARAMETERS:
	 
	 	open_conn = the parameter storing the open ssh connection to the TCS
		startAll = True/False, set to True to run all 'telescoped, xobs, camerad, shm, camera,
			xephem and telsched processed. If set to False, only the telescoped and xobs will
			run.
	
	"""
	
	
	if startAll == True:
		logging.info('Running all telescope startup processes...')
		target = send_command('startTel -all', open_conn)
	elif startAll == False:
		logging.info('Running telescope startup...')
		target = send_command('startTel', open_conn)
	else:
		logging.error('Invaild input for startAll, use True/False')
		raise ValueError('Invaild input for startAll, use True/False')

def killTel(open_conn, killAll = False):
	""" 
	*** NOT TESTED ***
	
	Send the 'startTel' command to the TCS machine. This will start a basic set of OCAAS processes
	 including 'telescoped' and 'xobs' [Check what these are]. If startAll is set to True then it 
	 will add the '-all' argument to the command, which will also start the camerad,shm,camera, 
	 xephem and telsched processes
	
	 PARAMETERS:
	 
	 	open_conn = the parameter storing the open ssh connection to the TCS
		startAll = True/False, set to True to run all 'telescoped, xobs, camerad, shm, camera,
			xephem and telsched processed. If set to False, only the telescoped and xobs will
			run.
	
	"""
	
	
	if killAll == True:
		logging.info('Stopping all telescope processes...')
		target = send_command('killTel -all', open_conn)
	elif killAll == False:
		logging.info('Stopping telescope startup...')
		target = send_command('killTel', open_conn)
	else:
		logging.error('Invaild input for killAll, use True/False')
		raise ValueError('Invaild input for killAll, use True/False')
		
def check_tele_coords(coords, is_alt_az):
	""" 
	Checks to make sure that coordinates that will be sent to the telescope are valid, i.e.
	 within valid ranges.
	 
	These check include that the list 'coords' connsists of two string components, of the form
	 '?? ?? ??'. 
	 
	 PARAMETERS:
	 
	 	coords -  The coordinates to be checked.
	 	is_alt_az - True/False - If set to true, the coordinates will be taken as altitude and
	 		azimuth.
	"""
	
	#Stuff check coords are OK values?
	if len(coords)!= 2:
		logging.error('Incorrect length for coords parameter, should be 2')
	else:
		for i in range(len(coords)):
		
			#print('Checking', coords[i], 'index:',i)
			valid_Coords = True
			try:
				j = str(coords[i])
				
			except:
				valid_Coords = False
			else:
				space_split = j.split(' ')
				colon_split = j.split(':')
				if len(space_split) == 3 or len(colon_split) == 3: 
					if len(space_split) == 3:
						valid_one = space_split
					if len(colon_split)==3:
						valid_one = colon_split
				else:
					valid_Coords = False
			
			try:
				valid_one = [float(valid_one[k]) for k in range(len(valid_one))]
			except:
				valid_Coords = False
			#Check the values entered are in valid ranges
			if valid_Coords == True:
				#Check mintues for all RA, DEC, Alt, Az,
				if valid_one[1] < 0 or valid_one[1] >= 60:
					valid_Coords =False
				# Check seconds for all RA, DEC, ALt, Az
				if valid_one[2] < 0 or valid_one[2]>= 60:
					valid_Coords =False
				
				# First value will have different ranges for RA, DEC, Alt, Az
				# i == 0 will be either RA or Alt..
				# is_alt_az==False for RA
				if i == 0 and is_alt_az == False:
					if valid_one[0] < 0 or valid_one[0] >=24:
						valid_Coords = False
				elif i == 0 and is_alt_az == True:
					if valid_one[0] <0 or valid_one[0] >90:
						valid_Coords =False
				# i == 1 will be DEC or Az
				# is_alt_az==False for DEC
				elif i== 1 and is_alt_az ==False:
					if valid_one[0] <-90 or valid_one[0] > 90:
						valid_Coords = False
				elif i == 1 and is_alt_az == True:
					if valid_one[0] <0 or valid_one[0] >=360:
						valid_Coords =False
				else:
					print("Issue with 'i' or 'is_alt_az'")
					
			if valid_Coords ==False:
				raise ValueError('Invalid Coordinates provided')
		
def slew_or_track_target(coords, open_conn, track_target=True, is_alt_az = False, equinox='J2000'):

	""" 
	Send the command require to get the telescope to point at a target,
	 with the option to track the target. Uses the TCS cli commands.
	
	Coordinates can be sent as RA and DEC or altitude/azimuth (if is_alt_az = True). If they are
	 in alt/az then the argument 'altaz' is added to the command string that gets sent to the TCS.
	
	 PARAMETERS:
	 
	 	coords = the RA and DEC or Alt/AZ coordinates for the telescope to move to 
	 	 and they can also be altitude and azimuth. Send in list as [RA, DEC] or [Alt, Az].
	 	 Each component should be formatted as 'hh mm ss' or 'dd mm ss' as appropriate. The 
	 	 dd component can be given as '+dd'. Will also accept hh:mm:ss dd:mm:ss as input.
	 	 Example for RA/DEC ['12 32 13','+23 21 42']
	 	
	 	open_conn = the parameter storing the open ssh connection to the TCS

	 	track_target = True/False. If true, the telescope will start tracking once
	 	 the target has been found.
	 	
	 	is_alt_az = True/False. If true, the 'altaz' argument will be added to the command 
	 	 so the telescope know that the coordinates are altitude and azimuth rather than
	 	 RA and DEC.
	 	 
	 	equinox = J2000 is the defualt. Bessellian epochs are not supported at present
	 	(e.g. B1950), please precess your coordinates first. The special equinox "A"
	 	specifies apparent place.
	 	
	"""
	#Check the coordinates that have been pas are valid values
	check_tele_coords(coords, is_alt_az)
	
	if track_target == False:
		command_str = 'slew '
		
	elif track_target == True:
		command_str = 'track '
	else:
		logging.error('Invaild input for track_target, use True/False')	
		raise ValueError('Invaild input for track_target, use True/False')
	
	if is_alt_az == True:
		command_str += 'altaz '
	elif is_alt_az == False:
		pass
	else:
		logging.error('Invaild input for track_target, use True/False')	
		raise ValueError('Invaild input for is_alt_az, use True/False')


	command_str += ' '.join(coords)

	#J2000 is the default, and the RA/DEC values are assumed to be J2000 is not specified
	if is_alt_az == False and equinox != 'J2000':
		command_str += ' '+equinox
	
	try:
	#Send the command to the TCS	
		target = send_command(command_str, open_conn)
	except timeout_decorator.TimeoutError:
		logging.critical('Failed to contact TCS')

	return target

def apply_offset_to_tele(ra_alt_off, dec_az_off, open_conn, units='arcsec', is_alt_az=False):
	""" 
	
	 Send the 'offset' command to get the telescope to move by an amount relative to it's current
	  position.
	  
	 The command can take two forms.
	   -  offset altaz unit altoff azoff
	   -  offset unit raoff decoff
	The first allows the offsets to be passed in alt/az coords, and the second allows it to be
	 passed in RA/DEC.
	 
	
	PARAMETERS:
	
	 	ra_alt_off = The offset in RA or altitude (if is_alt_az is True)
	 	
	 	dec_az_off = The offset in DEC or azimuth (if is_alt_az is True) 
	 	
	 	open_conn = the parameter storing the open ssh connection to the TCS

	 	is_alt_az = True/False. If true, the 'altaz' argument will be added to the command 
	 	 so the telescope know that the coordinates are altitude and azimuth rather than
	 	 RA and DEC.
		
		unit - either 'arcsec', 'arcmin' or 'deg'. 'arc' can also be used instead of 'arcmin'	
	
	"""
	command_str = 'offset '
	
	if is_alt_az == True:
		command_str += 'altaz '
	elif is_alt_az == False:
		pass
	else:
		logging.error('Invaild input for track_target, use True/False')	
		raise ValueError('Invaild input for is_alt_az, use True/False')

	valid_units = ['arcsec','arcmin','deg', 'arc']
	if units not in valid_units:
		logging.error('Invalid telescope offset unit provided')
		raise ValueError('Invalid telescope offset unit provided')
	
	command_str += units + ' '

	command_str += str(ra_alt_off)+' '
	command_str += str(dec_az_off)
	
	respond = send_command(command_str, open_conn)

	return respond

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Functions to send exposure commands - not sure how these work with new system
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def tcs_exposure_request(type, duration = 0, number = 1):
	"""
	Send the expose command to the TCS, along with the exposure type number of exposures and their 
	 duration. The supplied 'type' will be checked to make sure it is a valid type. Note 'dark' type
	 will be relabelled as 'thermal'.
	
	The expose command will get all of the CCD to expose simultaneously. If specified, number will
	be taken sequentially, waiting for each to read out before starting the next.
	
	Duration is required for all exposure except 'bias'. 
	
	THERMAL - A thermal (dark) exposure. The shutter will remain closed, and the CCD will integrate
		for the given duration, and then be read out.
		
	BIAS - A bias frame. The shutter will remain closed, and the CCD flushed and immediately read 
		out.
		
	FLAT - A flat field. The same as flagged as a flat field in the FITS headers.
	
	OBJECT - A target frame. The shutter will be opened and the CCD integrated for the given duration.
	
	
	PARAMETERS:
	
		type = the type of exposures wanted. A valid list includes 'thermal', 'dark', 'bias', 'flat', 
			and 'object'
			
		duration = the length of the exposure in seconds.
		
		number = the number of exposures wanted. The default will be '1' as this is want will be requested
			by the main observing script
	"""

	valid_types = ['thermal','dark', 'bias', 'flat','object']
	valid = type in valid_types
	if type == 'dark':
		type = 'thermal'

	if number <= 1:
		logging.error('Invalid number of exposures requested')
		return respond = set_err_code.STATUS_CODE_EXPOSURE_NOT_STARTED

	if duration <=0:
		logging.error('Invalid exposure time requested')
		return respond = set_err_code.STATUS_CODE_EXPOSURE_NOT_STARTED

	command_str = 'expose ' + type
	if number != 1:
		command_str += ' '+str(number)
	if type != 'bias':
		command_str += ' ' + str(duration)
		
		
	respond = send_command(command_str, open_conn)
	good_response = respond == 0

	if good_response:
		respond = set_err_code.STATUS_CODE_OK

	cam_temp = get_camera_status[2]
	if good_repsonse and cam_temp>-20:
		respond = set_err_code.STATUS_CODE_CCD_WARM

	else:
		respond = set_err_code.STATUS_CODE_EXPOSURE_NOT_STARTED


	return respond

	

def stopcam(open_conn):

	""" 
	Send the 'stopcam' command to the TCS machine. This will abort any exposure that may be in progress.
		
	**Not sure if will work with new system**
	
	PARAMETERS:
	
	 	open_conn = the parameter storing the open ssh connection to the TCS

	RETURN:
	
		....	
	"""

	respond = send_command('stopcam', open_conn)

def wait_till_read_out(open_conn):

	""" 
	Send the 'waitreadout' command to the TCS. This command will wait for the CCD shutter to close
	and readout to start before the can be moved. This is to avoid disturbing the exposure.

	**Noe sure if will work with new system**


	PARAMETERS:
	
	 	open_conn = the parameter storing the open ssh connection to the TCS
	
	"""

	respond = send_command('waitreadout', open_conn)
