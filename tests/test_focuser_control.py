import unittest
from unittest.mock import patch
import focuser_control as fc

try:
	import dummyserial as dummy_serial
except ModuleNotFoundError:
	import dummy_serial

"""
Note all unit tests that send/receive information to/from an open serial port 
 are test with dummy_serial, using a mock serial port. Tests to ensure the 
 actual devices are sending the information that is expected have so far not 
 been possible (30/10/18)
"""

class test_config_port_values(unittest.TestCase):
	"""
	Tests for the checking the baud_rate, stop_bit etc supplied by the config 
	file.
	"""
	
	# No exceptions if all working
	def test_baud_rate_present_correct(self):
		test_dict_ok = dict({'baud_rate':115200,'data_bits':8, 'stop_bits':1,
			'parity':'N'})
		# normally states what we expect to happen, here want to check it
		#doesn't raise exception
		fc.check_config_port_values_for_focuser(test_dict_ok)


	#if there is a baud rate, but wrong number
	def test_baud_rate_present_but_wrong_value(self):
		test_dict_wrongBD = dict({'baud_rate':1152000,'data_bits':8,
			'stop_bits':1, 'parity':'N'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the
			# other function
			fc.check_config_port_values_for_focuser(test_dict_wrongBD)

	
	# not baud rate present
	def test_baud_rate_not_present(self):
		test_dict_noBD = dict({'data_bits':8, 'stop_bits':1, 'parity':'N'})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fc.check_config_port_values_for_focuser(test_dict_noBD)


	#if there is a data bits value, but wrong number
	def test_data_bits_present_but_wrong_value(self):
		test_dict_wrongDB = dict({'baud_rate':115200,'data_bits':9,
			'stop_bits':1, 'parity':'N'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the
			#other function
			fc.check_config_port_values_for_focuser(test_dict_wrongDB)
	
	# not data bits present
	def test_data_bits_not_present(self):
		test_dict_noDB = dict({'baud_rate':115200, 'stop_bits':1, 'parity':'N'})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fc.check_config_port_values_for_focuser(test_dict_noDB)

	#if there is a stop bits value, but wrong number
	def test_stop_bits_present_but_wrong_value(self):
		test_dict_wrongSB = dict({'baud_rate':115200,'data_bits':8,
			'stop_bits':4, 'parity':'N'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the
			#other function
			fc.check_config_port_values_for_focuser(test_dict_wrongSB)
	
	# no stop bits present
	def test_stop_bits_not_present(self):
		test_dict_noSB = dict({'baud_rate':115200, 'data_bits':8, 'parity':'N'})
		#expect a keyError to be raised
		with self.assertRaises(KeyError):
			fc.check_config_port_values_for_focuser(test_dict_noSB)

	#if there is a parity value, but wrong
	def test_parity_present_but_wrong_value(self):
		test_dict_wrongPar = dict({'baud_rate':115200,'data_bits':8,
			'stop_bits':1, 'parity':'S'})
		with self.assertRaises(ValueError):
			# need self.test_dict... to refer to a property defined in the
			# other function
			fc.check_config_port_values_for_focuser(test_dict_wrongPar)
	
	# no parity present
	def test_parity_not_present(self):
		test_dict_noPar = dict({'baud_rate':115200,'data_bits':8,
			'stop_bits':1})
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

		#Pretend a serial port has already been opened has been initialised
		#using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {
			'<F1HELLO>': '!\nOptec 2in TCF-S','<F2HELLO>': '!\nOptec 2in TCF-N'}

	def test_wrong_focuser_no_name(self):

		with self.assertRaises(ValueError):
			fc.get_focuser_name(6,self.dummy_port)

	def test_good_number_name(self):
		self.assertEqual('Optec 2in TCF-S', fc.get_focuser_name(
			self.dummy_port,1))
		self.assertEqual('Optec 2in TCF-N', fc.get_focuser_name(
			self.dummy_port,2))

	def tearDown(self):
		self.dummy_port.close()


class test_halt_focuser(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
			#using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1HALT>': '!\nHALTED',
			'<F2HALT>': '!\nHALTED'}

	def test_wrong_focuser_no_halt(self):

		with self.assertRaises(ValueError):
			fc.halt_focuser(6,self.dummy_port)
	
	def test_good_number_halt(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.halt_focuser(self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
		
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.halt_focuser(self.dummy_port,x=2))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

	def tearDown(self):
		self.dummy_port.close()


@patch("PLC_interaction_functions.plc_get_telescope_tilt_status")
class test_home_focuser(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
			#using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1HOME>': '!\nH','<F2HOME>': '!\nH'}

	def test_wrong_focuser_no_home(self,mock_tilt):

		mock_tilt.return_value = dict({'Tilt_angle':"6h East <= x < RA East limit"})
		with self.assertRaises(ValueError):
			fc.home_focuser(6,self.dummy_port)

		mock_tilt.assert_called_once()
	
	def test_good_number_home(self,mock_tilt):
	
		mock_tilt.return_value = dict({'Tilt_angle':"6h East <= x < RA East limit"})
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.home_focuser(self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
		
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.home_focuser(self.dummy_port,x=2))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
		self.assertEqual(mock_tilt.call_count,2)
		
	def test_telescope_not_stowed(self, mock_tilt):
	
		mock_tilt.return_value = dict({'Tilt_angle':"1h East < x < 1h West"})
		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().error(fc.home_focuser(self.dummy_port,x=2))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

	def tearDown(self):
		self.dummy_port.close()

@patch("PLC_interaction_functions.plc_get_telescope_tilt_status")
class test_center_focuser(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
		# using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1CENTER>': '!\nM','<F2CENTER>': '!\nM'}

	def test_wrong_focuser_no_center(self, mock_tilt):

		mock_tilt.return_value = dict({'Tilt_angle':"6h East <= x < RA East limit"})
		with self.assertRaises(ValueError):
			fc.center_focuser(6,self.dummy_port)

		mock_tilt.assert_called_once()
	
	def test_good_number_center(self, mock_tilt):
		mock_tilt.return_value = dict({'Tilt_angle':"6h East <= x < RA East limit"})
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.center_focuser(self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
		
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.center_focuser(self.dummy_port,x=2))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
		self.assertEqual(mock_tilt.call_count,2)
		
	def test_telescope_not_stowed(self, mock_tilt):
	
		mock_tilt.return_value = dict({'Tilt_angle':"1h East < x < 1h West"})
		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().error(fc.home_focuser(self.dummy_port,x=2))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

	def tearDown(self):
		self.dummy_port.close()


class test_move_to_position(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
		# using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1MA042000>': '!\nM','<F2MA045023>': '!\nM'}

	def test_wrong_focuser_no_move_pos(self):

		with self.assertRaises(ValueError):
			fc.move_to_position(42345, 6,self.dummy_port)
	
	def test_good_number_move_pos(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.move_to_position(42000,
				self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
		
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.move_to_position(45023,
				self.dummy_port,x=2))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
	def check_pos_too_low(self):
		with self.assertRaises(ValueError):
			fc.move_to_position(-0.2356, self.dummy_port)

	def check_pos_too_high(self):
		with self.assertRaises(ValueError):
			fc.move_to_position(112001, self.dummy_port)

	def tearDown(self):
		self.dummy_port.close()

class test_move_focuser_in(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
		# using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1MIR1>': '!\nM','<F2MIR1>': '!\nM',
			'<F1MIR0>': '!\nM','<F2MIR0>': '!\nM'}

	def test_wrong_focuser_no_movein(self):

		with self.assertRaises(ValueError):
			fc.move_focuser_in(6,self.dummy_port, move_speed=1)
	
	def test_good_number_movein(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.move_focuser_in(self.dummy_port,
				move_speed=1))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
		
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.move_focuser_in(self.dummy_port,x=2,
				move_speed=1))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
	def test_not_valid_speed_in(self):
		with self.assertRaises(ValueError):
			fc.move_focuser_in(self.dummy_port, move_speed = 3)

		with self.assertRaises(ValueError):
			fc.move_focuser_in(self.dummy_port, move_speed = -0.3)

		with self.assertRaises(ValueError):
			fc.move_focuser_in(self.dummy_port, move_speed = 'hi')

	def tearDown(self):
		self.dummy_port.close()


class test_move_focuser_out(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
		# using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1MOR1>': '!\nM','<F2MOR1>': '!\nM',
			'<F1MOR0>': '!\nM','<F2MOR0>': '!\nM'}

	def test_wrong_focuser_no_moveout(self):

		with self.assertRaises(ValueError):
			fc.move_focuser_out(self.dummy_port,x=6, move_speed=1)
	
	def test_good_number_moveout(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.move_focuser_out(self.dummy_port,
				move_speed=1))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
		
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.move_focuser_out(self.dummy_port,x=2,
				move_speed=1))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
	def test_not_valid_speed_out(self):
		with self.assertRaises(ValueError):
			fc.move_focuser_out(self.dummy_port, move_speed = 3)

		with self.assertRaises(ValueError):
			fc.move_focuser_out(self.dummy_port, move_speed = -0.3)

		with self.assertRaises(ValueError):
			fc.move_focuser_out(self.dummy_port, move_speed = 'hi')

	def tearDown(self):
		self.dummy_port.close()


class test_end_relative_move(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
		#	using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1ERM>': '!\nSTOPPED',
			'<F2ERM>': '!\nSTOPPED'}

	def test_wrong_focuser_no_endmove(self):

		with self.assertRaises(ValueError):
			fc.end_relative_move(self.dummy_port, x=6)
	
	def test_good_number_endmove(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.end_relative_move(self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
		
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.end_relative_move(self.dummy_port,
				x=2))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

	def tearDown(self):
		self.dummy_port.close()


class test_get_status(unittest.TestCase):

	def setUp(self):
		#Pretend a serial port has already been opened has been initialised
		#	using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1GETSTATUS>': '!\nSTATUS1\nTemp(C)  = '\
			'+21.7\nCurr Pos = 108085\nTarg Pos = 000000\nIsMoving = 1\n' \
			'IsHoming = 1\nIsHomed  = 0\nFFDetect = 0\nTmpProbe = 1\nRemoteIO '\
			'= 0\nHnd Ctlr = 0\nEND'}

	def test_return_status(self):

		expected = 'STATUS1\nTemp(C)  = +21.7\nCurr Pos = 108085\nTarg Pos = ' \
		'000000\nIsMoving = 1\nIsHoming = 1\nIsHomed  = 0\nFFDetect = 0\n'\
		'TmpProbe = 1\nRemoteIO = 0\nHnd Ctlr = 0\nEND'
		actual = fc.get_focuser_status(self.dummy_port)
		self.assertEqual(actual,expected)
	
	def test_return_status_dict(self):
	
		expected = {'Temp(C)': '+21.7', 'Curr Pos': '108085',
			'Targ Pos': '000000', 'IsMoving': '1', 'IsHoming': '1',
			'IsHomed': '0', 'FFDetect': '0', 'TmpProbe': '1', 'RemoteIO': '0',
			'Hnd Ctlr': '0'}
		actual = fc.get_focuser_status(self.dummy_port, return_dict=True)
		self.assertEqual(actual,expected)

	def tearDown(self):
		self.dummy_port.close()

class test_get_config(unittest.TestCase):

	def setUp(self):
		#Pretend a serial port has already been opened has been initialised
		# using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1GETCONFIG>': '!\nCONFIG1\nNickname = '\
		'FocusLynx Foc2\nMax Pos = 125440\nDevTyp =OE\nTComp ON = 0\nTempCo A '\
		'= +0086\nTempCo B = +0086\nTempCo C = +0086\nTempCo D = +0000\n'\
		'TempCo E = +0000\nTCMode =A\nBLC En =0\nBLC Stps = +40\nLED Brt = '\
		'075\nTC@Start = 0\nEND'}

	def test_return_config(self):

		expected = 'CONFIG1\nNickname = FocusLynx Foc2\nMax Pos = 125440\n'\
		'DevTyp =OE\nTComp ON = 0\nTempCo A = +0086\nTempCo B = +0086\n'\
		'TempCo C = +0086\nTempCo D = +0000\nTempCo E = +0000\nTCMode =A'\
		'\nBLC En =0\nBLC Stps = +40\nLED Brt = 075\nTC@Start = 0\nEND'
		actual = fc.get_focuser_stored_config(self.dummy_port)
		self.assertEqual(actual,expected)
	
	def test_return_config_mess_dict(self):
	
		expected = {'Nickname': 'FocusLynx Foc2', 'Max Pos': '125440',
		'DevTyp': 'OE', 'TComp ON': '0', 'TempCo A': '+0086',
		'TempCo B': '+0086', 'TempCo C': '+0086', 'TempCo D': '+0000',
		'TempCo E': '+0000', 'TCMode': 'A', 'BLC En': '0', 'BLC Stps': '+40',
		'LED Brt': '075', 'TC@Start': '0'}
		actual = fc.get_focuser_stored_config(self.dummy_port,
			return_dict=True)
		self.assertEqual(actual,expected)
	

	def tearDown(self):
		self.dummy_port.close()

class test_set_device_name(unittest.TestCase):

	def setUp(self):

		self.goodname = 'testname'
		#Pretend a serial port has already been opened has been initialised
			#using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1SCNNtestname>': '!\nSET'}

	def test_wrong_focuser_no_setname(self):

		with self.assertRaises(ValueError):
			fc.set_device_name(self.dummy_port, self.goodname, x=6)
	
	def test_good_number_set_name(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_device_name(
				self.dummy_port,self.goodname))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')
		
	def test_name_too_long(self):
		with self.assertRaises(ValueError):
			fc.set_device_name(self.dummy_port, 'reallllyLONGNAMEEEEEE')

	def test_name_too_short(self):
		with self.assertRaises(ValueError):
			fc.set_device_name(self.dummy_port, '')


	def tearDown(self):
		self.dummy_port.close()

class test_set_device_type(unittest.TestCase):

	def setUp(self):
	
		self.goodtype='OB'
		self.badtype = 'BC'
	
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1SCDTOB>': '!\nSET'}


	def test_get_error_for_bad_type(self):
		with self.assertRaises(ValueError):
			fc.set_device_type(self.dummy_port, device_type = self.badtype)

		with self.assertRaises(ValueError):
			fc.set_device_type(self.dummy_port, device_type = 0.12)

	def test_good_type_bad_focuser(self):
		with self.assertRaises(ValueError):
			fc.set_device_type(self.dummy_port, device_type = self.goodtype, x=5)

	def test_good_type_good_focuser(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_device_type(self.dummy_port,
				device_type = self.goodtype))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')


	def tearDown(self):
		self.dummy_port.close()


class test_set_temp_comp_state(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
			#using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1SCTE1>': '!\nSET','<F1SCTE0>': '!\nSET'}

	def test_wrong_focuser_no_temp_comp(self):

		with self.assertRaises(ValueError):
			fc.set_temp_comp(self.dummy_port, temp_comp = False, x=6)

	def test_wrong_temp_comp_state(self):

		with self.assertRaises(ValueError):
			fc.set_temp_comp(self.dummy_port,'hiiii')

	def test_set_temp_comp_enabled(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_temp_comp(
				self.dummy_port,temp_comp =True))
			logging_response = cm.output[0]#.split(':')[0]
		self.assertEqual(logging_response, 'INFO:'+fc.__name__+':Temperature '\
				'compensation ENABLED for focuser 1')

	def test_set_temp_comp_disabled(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_temp_comp(self.dummy_port,
				temp_comp =False))
			logging_response = cm.output[0]#.split(':')[0]
		self.assertEqual(logging_response, 'INFO:'+fc.__name__+':Temperature '\
				'compensation DISABLED for focuser 1')
	
	def tearDown(self):
		self.dummy_port.close()

class test_set_temp_comp_mode(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
		#  using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1SCTMA>': '!\nSET'}

	def test_good_type_good_focuser(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_temp_comp_mode(
				self.dummy_port,mode = 'A'))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

	def test_wrong_focuser_no_temp_comp_mode(self):
		with self.assertRaises(ValueError):
			fc.set_temp_comp_mode(self.dummy_port, mode = 'A',x=3)

	def test_bad_mode(self):
		with self.assertRaises(ValueError):
			fc.set_temp_comp_mode(self.dummy_port,'hiiii')

		with self.assertRaises(ValueError):
			fc.set_temp_comp_mode(self.dummy_port,0.323)

		with self.assertRaises(ValueError):
			fc.set_temp_comp_mode(self.dummy_port, 'N')

	def tearDown(self):
		self.dummy_port.close()


class test_set_temp_comp_coeff(unittest.TestCase):

	def setUp(self):
		#Pretend a serial port has already been opened has been initialised
		# using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1SCTCA+0092>': '!\nSET',
			'<F1SCTCA-0001>':'!\nSET','<F1SCTCA+0000>':'!\nSET'}

	def test_wrong_focuser_no_temp_coeff_set(self):
		with self.assertRaises(ValueError):
			fc.set_temp_comp_coeff(self.dummy_port, 'A', 92, x=3)

	def test_bad_coeff_val(self):
		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().error(fc.set_temp_comp_coeff(
				self.dummy_port,'A', -10000))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().error(fc.set_temp_comp_coeff(
				self.dummy_port,'A', 120000))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().error(fc.set_temp_comp_coeff(
				self.dummy_port,'A', 0.0345))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().error(fc.set_temp_comp_coeff(
				self.dummy_port,'A', 'testword'))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

	def test_good_coeff_val(self):

		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_temp_comp_coeff(
				self.dummy_port,'A',92))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_temp_comp_coeff(
				self.dummy_port,'A',-1))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_temp_comp_coeff(
				self.dummy_port,'A',0))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

	def tearDown(self):
		self.dummy_port.close()

class test_set_temp_comp_start_state(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
		# using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1SCTS1>': '!\nSET','<F1SCTS0>': '!\nSET'}

	def test_wrong_focuser_no_temp_comp_start(self):

		with self.assertRaises(ValueError):
			fc.set_temp_comp_start_state(self.dummy_port, x=6,
				temp_comp_start = False)

	def test_wrong_temp_comp_state(self):

		with self.assertRaises(ValueError):
			fc.set_temp_comp_start_state(self.dummy_port,temp_comp_start = 'hiiii')

	def test_set_temp_comp_enabled(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_temp_comp_start_state(
				self.dummy_port,temp_comp_start = True))
			logging_response = cm.output[0]#.split(':')[0]
		self.assertEqual(logging_response, 'INFO:'+fc.__name__+':"Temperature '\
			'compensation at start" state set to ENABLED for focuser 1')

	def test_set_temp_comp_disabled(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_temp_comp_start_state(
				self.dummy_port,temp_comp_start = False))
			logging_response = cm.output[0]#.split(':')[0]
		self.assertEqual(logging_response, 'INFO:'+fc.__name__+':"Temperature '\
		'compensation at start" state set to DISABLED for focuser 1')
	
	def tearDown(self):
		self.dummy_port.close()


class test_set_backlash_comp(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
		# using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1SCBE1>': '!\nSET','<F1SCBE0>': '!\nSET'}

	def test_wrong_focuser_no_backlash_comp(self):

		with self.assertRaises(ValueError):
			fc.set_backlash_comp(self.dummy_port, backlash_comp = False, x=6)

	def test_wrong_backlash_comp_state(self):

		with self.assertRaises(ValueError):
			fc.set_backlash_comp(1,self.dummy_port,'hiiii')

	def test_set_backlash_comp_enabled(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_backlash_comp(
				self.dummy_port,backlash_comp = True))
			logging_response = cm.output[0]#.split(':')[0]
		self.assertEqual(logging_response, 'INFO:'+fc.__name__+':Backlash '\
		'compensation state set to ENABLED for focuser 1')

	def test_set_backlash_comp_disabled(self):
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_backlash_comp(
				self.dummy_port,backlash_comp = False))
			logging_response = cm.output[0]#.split(':')[0]
		self.assertEqual(logging_response, 'INFO:'+fc.__name__+':Backlash '\
			'compensation state set to DISABLED for focuser 1')
	
	def tearDown(self):
		self.dummy_port.close()

class test_set_backlash_steps(unittest.TestCase):

	def setUp(self):
		#Pretend a serial port has already been opened has been initialised
			#using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1SCBS10>': '!\nSET','<F1SCBS01>': '!\nSET'}

	def test_wrong_focuser_no_backlash_steps(self):
		with self.assertRaises(ValueError):
			fc.set_backlash_steps(self.dummy_port, backlash_steps = 20, x=6)

	def test_bad_step_value(self):
		#negative value
		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().error(fc.set_backlash_steps(
				self.dummy_port,backlash_steps = -2))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')
		#too large value
		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().error(fc.set_backlash_steps(
				self.dummy_port,backlash_steps = 103))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

		# decimal
		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().error(fc.set_backlash_steps(
				self.dummy_port,backlash_steps = 56.42))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

		#string
		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().error(fc.set_backlash_steps(
				self.dummy_port,backlash_steps = 'TEST'))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

	def test_ok_step_num(self):
	
		#Do both 1 and 10 to make sure the formatting is working
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_backlash_steps(
				self.dummy_port,backlash_steps = 1))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.set_backlash_steps(
				self.dummy_port,backlash_steps = 10))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

	def tearDown(self):
		self.dummy_port.close()


class test_set_LED_brightness(unittest.TestCase):

	def setUp(self):

		#Pretend a serial port has already been opened has been initialised
		# using dummy_serial
		self.dummy_port = dummy_serial.Serial(port='test_port', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<FFSCLB010>': '!\nSET'}

	def test_wrong_brightness(self):

		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().info(fc.set_LED_brightness(-0.23,
				self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().info(fc.set_LED_brightness(1000,
				self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')
		
		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().info(fc.set_LED_brightness('fds',
				self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

		with self.assertLogs(level='ERROR') as cm:
			fc.logging.getLogger().info(fc.set_LED_brightness(55.5,
				self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

	def tearDown(self):
		self.dummy_port.close()


@patch("common.open_port_from_config_param")
@patch("common.load_config")
class test_focuser_initial_configuration(unittest.TestCase):
	
	def setUp(self):
		self.test_dict = dict({'focuser_name': 'focuser1-south',
			'focuser_no': 1, 'port_name': 'focus1', 'baud_rate': 115200,
			'data_bits': 8, 'stop_bits': 1, 'parity': 'N', 'device_type': 'OB',
			'LED_brightness': 10, 'center_position': 56000, 'min_position': 0,
			'max_position': 112000, 'temp_compen': False,
			'temp_compen_mode': 'A', 'temp_compen_at_start': False,
			'temp_coeffA': 86, 'temp_coeffB': 46, 'temp_coeffC': 74,
			'temp_coeffD': 23, 'temp_coeffE': 23, 'backlash_compen': 1,
			'backlash_steps': 10})
		
		self.dummy_port = dummy_serial.Serial(port=self.test_dict['port_name'],
			timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
	
		dummy_serial.RESPONSES = {'<F1SCNNtestname>': '!\nSET', #device name
				'<F1SCDTOB>': '!\nSET', #device type
				'<FFSCLB010>': '!\nSET', # LED Brightness
				'<F1SCTE1>': '!\nSET','<F1SCTE0>': '!\nSET', #temp comp state
				'<F1SCTMA>': '!\nSET', #temp comp mode
				'<F1SCTCA+0088>': '!\nSET', '<F1SCTCB+0046>': '!\nSET',
				'<F1SCTCC+0074>': '!\nSET',
					'<F1SCTCD+0023>': '!\nSET',
					'<F1SCTCE+0023>': '!\nSET', #temp comp set coeff
				'<F1SCTS1>': '!\nSET','<F1SCTS0>': '!\nSET', #temp comp at start
				'<F1SCBE1>': '!\nSET','<F1SCBE0>': '!\nSET', #backlash comp
				}

	def test_can_set_configs(self, mock_dict, mock_port):

		mock_dict.return_value = self.test_dict
		mock_port.return_value = self.dummy_port

		fc.focuser_initial_configuration('focuser1-south.cfg')
		expected_port_open = False
		actual_port_open = self.dummy_port._isOpen
		self.assertEqual(expected_port_open,actual_port_open)


@patch("focuser_control.get_focuser_stored_config")
@patch("common.open_port_from_config_param")
@patch("common.load_config")
class test_startup_focuser(unittest.TestCase):

	def setUp(self):
		self.test_dict = dict({'focuser_name': 'focuser1-south',
			'focuser_no': 1, 'port_name': 'focus1', 'baud_rate': 115200,
			'data_bits': 8, 'stop_bits': 1, 'parity': 'N', 'device_type': 'OB',
			'LED_brightness': 10, 'center_position': 56000, 'min_position': 0,
			'max_position': 112000, 'temp_compen': False,
			'temp_compen_mode': 'A', 'temp_compen_at_start': False,
			'temp_coeffA': 86, 'temp_coeffB': 46, 'temp_coeffC': 74,
			'temp_coeffD': 23, 'temp_coeffE': 23, 'backlash_compen': 1,
			'backlash_steps': 10})
		
		self.dummy_port = dummy_serial.Serial(port=self.test_dict['port_name'],
			timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1HOME>': '!\nH'}
		
	
	def test_return_focuser_and_port(self, mock_dict, mock_port,
			mock_get_config):
		mock_dict.return_value = self.test_dict
		mock_port.return_value = self.dummy_port
		mock_get_config.return_value = dict({'TComp ON': 1, 'BLC En': 1})
			#Don't care about other settings
		
		expected_focuser_no = 1
		expected_port_open = True
		
		actual_focuser_no, actual_port = fc.startup_focuser('focuser1-south',
			config_file_loc='configs/')
		actual_port_open = actual_port._isOpen
		
		mock_port.assert_called_once_with(self.test_dict)
		mock_dict.assert_called_once_with('focuser1-south',path='configs/')
		self.assertEqual(expected_port_open,actual_port_open)
		self.assertEqual(expected_focuser_no, actual_focuser_no)
		
		
	def tearDown(self):
		self.dummy_port.close()

		
class test_shutdown_focuser(unittest.TestCase):

	def setUp(self):
		self.dummy_port = dummy_serial.Serial(port='port1', timeout=0.00001)
		dummy_serial.DEFAULT_BAUDRATE = 115200
		# Setup up the expected responses
		dummy_serial.RESPONSES = {'<F1CENTER>': '!\nM','<F2CENTER>': '!\nM'}
		
	def test_it_runs(self):
	
		with self.assertLogs(level='INFO') as cm:
			fc.logging.getLogger().info(fc.shutdown_focuser(self.dummy_port))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

		expected_port_open = False
		actual_port_open = self.dummy_port._isOpen
		self.assertEqual(expected_port_open, actual_port_open)



if __name__=="__main__":
	unittest.main()