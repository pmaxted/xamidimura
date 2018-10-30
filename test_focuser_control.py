import unittest
import focuser_control as fc
import dummy_serial

"""
Note all unit tests that send/receive information to/from an open serial port are test with dummy_serial, 
 using a mock serial port. Tests to ensure the actual devices are sending the information that is expected
 have so far not been possible (30/10/18)
"""


class test_config_port_values(unittest.TestCase):
	"""
	Tests for the checking the baud_rate, stop_bit etc supplied by the config file.
	"""
	
	# No exceptions if all working
	def test_baud_rate_present_correct(self):
		test_dict_ok = dict({'baud_rate':115200,'data_bits':8, 'stop_bits':1, 'parity':'N'})
		# normally states what we expect to happen, here want to check it doesn't raise exception
		fc.check_config_port_values_for_focuser(test_dict_ok)


	#if there is a baud rate, but wrong number
	def test_baud_rate_present_but_wrong_value(self):
		test_dict_wrongBD = dict({'baud_rate':1152000,'data_bits':8, 'stop_bits':1, 'parity':'N'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the other function
			fc.check_config_port_values_for_focuser(test_dict_wrongBD)

	
	# not baud rate present
	def test_baud_rate_not_present(self):
		test_dict_noBD = dict({'data_bits':8, 'stop_bits':1, 'parity':'N'})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fc.check_config_port_values_for_focuser(test_dict_noBD)


	#if there is a data bits value, but wrong number
	def test_data_bits_present_but_wrong_value(self):
		test_dict_wrongDB = dict({'baud_rate':115200,'data_bits':9, 'stop_bits':1, 'parity':'N'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the other function
			fc.check_config_port_values_for_focuser(test_dict_wrongDB)
	
	# not data bits present
	def test_data_bits_not_present(self):
		test_dict_noDB = dict({'baud_rate':115200, 'stop_bits':1, 'parity':'N'})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fc.check_config_port_values_for_focuser(test_dict_noDB)

	#if there is a stop bits value, but wrong number
	def test_stop_bits_present_but_wrong_value(self):
		test_dict_wrongSB = dict({'baud_rate':115200,'data_bits':8, 'stop_bits':4, 'parity':'N'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the other function
			fc.check_config_port_values_for_focuser(test_dict_wrongSB)
	
	# no stop bits present
	def test_stop_bits_not_present(self):
		test_dict_noSB = dict({'baud_rate':115200, 'data_bits':8, 'parity':'N'})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fc.check_config_port_values_for_focuser(test_dict_noSB)

	#if there is a parity value, but wrong
	def test_parity_present_but_wrong_value(self):
		test_dict_wrongPar = dict({'baud_rate':115200,'data_bits':8, 'stop_bits':1, 'parity':'S'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the other function
			fc.check_config_port_values_for_focuser(test_dict_wrongPar)
	
	# no parity present
	def test_parity_not_present(self):
		test_dict_noPar = dict({'baud_rate':115200,'data_bits':8, 'stop_bits':1})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fc.check_config_port_values_for_focuser(test_dict_noPar)

class test_start_end_command_char(unittest.TestCase):

	def test_add_chars_letters(self):

		expected = '<Hello>'
		actual = fc.get_start_end_char('Hello')

		self.assertEqual(expected, actual)

	def test_add_chars_numbers(self):

		expected = '<00421>'
		actual = fc.get_start_end_char('00421')

		self.assertEqual(expected,actual)

	def test_add_char_param(self):
		expected = '<123>'
		test_param = 123
		actual = fc.get_start_end_char(test_param)
		
		self.assertEqual(expected,actual)


class test_check_focuser_no(unittest.TestCase):

	def test_ok_number(self):

		expected = 2
		actual = fc.check_focuser_no(2)
		self.assertEqual(actual,expected)

	def test_bad_no(self):
		with self.assertRaises(ValueError):
			fc.check_focuser_no(6)
		with self.assertRaises(ValueError):
			fc.check_focuser_no(1.2)
		with self.assertRaises(ValueError):
			fc.check_focuser_no('1')
		with self.assertRaises(ValueError):
			fc.check_focuser_no('hi')

class test_get_focuser_name(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {
			'<F1HELLO>': 'Optec 2in TCF-S','<F2HELLO>': 'Optec 2in TCF-N'}

	def test_wrong_focuser_no(self):

		with self.assertRaises(ValueError):
			fc.get_focuser_name(6,self.dummy_port)

	def test_good_number(self):
		self.assertEqual('Optec 2in TCF-S', fc.get_focuser_name(1,self.dummy_port))
		self.assertEqual('Optec 2in TCF-N', fc.get_focuser_name(2,self.dummy_port))

	def tearDown(self):
		self.dummy_port.close()


class test_halt_focuser(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1HALT>': 'HALTED','<F2HALT>': 'HALTED'}

	def test_wrong_focuser_no(self):

		with self.assertRaises(ValueError):
			fc.halt_focuser(6,self.dummy_port)
	
	def test_good_number(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.halt_focuser(1,self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
		
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.halt_focuser(2,self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

	def tearDown(self):
		self.dummy_port.close()


if __name__=="__main__":
	unittest.main()