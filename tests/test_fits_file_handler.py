"""
test_fits_file_handler.py

 Contains the unit tests for the das fits file handler.

"""
import unittest
from unittest.mock import patch
import das_fits_file_handler as das
from astropy.io import fits

@patch("subprocess.run")
class test_check_file_process(unittest.TestCase):

	def setUp(self):
	
		self.direct_list = b"/data/das1/NORMAL/DAS1_001651071.fts\n"\
			b"/data/das1/NORMAL/DAS1_001650924.fts\n"\
			b"/data/das1/NORMAL/DAS1_001650969.fts\n"\
			b"/data/das1/NORMAL/DAS1_001651028.fts\n"\
			b"/data/das1/NORMAL/DAS1_001651075.fts\n"

		#self.sub1 = subprocess.CompleteProcess()

	def test_wrong_das_no(self, mock_sub):
	
		with self.assertRaises(ValueError):
			das.check_file_process('BIAS',9)
		
		mock_sub.not_called()
		
	def test_wrong_image_type(self, mock_sub):

		with self.assertRaises(ValueError):
			das.check_file_process(2345,1)
		
		mock_sub.assert_not_called()

	def test_no_direct_match(self, mock_sub):
	
		mock_sub.return_value = das.subprocess.CompletedProcess(args = ['ssh',
			'wasp@das1', 'ls', '/data/das1/NORMAL/DAS1_*.fts'], stdout=b'',
			stderr=b'ls: No match.\n', returncode=1)
			
		expected_path = None
		actual_path = das.check_file_process('OBJECT',1)
		
		self.assertEqual(expected_path, actual_path)

		mock_sub.assert_called_once()

	def test_no_direct_match_error(self, mock_sub):
	
		mock_sub.return_value = das.subprocess.CompletedProcess(args = ['ssh',
			'wasp@das1', 'ls', '/data/das1/NORMAL/DAS1_*.fts'], stdout=b'',
			stderr=b'BROKEN', returncode=1)
			

		with self.assertRaises(RuntimeError):
			das.check_file_process('OBJECT',1)

		mock_sub.assert_called_once()

	def test_ok_subprocess_response(self, mock_sub):
		
		mock_sub.return_value = das.subprocess.CompletedProcess(args = ['ssh',
			'wasp@das1', 'ls', '/data/das1/NORMAL/DAS1_*.fts'], 
			stdout=self.direct_list, stderr=b'', returncode=0)

		
		expected = '/data/das1/NORMAL/DAS1_001651075.fts'
		actual = das.check_file_process('OBJECT',1)
		
		self.assertEqual(expected, actual)

		mock_sub.assert_called_once()

@patch('os.listdir')
@patch('subprocess.run')
class test_get_last_fits_header(unittest.TestCase):

	def setUp(self):
	
		self.direct_list = b"CCD1_0000000001.fits\nCCD1_0000000002.fits\n"

	def test_wrong_das_no(self, mock_sub, mock_dirlist):
	
		with self.assertRaises(ValueError):
			das.get_last_fits_header(9)
		
		mock_sub.assert_not_called()
		mock_dirlist.assert_not_called()

	def test_no_files(self, mock_sub, mock_dirlist):
	
		mock_dirlist.return_value = ['20190205', '20190204']
		
		mock_sub.return_value = das.subprocess.CompletedProcess(
			args='ls CCD3*.fits', returncode=2, stdout=b'', 
			stderr=b'ls: cannot access CCD3*.fits: No such file or '\
			b'directory\n')
		
		expected_file = None
		expected_date_folder = '20190205'
		actual_file, actual_date_folder = das.get_last_fits_header(1)
		self.assertEqual(expected_file, actual_file)
		self.assertEqual(expected_date_folder, actual_date_folder)
		
		mock_dirlist.assert_called_once()
		mock_sub.assert_called_once()
		
	
	def test_all_ok(self, mock_sub, mock_dirlist):
		
		mock_dirlist.return_value = ['20190205', '20190204']
		
		mock_sub.return_value = das.subprocess.CompletedProcess(
			args='ls CCD1*.fits', returncode=2, stdout=self.direct_list, 
			stderr=b'')
			
			
		expected_file = 'CCD1_0000000002.fits'
		expected_date_folder = '20190205'
		actual_file, actual_date_folder = das.get_last_fits_header(1)
		self.assertEqual(expected_file, actual_file)
		self.assertEqual(expected_date_folder, actual_date_folder)
		
		mock_dirlist.assert_called_once()
		mock_sub.assert_called_once()
		
@patch('das_fits_file_handler.check_file_process')
class test_get_last_files(unittest.TestCase):


	def setUp(self):
		self.file_arr = ['/data/das1/FLAT/DAS1_Flat_001650822.fts',
			'/data/das1/BIAS/DAS1_Bias_001651096.fts',
			None,
			None,
			'/data/das1/NORMAL/DAS1_001651075.fts']
	
	def test_makes_dict(self, mock_check_file):
	
		mock_check_file.side_effect = self.file_arr
		
		expected_dict = dict({"FLAT":'/data/das1/FLAT/DAS1_Flat_001650822.fts',
			'BIAS':'/data/das1/BIAS/DAS1_Bias_001651096.fts',
			'THERMAL':None,
			'DARK': None,
			'OBJECT': '/data/das1/NORMAL/DAS1_001651075.fts'})
		
		actual = das.get_last_files(1)
		
		self.assertEqual(expected_dict, actual)
		
		self.assertEqual(mock_check_file.call_count,5)
		
		
class test_new_header_dict(unittest.TestCase):

	def setUp(self):
	
		self.dheader = fits.Header()
		self.dheader['XFACTOR']=1
		self.dheader['YFACTOR']=1
		self.dheader['LST']=' 7:38:38'
		self.dheader['DATE-OBS']='2019-01-30'
		self.dheader['UTSTART']='21:36:04.24'
		self.dheader['UTMIDDLE']='21:36:09.24' 
		self.dheader['RA']= '19:37:40.11'
		self.dheader['DEC']= '-0:00:33.8'
		self.dheader['CCDSPDH']= 1
		self.dheader['CCDSPDV']= 16
		self.dheader['ZENDIST']=  147.66
		self.dheader['AIRMASS']= -1.185
		self.dheader['MOONPHAS']=21.12
		self.dheader['MOONALT']= -26.946
		self.dheader['MOONDIST']=42.163

	def test_get_info_dict(self):
		
		expected = dict({
			'XFACTOR':(self.dheader['XFACTOR'],'Camera x binning factor'),
			'YFACTOR':(self.dheader['YFACTOR'], 'Camera y binning factor'),
			'LST'	 :(self.dheader['LST'], 'Local sidereal time'),
			'DASSTART':('2019-01-30T21:36:04.240','Start time from DAS machine'),
			'DASMIDD' :('2019-01-30T21:36:09.240', 'Exposure midpoint from DAS machine'),
			'IMAG-RA' :(self.dheader['RA'],'Nominal image center J2000 RA'),
			'IMAG-DEC':(self.dheader['DEC'],'Nominal image center J2000 Dec'),
			'CCDSPDH' : (self.dheader['CCDSPDH'],'CCD Readout time / pixel (usecs)'),
			'CCDSPDV' : (self.dheader['CCDSPDV'], 'CCD Access time / row (usecs)'),
			'ZENDIST' : (self.dheader['ZENDIST'],'Zenith Distance, degrees'),
			'AIRMASS' : (self.dheader['AIRMASS'],'Airmass calculation'),
			'MOONPHAS': (self.dheader['MOONPHAS'],'Percentage of full'),
			'MOONALT' : (self.dheader['MOONALT'], 'Degrees above horizon'),
			'MOONDIST': (self.dheader['MOONDIST'], 'Degrees from image center')
			})
		actual = das.new_header_dict(self.dheader)
		self.assertEqual(expected,actual)			


@patch('subprocess.run')
@patch('os.path.isdir')
class test_sort_data_output_dir(unittest.TestCase):

	def test_invalid_imagetype(self, mock_os,mock_subprocess):
	
		with self.assertRaises(ValueError):
			das.sort_data_output_dir('turkey','.')
			
		mock_subprocess.not_called()
		mock_os.not_called()
		
	def test_flat_cant_make_dir(self, mock_os, mock_subprocess):
	
		mock_os.return_value = False
		mock_subprocess.return_value = das.subprocess.CompletedProcess(
			args=['mkdir','flats'], returncode = 1,
			stderr = "mkdir: cannot create directory '/etc/foo': "\
			"Permission denied")
			
		with self.assertRaises(RuntimeError):
			das.sort_data_output_dir('FLAT','.')
		
		mock_os.assert_called_once_with('./flats')
		mock_subprocess.assert_called_once()

	def test_bias_cant_make_dir(self, mock_os, mock_subprocess):
	
		mock_os.return_value = False
		mock_subprocess.return_value = das.subprocess.CompletedProcess(
			args=['mkdir','bias'], returncode = 1,
			stderr = "mkdir: cannot create directory '/etc/foo': "\
			"Permission denied")
			
		with self.assertRaises(RuntimeError):
			das.sort_data_output_dir('BIAS','.')
		
		mock_os.assert_called_once_with('./bias')
		mock_subprocess.assert_called_once()
		

	def test_thermal_cant_make_dir(self, mock_os, mock_subprocess):
	
		mock_os.return_value = False
		mock_subprocess.return_value = das.subprocess.CompletedProcess(
			args=['mkdir','thermal'], returncode = 1,
			stderr = "mkdir: cannot create directory '/etc/foo': "\
			"Permission denied")
			
		with self.assertRaises(RuntimeError):
			das.sort_data_output_dir('THERMAL','.')
		
		mock_os.assert_called_once_with('./thermal')
		mock_subprocess.assert_called_once()
		
	def test_dark_cant_make_dir(self, mock_os, mock_subprocess):
	
		mock_os.return_value = False
		mock_subprocess.return_value = das.subprocess.CompletedProcess(
			args=['mkdir','dark'], returncode = 1,
			stderr = "mkdir: cannot create directory '/etc/foo': "\
			"Permission denied")
			
		with self.assertRaises(RuntimeError):
			das.sort_data_output_dir('DARK','.')
		
		mock_os.assert_called_once_with('./dark')
		mock_subprocess.assert_called_once()
		
	def test_object_cant_make_dir(self, mock_os, mock_subprocess):
	
		mock_os.return_value = False
		mock_subprocess.return_value = das.subprocess.CompletedProcess(
			args=['mkdir','normal'], returncode = 1,
			stderr = "mkdir: cannot create directory '/etc/foo': "\
			"Permission denied")
			
		with self.assertRaises(RuntimeError):
			das.sort_data_output_dir('OBJECT','.')
		
		mock_os.assert_called_once_with('./normal')
		mock_subprocess.assert_called_once()

	def test_flat_ok_path(self, mock_os, mock_subprocess):
	
		mock_os.return_value = True
		expected = './flats/'
		
		actual = das.sort_data_output_dir('FLAT','.')
		self.assertEqual(expected,actual)
		
		mock_os.assert_called_once()
		mock_subprocess.not_called()

	def test_bias_ok_path(self, mock_os, mock_subprocess):
	
		mock_os.return_value = True
		expected = './bias/'
		
		actual = das.sort_data_output_dir('BIAS','.')
		self.assertEqual(expected,actual)
		
		mock_os.assert_called_once()
		mock_subprocess.not_called()
		

	def test_thermal_ok_path(self, mock_os, mock_subprocess):
	
		mock_os.return_value = True
		expected = './thermal/'
		
		actual = das.sort_data_output_dir('THERMAL','.')
		self.assertEqual(expected,actual)
		
		mock_os.assert_called_once()
		mock_subprocess.not_called()

	def test_dark_ok_path(self, mock_os, mock_subprocess):
	
		mock_os.return_value = True
		expected = './dark/'
		
		actual = das.sort_data_output_dir('DARK','.')
		self.assertEqual(expected,actual)
		
		mock_os.assert_called_once()
		mock_subprocess.not_called()

	def test_object_ok_path(self, mock_os, mock_subprocess):
	
		mock_os.return_value = True
		expected = './normal/'
		
		actual = das.sort_data_output_dir('OBJECT','.')
		self.assertEqual(expected,actual)
		
		mock_os.assert_called_once()
		mock_subprocess.not_called()

""" 
@patch('fits.open')
@patch('subprocess.run')
class test_copy_over_file(unittest.TestCase):

	
	def test_wrong_das_no(self, mock_sub, mock_dirlist):
	
		with self.assertRaises(ValueError):
			das.get_last_fits_header(9)
		
		mock_sub.assert_not_called()
		mock_dirlist.assert_not_called()

"""
