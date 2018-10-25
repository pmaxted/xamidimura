import unittest
import filter_wheel_control as fwc

class test_config_port_values(unittest.TestCase):
	
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
class SerialTestObject(object):
	""" A mock serial port test class"""
	def __init__(self)
	""" creates a mock serial port which is a loopback object"""
	self._port = 'loop://'
	self.timepout = 0
	self._baudrate = 19200
	self.serialPort = serial.serial_for_url
"""
"""
class test_port_initialisation(unittest.TestCase):

	# Setup the dictionary to be used in all the other unit tests
	def setUp(self):
		# self. is needed otherwise the function will forget itself at the end
		self.test_dict = dict({'baud_rate':19200,'data_bits':8, 'stop_bits':1, 'parity':'N'})

	def test_initialise_no_errors(self):
		open_port = fwc.initialise_ifw_serial_connection(self.test_dict)
"""





if __name__ =='__main__':
	unittest.main()
