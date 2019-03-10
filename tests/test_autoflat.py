import unittest
from unittest.mock import patch
import autoflat as af
import numpy as np
from astropy.table import Table
#import time

"""

	Unittests for the autoflat script. Want to make sure it is behaving how it
	 is expected to before it has to be run under the pressue of actually
	 wanting to take flats
"""


class test_create_obs_recipe(unittest.TestCase):

	def test_dict_is_create(self):

		expected = dict({'TAR_NAME':'TEST',
		'IMG-RA':'N/A', 'IMG-DEC': 'N/A', 'FILTERS':'RX',
		'FOCUS_POS':50000, 'EXPTIME':np.array(3.0),
		'N_PATT':np.array([0]), 'S_PATT':np.array([0]),
		'N_FILT':np.array(['RX']), 'S_FILT':np.array(['RX']),
		'N_EXPO':np.array([3.0]), 'S_EXPO':np.array([3.0]),
		'N_FOCUS':np.array([50000]), 'S_FOCUS':np.array([50000])})

		actual = af.create_flat_obs_recipe('RX', 3.0, tar_name = 'TEST')

		self.assertEqual(expected,actual)

	def test_invalid_filter(self):

		with self.assertLogs(level='ERROR') as cm:
			af.logging.getLogger().error(af.create_flat_obs_recipe(
				'TEST', 3.0, tar_name = 'TEST'))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

#@patch('tcs_control.send_command')
@patch('tcs_control.wait_till_read_out')
@patch('tcs_control.tcs_exposure_request')
class take_flat(unittest.TestCase):

	def test_ok_request(self, mock_exposure, mock_wait):#, mock_tcs_command):

		mock_exposure.return_value = 0
		#mock_tcs_command.return_value = 'No return'

		expected = True
		actual = af.take_flat()

		self.assertEqual(expected,actual)
		mock_exposure.assert_called_once()
		mock_wait.assert_called_once()

	def test_max_failure(self, mock_exposure,mock_wait):

		mock_exposure.side_effect = [-1,-1,-1]

		expected = False
		actual = af.take_flat()

		self.assertEqual(expected,actual)
		self.assertEqual(mock_exposure.call_count,3)
		mock_wait.assert_not_called()

@patch('autoflat.take_flat')
class test_get_sky_outcome(unittest.TestCase):

	def test_no_flat_success(self, mock_flat):

		mock_flat.return_value = False
		expected = None
		actual = af.get_sky_outcome()

		self.assertEqual(expected,actual)
		mock_flat.assert_called_once

		with self.assertLogs(level='ERROR') as cm:
			af.logging.getLogger().error(af.get_sky_outcome())
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

	@patch('tcs_control.lastsky')
	def test_successful_flat(self, mock_sky_count, mock_flat):

		mock_sky_count = [1500,100,2500,100]
		mock_flat = True

		expected = 2000
		actual = af.get_sky_count()

class test_get_filter_sequence(unittest.TestCase):

	def setUp(self):
	
		self.morning_seq = af.morning_filter_order
		self.evening_seq = af.evening_filter_order
	
	def test_morning_sequence(self):

		expected = self.morning_seq
		actual = af.get_filter_sequence(morning=True)

		self.assertEqual(expected, actual)

	def test_evening_sequence(self):

		expected = self.evening_seq
		actual = af.get_filter_sequence(morning=False)

		self.assertEqual(expected, actual)

@patch('autoflat.get_sky_outcome')
class test_wait_for_right_count_evening(unittest.TestCase):

	def test_no_loop_needed(self, mock_sky_count):

		expected = 40000
		actual = af.wait_for_right_count_evening(40000)
		self.assertEqual(expected,actual)
		mock_sky_count.assert_not_called()

	@patch('autoflat.time.sleep')
	def test_loop_is_used(self, mock_sleep, mock_sky_count):
	#def test_loop_is_used(self, mock_sky_count):

		mock_sky_count.side_effect = [70000,60000,55000]
		mock_sleep = af.time.sleep(0.001)
		expected = 55000

		actual = af.wait_for_right_count_evening(80000)

		self.assertEqual(expected,actual)
		self.assertEqual(mock_sky_count.call_count,3)


class test_get_exposure_estimate(unittest.TestCase):

	def test_less_than_ideal(self):

		expected = 2
		actual = af.get_exposure_estimate(10000)

		self.assertEqual(expected, actual)

	def test_bad_count_value(self):

		expected = None
		actual = af.get_exposure_estimate(80000)
		
		self.assertEqual(expected,actual)
		
		with self.assertLogs(level='ERROR') as cm:
			af.logging.getLogger().error(af.get_exposure_estimate(80000))
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'ERROR')

	def test_ok_count(self):

		expected = 1
		actual = af.get_exposure_estimate(30000)

		self.assertEqual(expected,actual)

@patch('tcs_control.apply_offset_to_tele')
class test_do_telescope_offset(unittest.TestCase):

	def test_fail_to_offset(self, mock_offset):
	
		mock_offset.side_effect = ValueError()

		with self.assertLogs(level='WARNING') as cm:
			af.logging.getLogger().warning(af.do_telescope_offset())
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'WARNING')

	def test_ok_offset(self, mock_offset):

		mock_offset.return_value = 'ok'

		with self.assertLogs(level='INFO') as cm:
			af.logging.getLogger('autoflat').info(af.do_telescope_offset())
			logging_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_response, 'INFO')

@patch('autoflat.do_telescope_offset')
@patch('autoflat.get_sky_count')
@patch('observing.take_exposure')
@patch('autoflat.wait_for_right_count_evening')
@patch('autoflat.get_sky_outcome')
@patch('tcs_control.scratchmode')
@patch('observing.change_filter_loop')
class test_do_flats_evening(unittest.TestCase):

	def setUp(self):
	
		self.sunsetTime = af.observing.astro_time.Time('2019-02-26 17:11:44.996',
			scale='utc',format='iso')
		self.bestRow = Table(
			names = ['RA(hms)','DEC(dms)', 'limit'], dtype=['S10','S11','f'])
		self.bestRow.add_row(['00:42:28.8','-35:07:22.1','10.0'])

	def test_run_through_with_sat(self, mock_filter, mock_scratch, mock_sky_count,
			mock_wait, mock_exposure, mock_sky2,mock_offset):

		mock_filter.return_value = 0, 0
		#mock_scratch #don't need return value
		mock_sky_count.side_effect = [60000,40000,40000,40000,40000]
		mock_wait.return_value = 54000

		mock_sky2.side_effect = [50000,30000,15000,40000,30000,25000,20000,19999,
			30000,19999,15000,65000,55000,50000,2000,10001,
			1000,1000,10000,1000,1000,1000,2000,1000]

		af.do_flats_evening(self.sunsetTime,self.bestRow,'20190225',
			'fits_file_tests/20190225/')

		mock_offset.is_called()

@patch('autoflat.do_telescope_offset')
@patch('autoflat.get_sky_count')
@patch('observing.take_exposure')
@patch('autoflat.wait_for_right_count_morning')
@patch('autoflat.get_sky_outcome_morning')
@patch('tcs_control.scratchmode')
@patch('observing.change_filter_loop')
class test_do_flats_evening(unittest.TestCase):

	def setUp(self):
	
		self.sunsetTime = af.observing.astro_time.Time('2019-02-26 17:11:44.996',
			scale='utc',format='iso')
		self.bestRow = Table(
			names = ['RA(hms)','DEC(dms)', 'limit'], dtype=['S10','S11','f'])
		self.bestRow.add_row(['00:42:28.8','-35:07:22.1','10.0'])

	def test_run_through_with_sat(self, mock_filter, mock_scratch, mock_sky_count,
			mock_wait, mock_exposure, mock_sky2, mock_offset):

		mock_filter.return_value = 0, 0
		#mock_scratch #don't need return value
		mock_sky_count.side_effect = [12000,30000,30000,30000,30000]
		mock_wait.return_value = 22000

		mock_sky2.side_effect = [22000,23000,35000,56000, 23000,33000,56000, 22000,
			25000, 25000, 65000, 30000, 40000,56000, 12000,12000, 30000,30000,
			56000,56000,56000,56000]

		af.do_flats_morning(self.sunsetTime,self.bestRow,'20190225',
			'fits_file_tests/20190225/')

		mock_offset.is_called()






