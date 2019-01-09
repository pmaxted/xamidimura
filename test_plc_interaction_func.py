"""
test_plc_interaction_func.py
Jessica A. Evans
03/01/2019

Contains unit tests for the PLC_interaction_functions script.
	
	Currently tests:
		
		- class PLC_ERROR
		- def split_up_response

"""

import unittest
from unittest.mock import patch
import PLC_interaction_functions as plc
import settings_and_error_codes as set_err_codes
import dummy_serial

class test_PLC_ERROR_class(unittest.TestCase):

	def test_creates_execption(self):
		#check returns message
		
		expected_message = 'Test message'
		
		err = plc.PLC_ERROR(expected_message)
		actual_message = err.message
		self.assertEqual(expected_message,actual_message)

@patch("roof_control_functions.plc_command_response")
class test_get_D100_D102_status(unittest.TestCase):
	
	#Don't need to test this function works correctly, that is done in all other tests
	
	def test_error_getting_roof_status_error(self, mock_plc_response):
		returned_commands = ["@00RD148006000100015D*\r"]

		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.get_D100_D102_status()

		mock_plc_response.assert_called_once()


class test_split_up_response(unittest.TestCase):

	#Don't need to test this function works correctly, that is done in all other tests

	def test_invalid_response_error(self):
		response = "00RD0080060001000100005D*\r"

		with self.assertRaises(plc.PLC_ERROR):
			plc.split_up_response(response)


	def test_invalid_fcs(self):
		response = "@00RD0080060001000100005E*\r"

		with self.assertRaises(plc.PLC_ERROR):
			plc.split_up_response(response)

@patch("roof_control_functions.plc_command_response")
class test_create_and_send_new_command(unittest.TestCase):

	#Don't need to test this function works correctly, that is done in all other tests
	
	def test_command_fail_error(self, mock_plc_response):
		# Not sure if this is a valid incorrect command, it's just something that I know will fail
		returned_commands = ["@00WD0152*\r"]
		# 3rd response - Command accepted is "@00WD0053*\r", change to "@00WD0152*\r" for not accepted
		mock_plc_response.side_effect = returned_commands


		with self.assertRaises(plc.PLC_ERROR):
			plc.create_and_send_new_command('B002','0001','0001')

		mock_plc_response.called_once()


@patch("roof_control_functions.plc_command_response")
class test_plc_close_roof(unittest.TestCase):

	def test_complete_close(self, mock_plc_response):
		returned_commands = ["@00RD00000A270F0000000054*\r","@00RD0080060001000158*\r","@00WD0053*\r"]
		# 1st response - D150 roof status (0000000000001010) open closed, Remote control
		# 2nd response - D100 command stat (1000000000000110) open closed, mains power, watchdog
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands
		
		expected = 0
		actual = plc.plc_close_roof()
	
		self.assertEqual(mock_plc_response.call_count,3)
		self.assertEqual(expected,actual)
	
	
	def test_not_remote_control(self, mock_plc_response):
		returned_commands = ["@00RD000002270F000027*\r"]
		# 1st response - D150 roof status (0000000000000010) open closed
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_close_roof()

		mock_plc_response.called_once_with(plc.rcf.PLC_Request_Roof_Status)
	
	def test_motor_stop_pressed(self, mock_plc_response):
		returned_commands = ["@00RD00010A270F000055*\r"]
		# 1st response - D150 roof status (00000010000001001) Roof closed, Remote control, motor stop pressed
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_close_roof()

		mock_plc_response.called_once_with(plc.rcf.PLC_Request_Roof_Status)
		
	def test_AC_motor_power_fail(self, mock_plc_response):
		returned_commands = ["@00RD00100A270F000055*\r"]
		# 1st response - D150 roof status (0000000000001001) Roof closed, Remote control, motor stop pressed
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_close_roof()

		mock_plc_response.called_once_with(plc.rcf.PLC_Request_Roof_Status)
	
	def test_AC_motor_tripped(self, mock_plc_response):
		returned_commands = ["@00RD00020A270F000056*\r"]
		# 1st response - D150 roof status (0000001000001010) Roof closed, Remote control, motor stop pressed
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_close_roof()

		mock_plc_response.called_once_with(plc.rcf.PLC_Request_Roof_Status)


	def test_error_getting_roof_status(self, mock_plc_response):
		returned_commands = ["@00RD190009270F0000000024*\r"]
		# 1st response - D150 roof status (0000000000001001) Roof closed, Remote control
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_close_roof()

		mock_plc_response.assert_called_once()
	

@patch("roof_control_functions.plc_command_response")
class test_plc_get_plc_status(unittest.TestCase):

	def test_get_dict_no_messages(self, mock_plc_response):
		returned_commands = ["@00MS0000A827*\r"]
		mock_plc_response.side_effect = returned_commands

		expected_dict = dict({'PLC_Response_Code':returned_commands[0],
								'PLC_Status': set_err_codes.PLC_STATUS_STATUS['0'],
								'PLC_Operating_Mode':set_err_codes.PLC_STATUS_MODE['0']})
		
		actual_dict = plc.plc_get_plc_status(log_messages=False)
			
		self.assertEqual(expected_dict,actual_dict)
		mock_plc_response.assert_called_once()

	def test_log_dict_values(self, mock_plc_response):
		returned_commands = ["@00MS0000A827*\r"]
		mock_plc_response.side_effect = returned_commands

		with self.assertLogs(level='INFO') as cm:
			plc.logging.getLogger().info(plc.plc_get_plc_status(log_messages = True))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'INFO')


@patch("roof_control_functions.plc_command_response")
class test_plc_get_rain_status(unittest.TestCase):

	def test_error_getting_rain_status(self, mock_plc_response):
		returned_commands = ["@00RD190009270F0000000024*\r"]
		# 1st response - D150 roof status (0000000000001001) Roof closed, Remote control
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_get_rain_status()

		mock_plc_response.assert_called_once()


	def test_check_rain(self,mock_plc_response):
	
		# 1st response - D150 roof status (1111111111111001) Roof closed, Remote control
		returned_commands = ["@00RD0080100001000100005F*\r"]
		mock_plc_response.side_effect = returned_commands

		expected_dict = dict({'Rain_status': 'Check Rain',
								'PC_Communication_Timeout':1,
								'Power_Failure_Timeout':1})

		actual_dict = plc.plc_get_rain_status(log_messages=False)
		
		self.assertEqual(expected_dict,actual_dict)
		mock_plc_response.assert_called_once()

	def test_ignore_rain(self,mock_plc_response):
	
		# 1st response - D150 roof status (1111111111111001) Roof closed, Remote control
		returned_commands = ["@00RD0080000001000100005E*\r"]
		mock_plc_response.side_effect = returned_commands

		expected_dict = dict({'Rain_status': 'Ignore Rain',
								'PC_Communication_Timeout':1,
								'Power_Failure_Timeout':1})

		actual_dict = plc.plc_get_rain_status(log_messages=False)
		
		self.assertEqual(expected_dict,actual_dict)
		mock_plc_response.assert_called_once()

	def test_log_messages(self,mock_plc_response):
	
		# 1st response - D150 roof status (1111111111111001) Roof closed, Remote control
		returned_commands = ["@00RD0080000001000100005E*\r"]
		mock_plc_response.side_effect = returned_commands
	
		with self.assertLogs(level='INFO') as cm:
			plc.logging.getLogger().info(plc.plc_get_rain_status(log_messages = True))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'INFO')

@patch("roof_control_functions.plc_command_response")
class test_plc_get_roof_status(unittest.TestCase):

	def test_error_getting_roof_status(self, mock_plc_response):
		returned_commands = ["@00RD190009270F0000000024*\r"]
		# 1st response - D150 roof status (0000000000001001) Roof closed, Remote control
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_get_roof_status()

		mock_plc_response.assert_called_once()

	def test_all_set_but_close_moving(self,mock_plc_response):
	
		# 1st response - D150 roof status (1111111111111001) Roof closed, Remote control
		returned_commands = ["@00RD00FFF900010001000029*\r"]
		mock_plc_response.side_effect = returned_commands

		expected_dict = dict({'Roof_Closed':True,
							'Roof_Open':False,
							'Roof_Moving': False,
							'Roof_Control': 'Remote',
							'Roof_Raining': True,
							'Roof_Forced_Close': True,
							'High_Building_Temp': True,
							'Extractor_Fan': 'On',
							'Roof_Motor_Stop': 'Pressed',
							'Roof_AC_Motor_Tripped': True,
							'Roof_Motor_Being_Used': 'DC',
							'Roof_Close_Proximity': True,
							'Roof_Power_Failure': True,
							'Roof_Forced_Power_Closure': True,
							'Roof_Open_Proximity':True,
							'Roof_Door_Open': True,
							'PC_Communication_Timeout':1,
							'Power_Failure_Timeout':1})

		actual_dict = plc.plc_get_roof_status(log_messages = False)
		self.assertEqual(expected_dict,actual_dict)
		mock_plc_response.assert_called_once()
	
	def test_all_unset_but_open_moving(self,mock_plc_response):
	
		# 1st response - D150 roof status (0000000000000110) Roof closed, Remote control
		returned_commands = ["@00RD00000600010001000050*\r"]
		mock_plc_response.side_effect = returned_commands

		expected_dict = dict({'Roof_Closed':False,
							'Roof_Open':True,
							'Roof_Moving': True,
							'Roof_Control': 'Manual',
							'Roof_Raining': False,
							'Roof_Forced_Close': False,
							'High_Building_Temp': False,
							'Extractor_Fan': 'Off',
							'Roof_Motor_Stop': 'Not Pressed',
							'Roof_AC_Motor_Tripped': False,
							'Roof_Motor_Being_Used': 'AC',
							'Roof_Close_Proximity': False,
							'Roof_Power_Failure': False,
							'Roof_Forced_Power_Closure': False,
							'Roof_Open_Proximity': False,
							'Roof_Door_Open': False,
							'PC_Communication_Timeout':1,
							'Power_Failure_Timeout':1})

		actual_dict = plc.plc_get_roof_status(log_messages = False)
		self.assertEqual(expected_dict,actual_dict)
		mock_plc_response.assert_called_once()
	
	def test_log_status(self,mock_plc_response):
		returned_commands = ["@00RD00FFF900010001000029*\r"]
		mock_plc_response.side_effect = returned_commands
	
		with self.assertLogs(level='INFO') as cm:
			plc.logging.getLogger().info(plc.plc_get_roof_status(log_messages = True))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'INFO')


@patch("roof_control_functions.plc_command_response")
class test_get_telescope_tilt_status(unittest.TestCase):

	def test_drive_set_west_limit(self,mock_response):
		mock_response.return_value = "@00RD00B0050000270F6A0025*\r"

		expected_dict = dict({'Response Code':"@00RD00B0050000270F6A0025*\r",'Tel_drive_control':1,'Tilt_angle':"RA West limit"})

		actual_dict = plc.plc_get_telescope_tilt_status()
		self.assertEqual(expected_dict, actual_dict)
	
		mock_response.assert_called_once()

	def test_1hr_west_no_drive(self, mock_response):
		mock_response.return_value = "@00RD00B0050000270F020050*\r"

		expected_dict = dict({'Response Code':"@00RD00B0050000270F020050*\r",'Tel_drive_control':0,'Tilt_angle':"1h West <= x < 6h West"})

		actual_dict = plc.plc_get_telescope_tilt_status()
		self.assertEqual(expected_dict, actual_dict)

	def test_invalid_tilt_bit_combo(self, mock_response):
		mock_response.return_value = "@00RD00B0050000270F020151*\r"

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_get_telescope_tilt_status()

		mock_response.assert_called_once()

	def test_error_getting_roof_status(self, mock_plc_response):
		returned_commands = ["@00RD190009270F0000000024*\r"]
		# 1st response - D150 roof status (0000000000001001) Roof closed, Remote control
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_get_telescope_tilt_status()

		mock_plc_response.assert_called_once()


# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response")
class test_plc_open_roof(unittest.TestCase):

	def test_complete_open(self, mock_plc_response):
		returned_commands = ["@00RD000009270F00002C*\r","@00RD008005000100015B*\r","@00WD0053*\r"]
		# 1st response - D150 roof status (0000000000001001) Roof closed, Remote control
		# 2nd response - D100 command stat (1000000000000101) Roof closed, mains power, watchdog
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands
		
		expected = 0
		actual = plc.plc_open_roof()
	
		self.assertEqual(mock_plc_response.call_count,3)
		self.assertEqual(expected,actual)
	

	def test_not_remote_control(self, mock_plc_response):
		returned_commands = ["@00RD000001270F000024*\r","@00RD008005000100015B*\r","@00WD0053*\r"]
		# 1st response - D150 roof status (0000000000001001) Roof closed, Remote control
		# 2nd response - D100 command stat (1000000000000101) Roof closed, mains power, watchdog
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_open_roof()

		mock_plc_response.called_once_with(plc.rcf.PLC_Request_Roof_Status)
		
	def test_motor_stop_pressed(self, mock_plc_response):
		returned_commands = ["@00RD000109270F00002D*\r"]
		# 1st response - D150 roof status (0000000000001001) Roof closed, Remote control, motor stop pressed
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_open_roof()

		mock_plc_response.called_once_with(plc.rcf.PLC_Request_Roof_Status)

	def test_raining(self, mock_plc_response):
		returned_commands = ["@00RD000019270F00002D*\r"]
		# 1st response - D150 roof status (0001000000001001) Roof closed, Remote control, raining
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_open_roof()

		mock_plc_response.called_once_with(plc.rcf.PLC_Request_Roof_Status)

	def test_power_failure(self, mock_plc_response):
		returned_commands = ["@00RD001009270F00002D*\r"]
		# 1st response - D150 roof status (0000000000001001) Roof closed, Remote control,power failure
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_open_roof()

		mock_plc_response.called_once_with(plc.rcf.PLC_Request_Roof_Status)

	def test_error_getting_roof_status(self, mock_plc_response):
		returned_commands = ["@00RD190009270F0000000024*\r"]
		# 1st response - D150 roof status (0000000000001001) Roof closed, Remote control
		mock_plc_response.side_effect = returned_commands

		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_open_roof()

		mock_plc_response.assert_called_once()

# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response")
class test_request_roof_control(unittest.TestCase):

	def test_complete_request(self, mock_plc_response):
		returned_commands = ["@00RD008005000100015B*\r","@00WD0053*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000000000101) Roof closed, mains, watch dog
		# 2nd response - command accepted
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands
		
		expected = 0
		actual = plc.plc_request_roof_control()
	
		self.assertEqual(mock_plc_response.call_count,3)
		self.assertEqual(expected,actual)
		#mock_plc_response

	def test_request_with_bit_set(self, mock_plc_response):
		returned_commands = ["@00RD008105000100015A*\r","@00WD0053*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000100000101) Roof closed, mains, watch dog, request already set
		# 2nd response - command accepted
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands
		
		expected = 0
		actual = plc.plc_request_roof_control()
	
		self.assertEqual(mock_plc_response.call_count,3)
		self.assertEqual(expected,actual)



# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response")
class test_request_telescope_drive_control(unittest.TestCase):

	def test_complete_request(self, mock_plc_response):
		returned_commands = ["@00RD0080060001000158*\r","@00WD0053*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1100000000000110) Roof closed, mains, watch dog
		# 2nd response - command accepted
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands
		
		expected = 0
		actual = plc.plc_request_telescope_drive_control()
	
		self.assertEqual(mock_plc_response.call_count,3)
		self.assertEqual(expected,actual)
		#mock_plc_response

	def test_request_with_bit_set(self, mock_plc_response):
		returned_commands = ["@00RD00C0060001000123*\r","@00WD0053*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000100000101) Roof closed, mains, watch dog, request already set
		# 2nd response - command accepted
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands
		
		expected = 0
		actual = plc.plc_request_telescope_drive_control()
	
		self.assertEqual(mock_plc_response.call_count,3)
		self.assertEqual(expected,actual)



# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response")
class test_reset_watchdog(unittest.TestCase):


	def test_complete_reset(self, mock_plc_response):
		returned_commands = ["@00RD008005000100015B*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000100000101) Roof closed, mains, watch dog, request already set
		# 2nd response - command accepted
		mock_plc_response.side_effect = returned_commands

		expected = 0
		actual = plc.plc_reset_watchdog()
	
		self.assertEqual(mock_plc_response.call_count,2)
		self.assertEqual(expected,actual)



# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response")
class test_select_battery(unittest.TestCase):


	def test_complete_battery_request(self, mock_plc_response):
		returned_commands = ["@00RD008005000100015B*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000000000101) Roof closed, mains, watch dog
		# 2nd response - command accepted
		mock_plc_response.side_effect = returned_commands

		expected = 0
		actual = plc.plc_select_battery()
	
		self.assertEqual(mock_plc_response.call_count,2)
		self.assertEqual(expected,actual)



# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response")
class test_select_mains(unittest.TestCase):

	def test_complete_mains_request(self, mock_plc_response):
		returned_commands = ["@00RD008001000100015F*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000000000001) Roof closed, battery, watch dog
		# 2nd response - command accepted
		mock_plc_response.side_effect = returned_commands

		expected = 0
		actual = plc.plc_select_mains()
	
		self.assertEqual(mock_plc_response.call_count,2)
		self.assertEqual(expected,actual)


# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response")
class test_set_comms_timeout(unittest.TestCase):

	def test_complete_comms_request(self, mock_plc_response):
		returned_commands = ["@00RD008005000100015B*\r","@00WD0053*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1010000000000101) Roof closed, mains, watch dog, set comms
		# 2nd response - command accepted
		mock_plc_response.side_effect = returned_commands

		expected = 0
		actual = plc.plc_set_comms_timeout()
	
		self.assertEqual(mock_plc_response.call_count,3)
		self.assertEqual(expected,actual)

	def test_too_high_timeout(self,mock_plc_response):
		with self.assertRaises(ValueError):
			plc.plc_set_comms_timeout(10000)

		mock_plc_response.assert_not_called()

	def test_too_low_timeout(self,mock_plc_response):
		with self.assertRaises(ValueError):
			plc.plc_set_comms_timeout(-1)

		mock_plc_response.assert_not_called()

	def test_not_int(self,mock_plc_response):
		with self.assertRaises(ValueError):
			plc.plc_set_comms_timeout('sfdff')
		
		with self.assertRaises(ValueError):
			plc.plc_set_comms_timeout(4.234)

		mock_plc_response.assert_not_called()

# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response")
class test_set_power_timeout(unittest.TestCase):

	def test_complete_power_request(self, mock_plc_response):
		returned_commands = ["@00RD008005000100015B*\r","@00WD0053*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1010000000000101) Roof closed, mains, watch dog, power set
		# 2nd response - command accepted
		# 3rd response - Command accepted
		mock_plc_response.side_effect = returned_commands

		expected = 0
		actual = plc.plc_set_power_timeout()
	
		self.assertEqual(mock_plc_response.call_count,3)
		self.assertEqual(expected,actual)

	def test_too_high_timeout(self,mock_plc_response):
		with self.assertRaises(ValueError):
			plc.plc_set_power_timeout(10000)

		mock_plc_response.assert_not_called()

	def test_too_low_timeout(self,mock_plc_response):
		with self.assertRaises(ValueError):
			plc.plc_set_power_timeout(-1)

		mock_plc_response.assert_not_called()

	def test_not_int(self,mock_plc_response):
		with self.assertRaises(ValueError):
			plc.plc_set_power_timeout('sfdff')
		
		with self.assertRaises(ValueError):
			plc.plc_set_power_timeout(4.234)

		mock_plc_response.assert_not_called()

# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response")
class test_stop_roof(unittest.TestCase):

	def test_complete_stop_request(self, mock_plc_response):
		returned_commands = ["@00RD008005000100015B*\r","@00WD0053*\r"]
		# 1st response - D100 command status (1000000000000101) Roof closed, mains, watch dog
		# 2nd response - command accepted
		mock_plc_response.side_effect = returned_commands

		expected = 0
		actual = plc.plc_stop_roof()
	
		self.assertEqual(mock_plc_response.call_count,2)
		self.assertEqual(expected,actual)


# Mock this function as this is what actually send/receives commands from PLC box
@patch("roof_control_functions.plc_command_response")
class test_plc_is_roof_open(unittest.TestCase):

	def test_yes_is_open(self, mock_plc_response):
		
		# 1st response - D150 roof status (0000000000000110) Roof open, Remote control
		mock_plc_response.return_value = "@00RD00000A270F0000000054*\r"

		expected = True
		actual = plc.plc_is_roof_open()

		self.assertEqual(expected,actual)
		mock_plc_response.assert_called_once()

	def test_get_end_code(self, mock_plc_response):
		
		# 1st response - D150 roof status (0000000000000110) Roof open, Remote control
		mock_plc_response.return_value = "@00RD23000A270F0000000055*\r"


		with self.assertRaises(plc.PLC_ERROR):
			plc.plc_is_roof_open()
		mock_plc_response.assert_called_once()

if __name__ =='__main__':
	unittest.main()