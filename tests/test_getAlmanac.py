import getAlmanac as ga
import unittest
from unittest.mock import patch

"""
 Unit tests for the getAlmanac.py' script.

"""

class test_str2deg(unittest.TestCase):

	def test_val_not_str(self):

		with self.assertRaises(ValueError):
			ga.str2deg(29)

	def test_no_split_val_in_str(self):

		with self.assertRaises(ValueError):
			ga.str2deg('23345')


	def test_no_minus_sign(self):

		expected = 20.5
		actual = ga.str2deg('20:30:00')
		self.assertEqual(expected,actual)


	def test_minus_sign(self):


		expect1 = -20.5
		actual1 = ga.str2deg('-20:30:00')

		expect2 = -0.0
		actual2 = ga.str2deg('-00:00:00')

		self.assertEqual(expect1,actual1)
		self.assertEqual(expect2,actual2)


class test_set_up_observer(unittest.TestCase):

	def test_returns_saao_longlat(self):

		expected_long = 20.810555555555556
		expected_lat = -32.38083333333334

		actual_obs = ga.set_up_observer()
		self.assertEqual(actual_obs.location.lat.value, expected_lat)
		self.assertEqual(actual_obs.location.lon.value, expected_long)

class test_convert_time(unittest.TestCase):

	def setUp(self):
	
		self.jd = ga.Time(2458543.000000, format = 'jd')
		self.iso = ga.Time('2019-02-28 12:00:00.000', format='iso')
	
	def test_convert_jd_time(self):

		expected = self.iso
		actual = ga.convert_time(self.jd)
		self.assertEqual(expected,actual)

	def test_convert_iso_to_jd(self):

		expected = self.jd
		actual = ga.convert_time(self.iso)


class test_get_timingsISO(unittest.TestCase):

	def setUp(self):

		self.saao = ga.set_up_observer()
		self.current_time = ga.Time('2019-02-28 12:00:00', format='iso')

		self.out=ga.numpy.array([ga.Time('2019-02-28 17:09:26.325', format='iso'),
			ga.Time('2019-02-28 17:38:24.128', format = 'iso'),
			ga.Time('2019-02-28 18:07:51.499', format = 'iso'),
			ga.Time('2019-02-28 18:38:02.622', format = 'iso'),
			ga.Time('2019-03-01 03:00:51.701', format = 'iso'),
			ga.Time('2019-03-01 03:31:03.312', format = 'iso'),
			ga.Time('2019-03-01 04:00:31.680', format = 'iso'),
			ga.Time('2019-03-01 04:29:30.794', format = 'iso'),
			ga.Time('2019-02-28 23:46:06.154', format = 'iso'),
			ga.Time('2019-02-28 13:11:04.674', format = 'iso')])

	def test_get_times(self):

		expected = self.out
		actual = ga.get_timingsISO(self.saao, self.current_time)
		for i in range(len(actual)):
			self.assertEqual(expected[i].value[:-3],actual[i].value[:-3])

		self.assertEqual(len(expected),len(actual))

@patch('astropy.time.Time.now')
class test_calc_time_diff(unittest.TestCase):

	def setUp(self):

		#self.current_time = ga.Time('2019-02-28 12:00:00', format='iso')

		self.time_arr=ga.numpy.array([ga.Time('2019-02-28 17:09:26.325', format='iso'),
			ga.Time('2019-02-28 17:38:24.128', format = 'iso'),
			ga.Time('2019-02-28 18:07:51.499', format = 'iso'),
			ga.Time('2019-02-28 18:38:02.622', format = 'iso'),
			ga.Time('2019-03-01 03:00:51.701', format = 'iso'),
			ga.Time('2019-03-01 03:31:03.312', format = 'iso'),
			ga.Time('2019-03-01 04:00:31.680', format = 'iso'),
			ga.Time('2019-03-01 04:29:30.794', format = 'iso'),
			ga.Time('2019-02-28 23:46:06.154', format = 'iso'),
			ga.Time('2019-02-28 13:11:04.674', format = 'iso')])


	def test_daytime(self, mock_time):

		mock_time.return_value = ga.Time('2019-02-28 12:00:00', format='iso')

		expected_mess, expected_remain, expected_key_time = 'daytime', 0.214888,self.time_arr[0].value[:-3]

		actual_mess, actual_remain, actual_key_t = ga.calc_time_differences(
				self.time_arr)
		
		self.assertEqual(expected_mess, actual_mess)
		self.assertEqual(format(expected_remain, '2.6f'),
			format(actual_remain, '2.6f'))
		
		self.assertEqual(expected_key_time, actual_key_t.value[:-3])

	def test_afterSunset(self, mock_time):

		mock_time.return_value = ga.Time('2019-02-28 17:15:00', format='iso')

		expected_mess, expected_remain, expected_key_time = 'afterSunset', 0.01625148253,self.time_arr[0].value[:-3]

		actual_mess, actual_remain, actual_key_t = ga.calc_time_differences(
				self.time_arr)

		self.assertEqual(expected_mess, actual_mess)
		self.assertEqual(format(expected_remain, '2.6f'),
			format(actual_remain, '2.6f'))

	def test_afterCivil(self, mock_time):

		mock_time.return_value = ga.Time('2019-02-28 18:00:00', format='iso')

		expected_mess, expected_remain, expected_key_time = 'afterCivil', 0.00545716518,self.time_arr[3].value[:-3]

		actual_mess, actual_remain, actual_key_t = ga.calc_time_differences(
				self.time_arr)

		self.assertEqual(expected_mess, actual_mess)
		self.assertEqual(format(expected_remain, '2.6f'),
			format(actual_remain, '2.6f'))


	def test_nighteve_astro(self, mock_time):

		mock_time.return_value = ga.Time('2019-02-28 18:30:00', format='iso')

		expected_mess, expected_remain, expected_key_time = 'night', 0.3757327777, self.time_arr[5].value[:-3]

		actual_mess, actual_remain, actual_key_t = ga.calc_time_differences(
				self.time_arr)

		self.assertEqual(expected_mess, actual_mess)
		self.assertEqual(format(expected_remain, '2.6f'),
			format(actual_remain, '2.6f'))

	def test_night_between_astro(self, mock_time):

		mock_time.return_value = ga.Time('2019-03-01 00:30:00', format='iso')

		expected_mess, expected_remain, expected_key_time = 'night', 0.125732777, self.time_arr[4].value[:-3]

		actual_mess, actual_remain, actual_key_t = ga.calc_time_differences(
				self.time_arr)

		self.assertEqual(expected_mess, actual_mess)
		self.assertEqual(format(expected_remain, '2.6f'),
			format(actual_remain, '2.6f'))

	def test_nightmorn_astro(self, mock_time):

		mock_time.return_value = ga.Time('2019-03-01 3:03:00', format='iso')

		expected_mess, expected_remain, expected_key_time = 'night', 0.01948277779, self.time_arr[4].value[:-3]

		actual_mess, actual_remain, actual_key_t = ga.calc_time_differences(
				self.time_arr)

		self.assertEqual(expected_mess, actual_mess)
		self.assertEqual(format(expected_remain, '2.6f'),
			format(actual_remain, '2.6f'))

	def test_before_civil(self, mock_time):

		mock_time.return_value = ga.Time('2019-03-01 3:35:00', format='iso')

		expected_mess, expected_remain, expected_key_time = 'beforeCivil', 0.01772777358, self.time_arr[4].value[:-3]

		actual_mess, actual_remain, actual_key_t = ga.calc_time_differences(
				self.time_arr)

		self.assertEqual(expected_mess, actual_mess)
		self.assertEqual(format(expected_remain, '2.6f'),
			format(actual_remain, '2.6f'))

	def test_before_sunrise(self, mock_time):

		mock_time.return_value = ga.Time('2019-03-01 4:10:00', format='iso')

		expected_mess, expected_remain, expected_key_time = 'beforeSunrise', 0.013550854184561367, self.time_arr[7].value[:-3]

		actual_mess, actual_remain, actual_key_t = ga.calc_time_differences(
				self.time_arr)

		self.assertEqual(expected_mess, actual_mess)
		self.assertEqual(format(expected_remain, '2.6f'),
			format(actual_remain, '2.6f'))

@patch('getAlmanac.get_timingsISO')
@patch('astropy.time.Time.now')
class test_decide_observing_time(unittest.TestCase):

	def setUp(self):

		self.current_time = ga.Time('2019-02-28 12:00:00', format='iso')

		self.time_arr=ga.numpy.array([ga.Time('2019-02-28 17:09:26.325', format='iso'),
			ga.Time('2019-02-28 17:38:24.128', format = 'iso'),
			ga.Time('2019-02-28 18:07:51.499', format = 'iso'),
			ga.Time('2019-02-28 18:38:02.622', format = 'iso'),
			ga.Time('2019-03-01 03:00:51.701', format = 'iso'),
			ga.Time('2019-03-01 03:31:03.312', format = 'iso'),
			ga.Time('2019-03-01 04:00:31.680', format = 'iso'),
			ga.Time('2019-03-01 04:29:30.794', format = 'iso'),
			ga.Time('2019-02-28 23:46:06.154', format = 'iso'),
			ga.Time('2019-02-28 13:11:04.674', format = 'iso')])

	def test_pick_right_time(self, mock_time, mock_timings):

		mock_time.return_value = self.current_time
		mock_timings.return_value = self.time_arr

		expected_mess, expected_remain, expected_key_time = 'daytime', 0.214888,self.time_arr[0].value[:-3]

		actual_mess, actual_remain, actual_key_t = ga.calc_time_differences(
				self.time_arr)

		self.assertEqual(expected_mess, actual_mess)
		self.assertEqual(format(expected_remain, '2.6f'),
			format(actual_remain, '2.6f'))
		
		self.assertEqual(expected_key_time, actual_key_t.value[:-3])

