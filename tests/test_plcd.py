"""
test_plcd.py
Jessica A. Evans
03/01/2019

Contains unit tests for the plcd script.
	
	NOTE: no tests for the main function because haven't worked out how to
	 test the while loop
	

"""

import unittest
from unittest.mock import patch
import plcd
import settings_and_error_codes as set_err_codes
import serial


try:
	import dummyserial as dummy_serial
except ModuleNotFoundError:
	import dummy_serial


class test_PLC_ERROR_class(unittest.TestCase):

	def test_creates_execption(self):
		#check returns message
		
		expected_message = 'Test message'
		
		err = plcd.PLC_ERROR(expected_message)
		actual_message = err.message
		self.assertEqual(expected_message,actual_message)

class test_split_up_response(unittest.TestCase):

	#Don't need to test this function works correctly, that is done in all other tests

	def test_invalid_response_error(self):
		response = "00RD0080060001000100005D*\r"

		with self.assertRaises(plcd.PLC_ERROR):
			plcd.split_up_response(response)


	def test_invalid_fcs(self):
		response = "@00RD0080060001000100005E*\r"

		with self.assertRaises(plcd.PLC_ERROR):
			plcd.split_up_response(response)

@patch("roof_control_functions.plc_command_response_port_open")
class test_get_D100_D102_status(unittest.TestCase):

	def setUp(self):
		self.port = serial.Serial(baudrate = plcd.rcf.PLC_BAUD_RATE,
			parity=plcd.rcf.PLC_PARITY, stopbits = plcd.rcf.PLC_STOP_BITS,
			bytesize = plcd.rcf.PLC_CHARACTER_LENGTH,
			timeout = plcd.rcf.PLC_PORT_TIMEOUT) #port = PLC_COM_PORT,
	#Don't need to test this function works correctly, that is done in all other tests
	
	def test_error_getting_roof_status_error(self, mock_plc_response):
		returned_commands = ["@00RD148006000100015D*\r"]

		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plcd.PLC_ERROR):
			plcd.get_D100_D102_status(self.port)

		mock_plc_response.assert_called_once()




@patch("roof_control_functions.plc_command_response_port_open")
class test_create_and_send_new_command(unittest.TestCase):

	#Don't need to test this function works correctly, that is done in all other tests
	
	def setUp(self):
		self.port = serial.Serial(baudrate = plcd.rcf.PLC_BAUD_RATE,
			parity=plcd.rcf.PLC_PARITY, stopbits = plcd.rcf.PLC_STOP_BITS,
			bytesize = plcd.rcf.PLC_CHARACTER_LENGTH,
			timeout = plcd.rcf.PLC_PORT_TIMEOUT) #port = PLC_COM_PORT,
	
	def test_command_fail_error(self, mock_plc_response):
		# Not sure if this is a valid incorrect command, it's just something that I know will fail
		returned_commands = ["@00WD0152*\r"]
		# 3rd response - Command accepted is "@00WD0053*\r", change to "@00WD0152*\r" for not accepted
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plcd.PLC_ERROR):
			plcd.create_and_send_new_command('B002','0001','0001','0A00',self.port)

		mock_plc_response.called_once()



class test_decode_tilt_status(unittest.TestCase):

	def test_drive_set_west_limit(self):

		expected_dict = dict({'Tilt Response Code':"6A00",
			'Tel_drive_control':'Roof Controller',
			'Tilt_angle':"RA West limit"})

		actual_dict = plcd.decode_tilt_status("6A00")
		self.assertEqual(expected_dict, actual_dict)

	def test_1hr_west_no_drive(self):

		expected_dict = dict({'Tilt Response Code':"0200",
			'Tel_drive_control':'Normal - PC',
			'Tilt_angle':"1h West <= x < 6h West"})

		actual_dict = plcd.decode_tilt_status("0200")
		self.assertEqual(expected_dict, actual_dict)

	def test_invalid_tilt_bit_combo(self):

		with self.assertRaises(plcd.PLC_ERROR):
			plcd.decode_tilt_status("0201")


# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response_port_open")
class test_request_remote_roof_control(unittest.TestCase):

	def setUp(self):
		self.port = serial.Serial(baudrate = plcd.rcf.PLC_BAUD_RATE,
			parity=plcd.rcf.PLC_PARITY, stopbits = plcd.rcf.PLC_STOP_BITS,
			bytesize = plcd.rcf.PLC_CHARACTER_LENGTH,
			timeout = plcd.rcf.PLC_PORT_TIMEOUT)

	def test_complete_request(self, mock_plc_response):
		returned_commands = ["@00RD008005000100010A002A*\r","@00WD0053*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000000000101) Roof closed, mains, watch dog
		# 2nd response - command accepted
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands
		
		plcd.request_remote_roof_control(self.port)
		self.assertEqual(mock_plc_response.call_count,3)


	def test_request_with_bit_set(self, mock_plc_response):
		returned_commands = ["@00RD008105000100010A002B*\r","@00WD0053*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000100000101) Roof closed, mains, watch dog, request already set
		# 2nd response - command accepted
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands
		
		plcd.request_remote_roof_control(self.port)
	
		self.assertEqual(mock_plc_response.call_count,3)


# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response_port_open")
class test_request_telescope_drive_control(unittest.TestCase):

	def setUp(self):
		self.port = serial.Serial(baudrate = plcd.rcf.PLC_BAUD_RATE,
			parity=plcd.rcf.PLC_PARITY, stopbits = plcd.rcf.PLC_STOP_BITS,
			bytesize = plcd.rcf.PLC_CHARACTER_LENGTH,
			timeout = plcd.rcf.PLC_PORT_TIMEOUT)

	def test_complete_request(self, mock_plc_response):
		returned_commands = ["@00RD0080060001000158*\r","@00WD0053*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1100000000000110) Roof closed, mains, watch dog
		# 2nd response - command accepted
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands
		
		plcd.request_telescope_drive_control(self.port)
	
		self.assertEqual(mock_plc_response.call_count,3)


	def test_request_with_bit_set(self, mock_plc_response):
		returned_commands = ["@00RD00C0060001000123*\r","@00WD0053*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000100000101) Roof closed, mains, watch dog, request already set
		# 2nd response - command accepted
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands
		
		plcd.request_telescope_drive_control(self.port)
	
		self.assertEqual(mock_plc_response.call_count,3)

# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response_port_open")
class test_select_mains(unittest.TestCase):

	def setUp(self):
		self.port = serial.Serial(baudrate = plcd.rcf.PLC_BAUD_RATE,
			parity=plcd.rcf.PLC_PARITY, stopbits = plcd.rcf.PLC_STOP_BITS,
			bytesize = plcd.rcf.PLC_CHARACTER_LENGTH,
			timeout = plcd.rcf.PLC_PORT_TIMEOUT)

	def test_complete_mains_request(self, mock_plc_response):
		returned_commands = ["@00RD008001000100015F*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000000000001) Roof closed, battery, watch dog
		# 2nd response - command accepted
		mock_plc_response.side_effect = returned_commands


		plcd.select_mains(self.port)
	
		self.assertEqual(mock_plc_response.call_count,2)

class test_motor_stop_check(unittest.TestCase):

	def test_motor_stop_is_pressed(self):

		input_val = int("0109",16)
		expected = True
		actual = plcd.motor_stop_check(input_val)
		self.assertEqual(expected,actual)

		with self.assertLogs(level='ERROR') as cm:
			plcd.logging.getLogger().error(plcd.motor_stop_check(input_val))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'ERROR')

	def test_motor_stop_not_pressed(self):

		input_val = int("000A",16)
		expected = False
		actual = plcd.motor_stop_check(input_val)
		self.assertEqual(expected,actual)

		with self.assertLogs(level='INFO') as cm:
			plcd.logging.getLogger().info(plcd.motor_stop_check(input_val))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'INFO')


class test_remote_control_check(unittest.TestCase):

	def setUp(self):
		self.port = serial.Serial(baudrate = plcd.rcf.PLC_BAUD_RATE,
			parity=plcd.rcf.PLC_PARITY, stopbits = plcd.rcf.PLC_STOP_BITS,
			bytesize = plcd.rcf.PLC_CHARACTER_LENGTH,
			timeout = plcd.rcf.PLC_PORT_TIMEOUT)

	def test_is_set_to_remote(self):

		input_val = int("000A",16)
		expected = True
		actual = plcd.remote_control_check(input_val,self.port)

	@patch("plcd.request_remote_roof_control")
	def test_not_set_request_throws_error(self, mock_remote_request):

		mock_remote_request.side_effect = plcd.PLC_ERROR
		input_val = int("0002",16)


		with self.assertLogs(level='ERROR') as cm:
			plcd.logging.getLogger().error(plcd.remote_control_check(input_val,
				self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'WARNING')
		self.assertEqual(logging_actual_response2, 'ERROR')

	@patch("roof_control_functions.plc_command_response_port_open")
	@patch("plcd.request_remote_roof_control")
	def test_not_set_but_gets_set(self, mock_request, mock_response):

		#mock_request
		input_val = int("0002",16)
		mock_response.return_value = "@00RD00000A025802580A0056*\r"

		expected = True
		actual = plcd.remote_control_check(input_val,self.port)

		self.assertEqual(expected,actual)

		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.remote_control_check(input_val,
				self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'WARNING')
		self.assertEqual(logging_actual_response2, 'INFO')


@patch("plcd.subprocess.run")
class test_telescope_tilt_check(unittest.TestCase):
	
	def setUp(self):
		self.port = serial.Serial(baudrate = plcd.rcf.PLC_BAUD_RATE,
			parity=plcd.rcf.PLC_PARITY, stopbits = plcd.rcf.PLC_STOP_BITS,
			bytesize = plcd.rcf.PLC_CHARACTER_LENGTH,
			timeout = plcd.rcf.PLC_PORT_TIMEOUT)
		
		self.completedProcess = plcd.subprocess.CompletedProcess
		
	def test_telescope_is_parked(self,mock_process):
		
		self.completedProcess.stdout = b'standard park output\nFollowed by exit status\n0\n'
		mock_process.return_value = self.completedProcess 
		input_val = "0A00"
		expected = True
		actual_bool, actual_dict =  plcd.telescope_tilt_check(input_val,self.port)
		
		self.assertEqual(expected,actual_bool)
		mock_process.assert_not_called
		
	def test_not_parked_PLC_error_raised(self,mock_process):
		
		input_val = "0200"
		self.completedProcess.stdout = b'standard park output\nFollowed by exit status\n1\n'
		mock_process.return_value = self.completedProcess
		expected = False
		actual_bool,actual_dict = plcd.telescope_tilt_check(input_val,self.port)
		
		self.assertEqual(expected,actual_bool)
		
		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.telescope_tilt_check(input_val,
				self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
			logging_actual_response3 = cm.output[2].split(':')[0]
		self.assertEqual(logging_actual_response1, 'WARNING')
		self.assertEqual(logging_actual_response2, 'ERROR')
		self.assertEqual(logging_actual_response3, 'CRITICAL')
		
		self.assertEqual(mock_process.call_count,2)
	
	
	def test_not_parked_subprocess_error(self,mock_process):
		
		input_val = "0200"
		mock_process.side_effect = TimeoutError
		expected = False
		actual_bool,actual_dict = plcd.telescope_tilt_check(input_val,self.port)
		
		self.assertEqual(expected,actual_bool)
		
		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.telescope_tilt_check(input_val,
				self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'WARNING')
		self.assertEqual(logging_actual_response2, 'CRITICAL')
		
		self.assertEqual(mock_process.call_count,2)
	
	@patch("roof_control_functions.plc_command_response_port_open")	
	def test_telescopes_been_parked_roof_status_error(self, mock_response,mock_process,):

		input_val = "0200"
		self.completedProcess.stdout = b'standard park output\nFollowed by exit status\n0\n'
		mock_process.return_value = self.completedProcess 
		mock_response.return_value = "@00RD190009270F0000000024*\r"
		
		
		with self.assertRaises(plcd.PLC_ERROR):
			plcd.telescope_tilt_check(input_val, self.port)
		
		mock_process.assert_called_once()
		mock_response.assert_called_once()
	
	
	@patch("roof_control_functions.plc_command_response_port_open")
	def test_telescopes_been_parked_status_is_parked(self,mock_response, mock_process):

		input_val = "0200"
		self.completedProcess.stdout = b'standard park output\nFollowed by exit status\n0\n'
		mock_process.return_value = self.completedProcess 
		mock_response.return_value = "@00RD00000A025802580A0056*\r"
		
		expected = True
		actual_bool,actual_dict = plcd.telescope_tilt_check(input_val,self.port)
		self.assertEqual(expected,actual_bool)
		
		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.telescope_tilt_check(input_val,
				self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'WARNING')
		self.assertEqual(logging_actual_response2, 'INFO')
		
		self.assertEqual(mock_process.call_count,2)
		self.assertEqual(mock_response.call_count,2)
		
	@patch("roof_control_functions.plc_command_response_port_open")
	def test_telescopes_been_parked_status_not_parked(self,mock_response, mock_process):

		input_val = "0200"
		self.completedProcess.stdout = b'standard park output\nFollowed by exit status\n0\n'
		mock_process.return_value = self.completedProcess 
		mock_response.return_value = "@00RD00000A02580258020025*\r"
		
		expected = False
		actual_bool,actual_dict = plcd.telescope_tilt_check(input_val,self.port)
		self.assertEqual(expected,actual_bool)
		
		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.telescope_tilt_check(input_val,
				self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'WARNING')
		self.assertEqual(logging_actual_response2, 'CRITICAL')
		
		self.assertEqual(mock_process.call_count,2)
		self.assertEqual(mock_response.call_count,2)

@patch("roof_control_functions.plc_command_response_port_open")
class test_stop_roof_instructions(unittest.TestCase):
	
	def setUp(self):
		self.port = serial.Serial(baudrate = plcd.rcf.PLC_BAUD_RATE,
			parity=plcd.rcf.PLC_PARITY, stopbits = plcd.rcf.PLC_STOP_BITS,
			bytesize = plcd.rcf.PLC_CHARACTER_LENGTH,
			timeout = plcd.rcf.PLC_PORT_TIMEOUT)
	
	def test_complete_stop_request(self, mock_plc_response):
		returned_commands = ["@00RD008005000100015B*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000000000101) Roof closed, mains, watch dog
		# 2nd response - command accepted
		mock_plc_response.side_effect = returned_commands

		plcd.stop_roof_instructions(self.port)
	
		self.assertEqual(mock_plc_response.call_count,2)


@patch("plcd.request_telescope_drive_control")
@patch("plcd.select_mains")
@patch("plcd.motor_stop_check")
@patch("plcd.telescope_tilt_check")
@patch("roof_control_functions.plc_command_response_port_open")
class test_close_roof(unittest.TestCase):

	def setUp(self):
		self.port = serial.Serial(baudrate = plcd.rcf.PLC_BAUD_RATE,
			parity=plcd.rcf.PLC_PARITY, stopbits = plcd.rcf.PLC_STOP_BITS,
			bytesize = plcd.rcf.PLC_CHARACTER_LENGTH,
			timeout = plcd.rcf.PLC_PORT_TIMEOUT)

	@patch("plcd.get_D100_D102_status")
	def test_error_getting_roof_status_error(self, mock_d100, mock_response,
		mock_tilt_check, mock_motor_stop_check, mock_select_mains,
		mock_tele_drive):

		mock_response.return_value = "@00RD190009270F0000000024*\r"

		with self.assertRaises(plcd.PLC_ERROR):
			plcd.close_roof_instructions(self.port)
	
		mock_response.assert_called_once()
		mock_tilt_check.not_called()
		mock_motor_stop_check.not_called()
		mock_select_mains.not_called()
		mock_tele_drive.not_called()
		mock_d100.not_called()

	@patch("plcd.get_D100_D102_status")
	def test_roof_all_ready_closed(self, mock_d100, mock_response,
		mock_tilt_check, mock_motor_stop_check, mock_select_mains,
		mock_tele_drive):

		mock_response.return_value = "@00RD008105000100010A002B*\r"

		expected = 0
		actual = plcd.close_roof_instructions(self.port)
		self.assertEqual(expected,actual)

		mock_response.called_once()
		mock_tilt_check.not_called()
		mock_motor_stop_check.not_called()
		mock_select_mains.not_called()
		mock_tele_drive.not_called()
		mock_d100.not_called()

	@patch("plcd.get_D100_D102_status")
	def test_battery_in_use_select_mains_give_error(self, mock_d100, mock_response,
			mock_tilt_check, mock_motor_stop_check, mock_select_mains,
			mock_tele_drive):
		
		mock_response.return_value = "@00RD00040A02580258020021*\r"
		mock_tilt_check.return_value = True, dict(
			{'Tilt_Angle':"6h West <= x < RA West limit", 'Tel_drive_control':
				"Normal - PC"})

		mock_motor_stop_check.return_value = False
		mock_select_mains.side_effect = plcd.PLC_ERROR
		
		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.close_roof_instructions(self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
			logging_actual_response3 = cm.output[2].split(':')[0]
			logging_actual_response4 = cm.output[3].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO')
		self.assertEqual(logging_actual_response2, 'INFO')
		self.assertEqual(logging_actual_response3, 'WARNING')
		self.assertEqual(logging_actual_response4, 'ERROR')
		

		mock_response.called_once()
		mock_tilt_check.called_once()
		mock_motor_stop_check.called_once()
		mock_select_mains.called_once()
		mock_tele_drive.called_once()
		mock_d100.not_called()

	@patch("plcd.get_D100_D102_status")
	def test_battery_in_use_response_error(self, mock_d100, mock_response,
		mock_tilt_check, mock_motor_stop_check, mock_select_mains,
		mock_tele_drive):

		mock_response.side_effect = ["@00RD00040A02580258020021*\r",
			"@00RD190009270F0000000024*\r"]
		mock_tilt_check.return_value = True, dict(
			{'Tilt_Angle':"6h West <= x < RA West limit", 'Tel_drive_control':
				"Normal - PC"})

		mock_motor_stop_check.return_value = False
		
		with self.assertRaises(plcd.PLC_ERROR):
			plcd.close_roof_instructions(self.port)

		self.assertEqual(mock_response.call_count,2)
		mock_tilt_check.called_once()
		mock_motor_stop_check.called_once()
		mock_select_mains.called_once()
		mock_tele_drive.called_once()
		mock_d100.not_called()

	@patch("plcd.get_D100_D102_status")
	def test_battery_in_use_after_request(self, mock_d100, mock_response,
		mock_tilt_check, mock_motor_stop_check, mock_select_mains,
		mock_tele_drive):

		mock_response.side_effect = ["@00RD00040A02580258020021*\r",
			"@00RD00040A02580258020021*\r"]
		mock_tilt_check.return_value = True, dict(
			{'Tilt_Angle':"6h West <= x < RA West limit", 'Tel_drive_control':
				"Normal - PC"})

		mock_motor_stop_check.return_value = False

		with self.assertRaises(plcd.PLC_ERROR):
			plcd.close_roof_instructions(self.port)

		self.assertEqual(mock_response.call_count,2)
		mock_tilt_check.called_once()
		mock_motor_stop_check.called_once()
		mock_select_mains.called_once()
		mock_tele_drive.called_once()
		mock_d100.not_called()

	"""
	TEST TO CHECK UPS STUFF: ----
	"""
	@patch("plcd.get_D100_D102_status")
	def test_motor_trip(self, mock_d100, mock_response, mock_tilt_check,
			mock_motor_stop_check, mock_select_mains, mock_tele_drive):
			
		mock_response.return_value = "@00RD00020A02580258020027*\r"
		mock_tilt_check.return_value = True, dict(
			{'Tilt_Angle':"6h West <= x < RA West limit", 'Tel_drive_control':
				"Normal - PC"})

		mock_motor_stop_check.return_value = False

		with self.assertRaises(plcd.PLC_ERROR):
			plcd.close_roof_instructions(self.port)

		mock_response.called_once()
		mock_tilt_check.called_once()
		mock_motor_stop_check.called_once()
		mock_select_mains.called_once()
		mock_tele_drive.called_once()
		mock_d100.not_called()
	
	
	def test_request_tel_control_give_error(self,mock_response, mock_tilt_check,
			mock_motor_stop_check, mock_select_mains, mock_tele_drive):
	
		mock_response.side_effect= ["@00RD00000A025802584A0052*\r",
			"@00RD000010232802580A0022*\r","@00WD0053*\r"]
		# plcd.PLC_ERROR]

		mock_tilt_check.return_value = True, dict(
			{'Tilt_Angle':"6h West <= x < RA West limit", 'Tel_drive_control':
				"Roof Controller"})

		mock_motor_stop_check.return_value = False
		mock_tele_drive.side_effect = [plcd.PLC_ERROR]


		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.close_roof_instructions(self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
			logging_actual_response3 = cm.output[2].split(':')[0]
			logging_actual_response4 = cm.output[3].split(':')[0]
			logging_actual_response5 = cm.output[4].split(':')[0]
			logging_actual_response6 = cm.output[5].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO')
		self.assertEqual(logging_actual_response2, 'INFO')
		self.assertEqual(logging_actual_response3, 'INFO')
		self.assertEqual(logging_actual_response4, 'INFO')
		self.assertEqual(logging_actual_response5, 'INFO')
		self.assertEqual(logging_actual_response6, 'ERROR')

		mock_response.called_once()
		mock_tilt_check.called_once()
		mock_motor_stop_check.called_once()
		mock_select_mains.called_once()
		mock_tele_drive.called_once()
	
	
	def test_passed_checks_set_to_close_tel_check_fail(self,mock_response,
			mock_tilt_check, mock_motor_stop_check, mock_select_mains,
			mock_tele_drive):

		mock_response.side_effect= ["@00RD00000A025802580A0056*\r",
			"@00RD000010232802580A0022*\r","@00WD0053*\r"]#, plcd.PLC_ERROR]

		mock_tilt_check.return_value = True, dict(
			{'Tilt_Angle':"6h West <= x < RA West limit", 'Tel_drive_control':
				"Roof Controller"})

		mock_motor_stop_check.return_value = False
		mock_tele_drive.side_effect = ['ok',plcd.PLC_ERROR]
		
		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.close_roof_instructions(self.port))
		
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
			logging_actual_response3 = cm.output[2].split(':')[0]
			logging_actual_response4 = cm.output[3].split(':')[0]
			logging_actual_response5 = cm.output[4].split(':')[0]
			logging_actual_response6 = cm.output[5].split(':')[0]
			logging_actual_response7 = cm.output[6].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO')
		self.assertEqual(logging_actual_response2, 'INFO')
		self.assertEqual(logging_actual_response3, 'INFO')
		self.assertEqual(logging_actual_response4, 'INFO')
		self.assertEqual(logging_actual_response5, 'INFO')
		self.assertEqual(logging_actual_response6, 'INFO')
		self.assertEqual(logging_actual_response7, 'ERROR')
		
		mock_response.called_once()
		mock_tilt_check.called_once()
		mock_motor_stop_check.called_once()
		mock_select_mains.called_once()
		mock_tele_drive.called_once(self.port)


	@patch("time.sleep")
	def test_passed_checks_set_to_close_moving(self,mock_sleep,mock_response,
			mock_tilt_check, mock_motor_stop_check, mock_select_mains,
			mock_tele_drive):

		mock_response.side_effect= ["@00RD00000A025802580A0056*\r",
			"@00RD000010232802580A0022*\r","@00WD0053*\r",
			"@00RD00000C025802580A0054*\r","@00RD00000C025802580A0054*\r",
			"@00RD00000C025802580A0054*\r", "@00RD00000C025802580A0054*\r",
			"@00RD000009025802580A002E*\r"]

		mock_tilt_check.return_value = True, dict(
			{'Tilt_Angle':"6h West <= x < RA West limit", 'Tel_drive_control':
				"Roof Controller"})

		mock_motor_stop_check.return_value = False

		mock_sleep = plcd.time.sleep(0.01)

		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.close_roof_instructions(self.port))
			all_mess = [i.split(':')[0] for i in cm.output]
			for i in all_mess[:-1]:
				self.assertEqual(i, 'INFO')

		mock_tilt_check.called_once()
		mock_motor_stop_check.called_once()
		mock_select_mains.called_once()


@patch("plcd.request_telescope_drive_control")
#@patch("plcd.select_mains")
@patch("plcd.motor_stop_check")
#@patch("plcd.telescope_tilt_check")
@patch("roof_control_functions.plc_command_response_port_open")
class test_open_roof(unittest.TestCase):

	def setUp(self):
		self.port = serial.Serial(baudrate = plcd.rcf.PLC_BAUD_RATE,
			parity=plcd.rcf.PLC_PARITY, stopbits = plcd.rcf.PLC_STOP_BITS,
			bytesize = plcd.rcf.PLC_CHARACTER_LENGTH,
			timeout = plcd.rcf.PLC_PORT_TIMEOUT)


	@patch("plcd.get_D100_D102_status")
	def test_error_getting_roof_status_error(self, mock_d100, mock_response,
		mock_motor_stop_check, mock_tele_drive):

		mock_response.return_value = "@00RD190009270F0000000024*\r"

		with self.assertRaises(plcd.PLC_ERROR):
			plcd.open_roof_instructions(self.port)
	
		mock_response.assert_called_once()
		mock_motor_stop_check.not_called()
		mock_tele_drive.not_called()
		mock_d100.not_called()

	@patch("plcd.get_D100_D102_status")
	def test_roof_all_ready_open(self, mock_d100, mock_response,
		mock_motor_stop_check, mock_tele_drive):

		mock_response.return_value = "@00RD00000A000100010A0056*\r"

		expected = 0
		actual = plcd.open_roof_instructions(self.port)
		self.assertEqual(expected,actual)

		mock_response.called_once()
		mock_motor_stop_check.not_called()
		mock_tele_drive.not_called()
		mock_d100.not_called()

	@patch("plcd.get_D100_D102_status")
	def test_raining(self, mock_d100, mock_response,
		mock_motor_stop_check, mock_tele_drive):

		mock_response.return_value = "@00RD000019000100010A002F*\r"


		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.open_roof_instructions(self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO')
		self.assertEqual(logging_actual_response2, 'ERROR')


		mock_response.called_once()
		mock_motor_stop_check.not_called()
		mock_tele_drive.not_called()
		mock_d100.not_called()


	@patch("plcd.get_D100_D102_status")
	def test_tilt_check_not_parked(self, mock_d100, mock_response,
		mock_motor_stop_check, mock_tele_drive):

		mock_response.return_value = "@00RD0000090001000102005D*\r"
		mock_motor_stop_check.return_value = False

		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.open_roof_instructions(self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO')
		self.assertEqual(logging_actual_response2, 'WARNING')

		mock_response.called_once()
		mock_motor_stop_check.not_called()
		mock_tele_drive.not_called()
		mock_d100.not_called()

	@patch("plcd.get_D100_D102_status")
	def test_check_power_fail(self, mock_d100, mock_response,
		mock_motor_stop_check, mock_tele_drive):

		mock_response.return_value = "@00RD001009000100010A002F*\r"
		mock_motor_stop_check.return_value = False

		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.open_roof_instructions(self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
			logging_actual_response3 = cm.output[2].split(':')[0]
			logging_actual_response4 = cm.output[3].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO')
		self.assertEqual(logging_actual_response2, 'INFO')
		self.assertEqual(logging_actual_response3, 'INFO')
		self.assertEqual(logging_actual_response4, 'ERROR')

		mock_response.called_once()
		mock_motor_stop_check.called_once()
		mock_tele_drive.not_called()
		mock_d100.not_called()


	@patch("time.sleep")
	def test_tel_drive_request_fail_still_open(self, mock_sleep, mock_response,
		mock_motor_stop_check, mock_tele_drive):

		mock_response.side_effect = ["@00RD000009000100014A002A*\r",
			"@00RD000010232802580A0022*\r","@00WD0053*\r",
			"@00RD00000C025802580A0054*\r","@00RD00000C025802580A0054*\r",
			"@00RD00000A025802580A0056*\r"]
		mock_tele_drive.side_effect = plcd.PLC_ERROR
		mock_motor_stop_check.return_value = False
		mock_sleep = plcd.time.sleep(0.01)

		with self.assertLogs(level='WARNING') as cm:
			plcd.logging.getLogger().error(plcd.open_roof_instructions(self.port))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
			logging_actual_response3 = cm.output[2].split(':')[0]
			logging_actual_response4 = cm.output[3].split(':')[0] #error
			logging_actual_response5 = cm.output[4].split(':')[0]
			logging_actual_response6 = cm.output[5].split(':')[0]
			logging_actual_response7 = cm.output[6].split(':')[0]
			logging_actual_response8 = cm.output[7].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO')
		self.assertEqual(logging_actual_response2, 'INFO')
		self.assertEqual(logging_actual_response3, 'INFO')
		self.assertEqual(logging_actual_response4, 'ERROR')
		self.assertEqual(logging_actual_response5, 'INFO')
		self.assertEqual(logging_actual_response6, 'INFO')
		self.assertEqual(logging_actual_response7, 'INFO')
		self.assertEqual(logging_actual_response8, 'INFO')

		mock_response.called_once()
		mock_motor_stop_check.called_once()
		mock_tele_drive.called_once()


