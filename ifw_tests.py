import unittest
import filter_wheel_control as fwc
import dummy_serial #not anaconda, part of minimalmodbus, installed with pip3?


"""
 This script will contain all the unit test for the filter_wheel_control script. Contains test for most functions, but not the filterwheel setup or initialisation.Also current plan is to have unit tests for focuser and filter wheel in separate files, which will then be run from a master file -- not worked out how to do this
 yet....
 
 Can run the test how they currently are in terminal using
	> python ifw_tests.py
	
"""

class test_config_port_values(unittest.TestCase):
	"""
	Tests for the checking the baud_rate, stop_bit etc supplied by the config file.
	"""
	
	# No exceptions if all working
	def test_baud_rate_present_correct(self):
		test_dict_ok = dict({'baud_rate':19200,'data_bits':8, 'stop_bits':1, 'parity':'N'})
		# normally states what we expect to happen, here want to check it doesn't raise exception
		fwc.check_config_port_values_for_ifw(test_dict_ok)


	#if there is a baud rate, but wrong number
	def test_baud_rate_present_but_wrong_value(self):
		test_dict_wrongBD = dict({'baud_rate':192000,'data_bits':8, 'stop_bits':1, 'parity':'N'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the other function
			fwc.check_config_port_values_for_ifw(test_dict_wrongBD)

	
	# not baud rate present
	def test_baud_rate_not_present(self):
		test_dict_noBD = dict({'data_bits':8, 'stop_bits':1, 'parity':'N'})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fwc.check_config_port_values_for_ifw(test_dict_noBD)


	#if there is a data bits value, but wrong number
	def test_data_bits_present_but_wrong_value(self):
		test_dict_wrongDB = dict({'baud_rate':19200,'data_bits':9, 'stop_bits':1, 'parity':'N'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the other function
			fwc.check_config_port_values_for_ifw(test_dict_wrongDB)
	
	# not data bits present
	def test_data_bits_not_present(self):
		test_dict_noDB = dict({'baud_rate':19200, 'stop_bits':1, 'parity':'N'})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fwc.check_config_port_values_for_ifw(test_dict_noDB)

	#if there is a stop bits value, but wrong number
	def test_stop_bits_present_but_wrong_value(self):
		test_dict_wrongSB = dict({'baud_rate':19200,'data_bits':8, 'stop_bits':4, 'parity':'N'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the other function
			fwc.check_config_port_values_for_ifw(test_dict_wrongSB)
	
	# no stop bits present
	def test_stop_bits_not_present(self):
		test_dict_noSB = dict({'baud_rate':19200, 'data_bits':8, 'parity':'N'})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fwc.check_config_port_values_for_ifw(test_dict_noSB)

	#if there is a parity value, but wrong
	def test_parity_present_but_wrong_value(self):
		test_dict_wrongPar = dict({'baud_rate':19200,'data_bits':8, 'stop_bits':1, 'parity':'S'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the other function
			fwc.check_config_port_values_for_ifw(test_dict_wrongPar)
	
	# no parity present
	def test_parity_not_present(self):
		test_dict_noPar = dict({'baud_rate':19200,'data_bits':8, 'stop_bits':1})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fwc.check_config_port_values_for_ifw(test_dict_noPar)

"""
class test_port_initialisation(unittest.TestCase):

	# Setup the dictionary to be used in all the other unit tests
	def setUp(self):
		# self. is needed otherwise the function will forget itself at the end
		self.master,self.slave = pty.openpty()
		port1 = dummy_serial.Serial()#os.ttyname(self.slave)
		self.test_dict = dict({'baud_rate':19200,'data_bits':8, 'stop_bits':1, 'parity':'N', 'port_name':port1})
		port1.RESPONSES
	

#	def test_open_port

	def test_initialise_no_errors(self):
		open_port = fwc.initialise_ifw_serial_connection(self.test_dict)
#"""

class test_filter_names_to_string(unittest.TestCase):
	"""
	Tests to check the form_filter_names_string_from_config function.
	"""

	def setUp(self):
		self.test_dict = {'A':'RED','B':'GREEN','C':'BLUE','D':'WHITE','E':'INFRARED','F':'BLANK','G':'BLANK','H':'BLANK'}
		self.test_dict_bad_character = {'A':'R£D','B':'GREEN','C':'BLUE','D':'WHITE','E':'INFRARED','F':'BLANK','G':'BLANK','H':'BLANK'}
		self.test_dict_too_long = {'A':'REDDDDDDDD','B':'GREEN','C':'BLUE','D':'WHITE','E':'INFRARED','F':'BLANK','G':'BLANK','H':'BLANK'}
		self.test_dict_bad_ID = {'A':'RED','B':'GREEN','F':'BLUE','D':'WHITE','E':'INFRARED','F':'BLANK','G':'BLANK','H':'BLANK'}

	def test_form_string(self):
		resulting_string = fwc.form_filter_names_string_from_config_dict(self.test_dict)
		resulting_length = len(resulting_string)
		
		expected_string = 'RED     GREEN   BLUE    WHITE   INFRAREDBLANK   BLANK   BLANK   '
		expected_length = 64
		
		self.assertEqual(resulting_string, expected_string)
		self.assertEqual(resulting_length, expected_length)

	def test_bad_char(self):
		with self.assertRaises(ValueError):
			fwc.form_filter_names_string_from_config_dict(self.test_dict_bad_character)

	def test_name_too_long(self):
		with self.assertRaises(ValueError):
			fwc.form_filter_names_string_from_config_dict(self.test_dict_too_long)

	def test_incorrect_ID(self):
		with self.assertRaises(ValueError):
			fwc.form_filter_names_string_from_config_dict(self.test_dict_bad_ID)


class test_pass_filternames(unittest.TestCase):
	
	"""
	Tests to check the pass_filter_names function
	"""
	
	def setUp(self):
		
		self.name_string = 'RED     GREEN   BLUE    WHITE   INFRAREDBLANK   BLANK   BLANK   '
		self.bad_name_string = 'TESTING1 2 3 4'
		self.good_ID = 'A'
		self.bad_ID = 'K'
		
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.0001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {
			'WLOAD' + self.good_ID + '*'+ self.name_string: '!',
			 'WLOAD' + self.bad_ID + '*'+ self.name_string: 'ER=3'}
	
	def test_invalid_ID(self):

		"""
		Check error is logged if invalid filter ID is passed
		"""
		with self.assertLogs(level='ERROR') as cm:
			fwc.logging.getLogger().error(fwc.pass_filter_names(self.name_string, self.dummy_port, wheel_ID=self.bad_ID))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'ERROR')

	def test_correct_success_message(self):
		with self.assertLogs(level='INFO') as cm:
			fwc.logging.getLogger().error(fwc.pass_filter_names(self.name_string, self.dummy_port, wheel_ID=self.good_ID))
			logging_actual_response = cm.output[0].split(':')[0]

		self.assertEqual(logging_actual_response, 'INFO')

	def test_unexpected_response(self):
		with self.assertLogs(level='CRITICAL') as cm:
			fwc.logging.getLogger().critical(fwc.pass_filter_names(self.bad_name_string, self.dummy_port, wheel_ID=self.good_ID))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'CRITICAL')

	def tearDown(self):
		#close the dummy_port
		self.dummy_port.close()


class test_get_stored_filter_names(unittest.TestCase):
	""" 
	Test for the get_stored_filter_names function
	"""
	def setUp(self):
		
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.0001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {
			'WREAD': 'RED     GREEN   BLUE    WHITE   INFRAREDBLANK   BLANK   BLANK   '}


	def test_just_return_string_of_names(self):

		expected = 'RED     GREEN   BLUE    WHITE   INFRAREDBLANK   BLANK   BLANK   '
		actual = fwc.get_stored_filter_names(self.dummy_port, formatted_dict=False)
		self.assertEqual(actual, expected)

	def test_get_dict_of_names(self):
		expected = {'A':'RED','B':'GREEN','C':'BLUE','D':'WHITE','E':'INFRARED','F':'BLANK','G':'BLANK','H':'BLANK'}
		actual = fwc.get_stored_filter_names(self.dummy_port, formatted_dict=True)
		self.assertEqual(actual,expected)

	def tearDown(self):
		#close the dummy_port
		self.dummy_port.close()

class test_get_current_position(unittest.TestCase):
	""" 
	Test for the get_current_position function
	"""
	def setUp(self):
		
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.0001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {
			'WFILTR': '1'}

	def test_response(self):

		expected = 1
		actual = fwc.get_current_position(self.dummy_port)
		self.assertEqual(actual, expected)

	def tearDown(self):
		#close the dummy_port
		self.dummy_port.close()

class test_get_current_ID(unittest.TestCase):
	"""
	Test for the get_current_ID function
	"""
	def setUp(self):
		
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.0001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {
			'WIDENT': 'A'}

	def test_response(self):
	
		expected = 'A'
		actual = fwc.get_current_ID(self.dummy_port)
		self.assertEqual(actual, expected)
	
	def tearDown(self):
		#close the dummy_port
		self.dummy_port.close()

class test_get_both_pos_ID(unittest.TestCase):
	"""
	Test for the get_current_filter_position_and_ID function
	"""
	def setUp(self):
		
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {
			'WIDENT': 'A','WFILTR': '1'}

	def test_response(self):
	
		expected = ['A', 1]
		actual = fwc.get_current_filter_position_and_ID(self.dummy_port)
		self.assertEqual(actual, expected)
	
	def tearDown(self):
		#close the dummy_port
		self.dummy_port.close()


class test_goto_home_position(unittest.TestCase):
	"""
	Test for the get_currrent_filter_position_and_ID function
	"""
	def setUp(self):
		
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {
			'WHOME': 'A'}
	def test_return_message_if_true(self):

		expected = 'A'
		actual = fwc.goto_home_position(self.dummy_port, return_home_id = True)
		self.assertEqual(actual,expected)

	def test_log_errors(self):
		dummy_serial.RESPONSES = {'WHOME': 'ER=3'}
		with self.assertLogs(level='ERROR') as cm:
			fwc.logging.getLogger().error(fwc.goto_home_position(self.dummy_port, ))
			logging_actual_response = cm.output[0].split('.')[0]
		self.assertEqual(logging_actual_response, 'ERROR:root:ER=3')

		dummy_serial.RESPONSES = {'WHOME': 'ER=1'}
		with self.assertLogs(level='ERROR') as cm:
			fwc.logging.getLogger().error(fwc.goto_home_position(self.dummy_port, ))
			logging_actual_response = cm.output[0].split('.')[0]
		self.assertEqual(logging_actual_response, 'ERROR:root:ER=1')

	def test_log_errors(self):
		dummy_serial.RESPONSES = {'WHOME': 'ERROR TEST'}
		with self.assertLogs(level='ERROR') as cm:
			fwc.logging.getLogger().critical(fwc.goto_home_position(self.dummy_port, ))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'CRITICAL')

	def tearDown(self):
		#close the dummy_port
		self.dummy_port.close()

class test_goto_filter_position(unittest.TestCase):
	"""
	Tests for the goto_filter_position function
	"""
	def setUp(self):
		
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'WGOTO1': '*','WGOTO9':'ER=5'}

	def test_ok_position(self):
		with self.assertLogs(level='INFO') as cm:
			fwc.logging.getLogger().info(fwc.goto_filter_position(1,self.dummy_port))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'INFO')

	def test_bad_position(self):
		with self.assertLogs(level='ERROR') as cm:
			fwc.logging.getLogger().error(fwc.goto_filter_position(9,self.dummy_port))
			logging_actual_response = cm.output[0].split('.')[0]
		self.assertEqual(logging_actual_response, 'ERROR:root:ER=5')

	def test_other_errors(self):
		dummy_serial.RESPONSES = {'WGOTO1': 'ER=4'}
		with self.assertLogs(level='ERROR') as cm:
			fwc.logging.getLogger().error(fwc.goto_filter_position(1,self.dummy_port))
			logging_actual_response = cm.output[0].split('.')[0]
		self.assertEqual(logging_actual_response, 'ERROR:root:ER=4')

		dummy_serial.RESPONSES = {'WGOTO1': 'ER=6'}
		with self.assertLogs(level='ERROR') as cm:
			fwc.logging.getLogger().error(fwc.goto_filter_position(1,self.dummy_port))
			logging_actual_response = cm.output[0].split('.')[0]
		self.assertEqual(logging_actual_response, 'ERROR:root:ER=6')

		dummy_serial.RESPONSES = {'WGOTO1': 'TEST ERROR'}
		with self.assertLogs(level='CRITICAL') as cm:
			fwc.logging.getLogger().critical(fwc.goto_filter_position(1,self.dummy_port))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'CRITICAL')

	def tearDown(self):
		#close the dummy_port
		self.dummy_port.close()

class test_end_serial_commnication_close_port(unittest.TestCase):

	def setUp(self):
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'WEXITS': 'END'}

	def test_close_port(self):
		with self.assertLogs(level='INFO') as cm:
			fwc.logging.getLogger().info(fwc.end_serial_communication_close_port(self.dummy_port))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'INFO')

	def test_not_close_port(self):
		dummy_serial.RESPONSES = {'WEXITS': 'TEST ERROR'}
		with self.assertLogs(level='WARNING') as cm:
			fwc.logging.getLogger().warning(fwc.end_serial_communication_close_port(self.dummy_port))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'WARNING')


"""
class test_initial_filter_wheel_setup(unittest.TestCase):

	def setUp(self):
		#self.test_dict_ok = dict({'baud_rate':19200,'data_bits':8, 'stop_bits':1, 'parity':'N',
		#	'A':'RX', 'B':'GX','C':'BX','D':'WX', 'E':'IX'})
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'WEXITS': 'END'}
"""

class test_change_filter(unittest.TestCase):

	def setUp(self):
		self.test_dict_ok = dict({'baud_rate':19200,'data_bits':8, 'stop_bits':1, 'parity':'N',
		'A':'RX', 'B':'GX','C':'BX','D':'WX', 'E':'IX','F':'BLANK','G':'BLANK','H':'BLANK'})
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'WGOTO1': '*','WIDENT': 'A','WFILTR': '1'}

	def test_same_filter(self):
		
		with self.assertLogs(level='WARNING') as cm:
			fwc.logging.getLogger().warning(fwc.change_filter(1, self.dummy_port, self.test_dict_ok))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'WARNING')

	def tearDown(self):
		#close the dummy_port
		self.dummy_port.close()

class test_filter_wheel_shutdown(unittest.TestCase):

	def setUp(self):
		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'WEXITS': 'END','WHOME': 'A'}

	def test_for_log_message(self):
		with self.assertLogs(level='INFO') as cm:
			fwc.logging.getLogger().info(fwc.filter_wheel_shutdown(self.dummy_port))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'INFO')

if __name__ =='__main__':
	unittest.main()
