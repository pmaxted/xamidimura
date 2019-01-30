"""
observing.py


	*** Very much still work-in-progress, and may not permenantly remain under 
		this name. ***
	
	Purpose of this script is to carry out the functions required for observing,
	 e.g. startup instruments and carry out the required initialisation, obtain 
	 target infomation for a scheduled target.
		
	CURRENTLY the obslog2 table in the database is overwritten each time the 
	 main() function is run, because I did want to fill the database with 
	 rubbish while testing.
		
	Unittests and proper logging will needed to be put in place throughout
	
	
	CURRENT CLASSES
	----------------------------------------------------------------------
	exposure_obj
	----------------------------------------------------------------------
	To be used to get all the information for a particular exposure in one 
	 place, information such as exposure time, filter, etc.
	
	- __init__(self,exptime, filter_name,image_type, CCD_no, filter_wheel_name)
	
	- set_start_time(self)
	
	
	
	CURRENT FUNCTIONS:
	
	----------------------------------------------------------------------
	Used by other functions
	----------------------------------------------------------------------
	
	- get_current_UTC_time_in_isot_format()
	
	- get_current_weather(logfile_loc = 'logfiles/weather.log')
	
	- get_fits_header_info(focuser_config,focuser_position, weather_list, 
		expose_info, target_info)
	
	- get_obslog_info(fits_info_dict, CCDno, IMAGE_ID, status, savefile=True)
	
	- get_next_file_number(CCDno, fits_file_dir = 'fits_file_tests/')
	
	- get_observing_recipe(target_name, path = 'obs_recipes/')
	
	- take_exposure(obs_recipe, image_type, target_info, timeout_time =
		set_err_codes.telescope_coms_timeout)
	
	- [async] change_filters(filter_name, ifw_port, ifw_config,status)
	
	- exposure_TCS_response(expObN, expObS, timeout)
	
	- exposureTCSerrorcode(statN,statS, exptime)
	
	- go_to_target(coordsArr)
	
	- send_coords(coords,equinox='J2000')
	
	----------------------------------------------------------------------
	Main Function
	----------------------------------------------------------------------

	- main()


"""
import time
import sqlite3
import connect_database
import focuser_control as fc
import filter_wheel_control as fwc
import common
from astropy.io import fits
from astropy import time as astro_time
import subprocess
import os
import fnmatch
import logging
import numpy as np
import asyncio
import timeout_decorator
import tcs_control as tcs
import roof_control_functions as rcf
import PLC_interaction_functions as plc
import settings_and_error_codes as set_err_codes
import math
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fileHand = logging.FileHandler(filename = \
	set_err_codes.LOGFILES_DIRECTORY+'observingScript.log', mode = 'w')
fileHand.setLevel(logging.INFO)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s - '\
		'%(message)s','%Y-%m-%d_%H:%M:%S_UTC')
fileHand.setFormatter(formatter)
logger.addHandler(fileHand)


def get_current_UTC_time_in_isot_format():

	"""
	Acquires the current time from the system clock. Is in UTC scale and is 
		formatted in 'isot' format, i.e
		2001-01-02T03:04:05.678
		
	RETURN
		
		a = The correctly formatted time
	
	"""
	a = astro_time.Time.now()
	a.format = 'isot'

	return a

class exposure_obj(object):
	"""
		To be used to get all the information for a particular exposure in one
		 place, information such as exposure time, filter, etc.
	"""
	def __init__(self,exptime, filter_name,image_type, CCD_no,
		filter_wheel_name,file_num):
		"""
		Set up the object
		"""
		self.exptime = exptime
		self.filter = filter_name
		self.image_type = image_type
		self.CCD = CCD_no
		self.filter_wheel_name = filter_wheel_name
		self.file_num = file_num

	def set_start_time(self):
		"""
		When a exposure is started, use this function to get the current time 
		 and store it as the start time of the exposure. Also converts this to 
		 MJD, and calculate the mid exposure time. All stored in the object. 
		 Mid exposure time is calculate from the start time and half the 
		 specified exposure length.
		"""
	
		self.date_obs = get_current_UTC_time_in_isot_format()
		self.mjd_obs = self.date_obs.mjd

		self.mid_exp = self.date_obs + astro_time.TimeDelta(self.exptime/2.0,
		format='sec')
		self.mjd_mid = self.mid_exp.mjd

class target_obj(object):
	"""
	target object contain information about the target. Will include name, 
	 ra/dec coords and the type. Type is set to 'EB' by default (e.g. Eclipsing 
	 binary) but could in principle be anything. Might put some retrictions on 
	 at some point (i.e. must be a string)
	"""
	def __init__(self, name, coords, type ='EB'):

		self.name = name
		self.ra_dec = coords
		self.type = type

def get_current_weather(logfile_loc = 'logfiles/weather.log'):

	"""
	If the weather goes to a weather.log file on tcs, will want this script just
	 to read the last line of the weather log file. Will have to come up with 
	 something incase the the weather info cannot be retrieved
	- although not getting weather info would be a safety issue
		
	Uses python's subproccess to run a tail command to find the last line 
	 (of 107 bytes) in the log file. The input is reversed by the -r flag, so 
	 it actually takes the first 107 bytes
		
	
	Will assume the weather info is retrive as a string in the following 
		format...
	
	2454144.18988  12 187  23.8  23  826.0   2 DRY  -44.5 DRY ------------ 
		14.70 -99.99 -99.99  41 -99 -99 1.61
	
	and shows the following information:
	
	Col   Description
	1 = Julian day
	2 = Wind strength (km/s)
	3 = Wind direction (degrees East of North)
	4 = Internal temperature (˚C) [Vaisala]
	5 = Internal relative humidity (%) [Vaisala]
	6 = Pressure (mb)
	7 = Heater setting [Vaisala]
	8 = Vaisala rain detector [DRY/RAIN]
	9 = Relative sky tempurature (˚C) [Boltwood]
	10 = Boltwood rain detector [DRY/WET]
	11 = Weather daemon alert flags (see below)
	12 = External temperature (˚C)
	13 = unused auxillary temperature
	14 = unused auxillary temperature
	15 = External relative humidity (%)
	16 = unused auxillary temperature
	17 = unused auxillary temperature
	18 = Dew point (˚C)
	
	Weather daemon flags
	1 - T = Internal temperature max
	2 - C = Internal tempeerature min
	3 - H = Internal humidity
	4 - W = Wind
	5 - R = Boltwood rain detector
	6 - D = Dew point
	7 - T = External temperature max
	8 - C = External temperature min
	9 - H = External humidity
	10 - S = Storm
	11 - K = Cloud
	12 - N = Sun above horizon
	
	
	PARAMETERS
	
		logfile_loc = directory to where the weather log file is. Will need to 
			update once file structure is sorted
	
	RETURN
	
		retreived_line =  list of weather values, with each value stored as a 
			string
	
	
	"""

	# use tail to find the last 107 bytes of the weather log file. The -c means
	#  it searches bytes, and -r means the input is reversed -hopefully this
	#  will make it quicker for larger files, but not tested
	sub1 = subprocess.Popen(['tail','-r','-c','107',logfile_loc],
		stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	outp = sub1.communicate()
	if len(outp[0]) > 2:
		retrieved_line = outp[0].decode('utf-8')
	else:
		print('INFO: Error reading weather log file')
	
	retrieved_line = retrieved_line.split()

	return retrieved_line


def get_fits_header_info(focuser_config,focuser_position, weather_list,
		expose_info, target_info, telescope_pointing):

	"""
	This function would get all the info required for an entry into for the 
	 fits header. Most of this info is also used in the observing log database 
	 entry.
	 
	 ** Not worked out all the details yet ** 
	Some strings used as place holders, most are from the target infomation
	 
	 
	 PARAMETERS:
	 
		focuser_config = a dictionary construction from the configuration 
			settings retrived from the focuser (not the config file)
			
		focuser_pos = number passed from elsewhere (or could endup being the 
			full dictionary)
		
		weather_list = list containing values for different weather 
			observations. See get_current_weather() for more info in what each
			represents
			
		expose_info = An exposure_obj, contain infomation such as the exposure
			time, filter, and exposure start time.
			
		target_info = will pass the required target infomation.
		
	RETURN:
	
		fits_info_dict = the dictionary that is formed from all the infomation.
	
	"""
	try:
		cam_temp = tcs.get_camera_status()[2]
	except:
		cam_temp = 'NA'
		logger.warning('Unable to get camera temperature')
	
	# FOR FITS HEADER...
	fits_info_dict = {
		'OBSERVAT': ('SAAO', 'Observatory name'),
		'TELESCOP': ('Xamidimura', 'Telescope name'),
		'INSTRUME': (expose_info.CCD, 'CCD1-South/CCD2-North'),
		'FILTRWHL': (expose_info.filter_wheel_name, 'ifw1-South/ifw2-North'),
		'FOCUSER' : (focuser_config['Nickname'], \
									'focuser1-south/focuser2-north'),
		'DATE'    : (get_current_UTC_time_in_isot_format().value, \
									'File creation date/time (UTC)'),
		'OBJECT'  : (target_info.name, 'Target name'),
		'IMAGETYP': (expose_info.image_type, 'Flat/bias/dark/science/other'),
					
		'OBJ-RA'  : (target_info.ra_dec[0], 'Expected Target RA'),
		'OBJ-DEC' : (target_info.ra_dec[1], 'Expected Target DEC'),
		'TEL-RA'  : (telescope_pointing[0], 'Telescope RA'),
		'TEL-DEC' : (telescope_pointing[1], 'Telescope DEC'),
		'IMAG-RA' : ("Calculate", 'Nominal image position, pxl (1024,1024) J2000'),
		'IMAG-DEC': ("Calculate", 'Nominal image position, pxl (1024,1024) J2000'),
	
		'EQUINOX' :(2000, 'Used coordinate system'),
		'DATE-OBS': (expose_info.date_obs.value, \
									'Exp start CCYY-MM-DDTHH:MM:SS.sss(UTC)'),
		'MID_EXP' : (expose_info.mid_exp.value, \
									'Exp middle CCYY-MM-DDTHH:MM:SS.sss(UTC)'),
		'MJD_OBS' : (expose_info.mjd_obs, 'MJD at start'),
		'MJD_MID' : (expose_info.mjd_mid, 'MJD at mid-point'),
		'EXPTIME' : (expose_info.exptime, 'Integration time (s)'),
	
		'FILT_NAM': (expose_info.filter, 'Rx/Gx/Bx/Wx/Ix'),
		'FOCU_POS': (focuser_position, 'Position of focuser at exp. start'),
	
		'LATITUDE': ('-32:22:51', 'Site Latitude, degrees +N'),
		'LONGITUD': ('20:48:38', 'Site Longitude, degrees +E'),
		'ALTITUDE': ('1.8E+03', 'Site elevation (meters) above sea level'),
	
		'BIASSEC' : ('[2068:2148,1:2048]', 'Bias section'), # Don't know if these are correct
		'TRIMSEC' : ('[6:2053,1:2048]',	'Illuminated section'), # Taken from WASP fits file.
		#'GAIN'    : ("NOT SURE", '???'),
		'CCD_TEMP': (cam_temp, 'Camera temperature'),
	
		#"From focuser config -- Run get config everytime, or run once before hand??"
		'TEMP_COM':	(focuser_config['TComp ON'], \
									'Temperature compensation (ON=1/OFF=0)'),
		'TCOMSTRT':	(focuser_config['TC@Start'], \
								'Temperature compensation @ start (ON=1/OFF=0)'),
		'TCOMMODE': (focuser_config['TCMode']  , \
											'Temperature compensation mode'),
		'TCOM_COA': (focuser_config['TempCo A'], \
									'Temperature compensation coefficient A'),
		'TCOM_COB': (focuser_config['TempCo B'], \
									'Temperature compensation coefficient B'),
		'TCOM_COC':	(focuser_config['TempCo C'], \
									'Temperature compensation coefficient C'),
		'TCOM_COD':	(focuser_config['TempCo D'], \
									'Temperature compensation coefficient D'),
		'TCOM_COE':	(focuser_config['TempCo E'], \
									'Temperature compensation coefficient E'),
		'BCK_LASH':	(focuser_config['BLC En']  ,
									'Backlash compensation (ON =1/OFF=0)'),
		'BCK_STEP':	(focuser_config['BLC Stps'], \
									'Steps used for backlash compensation'),
		'COMMENT' : ('Weather log from: '+weather_list[0]+', '\
					+astro_time.Time(float(weather_list[0]), format='jd').isot),

		'WXTEMP'  : (weather_list[4], 'Inside ambient air temp, C'),
		'WXPRES'  : (weather_list[5], 'Atm pressure, mB'),
		'WXWNDSPD': (weather_list[1], 'Wind speed, kph'),
		'WXWNDDIR': (weather_list[2], 'Wind dir, degs E of N'),
		'WXHUMID' : (weather_list[3], 'Inside humidity, percent'),
		'WXDEW'   : (weather_list[17], 'Inside dew point, C'),
		'WXOTEMP' : (weather_list[12], 'Outside ambient air temp, C'),
		'WXOHUMID': (weather_list[15], 'Outside humidity, percent')}
	"""
	ZENDIST =               30.756 / Zenith Distance, degrees
	AIRMASS =                1.163 / Airmass calculation
	#MOONPHAS=                 80.2 / Percentage of full
	#MOONALT =               73.889 / Degrees above horizon
	#MOONDIST=               34.008 / Degrees from image center
	}
	"""
	return fits_info_dict


def get_obslog_info(fits_info_dict, CCDno, IMAGE_ID,target_info,datestr,status,
	savefile=True):

	"""
	This function will gather all the info needed for the entry into the 
		observation log
	
	PARAMETERS:
	
		fits_info_dict = This is the gather info for the fits header. Most of 
			the information is used in there so don't want to repeat the 
			gathering process
					
	RETURN:
	
		obslog_dict = Dictionary containing the information to go into the 
			observing log table.
	
	
	"""

	#IMAGE_ID = '{0:>010}'.format(IMAGE_ID)
	obslog_dict = {'IMAGE_ID': int(str(IMAGE_ID)+str(CCDno)),
	'CCD_ID'     : str(CCDno),
	'FILE'    : 'CCD'+str(CCDno)+'_'+datestr+'_'+'{0:>08}'.format(IMAGE_ID)+'.fits',
	'TAR_NAME': target_info.name,#"OBJECT from FITS header", Need the [0] to
		#get value not comment
	'TAR_TYPE': target_info.type,
	'DATE_OBS': fits_info_dict['DATE-OBS'][0],#"FITS header",
	'MJD_OBS' : fits_info_dict['MJD_OBS'][0],#"FITS header",
	'IMAGETYP': fits_info_dict['IMAGETYP'][0],#"FITS header",
	'FILT_NAM': fits_info_dict['FILT_NAM'][0],#"FITS header",
	'EXPTIME' : fits_info_dict['EXPTIME'][0],#"FITS header",
	'OBJ_RA'  : fits_info_dict['OBJ-RA'][0],#"FITS header",
	'OBJ_DEC' : fits_info_dict['OBJ-DEC'][0],#"FITS header",
	'TEL_RA'  : target_info.ra_dec[0],#"FITS header",
	'TEL_DEC' : target_info.ra_dec[1],#"FITS header",
	'IMAG_RA'  : fits_info_dict['IMAG-RA'][0],#"FITS header",
	'IMAG_DEC' : fits_info_dict['IMAG-DEC'][0],#"FITS header",
	'INSTRUME': fits_info_dict['INSTRUME'][0],#"FITS header",
	'FOCUSER' : fits_info_dict['FOCUSER'][0],#"FITS header",
	'STATUS'  : status,
	'SAVED'	  : savefile #no fits header created for status <0. 1= True/0=False
	}

	return obslog_dict


def sort_all_logging_info(exposure_class, target_class, focuser_info, conn,
		curs,status, datestr, fits_folder):

	"""
	
	Will gather status info, weather info, telescope RA/Dec etc to be pass to 
	 the function that create the dictonaries for the fits header and observing
	 log record. Creates the fits header and
	
	
	PARAMETERS:
		target_class = contains things such as target name, position, requested 
			filters and exposures.
		exposure_class = contains info for the current exposure, e.g. exposure 
			length, filter, image_type, start time?
		focuser_info = [no, port, config]
		filter_port = active port for filter wheel
	
		conn = sqlite3 connection to the database
		curs = sqlite cursor object to send sql strings to query/control table 
			in database
	
	
	"""
	#focus_status_dict = dict({'Temp(C)':'+21.7','Curr Pos':108085,'Targ Pos':000000,'IsMoving': 1,'IsHoming':1,'IsHomed':0,'FFDetect': 0,'TmpProbe':1, 'RemoteIO':0,'Hnd Ctlr':0})
	focus_status_dict = fc.get_focuser_status(focuser_info[0],focuser_info[1],
		return_dict=True)

	try:
		current_tel_pointing = tcs.get_tel_pointing()
	except:
		current_tel_pointing = ['NA','NA','NA']
	telescope_RA_DEC = current_tel_pointing[:2]
	
	
	# Get weather
	current_weather = get_current_weather()
	# Fetch
	fits_dict = get_fits_header_info(focuser_info[2],
			focus_status_dict['Curr Pos'], current_weather, exposure_class,
			target_class, telescope_RA_DEC)
	
	#turn the dictionary into a fits header
	image_header = fits.Header()
	for i in fits_dict:
		image_header[i] = fits_dict[i]
	primaryHDU = fits.PrimaryHDU(header =image_header)


	if status < 0:
		savefile = False
	else:
		savefile = True

	# Fetch Observing log info
	obs_dict = get_obslog_info(fits_dict,exposure_class.CCD,
		IMAGE_ID=exposure_class.file_num, datestr=datestr, savefile = savefile,
		status=status, target_info=target_class)

	# these format the dictionary keys and value to put into the SQL request..
	aa = ','.join(obs_dict.keys())
	values_place_holder = len(obs_dict.keys())*'?,'
	#Set up SQL request
	sql ='''INSERT INTO '''+str(set_err_codes.OBSERVING_LOG_DATABASE_TABLE )+\
		'''('''+aa+''') VALUES('''+(values_place_holder)[:-1]+')'
	curs.execute(sql,tuple(obs_dict.values()))
	conn.commit()

	#save fits header
	if savefile == True:
		primaryHDU.writeto(fits_folder+obs_dict['FILE'], overwrite=True)

	return exposure_class.file_num + 1

def get_next_file_number(CCDno, datestr,
			fits_file_dir = set_err_codes.DATA_FILE_DIRECTORY):

	"""
	Will get a list of fits files that match the CCD number. Take the last file,
	 extract the file number.
	
	PARAMETERS:
	
		CCDno = 1 or 2, to represent which CCD you want the file number for.
		datestr = A string representing the night the observations were taken.
		fits_file_dir = the directory where the fits files should be stored.
	
	RETURN
	
		next_file_no = The number of the last file for a particular CCD. If no 
			files present, will return 1
	"""
	
	if CCDno not in [1,2]:
		logger.error('Invalid CCD number')
	
	else:

		file_list = os.listdir(fits_file_dir)
		matched = fnmatch.filter(file_list, 'CCD'+str(CCDno)+'_'+datestr+'_*.fits')
	
		try:
			last_file = matched[-1]
			next_file_no = int(last_file[14:-5]) + 1
	
		except:
			print('No file in current directory. Starting from File No: 1')
			next_file_no =  1


		return next_file_no

def get_next_fits_folder(date_str,
		fits_file_dir = set_err_codes.DATA_FILE_DIRECTORY):
	"""

	Will search dirctory for a folder specified by 'date_str', if one doesn't 
	 exist on will be created. This is so that all fits files create on one day
	 will be stored in the same folder.
	 
	 
	 PARAMETERS:
	 
		date_str = a sting representation of the date you want the fits files
			to be stored under. An example would be '20190128'
		
		fits_file_dir = a path showing where the fits files should be stored.
	 
	"""

	file_list = os.listdir(fits_file_dir)
	if date_str not in file_list:
		subprocess.run(['mkdir', fits_file_dir+date_str])


	data_file_dir = fits_file_dir+date_str+'/'

	return data_file_dir


def get_date_str():

	"""
	For use when naming files and folders, based on the date, but want to 
	 group them based on the evening date.
	 
	 
	 RETURN:
	 
		date_str = a 8 digit str represent the date in which the observations
		 were started. Note, it is based on the nigght starting, so for example
		 observations started at 1am on the 28th of Jan, will be store under the
		 27th of Jan.
	 
	"""

	current_timedate = astro_time.Time.now()
	current_in_jd = current_timedate.jd

	noon_jd = math.floor(current_in_jd)

	if current_in_jd - noon_jd < 0.875: # this works out as 9am UTC
		noon_normal = astro_time.Time(noon_jd, scale='utc', format='jd')#.format ='iso'
		noon_normal.format = 'iso'
		date_str = str(noon_normal.value[:10])
		date_str = ''.join(date_str.split('-'))
	else:
		current_timedate.format='iso'
		date_str = str(current_timedate.value[:10])
		date_str = ''.join(date_str.split('-'))


	return date_str



def get_observing_recipe(target_name, path = 'obs_recipes/'):

	"""
	When passed a target name, this function will load in the appropriate 
	 observing recipe for that particular target. The information will be 
	returned as a dictinary.
	 
	It will also take the observing pattern indicies (marked as N-PATT and 
	 S-PATT) and create the appropriate filter, exposure and focus lists and 
	 add them to the dictionary. This is done as of the function to make life 
	 easier for whoever create the observing scripts.
	 
	Note the observing recipes are assumed to be saved in a file with a name 
	 format of 'target_name'.obs
		
	** NOTE The same exposure times are used for the North and South Exposures 
		- Recommend using the same filter pattern in both telescopes **
	 
	PARAMETERS:
	
		target_name = string, name of the target for which the observing recipe 
			should be loaded.
			
	RETURN
	
		observing_recipe = dictionary containing all the information needed for
			observing. In addition to the filed stated in the .obs file, there 
			will also be the following:
				N_FILT, S_FILT, N_EXPO, S_EXPO, N_FOCUS, S_FOCUS
			to dictate the full filter list, exposure list and focus position 
			list for each telescope.
	
	"""

	#Create filename and load info as dictionary
	filename = target_name+'.obs'
	observing_recipe = common.load_config(filename, path=path)
	
	try:
		observing_recipe['EXPTIME'] = np.array(observing_recipe['EXPTIME'],
			dtype=float)
	except:
		logger.error('Observing recipe exposure times in wrong format')

	if len(observing_recipe['EXPTIME']) != len(observing_recipe['N_PATT']) or \
		len(observing_recipe['EXPTIME']) != len(observing_recipe['S_PATT']):
		logger.error('Number of Exposure times does not match the number of '\
			'filters in the filter pattern.')
	
	try:
		# Create the full lists and add to the dictionary
		n_filt = np.take(observing_recipe['FILTERS'],observing_recipe['N_PATT'])
		s_filt = np.take(observing_recipe['FILTERS'],observing_recipe['S_PATT'])
		
		n_expo = observing_recipe['EXPTIME']
		s_expo = observing_recipe['EXPTIME']
		
		n_focus = np.take(observing_recipe['FOCUS_POS'],
			observing_recipe['N_PATT'])
		s_focus = np.take(observing_recipe['FOCUS_POS'],
			observing_recipe['S_PATT'])


	except:
		#check for sensible values in the patterns
		valid_index = np.arange(0,len(observing_recipe['FILTERS']))
		N_uniq = np.unique(observing_recipe['N_PATT'])
		S_uniq = np.unique(observing_recipe['S_PATT'])
	
		for i in N_uniq:
			if i not in valid_index:
				logger.error('Check recipe: Invalid value in the N_PATT for '\
					+target_name)
				#print('Invalid value in the N_PATT for '+target_name)

		for i in S_uniq:
			if i not in valid_index:
				logger.error('Check recipe: Invalid value in the S_PATT for '+\
					target_name)
				#print('Invalid value in the S_PATT for '+target_name)
				
		logger.error('Problem with observing script for target: ' + target_name)

	else:
		observing_recipe['N_FILT'] = n_filt
		observing_recipe['S_FILT'] = s_filt

		observing_recipe['N_EXPO'] = n_expo
		observing_recipe['S_EXPO'] = s_expo

		observing_recipe['N_FOCUS'] = n_focus
		observing_recipe['S_FOCUS'] = s_focus
		
		if len(observing_recipe['N_FILT']) != len(observing_recipe['S_FILT']):
			logger.warning('Length of filter patterns for both telescopes are '\
				'unequal, will use shorter length')
		

		return observing_recipe

def take_exposure(obs_recipe, image_type, target_info_ob, datestr,
			fits_folder, timeout_time=set_err_codes.telescope_coms_timeout ):
	
	"""
	Part of the functions used to execute the exposures Need to add the actual 
	 call to the TCS and get response function.
	 
	For both telescopes, this will loop through the expanded filter pattern in 
	 the observing recipe and run an exposure for each. Filters for each will 
	 be change simultaneously.
	 
	It will take the infomation for the North telescope to dictate the exposure
	 time length, (will be the same for south telescope). Both telescopes use 
	 the same exposure time because of how the 'expose' command is define on 
	 the TCS computer. It exposes both camera for a set time, and changing this 
	 will be complex
	
	 
	Possible error codes logged from exposure request:
		0 if exposure command is received, exposure successful
		1 if CCD temp > -20
		-1 weather alert received, exposure aborted
		-2 exposure aborted, other reason
		-3 if recieve but exposure not started
		-4 Unexpected response from TCS
		-5 Timeout from TCS (60sec)
		-6 Issue with filterwheel
	  
	PARAMETERS
	
		obs_recipe = A loaded observing recipe, load from a file using the 
			get_observing_recipe function. Requires the exposure list, filter 
			list and list of focus positions.
		image_type = The type of image being taken, e.g. SCIENCE, BIAS, FLAT...
		target_info = infomation loaded from the target database about the 
			object being observed.
	
	"""
	global next_no1
	global next_no2
	for j in range(len(obs_recipe['N_FILT'])):
		exp_objN = exposure_obj(obs_recipe['N_EXPO'][j],obs_recipe['N_FILT'][j],
			image_type,2, ifw2_config['name'], next_no2)
		exp_objS = exposure_obj(obs_recipe['S_EXPO'][j],obs_recipe['S_FILT'][j],
			image_type,1, ifw1_config['name'], next_no1)

		"""
		statusN = asyncio.Future()
		statusS = asyncio.Future()
		#Change the filters if need be, don't want to have to wait for one
		#  filter to change before starting on the second, so the asyncio
		#  module will allow the to be change simultaneously
		filter_loop1 = asyncio.get_event_loop()
		filterS = filter_loop1.create_task(change_filters(exp_objS.filter,
			ifw1_port, ifw1_config,statusS))
		filterN = filter_loop1.create_task(change_filters(exp_objN.filter,
			ifw2_port, ifw2_config,statusN))
		filter_loop1.run_until_complete(asyncio.gather(filterS,filterN))
		statusN = statusN.result()
		statusS = statusS.result()
		
		"""

		try:
			# First send the command to the telescope and expect an '0'
			#  acknowledgement if it was received and started.
			statusN, statusS = exposure_TCS_response(exp_objN,exp_objS)#,
#				timeout=timeout_time)
			# This function waits for a time equal to the exposure time, in
			#  case a weather alert is received during the exposure. Need to
			#  have the two stages otherwise there would be a timeout error for
			#  long exposure (i.e. > that set timeout)
			statusN, statusS = exposureTCSerrorcode(statusN,statusS,
				exp_objN.exptime)
		
		except subprocess.TimeoutExpired:
			logger.error('TIMEOUT: No response from TCS. Exposure abandoned.')
			statusS = set_err_codes.STATUS_CODE_NO_RESPONSE
			statusN = set_err_codes.STATUS_CODE_NO_RESPONSE

		#Do observing log and fits header
		next_no1 = sort_all_logging_info(exp_objS,target_info_ob,focuser1_info,
			dbconn,dbcurs,statusS,datestr, fits_folder)
		next_no2 = sort_all_logging_info(exp_objN,target_info_ob,focuser2_info,
			dbconn,dbcurs,statusN, datestr, fits_folder)

async def change_filters(filter_name, ifw_port, ifw_config,status):
		"""
		Allows both filterwheels to change the filter with having to wait for 
			the other filterwheel.
		"""

		#change filter wheel to appropriate filter if need be:
		# uncomment when open port available
		try:
			#will need to check this
			await asyncio.wait_for(fwc.change_filter(filter_name, ifw_port,
				ifw_config))
			# Don't think need to wait for the filter wheel, because this is
			#  built into to got position function, in the filter wheel control
			#  functions. No other commands are sent until that function
			#  receives the expected response from the filterwheel
		
		except fwc.FilterwheelError:
			logger.error('Problem with check/change filterwheel request: ' + \
				ifw_config[name])
			status.set_result(set_err_codes.STATUS_CODE_FILTER_WHEEL_TIMEOUT)
		except timeout_decorator.TimeoutError():
			logger.error('Timeout on filterwheel connection (120 sec) for '\
				'filterwheel: '+ifw_config[name])
			status.set_result(set_err_codes.STATUS_CODE_FILTER_WHEEL_TIMEOUT)


def exposure_TCS_response(expObN, expObS):
	"""
	Send command to TCS to carry out exposure. Will expect an immediate response
	 to be returned. Response will be as follows:

		 0 if exposure command is received
		 1 if CCD temp > -20
		 -3 if recieve but exposure not started
		 
	The exposureTCSerrorcode function will then wait for the exposure to 
	 complete, or take action if there is a weather alert [Doesn't take action 
	 yet 4/12/18].

	PARAMETERS
	
		expObN - an exposure object for north tele, to have access to the 
			exposure time, and to set the start time
		expObS - an exposure object for South tele, to have access to the 
			exposure time, and to set the start time
		telescope - either North/South depending on the telescope doing the 
			requesting
		num - the error code. Is a asyncio future so is declared in a previous 
			function and is initially set here.
	"""
	
	logger.info('Starting ' + str(expObN.exptime) + ' sec exposure')
	#set the start time for the exposure
	expObN.set_start_time()
	expObS.set_start_time()
	
	#SEND EXPOSURE COMMAND TO TCS - get status depending on response
	#print('Pretending to take exposure: Exposure time -',expObN.exptime)
	#repsonse_stat = 0
	response_stat = tcs.tcs_exposure_request(expObN.image_type,
			duration=expObN.exptime)
	
	statN = response_stat
	statS = response_stat

	return statN, statS



def exposureTCSerrorcode(statN,statS, exptime):
	"""
	This will look at the response recieved from the TCS and take action as 
	 appropriate, mainly creating logging messages. If the exposure was started 
	 successfully (0 or 1) then it will wait for the appropriate exposure time.
	 
	 Responses:
		0 if exposure command is received
		1 if CCD temp > -20
		-1 weather alert received, exposure aborted
		-2 exposure aborted, other reason
		-3 if recieve but exposure not started
		-4 Unexpected response from TCS
	 
	***Will need to add in the code to handle recieving an weather alert or an 
		abort request.***
	
	PARAMETERS
		num - the error code as recieved from the TCS command. Is an asyncio 
			future so is declared in a previous function and is just set here.
		exptime - exposure time in seconds
		telescope - either North/South depending on the telescope doing the 
			requesting
	"""
	#return num
	OK_to_Exp_North = statN == set_err_codes.STATUS_CODE_OK or \
		statN == set_err_codes.STATUS_CODE_CCD_WARM
	OK_to_Exp_South = statS == set_err_codes.STATUS_CODE_OK or \
		statS == set_err_codes.STATUS_CODE_CCD_WARM
	if OK_to_Exp_North or OK_to_Exp_South:
	
		if statN == set_err_codes.STATUS_CODE_CCD_WARM:
			logger.warning('North CCD Temp > -20')
		if statS == set_err_codes.STATUS_CODE_CCD_WARM:
			logger.warning('South CCD Temp > -20')
		#while [no weather alert]
		# change to using the wait command on the TCS
		time.sleep(exptime)# put in here something to stop this if there is a
									#weather alert
		logger.info('Exposure complete.')
		#else:
		#	num.set_result(set_err_codes.STATUS_CODE_WEATHER_INTERRUPT)
		#	logger.warning('Weather alert during exposure')
		# or (set_err_codes.STATUS_CODE_OTHER_INTERRUPT exposure interrupted - non weather)
	elif statN == set_err_codes.STATUS_CODE_EXPOSURE_NOT_STARTED or \
				statS == set_err_codes.STATUS_CODE_EXPOSURE_NOT_STARTED:
		logger.error('Command received by TCS, but exposure not started')

	else:
		logger.error('Unexpected response')
		statN = set_err_codes.STATUS_CODE_UNEXPECTED_RESPONSE
		statS = set_err_codes.STATUS_CODE_UNEXPECTED_RESPONSE

	return statN, statS


def go_to_target(coordsArr):
	"""
	Will carry out the necessary steps require to get the telescope to move to 
	 a new target position. These include ensure the new coordinates are valid 
	 and that telescope actually needs to change position. Will check if the 
	 roof is open. If the roof is closed, it will check whether or not it is 
	 safe to open, i.e. is it raining, etc. If the roof is moving will see if 
	 the roof is open/closed before continuing.
	
	PARAMETERS
		
		coordsArr = array of the form [RA,DEC], contains the coordinates of 
			the target.
		
		timeout = Time to wait for a response from the telescope regarding 
			taking the new coords
	
	"""

	# Check the supplied coordinates are ok to be passed
	try:
		tcs.check_tele_coords(coordsArr, False)
		valid_coord = True
	except:
		logger.error('Target coordinates have wrong format for telescope.')
		valid_coord = False


	# Get current telescope pointing, do we need to change position?
	current_ra_dec = tcs.get_tel_target()[0:2]
	if current_ra_dec == coordsArr:
		logger.info('Same coordinates, do not need to move target')
		need_to_change = False
	else:
		need_to_change = True

	
	# Check that the roof is open, first get status
	try:
		roof_dict = plc.plc_get_roof_status(log_messages = False)

	except:
		"""**** CLOSE UP****"""
		print("ADD INSTRUCTIONS TO SHUTDOWN EVERYTHING ELSE")
		logger.critical('Cannot communicate with PLC, cannot get roof status')

	else:
		roof_open_bool = roof_dict['Roof_Open']
		if roof_open_bool == False:
		
			logger.warning('Roof is not open. Will try to open if safe to do so')
			try:
			# run subprocess to open th roof. It will do all the required check.
			# get to the process to do something so you know it's complete
				subprocess.run('open_roof')
			except:
				logger.error('COULD NOT open roof')
			
			else:
				roof_open_bool = True

		else:
			logger.info('Roof is open')

		# Should now be ok to tell the telescope to move
		if valid_coord == True and roof_open_bool == True and \
				need_to_change == True:
	
			pass_coord_attempts_count = 0
			while pass_coord_attempts_count < set_err_codes.pass_coord_attempts:
				try:
					send_coords(coordsArr)
				except timeout_decorator.TimeoutError:
					pass_coord_attempts_count += 1
					logger.error('Request timed out. Could not pass '\
						'coordinates to telescope.')
				else:
					logging.info('Coordinates pass successfully.')
					break
			if pass_coord_attempts_count >= set_err_codes.pass_coord_attempts:
				logger.critical('Too many attempts to pass telescope coords! '\
					'Closing up')
				#Add in code to close
				"""**** CLOSE UP****"""
				print("ADD INSTRUCTIONS TO SHUTDOWN EVERYTHING ELSE")
			
		else:
			logger.info('Telescope pointing unchanged')

@timeout_decorator.timeout(set_err_codes.telescope_coms_timeout,
		use_signals=False)
def send_coords(coords,equinox='J2000'):
	"""
	Once working this function will be what sends the target coordinates to 
	 the telescope. Once on the target, the telescope will start tracking it. 
	 A 30sec timeout is applied.
	 
	Assumes the coords are sent as RA/DEC with equinox=J2000
	"""
	tcs.slew_or_track_target(coords, tcs_conn, equinox = equinox)
	#print('ASSUMED TO BE SLEWING!!!')


def connect_to_instruments():
	"""
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set up all the instruments, i.e. focuser and filter wheel
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	"""
	#Load focuserNo and open port communication to the focusers - the homing can
	#  take up 20s to complete

	focuser_no1, focuser1_port = fc.startup('focuser1-south.cfg') #proper
	focuser_no2, focuser2_port = fc.startup('focuser2-north.cfg') #proper
	
	#focuser_no1, focuser1_port = 1, 'port1' #Just temporary
	#focuser_no2, focuser2_port = 2, 'port2' #Just temporary
	
	# Want to load the current focuser configuration settings so don't have to
	#  check it everytime we need to write a fits header or output to observing
	#  log. Might need to update this if the config setting get updated during
	#  the night but this probably unlikely

	focuser1_config_dict = fc.get_focuser_stored_config(port, x=focuser_no1,
			return_dict = False)
	focuser2_config_dict = fc.get_focuser_stored_config(port, x=focuser_no2,
			return_dict = False)
			
	#focuser1_config_dict = {'Nickname': 'FocusLynx FocSOUTH', 'Max Pos': '125440', 'DevTyp': 'OE', 'TComp ON': '0', 'TempCo A': '+0086', 'TempCo B': '+0086', 'TempCo C': '+0086', 'TempCo D': '+0000', 'TempCo E': '+0000', 'TCMode': 'A', 'BLC En': '0', 'BLC Stps': '+40', 'LED Brt': '075', 'TC@Start': '0'} #Just temporary
	#focuser2_config_dict = {'Nickname': 'FocusLynx FocNORTH', 'Max Pos': '125440', 'DevTyp': 'OE', 'TComp ON': '0', 'TempCo A': '+0086', 'TempCo B': '+0086', 'TempCo C': '+0086', 'TempCo D': '+0000', 'TempCo E': '+0000', 'TCMode': 'A', 'BLC En': '0', 'BLC Stps': '+40', 'LED Brt': '075', 'TC@Start': '0'} #Just temporary
	
	
	focuser1_info = [focuser_no1,focuser1_port,focuser1_config_dict]
	focuser2_info = [focuser_no2,focuser2_port,focuser2_config_dict]

	ifw1_port, ifw1_config = fwc.filter_wheel_startup('ifw1-south.cfg') #proper
	ifw2_port, ifw2_config = fwc.filter_wheel_startup('ifw2-north.cfg')
	
	#ifw1_port, ifw1_config = 'port_ifw1', common.load_config('ifw1-south.cfg', path='configs/') #Just temporary
	#ifw2_port, ifw2_config = 'port_ifw2', common.load_config('ifw2-north.cfg', path='configs/')
	
	return focuser1_info, focuser2_info, ifw1_config, ifw1_port,\
		ifw2_config, ifw2_port

def get_image_type(next_target_name):

	
	if next_target_name[:4] == 'BIAS' or next_target_name[:4] == 'Bias' or \
		next_target_name[:4] == 'bias':
		
		image_type = 'BIAS'
	
	elif next_target_name[:4] == 'FLAT' or next_target_name[:4] == 'Flat' or \
		next_target_name[:4] == 'flat':
	
		image_type = 'FLAT'
	
	elif next_target_name[:4] == 'DARK' or next_target_name[:4] == 'Dark' or \
		next_target_name[:4] == 'dark':
		
		image_type = 'DARK'
	elif next_target_name[:4] == 'THER' or next_target_name[:4] == 'Ther' or \
		next_target_name[:4] == 'ther':
		
		image_type = 'THERMAL'
	
	else:
		image_type = 'OBJECT'

	return image_type


def setup_file_logs_storage():

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	#Connect to table in the database, so that an observing log can be stored
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

	global dbconn,dbcurs
	dbconn, dbcurs = connect_database.connect_to()
	#Not permenant, just here while testing so dont end up with a huge database
	#  with pointless rows
	connect_database.remove_table_if_exists(dbcurs,
		set_err_codes.OBSERVING_LOG_DATABASE_TABLE )
	dbcurs.execute('CREATE TABLE '+set_err_codes.OBSERVING_LOG_DATABASE_TABLE +\
		' (IMAGE_ID text, CCD_ID INTERGER, FILE text, TAR_NAME text, '\
		'TAR_TYPE text, DATE_OBS text, MJD_OBS real, IMAGETYP text, FILT_NAM '\
		'text, EXPTIME real, OBJ_RA text, OBJ_DEC text, TEL_RA text, TEL_DEC '\
		'text, IMAG_RA text, IMAG_DEC text, INSTRUME text, FOCUSER text, '\
		'STATUS INTEGER, SAVED int2);')
	dbconn.commit()

	datestr = get_date_str()
	file_dir = get_next_fits_folder(datestr)
	
	global next_no1
	next_no1 = get_next_file_number(1, datestr, fits_file_dir=file_dir)
	global next_no2
	next_no2 = get_next_file_number(2, datestr, fits_file_dir=file_dir)


	return dbconn, dbcurs, datestr, file_dir, next_no1, next_no2


def basic_exposure(target_name, target_coords, target_type):

	#connect to instruments
	global focuser1_info
	global focuser2_info
	global ifw1_config, ifw1_port
	global ifw2_config, ifw2_port
	
	focuser1_info, focuser2_info, ifw1_config, ifw1_port, ifw2_config,\
			ifw2_port = connect_to_instruments()


	#connect to database and sort out file names
	global dbconn, dbcurs
	global next_no1, next_no2
	dbconn, dbcurs, datestr, file_dir, next_no1, next_no2 = setup_file_logs_storage()

	obs_recipe = get_observing_recipe(target_name)
	image_type = get_image_type(target_name)

	#create target object
	target = target_obj(target_name,target_coords,target_type)

	take_exposure(obs_recipe,image_type,target,datestr=datestr,
		fits_folder = file_dir)


def main():

	"""
	main function to run all the observing stuff, but is very much work in 
		progress.
	"""

	
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set up all the instruments, i.e. focuser and filter wheel
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	global focuser1_info
	global focuser2_info
	global ifw1_config, ifw1_port
	global ifw2_config, ifw2_port
	focuser1_info, focuser2_info, ifw1_config, ifw1_port, ifw2_config,\
			ifw2_port = connect_to_instruments()

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	#Connect to table in the database, so that an observing log can be stored
	#  and sort out the next file name and folder
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	global dbconn, dbcurs
	global next_no1, next_no2
	dbconn, dbcurs, datestr, file_dir, next_no1, next_no2 = \
					setup_file_logs_storage()



	"""
	Run Scheduler to find target - return target Name
	Look up target name in the database to find require info
	
		- Target info should provide:
			RA/DEC of target
			Name
	"""
	next_target_name = 'test_target_single_Texp'
	"""
	target_db_rows = connect_database.match_target_name(next_target_name,
		set_err_codes.TARGET_INFORMATION_TABLE, dbcurs)
	
	if len(target_db_rows)>1:
		logger.warning('Multiple targets found, selecting first one: '\
			+ rows[0][3])
	elif len(target_db_rows < 1):
		logger.warning('No target name found')
	else:
		#loaded_target_info = 'target_class' #into object?/organise the info
	"""
	loaded_target_info = dict({'TARGET_ID':'1', 'TAR_NAME':next_target_name,#'WASP0426-38',
			'RA':'04:26:03.78', 'DEC':'-38:32:13.9', 'T_0':6144.4344,
			'Period':13.243062})
	
	next_target = target_obj(loaded_target_info['TAR_NAME'], [loaded_target_info['RA'],loaded_target_info['DEC']])

	#what to do if no observing recipe for target??
	obs_recipe = get_observing_recipe(next_target.name)
	
	image_type = get_image_type(next_target.name)


	
	"""
	Move telescope to the target
	"""
	
	test_coords = ['10:46:04', '-46:08:06']
	go_to_target(test_coords)#target_class.coords)
	
	
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	#THen this will be part of the loop that runs when taking exposures
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	#i =0
	#while i <3:
	take_exposure(obs_recipe,image_type,next_target, datestr=datestr,
		fits_folder = file_dir)
	#i+=1
	#test1()

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	#This is testing stuff to show all the rows in the obslog2 table
	connect_database.show_all_rows_in_table(
		set_err_codes.OBSERVING_LOG_DATABASE_TABLE ,dbcurs)
	connect_database.close_connection(dbconn,dbcurs)
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
def main()
if __name__ == '__main__':
	main()

"""