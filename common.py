"""
common.py
Jessica A. Evans
15/10/2018
"""
import os
import re
import serial # not a standard library
import time
import logging
import dummy_serial

def load_config(fileName, path='/.'):

	"""
	Load configuration information from a file, as a dictionary.
	 Tries to convert from string to integers and floats where possible,
	  others left as strings.
	

	PARAMETERS

		file = name of the config file.
		path = path to directory containing config file. Default is current directory.

	RETURN

		config_dict = A dictionary containing the "param, value" as taken from the specified 
				file 	
	"""
	# Join the path and file name
	direct = os.path.join(path,fileName)


	#Check the path and file exists, throw OSError is not
	path_bool = os.path.isdir(path)
	if path_bool == False:
		raise OSError(str("'"+path+"' ") + "does not exist")
		
	else: 
		file_bool = os.path.isfile(direct)
		if file_bool == False:
			raise OSError(str("'"+fileName+"' ") + "does not exist")			

	#Open the config file, split up the file based on the spaces. File is read in one go
	with open(direct, 'r') as f:
		config_dict = dict(re.findall(r'(\S+)\s+(.+)', f.read()))
	
		
	#This will convert what it can to integers and then floats, the rest is left as
	#  a string.
	for param_name in config_dict:
		
		if config_dict[param_name] == 'True':
			config_dict[param_name] = True
		
		#Make sure that comment (marked by '#') are removed before trying to convert
		try: 
			config_dict[param_name] = config_dict[param_name].split('#')[0].strip()
		except:
			pass		

		try: #try to convert to integer
			config_dict[param_name] = int(config_dict[param_name])
		except:
			try: #If it can't try to convert to float
				config_dict[param_name]=float(config_dict[param_name])
			except: # If neither work, try to check if its a boolean in string format, otherwise
						# leave it how it was read in
				if config_dict[param_name] == 'True':
					config_dict[param_name] = True
				if config_dict[param_name] == 'False':
					config_dict[param_name] = False
				
				pass
	
	return config_dict
"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  SERIAL PORT CONTROL FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

def open_port_from_config_param(config_dict):
	"""
	Use the baud rate, no of data bits, stop bits and parity parameters from a config dictionary to
		 open a serial port using pySerial. The port is an object that is returned
		 
	
	PARAMETERS
	
		config_dict = the dictionary contain the require parameters. Function require the following keys to
		 be present in the dictionary: ""
		 
	RETURN
	
		open_port = ...
	
	"""

	#currently the port does not open as it require a port name, not sure what that will be yet,
	#  It should be something that will be defined in the config file
	open_port = serial.Serial(port=config_dict['port_name'], baudrate=config_dict['baud_rate'], bytesize=config_dict['data_bits'], #parity=config_dict['parity'], stopbits='STOPBITS_' + str(config_dict['stop_bits']))
		parity=config_dict['parity'], stopbits=config_dict['stop_bits'])

	return open_port

def send_command_get_response(command, port_name, sleep_time = 0.01):
	"""
	*****************************
	*** Not tested (18/10/18) ***
	*****************************
	
	Write a command to the port specified by 'port_name' and then return the response. The 
	 response is expected to be sent back straight away
	 
	 The port that is passed should already be open, the function will raise an exception
	 if not
	
	PARAMETERS
	
		command = the string command that will be converted to bytes then passed to the port
		port_name = the variable name of the open port, to which the command will be passed.
		
	RETURN
	
		message = if the port is open, the response to the command will be returned.
	
	"""
	
	#The try/except is in place for the unit testing. the dummy-serial port created for during
	# testing does not have a is.open function, so this is designed to handle this. If dummy_port_bool
	# will be False and run as orginally intended is is.open can be run on the port.
	dummy_port_bool = False
	try:
		# Check if the port is open...
		open_bool = port_name.is_open
	except:
		open_bool = True
		dummy_port_bool = True
	
	if open_bool == False:
		raise Execption('The specified port is not open')
	else:
		if dummy_port_bool == False:
		
			port_name.write(command.encode('utf-8'))
			while port_name.in_waiting == 0:
				time.sleep(sleep_time) #in seconds

			message_bytes = port_name.in_waiting
			#print(message_bytes)
			if message_bytes>=3:
			
				# By default the read_until function will read bytes until a LF is found
				message = open_p.read_until().decode('utf-8').strip()
				#print('Device message: ' + message)
		else:
				port_name.write((command).encode('utf-8'))
				message = port_name.read(64).decode('utf-8').strip('\n')
				#message = port_name.read(64).decode('utf-8')#
				#print(message+'!')
				#message = message#.strip('\n')

		return message

def send_command_two_response(command, port_name, expected_end='\n', sleep_time = 0.01):
	"""
		*****************************
		*** Not tested (23/10/18) ***
		*****************************
		
	Write a command to the port specified by 'port_name' and then return the response. Expecting
	 an immediate '!\n' response if command correctly received, this will then be followed by a 
	 response message. In not received correctly, then it will just be a string with the error 
	 code and message.
	
	 The port that is passed should already be open, the function will raise an exception
	 if not
	 
	 PARAMETERS
	 
		command = the string command that will be converted to bytes then passed to the port
		port_name = the variable name of the open port, to which the command will be passed.
		
	RETURN
		
		message = if the port is open, the response to the command will be returned.
		
	"""
	dummy_port_bool = False
	try:
		# Check if the port is open...
		open_bool = port_name.is_open
	except:
		open_bool = True
		dummy_port_bool = True
	
	if open_bool == False:
		raise Execption('The specified port is not open')
	else:
		if dummy_port_bool == False:
			port_name.write(command.encode('utf-8'))
			while port_name.in_waiting == 0:
				time.sleep(sleep_time) #in seconds
		
			message_bytes = port_name.in_waiting
			#print(message_bytes)
			if message_bytes>=2:
			
				# By default the read_until function will read bytes until a LF is found
				message = open_p.read_until().decode('utf-8').strip()

				if message != '!':
					print(command +' was unsuccessful.' + message)
					logging.info(command + ' unsuccessful')
					logging.error(message)
				else:
					message = open_p.read_until(expected_end).decode('utf-8').strip()
					logging.info(command + ' successfully passed')

		else:
			port_name.write((command).encode('utf-8'))
			message = port_name.read(2).decode('utf-8').strip()
			#print('First Line' + message)

			if message != '!':
				#print(command +' was unsuccessful.' + message)
				logging.info(command + ' unsuccessful')
				logging.error(message)
			else:
				message = port_name.read(1000)
				#print('Second: '+message)
				message = message.decode('utf-8').strip()
				#logging.info(command + ' successfully passed')
		
		return message



def close_port(port_that_is_open):
	"""
	Will immediately close an open port
	

	PARAMETERS
	
		port_that_is_open = name of the port that is currently open and should be closed
		
	RETURN
	
		closed_port = port variable is renamed and returned close
	
	"""

	closed_port = port_that_is_open.close()
	return closed_port
