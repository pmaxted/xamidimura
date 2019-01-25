"""
test_observing.py


Contains the unit tests for 'observing.py' script

"""

import unittest
from unittest.mock import patch
import settings_and_error_codes as set_err_codes
import observing

@patch("tcs_control.tcs_exposure_request")
class test_exposure_TCS_response(unittest.TestCase):

	def test_ok_exposure_request(self, mock_exposure_request):

		northEXP = observing.exposure_obj(0.02,'RX','OBJECT',2,'ifw-north',22)
		southEXP = observing.exposure_obj(0.02,'GX','OBJECT',1,'ifw-south',22)

		mock_exposure_request.return_value = set_err_codes.STATUS_CODE_OK

		expectedN, expectedS = set_err_codes.STATUS_CODE_OK, set_err_codes.STATUS_CODE_OK
		actualN, actualS = observing.exposure_TCS_response(northEXP,southEXP)
		self.assertEqual(expectedN,actualN)
		self.assertEqual(expectedS,actualS)

@patch("time.sleep")
class test_exposureTCSerrorcode(unittest.TestCase):

	def test_ok_status(self, mock_sleep):

		expectedN, expectedS = set_err_codes.STATUS_CODE_OK, set_err_codes.STATUS_CODE_OK

		actualN, actualS = observing.exposureTCSerrorcode(0,0,0.002)
		self.assertEqual(expectedN,actualN)
		self.assertEqual(expectedS,actualS)
	
		mock_sleep.assert_called_once_with(0.002)

	def test_warm_ccd_warning(self, mock_sleep):

		expectedN, expectedS = set_err_codes.STATUS_CODE_CCD_WARM, set_err_codes.STATUS_CODE_CCD_WARM

		actualN, actualS = observing.exposureTCSerrorcode(1,1,0.002)
		self.assertEqual(expectedN,actualN)
		self.assertEqual(expectedS,actualS)

		mock_sleep.assert_called_once_with(0.002)


		with self.assertLogs(level='WARNING') as cm:
			observing.logging.getLogger().info(observing.exposureTCSerrorcode(1,1,0.002))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'WARNING') #mentions same coords
		self.assertEqual(logging_actual_response2, 'WARNING')
		
		
	def test_received_not_started(self,mock_sleep):

		expectedN, expectedS = set_err_codes.STATUS_CODE_EXPOSURE_NOT_STARTED, set_err_codes.STATUS_CODE_EXPOSURE_NOT_STARTED

		actualN, actualS = observing.exposureTCSerrorcode(set_err_codes.STATUS_CODE_EXPOSURE_NOT_STARTED,set_err_codes.STATUS_CODE_EXPOSURE_NOT_STARTED,0.001)
		
		mock_sleep.assert_not_called()
		
		with self.assertLogs(level='ERROR') as cm:
			observing.logging.getLogger().info(observing.exposureTCSerrorcode(-3,-3,0.002))
			logging_actual_response1 = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response1, 'ERROR')

	def test_unexpected_response(self,mock_sleep):

		expectedN, expectedS = set_err_codes.STATUS_CODE_UNEXPECTED_RESPONSE, set_err_codes.STATUS_CODE_UNEXPECTED_RESPONSE

		actualN, actualS = observing.exposureTCSerrorcode(34,23,0.001)
		
		with self.assertLogs(level='ERROR') as cm:
			observing.logging.getLogger().info(observing.exposureTCSerrorcode(34,23,0.002))
			logging_actual_response1 = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response1, 'ERROR')

		mock_sleep.assert_not_called()

@patch("time.sleep")
class test_wait_for_roof_to_stop_moving(unittest.TestCase):

	def test_invalid_dict_no_roof_moving(self, mock_sleep):
		
		bad_status_dict = dict({'Roof_Control': 'Remote',
							'Roof_Motor_Stop': 'Not Pressed',
							'Roof_Power_Failure': False })

		with self.assertRaises(KeyError):
			observing.wait_for_roof_to_stop_moving(bad_status_dict)

		mock_sleep.assert_not_called()


	def test_roof_moving_false(self, mock_sleep):
		status_dict = dict({'Roof_Moving':False,
							'Roof_Control': 'Remote',
							'Roof_Motor_Stop': 'Not Pressed',
							'Roof_Power_Failure': False })

		with self.assertLogs(level='WARNING') as cm:
			observing.logging.getLogger().warning(observing.wait_for_roof_to_stop_moving(status_dict))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'WARNING')
		
		mock_sleep.assert_not_called()

	@patch("PLC_interaction_functions.plc_get_roof_status")
	def test_movement_timeout(self, mock_plc_roof_dict, mock_sleep):

		input_dict = dict({'Roof_Closed': False, 'Roof_Open': False, 'Roof_Moving': True})
		mock_plc_roof_dict.return_value = dict({'Roof_Closed': False, 'Roof_Open': False, 'Roof_Moving': True})

		with self.assertRaises(TimeoutError):
			observing.wait_for_roof_to_stop_moving(input_dict,0.2)

		mock_sleep.assert_called()

	@patch("PLC_interaction_functions.plc_get_roof_status")
	def test_roof_moves_closed(self, mock_plc_dict, mock_sleep):

		#print('The "test_roof_moves_closed" test checks a timeout function')

		input_dict = dict({'Roof_Closed': False, 'Roof_Open': False, 'Roof_Moving': True})
		mock_plc_dict.return_value = dict({'Roof_Closed': True, 'Roof_Open': False, 'Roof_Moving': False})

		expected_roof_open = False
		expected_dict = mock_plc_dict.return_value

		actual_roof_open, actual_roof_dict = observing.wait_for_roof_to_stop_moving(input_dict,1.2)

		self.assertEqual(actual_roof_dict,expected_dict)
		self.assertEqual(expected_roof_open, actual_roof_open)

		mock_plc_dict.assert_called_once()
		mock_sleep.assert_called()

	@patch("PLC_interaction_functions.plc_get_roof_status")
	def test_roof_moves_open(self, mock_plc_dict, mock_sleep):
		
		#print('The "test_roof_moves_open" test checks a timeout function')

		input_dict = dict({'Roof_Closed': False, 'Roof_Open': False, 'Roof_Moving': True})
		mock_plc_dict.return_value = dict({'Roof_Closed': False, 'Roof_Open': True, 'Roof_Moving': False})

		expected_roof_open = True
		expected_dict = mock_plc_dict.return_value

		actual_roof_open, actual_roof_dict = observing.wait_for_roof_to_stop_moving(input_dict,1.2)

		self.assertEqual(actual_roof_dict,expected_dict)
		self.assertEqual(expected_roof_open, actual_roof_open)

		mock_plc_dict.assert_called_once()
		mock_sleep.assert_called()

	@patch("PLC_interaction_functions.plc_get_roof_status")
	def test_roof_set_open_and_closed(self, mock_plc_dict,mock_sleep):

		input_dict = dict({'Roof_Closed': False, 'Roof_Open': False, 'Roof_Moving': True})
		mock_plc_dict.return_value = dict({'Roof_Closed': True, 'Roof_Open': True, 'Roof_Moving': False})

		with self.assertRaises(RuntimeError):
			observing.wait_for_roof_to_stop_moving(input_dict,1.2)

		mock_sleep.assert_called_once_with(1)

class test_check_control_motor_stop_and_power_safety(unittest.TestCase):

	def setUp(self):
	
		self.status_dict = dict({'Roof_Control': 'Remote',
							'Roof_Motor_Stop': 'Not Pressed',
							'Roof_Power_Failure': False })

	def test_invalid_dictionary_check_no_roof_control(self):
		
		bad_status_dict = dict({'Roof_Motor_Stop': 'Not Pressed',
							'Roof_Power_Failure': False})
		
		with self.assertRaises(KeyError):
			observing.check_control_motor_stop_and_power_safety(bad_status_dict)

	def test_invalid_dictionary_check_no_motor_stop(self):
		
		bad_status_dict = dict({'Roof_Control': 'Remote',
							'Roof_Power_Failure': False})
		
		with self.assertRaises(KeyError):
			observing.check_control_motor_stop_and_power_safety(bad_status_dict)

	def test_invalid_dictionary_check_no_power_failure(self):
		
		bad_status_dict = dict({'Roof_Control': 'Remote',
								'Roof_Motor_Stop': 'Not Pressed'})
		
		with self.assertRaises(KeyError):
			observing.check_control_motor_stop_and_power_safety(bad_status_dict)

	def test_checks_set_ok(self):

		expected_safe_to_open = True
		expected_dict = self.status_dict

		actual_safe_to_open, actual_roof_dict = observing.check_control_motor_stop_and_power_safety(self.status_dict)

		self.assertEqual(expected_safe_to_open,actual_safe_to_open)
		self.assertEqual(expected_dict,actual_roof_dict)

	def test_manual_control_motor_stop_not_ok(self):

		input_dict =  dict({'Roof_Control': 'Manual',
							'Roof_Motor_Stop': 'Pressed',
							'Roof_Power_Failure': False })

		with self.assertLogs(level='ERROR') as cm:
			observing.logging.getLogger().error(observing.check_control_motor_stop_and_power_safety(input_dict))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'ERROR')

	def test_manual_control_power_failure_not_ok(self):

		input_dict =  dict({'Roof_Control': 'Manual',
							'Roof_Motor_Stop': 'Not Pressed',
							'Roof_Power_Failure': True })

		expected_safe_to_open = False
		actual_safe_to_open, actual_roof_dict =observing.check_control_motor_stop_and_power_safety(input_dict)
		self.assertEqual(expected_safe_to_open,actual_safe_to_open)
		self.assertEqual(input_dict,actual_roof_dict)

		with self.assertLogs(level='ERROR') as cm:
			observing.logging.getLogger().error(observing.check_control_motor_stop_and_power_safety(input_dict))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'ERROR')

	@patch("PLC_interaction_functions.plc_request_roof_control")
	def test_change_control_fail_roof_request(self, mock_plc_response):
	
		mock_plc_response.side_effect = observing.plc.PLC_ERROR
	
		input_dict =  dict({'Roof_Control': 'Manual',
							'Roof_Motor_Stop': 'Not Pressed',
							'Roof_Power_Failure': False })
	
		expected_safe_to_open = False
		actual_safe_to_open, actual_roof_dict =observing.check_control_motor_stop_and_power_safety(input_dict)
		self.assertEqual(expected_safe_to_open,actual_safe_to_open)
		self.assertEqual(input_dict,actual_roof_dict)

	@patch("PLC_interaction_functions.plc_get_roof_status")
	@patch("PLC_interaction_functions.plc_request_roof_control")
	def test_change_control_success(self, mock_request_control, mock_plc_dict):

		mock_request_control.return_value = 0
		mock_plc_dict.return_value = self.status_dict
	
		input_dict =  dict({'Roof_Control': 'Manual',
							'Roof_Motor_Stop': 'Not Pressed',
							'Roof_Power_Failure': False })
	
		expected_safe_to_open = True
		actual_safe_to_open, actual_roof_dict =observing.check_control_motor_stop_and_power_safety(input_dict)
		self.assertEqual(expected_safe_to_open,actual_safe_to_open)
		self.assertEqual(self.status_dict,actual_roof_dict)


class test_its_raining_instructions(unittest.TestCase):

	def test_log_critical_message(self):

		with self.assertLogs(level='CRITICAL') as cm:
			observing.logging.getLogger().critical(observing.its_raining_instructions())
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'CRITICAL')

@patch("observing.check_control_motor_stop_and_power_safety")
@patch("observing.wait_for_roof_to_stop_moving")
@patch("observing.its_raining_instructions")
class test_check_safe_to_open_roof(unittest.TestCase):

	def test_raining_check(self, mock_raining_func, mock_waiting_func, mock_check_func):
	
		test_dict = dict({'Roof_Raining':True})
		observing.check_safe_to_open_roof(test_dict)

		mock_raining_func.called_once()
		mock_waiting_func.not_called()
		mock_check_func.not_called()

	def test_roof_moving(self, mock_raining_func, mock_waiting_func, mock_check_func):

		test_dict = dict({'Roof_Raining':False,'Roof_Moving':True})
		
		mock_waiting_func.return_value = True, test_dict
		
		expected_roof_open,expected_safe_to_open,expected_dict = True, False, test_dict
		
		
		actual_roof_open, actual_safe_to_open, actual_roof_dict = observing.check_safe_to_open_roof(test_dict)
		
		self.assertEqual(expected_roof_open, actual_roof_open)
		self.assertEqual(expected_safe_to_open, actual_safe_to_open)
		self.assertEqual(expected_dict, actual_roof_dict)
		mock_raining_func.not_called()
		mock_waiting_func.called_once_with(test_dict)
		mock_check_func.not_called()


	def test_check_safe_to_open(self,mock_raining_func, mock_waiting_func, mock_check_func):
		test_dict = dict({'Roof_Raining':False,'Roof_Moving':False})
		
		mock_check_func.return_value = True, test_dict

		expected_roof_open, expected_safe_to_open,expected_dict = False, True, test_dict

		actual_roof_open, actual_safe_to_open, actual_roof_dict = observing.check_safe_to_open_roof(test_dict)

		self.assertEqual(expected_roof_open, actual_roof_open)
		self.assertEqual(expected_safe_to_open, actual_safe_to_open)
		self.assertEqual(expected_dict, actual_roof_dict)
		mock_raining_func.not_called()
		mock_waiting_func.not_called()
		mock_check_func.called_once_with(test_dict)



@patch("PLC_interaction_functions.plc_get_roof_status")
@patch("tcs_control.get_tel_target") #01 09 34.19 -46 15 56.1
class test_go_to_target(unittest.TestCase):

	def setUp(self):
	
		self.test_returned_coords =['21 27 38.2', '-45 54 31', '+41 07 02.2', '+55 50 55', '234 41 45']

	def test_valid_coords_false(self, mock_tel_target, mock_roof_status):

		test_coords = ['df af ag','fdda sfd fa']
		mock_tel_target.return_value = ['21 27 38.2', '-45 54 31', '+41 07 02.2', '+55 50 55', '234 41 45']
		mock_roof_status.return_value = dict({'Roof_Open': True})

		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'ERROR') # from wrong coords
		self.assertEqual(logging_actual_response2, 'INFO') #final message

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()

	def test_same_coords_need_to_change_false(self,mock_tel_target, mock_roof_status):
	
		test_coords = ['21 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		
		mock_roof_status.return_value = dict({'Roof_Open': True})
		
		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO') #mentions same coords
		self.assertEqual(logging_actual_response2, 'INFO') #final message

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()


	def test_unable_to_get_roof_status(self, mock_tel_target,mock_roof_status):

		test_coords = ['21 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords

		mock_roof_status.side_effect = observing.plc.PLC_ERROR

		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO') #mentions same coords
		self.assertEqual(logging_actual_response2, 'CRITICAL') #final message

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()

	@patch("observing.check_safe_to_open_roof")
	def test_got_status_roof_closed_safe_to_open_and_open(self,mock_check_open_safety,mock_tel_target,mock_roof_status):

		test_coords = ['21 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_status.return_value = dict({'Roof_Open': False})
		mock_check_open_safety.return_value = True, True, dict({'Roof_Open': True})
		
		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			#logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO') #mentions same coords
		#self.assertEqual(logging_actual_response2, 'CRITICAL') #final message

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()
		mock_check_open_safety.assert_called_once()


	@patch("PLC_interaction_functions.plc_open_roof")
	@patch("observing.check_safe_to_open_roof")
	def test_got_status_roof_closed_safe_to_open_cant_open(self,mock_check_open_safety,mock_plc_roof_function, mock_tel_target,mock_roof_status):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_status.return_value = dict({'Roof_Open': False})
		mock_check_open_safety.return_value = False, True, dict({'Roof_Open': False})
		mock_plc_roof_function.side_effect = observing.plc.PLC_ERROR
		
		with self.assertLogs(level='CRITICAL') as cm:
			observing.logging.getLogger().critical(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response1, 'CRITICAL')
		

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()
		mock_check_open_safety.assert_called_once()
		mock_plc_roof_function.assert_called_once()


	@patch("observing.send_coords")
	@patch("observing.wait_for_roof_to_stop_moving")
	@patch("PLC_interaction_functions.plc_open_roof")
	@patch("observing.check_safe_to_open_roof")
	def test_got_status_roof_closed_safe_to_open_can_open(self,mock_check_open_safety,mock_plc_roof_function, mock_wait_function,mock_send_coords,mock_tel_target,mock_roof_status):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_status.return_value = dict({'Roof_Open': False})
		mock_check_open_safety.return_value = False, True, dict({'Roof_Open': False})
		mock_plc_roof_function.return_value = 0
		mock_wait_function.return_value = True, dict({'Roof_Open': True})
		
		
		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO')
		

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()
		mock_check_open_safety.assert_called_once()
		mock_plc_roof_function.assert_called_once()
		mock_wait_function.assert_called_once()
		mock_send_coords.assert_called_once()


	@patch("observing.check_safe_to_open_roof")
	def test_got_status_roof_closed_not_safe_to_open(self,mock_check_open_safety,mock_tel_target,mock_roof_status):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_status.return_value = dict({'Roof_Open': False})
		mock_check_open_safety.return_value = False, False, dict({'Roof_Open': False})

		
		with self.assertLogs(level='CRITICAL') as cm:
			observing.logging.getLogger().critical(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response1, 'CRITICAL')
		

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()
		mock_check_open_safety.assert_called_once()


	@patch("observing.send_coords")
	def test_got_status_all_conditions_ok(self, mock_send_coords, mock_tel_target, mock_roof_status):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_status.return_value = dict({'Roof_Open': True})

		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO') #roof is open
		self.assertEqual(logging_actual_response2, 'INFO') #coords pass ok

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()
		mock_send_coords.assert_called_once()

	@patch("observing.send_coords")
	def test_send_coords_timeout_one_error(self, mock_send_coords, mock_tel_target, mock_roof_status):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_send_coords.side_effect = [observing.timeout_decorator.TimeoutError, 'ok']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_status.return_value = dict({'Roof_Open': True})

		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
			logging_actual_response3 = cm.output[2].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO') #roof is open
		self.assertEqual(logging_actual_response2, 'ERROR') #coords not passed ok
		self.assertEqual(logging_actual_response3, 'INFO') #coords passed ok

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()
		mock_send_coords.assert_called()
		self.assertEqual(mock_send_coords.call_count,2)

	@patch("observing.send_coords")
	def test_send_coords_timeout_too_many_attempts(self, mock_send_coords, mock_tel_target, mock_roof_status):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_send_coords.side_effect = [observing.timeout_decorator.TimeoutError, observing.timeout_decorator.TimeoutError, observing.timeout_decorator.TimeoutError]
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_status.return_value = dict({'Roof_Open': True})

		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
			logging_actual_response3 = cm.output[-2].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO') #roof is open
		self.assertEqual(logging_actual_response2, 'ERROR') #coords pass ok
		self.assertEqual(logging_actual_response3, 'CRITICAL')

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()
		mock_send_coords.assert_called()
		self.assertEqual(mock_send_coords.call_count,2)

if __name__ =='__main__':
	unittest.main()