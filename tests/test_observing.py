"""
test_observing.py


Contains the unit tests for 'observing.py' script

"""

import unittest
from unittest.mock import patch
import settings_and_error_codes as set_err_codes
import observing
import numpy as np

class test_get_current_UTC_time_in_isot_format(unittest.TestCase):

	def test_it_works(self):

		expected_format = 'isot'
		actual_value = observing.get_current_UTC_time_in_isot_format()

		self.assertEqual(expected_format, actual_value.format)

	
class test_exposure_object(unittest.TestCase):

	def setUp(self):

		self.exp_ob = observing.exposure_obj(30,'RX','FLAT',1,'A','1')
		self.test_time =observing.astro_time.Time("2019-01-28 12:00:00.000",
			format = 'iso', scale='utc')

	@patch('observing.get_current_UTC_time_in_isot_format')
	def test_set_exposure_start_time(self, mock_time):

		mock_time.return_value = self.test_time
		expected_date_obs ="2019-01-28 12:00:00.000"
		expected_mjd_obs = 58511.5
		expected_mid_exp = "2019-01-28 12:00:15.000"#58511.50017361111
		expected_mjd_mid = 58511.50017361111

		self.exp_ob.set_start_time()
		
		actual_date_obs = self.exp_ob.date_obs
		actual_mjd_obs = self.exp_ob.mjd_obs
		actual_mid_exp = self.exp_ob.mid_exp
		actual_mjd_mid = self.exp_ob.mjd_mid

		self.assertEqual(expected_date_obs,actual_date_obs)
		self.assertEqual(expected_mjd_obs,actual_mjd_obs)
		self.assertEqual(expected_mid_exp,actual_mid_exp.value)
		self.assertEqual(expected_mjd_mid,actual_mjd_mid)

@patch('subprocess.Popen.communicate')
@patch('subprocess.Popen')
class test_get_current_weather(unittest.TestCase):

	def setUp(self):
	
		self.readline = b'2019-02-01 16:13:02.07 -998.0 19.7 -2.0 66 13.1 '\
			b'0-0-2-4-2 WET NONE'


	def test_error_reading_logfile(self, mock_process, mock_communicate):

		mock_process.return_value = observing.subprocess.Popen
		mock_communicate.return_value = (b'', b'')

		with self.assertLogs(level='ERROR') as cm:
			observing.logging.getLogger().error(observing.get_current_weather())
			logging_actual_response1 = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response1, 'ERROR')


	def test_get_line_ok(self, mock_process, mock_communicate):

		mock_process.return_value = observing.subprocess.Popen
		mock_communicate.return_value = (
			b'2019-02-01 16:13:02.07 -998.0 19.7 -2.0 66 13.1 '\
			b'0-0-2-4-2 WET NONE', b'')

		expected =['2019-02-01', '16:13:02.07', '-998.0', '19.7', '-2.0', '66',
			'13.1',	'0-0-2-4-2', 'WET', 'NONE' ]

		actual = observing.get_current_weather()
		self.assertEqual(actual, expected)

@patch('observing.get_current_UTC_time_in_isot_format')
@patch('tcs_control.get_camera_status')
class test_get_fits_header_info(unittest.TestCase):

	def setUp(self):
	
		self.focuser_config = {'Nickname': 'FocusLynx Foc2', 'Max Pos': '125440',
		'DevTyp': 'OE', 'TComp ON': '0', 'TempCo A': '+0086',
		'TempCo B': '+0086', 'TempCo C': '+0086', 'TempCo D': '+0000',
		'TempCo E': '+0000', 'TCMode': 'A', 'BLC En': '0', 'BLC Stps': '+40',
		'LED Brt': '075', 'TC@Start': '0'}
		self.focuser_position = 108085
		self.weather = ['2019-02-01', '16:13:02.07', '-998.0', '19.7', '-2.0', '66',
			'13.1',	'0-0-2-4-2', 'WET', 'NONE' ]
		self.expose_info = observing.exposure_obj(30,'RX','FLAT',1,'A','1')
		self.target_info = observing.target_obj('TEST',
			coords=['0:10:20','-3:40:50'], type='OBJECT')
		self.telescope_pointing = ['0:10:20','-3:40:50']
	
		self.test_time =observing.astro_time.Time("2019-01-28 12:00:00.000",
			format = 'iso', scale='utc')

	

	def test_can_get_info_dict_CCD_temp_ok(self, mock_cam_stat, mock_time):

		mock_cam_stat.return_value = ['IDLE','AtTemp',-22,-50]
		mock_time.return_value = self.test_time

		self.expose_info.set_start_time()
		actual = observing.get_fits_header_info(self.focuser_config,
			self.focuser_position,self.weather, self.expose_info, self.target_info,
			self.telescope_pointing)

		expected = {
		'OBSERVAT': ('SAAO', 'Observatory name'),
		'TELESCOP': ('Xamidimura', 'Telescope name'),
		'INSTRUME': (1, 'CCD1-South/CCD2-North'),
		'FILTRWHL': ('A', 'ifw1-South/ifw2-North'),
		'FOCUSER' : ('FocusLynx Foc2', \
									'focuser1-south/focuser2-north'),
		'DATE'    : ("2019-01-28 12:00:00.000", \
									'File creation date/time (UTC)'),
		'OBJECT'  : ('TEST', 'Target name'),
		'IMAGETYP': ('FLAT', 'Flat/bias/dark/science/other'),
					
		'OBJ-RA'  : ('0:10:20', 'Expected Target RA'),
		'OBJ-DEC' : ('-3:40:50', 'Expected Target DEC'),
		'TEL-RA'  : ('0:10:20', 'Telescope RA'),
		'TEL-DEC' : ('-3:40:50', 'Telescope DEC'),
		'IMAG-RA' : ("Calculate", 'Nominal image position, pxl (1024,1024) J2000'),
		'IMAG-DEC': ("Calculate", 'Nominal image position, pxl (1024,1024) J2000'),
	
		'EQUINOX' :(2000, 'Used coordinate system'),
		'DATE-OBS': ("2019-01-28 12:00:00.000", \
									'Exp start CCYY-MM-DDTHH:MM:SS.sss(UTC)'),
		'MID_EXP' : ("2019-01-28 12:00:15.000", \
									'Exp middle CCYY-MM-DDTHH:MM:SS.sss(UTC)'),
		'MJD_OBS' : (58511.5, 'MJD at start'),
		'MJD_MID' : (58511.50017361111, 'MJD at mid-point'),
		'EXPTIME' : (30, 'Integration time (s)'),
	
		'FILT_NAM': ('RX', 'Rx/Gx/Bx/Wx/Ix'),
		'FOCU_POS': (108085, 'Position of focuser at exp. start'),
	
		'LATITUDE': ('-32:22:51', 'Site Latitude, degrees +N'),
		'LONGITUD': ('20:48:38', 'Site Longitude, degrees +E'),
		'ALTITUDE': (1800, 'Site elevation (meters) above sea level'),
	
		'BIASSEC' : ('[2068:2148,1:2048]', 'Bias section'), # Don't know if these are correct
		'TRIMSEC' : ('[6:2053,1:2048]',	'Illuminated section'), # Taken from WASP fits file.
		#'GAIN'    : ("NOT SURE", '???'),
		'CCD_TEMP': (-22, 'Camera temperature'),
	
		#"From focuser config -- Run get config everytime, or run once before hand??"
		'TEMP_COM':	('0', \
									'Temperature compensation (ON=1/OFF=0)'),
		'TCOMSTRT':	('0', \
								'Temperature compensation @ start (ON=1/OFF=0)'),
		'TCOMMODE': ('A'  , \
											'Temperature compensation mode'),
		'TCOM_COA': ('+0086', \
									'Temperature compensation coefficient A'),
		'TCOM_COB': ('+0086', \
									'Temperature compensation coefficient B'),
		'TCOM_COC':	('+0086', \
									'Temperature compensation coefficient C'),
		'TCOM_COD':	('+0000', \
									'Temperature compensation coefficient D'),
		'TCOM_COE':	('+0000', \
									'Temperature compensation coefficient E'),
		'BCK_LASH':	('0'  ,
									'Backlash compensation (ON =1/OFF=0)'),
		'BCK_STEP':	('+40', \
									'Steps used for backlash compensation'),
		'COMMENT' : ('Weather log from: '+"2019-02-01T16:13:02.070"+' UTC, '+'2458516.175718'),
			
		'WXCON_CO': ('0-0-2-4-2', 'Cloud/wind/rain/sky/day codes'),
		'WXWNDSPD': ('-2.0', 'Wind speed, kph'),
		'WXDEW'   : ('13.1', 'Dew point, C'),
		'WXOTEMP' : ('19.7', 'Outside ambient air temp, C'),
		'WXSKYT'  : ('-998.0', 'Sky temperature'),
		'WXOHUMID': ('66', 'Outside humidity, percent')}

		self.assertEqual(expected, actual)

	def test_can_get_info_dict_CCD_temp_not_ok(self, mock_cam_stat, mock_time):

		mock_cam_stat.side_effect = observing.subprocess.TimeoutExpired
		mock_time.return_value = self.test_time

		self.expose_info.set_start_time()
		actual = observing.get_fits_header_info(self.focuser_config,
			self.focuser_position,self.weather, self.expose_info, self.target_info,
			self.telescope_pointing)

		expected = {
		'OBSERVAT': ('SAAO', 'Observatory name'),
		'TELESCOP': ('Xamidimura', 'Telescope name'),
		'INSTRUME': (1, 'CCD1-South/CCD2-North'),
		'FILTRWHL': ('A', 'ifw1-South/ifw2-North'),
		'FOCUSER' : ('FocusLynx Foc2', \
									'focuser1-south/focuser2-north'),
		'DATE'    : ("2019-01-28 12:00:00.000", \
									'File creation date/time (UTC)'),
		'OBJECT'  : ('TEST', 'Target name'),
		'IMAGETYP': ('FLAT', 'Flat/bias/dark/science/other'),
					
		'OBJ-RA'  : ('0:10:20', 'Expected Target RA'),
		'OBJ-DEC' : ('-3:40:50', 'Expected Target DEC'),
		'TEL-RA'  : ('0:10:20', 'Telescope RA'),
		'TEL-DEC' : ('-3:40:50', 'Telescope DEC'),
		'IMAG-RA' : ("Calculate", 'Nominal image position, pxl (1024,1024) J2000'),
		'IMAG-DEC': ("Calculate", 'Nominal image position, pxl (1024,1024) J2000'),
	
		'EQUINOX' :(2000, 'Used coordinate system'),
		'DATE-OBS': ("2019-01-28 12:00:00.000", \
									'Exp start CCYY-MM-DDTHH:MM:SS.sss(UTC)'),
		'MID_EXP' : ("2019-01-28 12:00:15.000", \
									'Exp middle CCYY-MM-DDTHH:MM:SS.sss(UTC)'),
		'MJD_OBS' : (58511.5, 'MJD at start'),
		'MJD_MID' : (58511.50017361111, 'MJD at mid-point'),
		'EXPTIME' : (30, 'Integration time (s)'),
	
		'FILT_NAM': ('RX', 'Rx/Gx/Bx/Wx/Ix'),
		'FOCU_POS': (108085, 'Position of focuser at exp. start'),
	
		'LATITUDE': ('-32:22:51', 'Site Latitude, degrees +N'),
		'LONGITUD': ('20:48:38', 'Site Longitude, degrees +E'),
		'ALTITUDE': (1800, 'Site elevation (meters) above sea level'),
	
		'BIASSEC' : ('[2068:2148,1:2048]', 'Bias section'), # Don't know if these are correct
		'TRIMSEC' : ('[6:2053,1:2048]',	'Illuminated section'), # Taken from WASP fits file.
		#'GAIN'    : ("NOT SURE", '???'),
		'CCD_TEMP': ('NA', 'Camera temperature'),
	
		#"From focuser config -- Run get config everytime, or run once before hand??"
		'TEMP_COM':	('0', \
									'Temperature compensation (ON=1/OFF=0)'),
		'TCOMSTRT':	('0', \
								'Temperature compensation @ start (ON=1/OFF=0)'),
		'TCOMMODE': ('A'  , \
											'Temperature compensation mode'),
		'TCOM_COA': ('+0086', \
									'Temperature compensation coefficient A'),
		'TCOM_COB': ('+0086', \
									'Temperature compensation coefficient B'),
		'TCOM_COC':	('+0086', \
									'Temperature compensation coefficient C'),
		'TCOM_COD':	('+0000', \
									'Temperature compensation coefficient D'),
		'TCOM_COE':	('+0000', \
									'Temperature compensation coefficient E'),
		'BCK_LASH':	('0'  ,
									'Backlash compensation (ON =1/OFF=0)'),
		'BCK_STEP':	('+40', \
									'Steps used for backlash compensation'),
		'COMMENT' : ('Weather log from: '+"2019-02-01T16:13:02.070"+' UTC, '+'2458516.175718'),
			
		'WXCON_CO': ('0-0-2-4-2', 'Cloud/wind/rain/sky/day codes'),
		'WXWNDSPD': ('-2.0', 'Wind speed, kph'),
		'WXDEW'   : ('13.1', 'Dew point, C'),
		'WXOTEMP' : ('19.7', 'Outside ambient air temp, C'),
		'WXSKYT'  : ('-998.0', 'Sky temperature'),
		'WXOHUMID': ('66', 'Outside humidity, percent')}

		self.assertEqual(expected, actual)


class test_get_obslog_info(unittest.TestCase):

	def setUp(self):

		self.fit_info_dict = {
		'OBSERVAT': ('SAAO', 'Observatory name'),
		'TELESCOP': ('Xamidimura', 'Telescope name'),
		'INSTRUME': (1, 'CCD1-South/CCD2-North'),
		'FILTRWHL': ('A', 'ifw1-South/ifw2-North'),
		'FOCUSER' : ('FocusLynx Foc2', \
									'focuser1-south/focuser2-north'),
		'DATE'    : ("2019-01-28 12:00:00.000", \
									'File creation date/time (UTC)'),
		'OBJECT'  : ('TEST', 'Target name'),
		'IMAGETYP': ('FLAT', 'Flat/bias/dark/science/other'),
					
		'OBJ-RA'  : ('0:10:20', 'Expected Target RA'),
		'OBJ-DEC' : ('-3:40:50', 'Expected Target DEC'),
		'TEL-RA'  : ('0:10:20', 'Telescope RA'),
		'TEL-DEC' : ('-3:40:50', 'Telescope DEC'),
		'IMAG-RA' : ("Calculate", 'Nominal image position, pxl (1024,1024) J2000'),
		'IMAG-DEC': ("Calculate", 'Nominal image position, pxl (1024,1024) J2000'),
	
		'EQUINOX' :(2000, 'Used coordinate system'),
		'DATE-OBS': ("2019-01-28 12:00:00.000", \
									'Exp start CCYY-MM-DDTHH:MM:SS.sss(UTC)'),
		'MID_EXP' : ("2019-01-28 12:00:15.000", \
									'Exp middle CCYY-MM-DDTHH:MM:SS.sss(UTC)'),
		'MJD_OBS' : (58511.5, 'MJD at start'),
		'MJD_MID' : (58511.50017361111, 'MJD at mid-point'),
		'EXPTIME' : (30, 'Integration time (s)'),
	
		'FILT_NAM': ('RX', 'Rx/Gx/Bx/Wx/Ix'),
		'FOCU_POS': (108085, 'Position of focuser at exp. start'),
	
		'LATITUDE': ('-32:22:51', 'Site Latitude, degrees +N'),
		'LONGITUD': ('20:48:38', 'Site Longitude, degrees +E'),
		'ALTITUDE': (1800, 'Site elevation (meters) above sea level'),
	
		'BIASSEC' : ('[2068:2148,1:2048]', 'Bias section'), # Don't know if these are correct
		'TRIMSEC' : ('[6:2053,1:2048]',	'Illuminated section'), # Taken from WASP fits file.
		#'GAIN'    : ("NOT SURE", '???'),
		'CCD_TEMP': ('NA', 'Camera temperature'),
	
		#"From focuser config -- Run get config everytime, or run once before hand??"
		'TEMP_COM':	('0', \
									'Temperature compensation (ON=1/OFF=0)'),
		'TCOMSTRT':	('0', \
								'Temperature compensation @ start (ON=1/OFF=0)'),
		'TCOMMODE': ('A'  , \
											'Temperature compensation mode'),
		'TCOM_COA': ('+0086', \
									'Temperature compensation coefficient A'),
		'TCOM_COB': ('+0086', \
									'Temperature compensation coefficient B'),
		'TCOM_COC':	('+0086', \
									'Temperature compensation coefficient C'),
		'TCOM_COD':	('+0000', \
									'Temperature compensation coefficient D'),
		'TCOM_COE':	('+0000', \
									'Temperature compensation coefficient E'),
		'BCK_LASH':	('0'  ,
									'Backlash compensation (ON =1/OFF=0)'),
		'BCK_STEP':	('+40', \
									'Steps used for backlash compensation'),
		'COMMENT' : ('Weather log from: '+"2019-02-01T16:13:02.070"+' UTC, '+'2458516.175718'),
			
		'WXCON_CO': ('0-0-2-4-2', 'Cloud/wind/rain/sky/day codes'),
		'WXWNDSPD': ('-2.0', 'Wind speed, kph'),
		'WXDEW'   : ('13.1', 'Dew point, C'),
		'WXOTEMP' : ('19.7', 'Outside ambient air temp, C'),
		'WXSKYT'  : ('-998.0', 'Sky temperature'),
		'WXOHUMID': ('66', 'Outside humidity, percent')}

		self.CCDno = 1
		self.IMAGE_ID = 1
		self.target_info = observing.target_obj('TEST',
			coords=['0:10:20','-3:40:50'], type='OBJECT')

		self.datestr = '20190128'
		self.status = 0
		self.savefile = False

	def test_produces_obslog_dict(self):

		expected = {'IMAGE_ID': 11,
		'CCD_ID'     : 1,
		'FILE'    : 'CCD'+'1'+'_'+'20190128'+'_'+'000000011'+'.fits',
		'TAR_NAME': 'TEST',#"OBJECT from FITS header", Need the [0] to
		#get value not comment
		'TAR_TYPE': 'FLAT',
		'DATE_OBS': "2019-01-28 12:00:00.000",#"FITS header",
		'MJD_OBS' : 58511.5,#"FITS header",
		'IMAGETYP': 'FLAT;',#"FITS header",
		'FILT_NAM': 'RX',#"FITS header",
		'EXPTIME' : 30,#"FITS header",
		'OBJ_RA'  : '0:10:20',#"FITS header",
		'OBJ_DEC' : '-3:40:50',#"FITS header",
		'TEL_RA'  : '0:10:20',#"FITS header",
		'TEL_DEC' : '-3:40:50',#"FITS header",
		'IMAG_RA'  : 'Calculate',#"FITS header",
		'IMAG_DEC' : 'Calculate',#"FITS header",
		'INSTRUME': '1',#"FITS header",
		'FOCUSER' : 'FocusLynx Foc2',#"FITS header",
		'STATUS'  : self.status,
		'SAVED'	  : self.savefile #no fits header created for status <0. 1= True/0=False
		}

		actual  = observing.get_obslog_info(self.fit_info_dict, self.CCDno,
			self.IMAGE_ID, self.target_info, self.datestr, self.status,
			self.savefile)

@patch('astropy.io.fits.PrimaryHDU.writeto')
@patch('observing.get_current_UTC_time_in_isot_format')
@patch('sqlite3.connect.cursor')
@patch('sqlite3.connect')
@patch('observing.get_current_weather')
@patch('tcs_control.get_tel_pointing')
@patch('focuser_control.get_focuser_status')
class test_sort_all_logging(unittest.TestCase):

	def setUp(self):

		self.focuser_status = {'Temp(C)':'+21.7','Curr Pos':108085,
			'Targ Pos':000000,'IsMoving': 1,'IsHoming':1,'IsHomed':0,
			'FFDetect': 0,'TmpProbe':1, 'RemoteIO':0,'Hnd Ctlr':0}
		self.tel_point = ['0:10:20','-3:40:50']
		self.current_weather = ['2019-02-01', '16:13:02.07', '-998.0', '19.7',
			'-2.0', '66', '13.1',	'0-0-2-4-2', 'WET', 'NONE' ]
			
		self.exp_class = observing.exposure_obj(30,'RX','FLAT',1,'A',1)
		self.target_class = observing.target_obj('TEST',
			coords=['0:10:20','-3:40:50'], type='OBJECT')
		self.focuser_info = [1,'focuser1_port',{'Nickname':
			'FocusLynx FocSOUTH', 'Max Pos': '125440', 'DevTyp': 'OE',
			'TComp ON': '0', 'TempCo A': '+0086', 'TempCo B': '+0086',
			'TempCo C': '+0086', 'TempCo D': '+0000', 'TempCo E': '+0000',
			'TCMode': 'A', 'BLC En': '0', 'BLC Stps': '+40', 'LED Brt': '075',
			'TC@Start': '0'}]
			
		self.test_time =observing.astro_time.Time("2019-01-28 12:00:00.000",
			format = 'iso', scale='utc')
		
		self.datestr = '20190128'
		self.fits_folder = 'fits_file_tests/20190128/'


	def test_runs_ok_save_header(self, mock_focuser_status, mock_tel_point, mock_weather, mock_conn, mock_curs, mock_time, mock_fits_write):

		mock_focuser_status.return_value = self.focuser_status
		mock_tel_point.return_value = self.tel_point
		mock_weather.return_value = self.current_weather
		mock_time.return_value = self.test_time

		self.exp_class.set_start_time()

		mock_curs.execute()
		mock_conn.commit()

		expected = 2
		actual = observing.sort_all_logging_info(self.exp_class,
			self.target_class, self.focuser_info, mock_conn, mock_curs,0,
			self.datestr, self.fits_folder)

		self.assertEqual(actual,expected)
		mock_fits_write.assert_called_once_with(self.fits_folder+'CCD1_20190128_00000001.fits',overwrite=True)

		mock_conn.commit.assert_called()
		mock_curs.execute.assert_called()
		mock_weather.assert_called_once()
		mock_tel_point.assert_called_once()
		mock_focuser_status.assert_called_once

	def test_runs_ok_not_save_header(self, mock_focuser_status, mock_tel_point, mock_weather, mock_conn, mock_curs, mock_time, mock_fits_write):

		mock_focuser_status.return_value = self.focuser_status
		mock_tel_point.return_value = self.tel_point
		mock_weather.return_value = self.current_weather
		mock_time.return_value = self.test_time

		self.exp_class.set_start_time()

		mock_curs.execute()
		mock_conn.commit()

		expected = 2
		actual = observing.sort_all_logging_info(self.exp_class,
			self.target_class, self.focuser_info, mock_conn, mock_curs,-3,
			self.datestr, self.fits_folder)

		self.assertEqual(actual,expected)
		mock_fits_write.assert_not_called()

		mock_conn.commit.assert_called()
		mock_curs.execute.assert_called()
		mock_weather.assert_called_once()
		mock_tel_point.assert_called_once()
		mock_focuser_status.assert_called_once

	def test_runs_ok_save_header_fail_tel_point(self, mock_focuser_status, mock_tel_point, mock_weather, mock_conn, mock_curs, mock_time,
		mock_fits_write):

		mock_focuser_status.return_value = self.focuser_status
		mock_tel_point.side_effect = observing.subprocess.TimeoutExpired
		mock_weather.return_value = self.current_weather
		mock_time.return_value = self.test_time

		self.exp_class.set_start_time()

		mock_curs.execute()
		mock_conn.commit()

		expected = 2
		actual = observing.sort_all_logging_info(self.exp_class,
			self.target_class, self.focuser_info, mock_conn, mock_curs,0,
			self.datestr, self.fits_folder)

		self.assertEqual(actual,expected)
		mock_fits_write.assert_called_once_with(self.fits_folder+'CCD1_20190128_00000001.fits',overwrite=True)

		mock_conn.commit.assert_called()
		mock_curs.execute.assert_called()
		mock_weather.assert_called_once()
		mock_tel_point.assert_called_once()
		mock_focuser_status.assert_called_once()

@patch('os.listdir')
class test_get_next_file_number():

	def setUp(self):

		self.file_list = ['CCD1_20190204_00000001.fits', 'CCD1_20190204_00000002.fits', 'CCD1_20190204_00000003.fits', 'CCD1_20190204_00000004.fits', 'CCD1_20190204_00000005.fits', 'CCD1_20190204_00000006.fits', 'CCD1_20190204_00000007.fits', 'CCD1_20190204_00000008.fits', 'CCD1_20190204_00000009.fits', 'CCD1_20190204_00000010.fits', 'CCD1_20190204_00000011.fits', 'CCD1_20190204_00000012.fits', 'CCD2_20190204_00000001.fits', 'CCD2_20190204_00000002.fits', 'CCD2_20190204_00000003.fits', 'CCD2_20190204_00000004.fits', 'CCD2_20190204_00000005.fits', 'CCD2_20190204_00000006.fits', 'CCD2_20190204_00000007.fits', 'CCD2_20190204_00000008.fits', 'CCD2_20190204_00000009.fits', 'CCD2_20190204_00000010.fits', 'CCD2_20190204_00000011.fits', 'CCD2_20190204_00000012.fits']

	def test_invalid_ccdno(self, mock_dirlist):

		with self.assertLogs(level='ERROR') as cm:
			fwc.logging.getLogger().error(observing.get_next_file_number(1,
			'20190204'))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'ERROR')

		mock_dirlist.assert_not_called()

	def test_get_last_file_no(self, mock_dirlist):

		mock_dirlist = self.file_list

		expected = 13
		actual = observing.get_next_file_number(1, '20190204')
		self.assertEqual(expected,actual)

		mock_dirlist.assert_called_once()

	def test_no_previous_file(self, mock_dirlist):

		mock_dirlist = []

		expected = 1
		actual = observing.get_next_file_number(1, '20190204')

		self.assertEqual(ex,actual)

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

@patch('common.load_config')
class test_get_observing_recipe(unittest.TestCase):

	def setUp(self):

		self.loaded_dict = {'TAR_NAME': 'BIAS_standard', 'IMG-RA': 'N/A',
		'IMG-DEC': 'N/A', 'FILTERS': ['WX','IX'], 'FOCUS_POS': [50000,50000],
		'EXPTIME': np.array([ 1.,  1.]), 'N_PATT': np.array([0, 1]),
		'S_PATT': np.array([0, 1])}
	
		self.dict_bad_exp = {'TAR_NAME': 'BIAS_standard', 'IMG-RA': 'N/A',
		'IMG-DEC': 'N/A', 'FILTERS': ['WX','IX'], 'FOCUS_POS': 50000,
		'EXPTIME': ['erf','ere'], 'N_PATT': np.array([0, 1]),
		'S_PATT': np.array([0, 1])}
	
		self.dict_bad_exp_len = {'TAR_NAME': 'BIAS_standard', 'IMG-RA': 'N/A',
		'IMG-DEC': 'N/A', 'FILTERS': ['WX','IX'], 'FOCUS_POS': 50000,
		'EXPTIME': [1.,1.,1.,1.], 'N_PATT': np.array([0, 1]),
		'S_PATT': np.array([0, 1])}

	def test_all_ok(self, mock_config):

		mock_config.return_value = self.loaded_dict

		expected = {'TAR_NAME': 'BIAS_standard', 'IMG-RA': 'N/A',
		'IMG-DEC': 'N/A', 'FILTERS': ['WX','IX'], 'FOCUS_POS': [50000,50000],
		'EXPTIME': np.array([ 1.,  1.]), 'N_PATT': np.array([0, 1]),
		'S_PATT': np.array([0, 1]), 'N_FOCUS':[50000,50000],'S_FOCUS':[50000,50000],
		'N_EXPO':[1.,1.], 'S_EXPO':[1.,1.], 'N_FILT':['WX','IX'],
		'S_FILT':['WX','IX']}

		actual = observing.get_observing_recipe('BIAS_standard')
		for i in expected.keys():
			assert i in actual.keys()
			try:
				self.assertEqual(expected[i], actual[i])
			except ValueError:

				for j in range(len(expected[i])):
					#print(expected[i][j], actual[i][j])
					self.assertEqual(expected[i][j], actual[i][j])

	def test_bad_exp(self, mock_config):

		mock_config.return_value = self.dict_bad_exp

		with self.assertLogs(level='ERROR') as cm:
			observing.logging.getLogger().error(observing.get_observing_recipe(
				'BIAS_standard'))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'ERROR')

	def test_bad_exp(self, mock_config):

		mock_config.return_value = self.dict_bad_exp_len

		with self.assertLogs(level='ERROR') as cm:
			observing.logging.getLogger().error(observing.get_observing_recipe(
				'BIAS_standard'))
			logging_actual_response = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response, 'ERROR')


@patch('tcs_control.apply_offset_to_tele')
@patch('update_point_off.read_offset_values')
class test_check_point_offset_need(unittest.TestCase):

	def test_no_pointing_offset(self, mock_offset_read,
		mock_apply_offset):
		
		#mock_offset_bool.return_value = False

		observing.check_point_offset_need(use_offs = False)

		mock_offset_read.assert_not_called()
		mock_apply_offset.assert_not_called()

	def test_check_offset_its_zero(self, mock_offset_read,
		mock_apply_offset):
		
		#mock_offset_bool.return_value = True
		mock_offset_read.return_value = 0.00,0.00
		
		observing.check_point_offset_need(use_offs=True)
		
		mock_offset_read.assert_called_once()
		mock_apply_offset.assert_not_called()

	def test_check_offset_apply(self, mock_offset_read,
		mock_apply_offset):
		
		#mock_offset_bool.return_value = True
		mock_offset_read.return_value = 0.023,0.0043
		
		observing.check_point_offset_need(use_offs=True)
		
		mock_offset_read.assert_called_once()
		mock_apply_offset.assert_called_once_with(0.023,0.0043, units='deg')
"""
@patch('filter_wheel_control.change_filter')
class test_change_filter_loop(unittest.TestCase):

	def setUp(self):
	
		self.instrument_info = observing.connect_to_instruments()
	

	def test_filter_wheel_timeout(self, mock_change):
	
		mock_change.side_effect = ValueError()

		expectedN = -6
		expectedS = -6

		actualN, actualS = observing.change_filter_loop('RX','RX')
		self.assertEqual(expectedN, actualN)
		self.assertEqual(expectedS, actualS)


	# Note mock doesn't support coroutines (which is what the change filter is
	# in the create task function. Haven't yet worked out how to unit test this
	def test_filter_wheel_change_ok(self, mock_change):

		#mock_change = observing.asyncio.coroutine
		#mock_coroutine.return_value = True
		expectedN = 0
		expectedS = 0

		actualN, actualS = observing.change_filter_loop('RX','RX')
		self.assertEqual(expectedN, actualN)
		self.assertEqual(expectedS, actualS)
"""

#class test_



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
class test_roof_open_check(unittest.TestCase):

	def test_fail_get_roof_dict(self, mock_roof_status):

		mock_roof_status.side_effect = observing.plc.PLC_ERROR

		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.roof_open_check())
			logging_actual_response2 = cm.output[0].split(':')[0]
			#logging_actual_response2 = cm.output[1].split(':')[0]
		#self.assertEqual(logging_actual_response1, 'INFO') #mentions same coords
		self.assertEqual(logging_actual_response2, 'CRITICAL') #final message

		mock_roof_status.assert_called_once()

	def test_get_dict_roof_open(self, mock_roof_status):

		mock_roof_status.return_value = {'Roof_Open':True}

		expected = True
		actual = observing.roof_open_check()
		self.assertEqual(expected,actual)

	@patch("subprocess.run")
	def test_roof_closed_error_opening(self,mock_process, mock_roof_status):

		mock_roof_status.return_value = {'Roof_Open':False}

		mock_process.side_effect = observing.subprocess.TimeoutExpired


		with self.assertLogs(level='ERROR') as cm:
			observing.logging.getLogger().error(observing.roof_open_check())
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'WARNING') #mentions same coords
		self.assertEqual(logging_actual_response2, 'ERROR') #final message

	@patch("subprocess.run")
	def test_roof_closed_ok_opening(self, mock_process, mock_roof_status):

		mock_roof_status.return_value = {'Roof_Open':False}

		actual = observing.roof_open_check()
		expected = True
		self.assertEqual(expected,actual)

@patch("observing.roof_open_check")
@patch("tcs_control.get_tel_target") #01 09 34.19 -46 15 56.1
class test_go_to_target(unittest.TestCase):

	def setUp(self):
	
		self.test_returned_coords =['21 27 38.2', '-45 54 31', '+41 07 02.2',
			'+55 50 55', '234 41 45']

	def test_valid_coords_false(self, mock_tel_target, mock_roof_check):

		test_coords = ['df af ag','fdda sfd fa']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_check.return_value = True

		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(
				test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'ERROR') # from wrong coords
		self.assertEqual(logging_actual_response2, 'INFO') #final message

		mock_tel_target.assert_called_once()
		mock_roof_check.assert_called_once()

	def test_same_coords_need_to_change_false(self,mock_tel_target,
			mock_roof_check):
	
		test_coords = ['21 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		
		mock_roof_check.return_value = True
		
		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(
				test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO') #mentions same coords
		self.assertEqual(logging_actual_response2, 'INFO') #final message

		mock_tel_target.assert_called_once()
		mock_roof_check.assert_called_once()

	@patch("observing.send_coords")
	def test_got_status_all_conditions_ok(self, mock_send_coords,
			mock_tel_target, mock_roof_check):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_check.return_value = True

		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(
					test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
		self.assertEqual(logging_actual_response1, 'INFO') #roof is open
		self.assertEqual(logging_actual_response2, 'INFO') #coords pass ok

		mock_tel_target.assert_called_once()
		mock_roof_check.assert_called_once()
		mock_send_coords.assert_called_once()

	@patch("observing.send_coords")
	def test_send_coords_timeout_one_error(self, mock_send_coords,
			mock_tel_target, mock_roof_check):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_send_coords.side_effect = [observing.timeout_decorator.TimeoutError,
			'ok']
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_check.return_value = True

		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(
				test_coords))
			logging_actual_response2 = cm.output[0].split(':')[0]
			logging_actual_response3 = cm.output[1].split(':')[0]
		#self.assertEqual(logging_actual_response1, 'INFO') #roof is open
		self.assertEqual(logging_actual_response2, 'ERROR') #coords not passed ok
		self.assertEqual(logging_actual_response3, 'INFO') #coords passed ok
		

		mock_tel_target.assert_called_once()
		mock_roof_check.assert_called_once()
		mock_send_coords.assert_called()
		self.assertEqual(mock_send_coords.call_count,2)

	@patch("observing.send_coords")
	def test_send_coords_timeout_too_many_attempts(self, mock_send_coords,
			mock_tel_target, mock_roof_check):

		test_coords = ['22 27 38.2', '-45 54 31']
		mock_send_coords.side_effect = [observing.timeout_decorator.TimeoutError,
				observing.timeout_decorator.TimeoutError,
				observing.timeout_decorator.TimeoutError]
		mock_tel_target.return_value = self.test_returned_coords
		mock_roof_check.return_value = True

		with self.assertLogs(level='INFO') as cm:
			observing.logging.getLogger().info(observing.go_to_target(
			test_coords))
			logging_actual_response1 = cm.output[0].split(':')[0]
			logging_actual_response2 = cm.output[1].split(':')[0]
			logging_actual_response3 = cm.output[-2].split(':')[0]
		self.assertEqual(logging_actual_response1, 'ERROR') #roof is open
		self.assertEqual(logging_actual_response2, 'ERROR') #coords pass ok
		self.assertEqual(logging_actual_response3, 'CRITICAL')
	

		mock_tel_target.assert_called_once()
		mock_roof_check.assert_called_once()
		mock_send_coords.assert_called()
		self.assertEqual(mock_send_coords.call_count,2)

"""
class test_send_coords(unittest.TestCase):
covered by the tests in go to target
"""

@patch("filter_wheel_control.filter_wheel_startup")
@patch("focuser_control.get_focuser_stored_config")
@patch("focuser_control.startup_focuser")
class test_connect_to_instruments(unittest.TestCase):

	def setUp(self):

		self.config_dict = {'Nickname': 'FocusLynx FocSOUTH',
		'Max Pos': '125440', 'DevTyp': 'OE', 'TComp ON': '0',
		'TempCo A': '+0086', 'TempCo B': '+0086', 'TempCo C': '+0086',
		'TempCo D': '+0000', 'TempCo E': '+0000', 'TCMode': 'A',
		'BLC En': '0', 'BLC Stps': '+40', 'LED Brt': '075', 'TC@Start': '0'}

		self.focuser_config_file = {'focuser_name': 'focuser1-south',
			'focuser_no': 1, 'port_name': 'focus1', 'baud_rate': 115200,
			'data_bits': 8, 'stop_bits': 1, 'parity': 'N', 'device_type': 'OB',
			'LED_brightness': 10, 'center_position': 56000, 'min_position': 0,
			'max_position': 112000, 'temp_compen': False,
			'temp_compen_mode': 'A', 'temp_compen_at_start': False,
			'temp_coeffA': 86, 'temp_coeffB': 46, 'temp_coeffC': 74,
			'temp_coeffD': 23, 'temp_coeffE': 23, 'backlash_compen': 1,
			'backlash_steps': 10}

		self.wheel_config_file = {'baud_rate':19200,'data_bits':8,
			'stop_bits':1, 'parity':'N',
		'no_of_filters': 8,
		'1':'RX', '2':'GX','3':'BX','4':'WX', '5':'IX','6':'BLANK',
		'7':'BLANK','8':'BLANK', '9':'BLANK'}

	def test_all_ok(self, mock_focus_startup, mock_focuser_config, mock_wheel_start):

		mock_focus_startup.return_value = 1, 'focus1'
		mock_focuser_config.return_value = self.config_dict
		mock_wheel_start.return_value = 'port1', self.wheel_config_file


		expected = ([1,'focus1',self.config_dict],[1,'focus1',self.config_dict],
		 self.wheel_config_file, 'port1', self.wheel_config_file, 'port1')

		actual = observing.connect_to_instruments()
		self.assertEqual(expected,actual)

"""
# Can't really unit test whether not the focusers/filterwheel shutdown, is more
 of a system test. The function that are called by this particualar function
 is tested elsewhere
class test_shutdown_instruments()
"""

class test_get_image_type(unittest.TestCase):

	def test_object(self):

		expected = 'OBJECT'
		actual = observing.get_image_type('sdfsdjf')

		self.assertEqual(expected,actual)


	def test_bias(self):

		expected = 'BIAS'
		actual1 = observing.get_image_type('BIAS_standard')
		actual2 = observing.get_image_type('bias_test')
		actual3 = observing.get_image_type('Bias_123')

		self.assertEqual(expected,actual1)
		self.assertEqual(expected,actual2)
		self.assertEqual(expected,actual3)

	def test_flat(self):

		expected = 'FLAT'
		actual1 = observing.get_image_type('FLAT_standard')
		actual2 = observing.get_image_type('flat_test')
		actual3 = observing.get_image_type('Flat_123')

		self.assertEqual(expected,actual1)
		self.assertEqual(expected,actual2)
		self.assertEqual(expected,actual3)

	def test_dark(self):

		expected = 'DARK'
		actual1 = observing.get_image_type('DARK_standard')
		actual2 = observing.get_image_type('dark_test')
		actual3 = observing.get_image_type('Dark_123')

		self.assertEqual(expected,actual1)
		self.assertEqual(expected,actual2)
		self.assertEqual(expected,actual3)

	def test_thermal(self):

		expected = 'THERMAL'
		actual1 = observing.get_image_type('THERMAL_standard')
		actual2 = observing.get_image_type('therm_test')
		actual3 = observing.get_image_type('Ther_123')

		self.assertEqual(expected,actual1)
		self.assertEqual(expected,actual2)
		self.assertEqual(expected,actual3)


@patch("connect_database.match_target_id")
class test_get_next_target_info(unittest.TestCase):

	#XAMI041116.67-392440.1
	def setUp(self):

		self.mock_cursor = 'test_cursor'
		self.targ_id = 'XAMI041116.67-392440.1'
		self.targ_name = 'WASP0411-39'
		self.tar_row = [('XAMI041116.67-392440.1', 'WASP0411-39', '04:11:16.67',
		 '-39:24:40.1', 'EB', 11.9, 'F1', 5379.288, 14.80612, 0.48, 0.34, 0.025,
		  0.033, 0.49, 'Dbl*')]

		self.multi_tar_row = [('XAMI041116.67-392440.1', 'WASP0411-39', '04:11:16.67',
		 '-39:24:40.1', 'EB', 11.9, 'F1', 5379.288, 14.80612, 0.48, 0.34, 0.025,
		  0.033, 0.49, 'Dbl*'),('XAMI041116.67-392440.1', 'WASP0411-39', '04:11:16.67',
		 '-39:24:40.1', 'EB', 11.9, 'F1', 5379.288, 14.80612, 0.48, 0.34, 0.025,
		  0.033, 0.49, 'Dbl*')]

	def test_none_returned(self, mock_return):

		mock_return.return_value = []

		with self.assertLogs(level='WARNING') as cm:
			observing.logging.getLogger().info(observing.get_next_target_info(
				self.targ_id, self.mock_cursor))
			logging_actual_response1 = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response1, 'WARNING')

		#expected_name = 'XAMI041116.67-392440.1'
		#actual_tar = observing.get_next_target_info(self.targ_id,
		#	self.mock_cursor)

		mock_return.assert_called_once()

	def test_multiple_rows(self, mock_return):

		mock_return.return_value = self.multi_tar_row
	
		with self.assertLogs(level='WARNING') as cm:
			observing.logging.getLogger().info(observing.get_next_target_info(
				self.targ_id, self.mock_cursor))
			logging_actual_response1 = cm.output[0].split(':')[0]
		self.assertEqual(logging_actual_response1, 'WARNING')

		expected_name = self.targ_name
		actual_tar = observing.get_next_target_info(self.targ_id,
			self.mock_cursor)
			
		self.assertEqual(expected_name, actual_tar.name)

		self.assertEqual(mock_return.call_count,2)

#@patch("settings_and_error_codes.run_camera_cooling")
@patch("tcs_control.camstart")
class test_evening_startup(unittest.TestCase):

	def test_no_cooling(self, mock_tcs):

		#mock_run = False
		mock_tcs.return_value = 'Hi'
		observing.evening_startup(False)
		mock_tcs.assert_not_called()

	def test_yes_cooling(self, mock_tcs):

		mock_tcs.return_value = 'Hi'
		observing.evening_startup(True)
		mock_tcs.assert_called_once()

@patch("tcs_control.stopwasp")
class test_morning_shutdown(unittest.TestCase):

	def test_no_cooling(self, mock_tcs):

		#mock_run = False
		mock_tcs.return_value = 'Hi'
		observing.morning_shutdown(False)
		mock_tcs.assert_not_called()

	def test_yes_cooling(self, mock_tcs):

		mock_tcs.return_value = 'Hi'
		observing.morning_shutdown(True)
		mock_tcs.assert_called_once()


@patch("getAlmanac.decide_observing_time")
class test_wait_function(unittest.TestCase):

	def test_work(self, mock_almanac):

		mock_almanac.return_value = 'daytime', 0.1112324, observing.astro_time.Time('2019-03-01')
		observing.wait_function(0.01)
		mock_almanac.assert_called_once()



@patch("observing.disconnect_database")
@patch("observing.shutdown_instruments")
@patch("observing.setup_file_logs_storage")
@patch("autoflat.do_flats_morning")
@patch("autoflat.do_flats_evening")
@patch("observing.go_to_target")
@patch("observing.take_bias_frames")
@patch("observing.roof_open_check")
@patch("observing.morning_shutdown")
@patch("getAlmanac.decide_observing_time")
@patch("observing.evening_startup")
@patch("observing.connect_to_instruments")
@patch("time.sleep")
class test_main(unittest.TestCase):

	def setUp(self):

		observing.setup_file_logs_storage()

		self.day_almanac = 'daytime', 0.1112324, observing.astro_time.Time(
			'2019-03-05 17:03:28.613')
		self.afterSunset = 'afterSunset', 0.02, observing.astro_time.Time(
			'2019-03-05 17:32:14.065')
		self.afterCivil = 'afterCivil', 0.02, observing.astro_time.Time(
			'2019-03-05 18:01:23.157')
		self.night = 'night', 0.35, observing.astro_time.Time(
			'2019-03-06 03:05:42.390')
		self.beforeCivil = 'beforeCivil', 0.015, observing.astro_time.Time(
			'2019-03-06 04:04:38.581')
		self.beforeSunrise = 'beforeSunrise', 0.00432,observing.astro_time.Time(
			'2019-03-06 04:33:25.319', format='iso')
			
		self.focuser_info = [1, 'focus1', {'Nickname': 'FocusLynx FocSOUTH',
		'Max Pos': '125440', 'DevTyp': 'OE', 'TComp ON': '0',
		'TempCo A': '+0086', 'TempCo B': '+0086', 'TempCo C': '+0086',
		'TempCo D': '+0000', 'TempCo E': '+0000', 'TCMode': 'A',
		'BLC En': '0', 'BLC Stps': '+40', 'LED Brt': '075', 'TC@Start': '0'}]

		self.wheel_config ={'baud_rate':19200,'data_bits':8,
			'stop_bits':1, 'parity':'N',
		'no_of_filters': 8,
		'1':'RX', '2':'GX','3':'BX','4':'WX', '5':'IX','6':'BLANK',
		'7':'BLANK','8':'BLANK', '9':'BLANK'}

		self.wheel_port = 'port1'


		self.instrument_connect = (self.focuser_info, self.focuser_info,
			self.wheel_config, self.wheel_port, self.wheel_config,
			self.wheel_port)
	
		self.datestr = '20190305'
		self.file_dir = 'fits_file_tests/20190305'
	
		self.tar_row = [('XAMI041116.67-392440.1', 'WASP0411-39', '04:11:16.67',
		 '-39:24:40.1', 'EB', 11.9, 'F1', 5379.288, 14.80612, 0.48, 0.34, 0.025,
		  0.033, 0.49, 'Dbl*')]
	
		self.obs_recipe = {'TAR_NAME': 'WASP0411-39', 'IMG-RA': 'N/A',
		'IMG-DEC': 'N/A', 'FILTERS': ['WX','IX'], 'FOCUS_POS': [50000,50000],
		'EXPTIME': np.array([ 1.,  1.]), 'N_PATT': np.array([0, 1]),
		'S_PATT': np.array([0, 1]), 'N_FOCUS':[50000,50000],'S_FOCUS':[50000,50000],
		'N_EXPO':[1.,1.], 'S_EXPO':[1.,1.], 'N_FILT':['WX','IX'],
		'S_FILT':['WX','IX']}
	
		self.target_info = observing.target_obj('WASP0411-39',
			coords=['04:11:16.67','-39:24:40.1'], type='EB')

	
	def test_daytime_loop_till_change(self, mock_sleep, mock_connect, mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):


		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
		self.day_almanac, self.beforeSunrise, self.day_almanac]

		observing.main()

		mock_morning_shut.assert_called_once()

	def test_after_sunset_roof_open(self, mock_sleep, mock_connect,
		mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):


		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
		self.day_almanac, self.afterSunset, self.beforeSunrise, self.day_almanac]
		
		mock_roof_check.return_value = True

		observing.main()

		mock_bias.assert_called_once()
		mock_go_target.assert_called_once()
		mock_morning_shut.assert_called_once()

	def test_after_sunset_roof_not_open(self, mock_sleep, mock_connect,
		mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):


		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
		self.day_almanac, self.afterSunset, self.afterSunset,
			self.beforeSunrise, self.day_almanac]
		
		mock_roof_check.return_value = False

		observing.main()

		mock_bias.assert_called_once()
		mock_go_target.assert_not_called()
		mock_morning_shut.assert_called_once()
		mock_go_target.assert_not_called()
		mock_morn_flat.assert_not_called()
		mock_eve_flat.assert_not_called()

	def test_after_civil_roof_not_open(self, mock_sleep, mock_connect,
		mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):


		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
			self.day_almanac, self.afterSunset, self.beforeSunrise,
			self.day_almanac]
		
		mock_roof_check.return_value = False

		observing.main()

		mock_bias.assert_called_once()
		mock_go_target.assert_not_called()
		mock_eve_flat.assert_not_called()
		mock_morn_flat.assert_not_called()
		mock_morning_shut.assert_called_once()
	
	def test_after_civil_roof_open_ok_tremain_best_field_true(self, mock_sleep,
		mock_connect, mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):


		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
		self.day_almanac, self.afterSunset, self.afterSunset,self.afterCivil,
		self.beforeSunrise, self.day_almanac]
		
		mock_roof_check.return_value = True

		observing.main()

		mock_bias.assert_called_once()
		mock_go_target.assert_called_once()
		mock_eve_flat.assert_called_once()
		mock_morn_flat.assert_not_called()
		mock_morning_shut.assert_called_once()

	def test_after_civil_roof_open_ok_tremain_best_field_false(self, mock_sleep,
		mock_connect, mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):


		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
		self.day_almanac, self.afterCivil,
		self.beforeSunrise, self.day_almanac]
		
		mock_roof_check.return_value = True

		observing.main()

		mock_bias.assert_not_called()
		mock_go_target.assert_called_once()
		mock_eve_flat.assert_called_once()
		mock_morn_flat.assert_not_called()
		mock_morning_shut.assert_called_once()

	def test_after_civil_roof_open_not_ok_tremain_best_field_true(self, mock_sleep,
		mock_connect, mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):


		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
		self.day_almanac, #self.afterSunset, self.afterSunset,
		('afterCivil', 0.001, observing.astro_time.Time(
			'2019-03-05 18:01:23.157')),
		self.beforeSunrise, self.day_almanac]
		
		mock_roof_check.return_value = True

		observing.main()

		mock_bias.assert_not_called()#assert_called_once()
		mock_go_target.assert_not_called()
		mock_eve_flat.assert_not_called()
		mock_morn_flat.assert_not_called()
		mock_morning_shut.assert_called_once()


	def test_night_roof_closed(self, mock_sleep,
		mock_connect, mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):

		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
		self.day_almanac, self.night, self.night, self.night,
		self.beforeSunrise, self.day_almanac]
		
		mock_roof_check.return_value = False

		observing.main()

		mock_bias.assert_not_called()#assert_called_once()
		mock_go_target.assert_not_called()
		mock_eve_flat.assert_not_called()
		mock_morn_flat.assert_not_called()
		mock_morning_shut.assert_called_once()

	@patch("observing.take_exposure")
	@patch("observing.get_observing_recipe")
	@patch("observing.get_next_target_info")
	def test_night_roof_open(self, mock_target, mock_obs_recipe,mock_exposure,
		mock_sleep, mock_connect, mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):

		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
		self.day_almanac, self.night,
		self.beforeSunrise, self.day_almanac]
		
		mock_roof_check.return_value = True
		
		mock_target.return_value = self.target_info
		mock_obs_recipe.return_value = self.obs_recipe

		observing.main()

		mock_bias.assert_not_called()#assert_called_once()
		mock_go_target.assert_called_once_with(self.target_info.ra_dec)
		mock_eve_flat.assert_not_called()
		mock_morn_flat.assert_not_called()
		mock_morning_shut.assert_called_once()



	def test_before_civil_roof_not_open(self, mock_sleep, mock_connect,
		mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):


		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
			self.day_almanac, self.beforeCivil, self.beforeSunrise,
			self.day_almanac]
		
		mock_roof_check.return_value = False

		observing.main()

		mock_bias.assert_not_called()
		mock_go_target.assert_not_called()
		mock_eve_flat.assert_not_called()
		mock_morn_flat.assert_not_called()
		mock_morning_shut.assert_called_once()


	def test_before_civil_roof_open_ok_tremain_(self, mock_sleep,
		mock_connect, mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):


		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
		self.day_almanac, self.beforeCivil,
		self.beforeSunrise, self.day_almanac]
		
		mock_roof_check.return_value = True

		observing.main()

		mock_bias.assert_not_called()
		mock_go_target.assert_called_once()
		mock_eve_flat.assert_not_called()
		mock_morn_flat.assert_called_once()
		mock_morning_shut.assert_called_once()


	def test_before_civil_roof_open_not_ok_tremain(self, mock_sleep,
		mock_connect, mock_evening_start,
		mock_almanac, mock_morning_shut, mock_roof_check, mock_bias,
		mock_go_target, mock_eve_flat, mock_morn_flat, mock_sort_files,
		mock_instrument_shut, mock_disconnect):


		mock_sleep = observing.time.sleep(0.001)
		mock_connect.return_value = self.instrument_connect
		mock_sort_files.return_value = self.datestr, self.file_dir
		
		mock_almanac.side_effect = [self.day_almanac, self.day_almanac,
		self.day_almanac, #self.afterSunset, self.afterSunset,
		('beforeCivil', 0.001, observing.astro_time.Time(
			'2019-03-05 18:01:23.157')),
		self.beforeSunrise, self.day_almanac]
		
		mock_roof_check.return_value = True

		observing.main()

		mock_bias.assert_not_called()#assert_called_once()
		mock_go_target.assert_not_called()
		mock_eve_flat.assert_not_called()
		mock_morn_flat.assert_not_called()
		mock_morning_shut.assert_called_once()


	def tearDown(self):

		observing.disconnect_database()



if __name__ =='__main__':
	unittest.main()