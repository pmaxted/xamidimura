"""
test_observing.py


Contains the unit tests for 'observing.py' script

"""

import unittest
from unittest.mock import patch
import settings_and_error_codes as set_err_codes
import observing

class test_get_next_fits_folder(unittest.TestCase):

	@patch("observing.subprocess.run")
	def test_make_dir(self, mock_make_dir):
	
		input_dir = 'fits_file_tests/'
		input_folder = '20110128'
	
		expected = 'fits_file_tests/20110128/'
		actual = observing.get_next_fits_folder(input_folder,input_dir)
		self.assertEqual(expected,actual)
	
	


@patch("astropy.time.Time.now")
class test_get_date_str(unittest.TestCase):

	def test_date_from_afternoon(self, mock_date):

		mock_date.return_value = observing.astro_time.Time(
			"2019-01-28 14:54:34.543", format = 'iso', scale='utc')

		expected = '20190128'
		actual = observing.get_date_str()

		self.assertEqual(expected,actual)

	def test_date_evening(self, mock_date):

		mock_date.return_value = observing.astro_time.Time(
			"2019-01-28 23:54:34.543", format = 'iso', scale='utc')

		expected = '20190128'
		actual = observing.get_date_str()

		self.assertEqual(expected,actual)

	def test_date_early_morning(self, mock_date):

		mock_date.return_value = observing.astro_time.Time(
			"2019-01-29 3:54:34.543", format = 'iso', scale='utc')

		expected = '20190128'
		actual = observing.get_date_str()

		self.assertEqual(expected,actual)

	def test_date_change_over1(self, mock_date):

		mock_date.return_value = observing.astro_time.Time(
			"2019-01-29 09:00:00", format = 'iso', scale='utc')

		expected = '20190129'
		actual = observing.get_date_str()

		self.assertEqual(expected,actual)

	def test_date_change_over2(self, mock_date):

		mock_date.return_value = observing.astro_time.Time(
			"2019-01-29 08:59:59.999", format = 'iso', scale='utc')

		expected = '20190128'
		actual = observing.get_date_str()

		self.assertEqual(expected,actual)


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

		expectedN, expectedS = set_err_codes.STATUS_CODE_CCD_WARM, \
			set_err_codes.STATUS_CODE_CCD_WARM

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


	def test_got_status_roof_closed_safe_to_open_and_open(self, mock_tel_target,mock_roof_status):

		test_coords = ['21 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_status.return_value = dict({'Roof_Open': False})
		
		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			#logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO') #mentions same coords
		#self.assertEqual(logging_actual_response2, 'CRITICAL') #final message

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()



	@patch("subprocess.run")
	def test_got_status_roof_closed_safe_to_open_cant_open(self,mock_open_roof, mock_tel_target,mock_roof_status):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_status.return_value = dict({'Roof_Open': False})
		mock_open_roof.side_effect = observing.plc.PLC_ERROR
		
		with self.assertLogs(level='ERROR') as cm:
			observing.logging.getLogger().error(observing.go_to_target(test_coords))
			logging_actual_response0 = cm.output[0].split(':')[0]
			logging_actual_response1 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response0, 'WARNING')
		self.assertEqual(logging_actual_response1, 'ERROR')
		

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()
		mock_open_roof.assert_called_once()


	@patch("observing.send_coords")
	@patch("subprocess.run")
	def test_got_status_roof_closed_safe_to_open_can_open(self,mock_open_roof, mock_send_coords,mock_tel_target,mock_roof_status):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_status.return_value = dict({'Roof_Open': False})
		
		
		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(test_coords))
			logging_actual_response0 = cm.output[0].split(':')[0]
			logging_actual_response1 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response0, 'WARNING')
		self.assertEqual(logging_actual_response1, 'INFO')
	

		mock_tel_target.assert_called_once()
		mock_roof_status.assert_called_once()
		mock_open_roof.assert_called_once()
		mock_send_coords.assert_called_once()


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