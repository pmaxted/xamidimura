"""
observing.py


	*** Very much still work-in-progress, and may not permenantly remain under this name. ***
	
	Purpose of this script is to carry out the functions required for observing, e.g. startup instruments 
		and carry out the required initialisation, obtain target infomation for a scheduled target.
		
	CURRENTLY the obslog2 table in the database is overwritten each time the main() function is run,
		because I did want to fill the database with rubbish while testing.
		
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
	
	- get_fits_header_info(focuser_config,focuser_position, weather_list, expose_info, target_info)
	
	- get_obslog_info(fits_info_dict, CCDno, IMAGE_ID = 1)
	
	- get_next_file_number(CCDno, fits_file_dir = 'fits_file_tests/')
	
	----------------------------------------------------------------------
	Main Function
	----------------------------------------------------------------------

	- main()


"""

import sqlite3
import connect_database
import focuser_control as fc
import filter_wheel_control as fwc
import common
from astropy.io import fits
from astropy import time
import subprocess
import os
import fnmatch
import logging

logging.basicConfig(filename = 'logfiles/observingScript.log',filemode='w',level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
observe_log_DBtable = 'obslog2'


def get_current_UTC_time_in_isot_format():

	"""
	Acquires the current time from the system clock. Is in UTC scale and is formatted in 'isot' format, i.e
		2001-01-02T03:04:05.678
		
	RETURN
		
		a = The correctly formatted time
	
	"""
	a = time.Time.now()
	a.format = 'isot'

	return a

class exposure_obj(object):
	"""
		To be used to get all the information for a particular exposure in one
		 place, information such as exposure time, filter, etc.
	"""
	def __init__(self,exptime, filter_name,image_type, CCD_no, filter_wheel_name,file_num):
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
		When a exposure is started, use this function to get the current time and store it as
		 the start time of the exposure. Also converts this to MJD, and calculate the mid exposure
		 time. All stored in the object. Mid exposure time is calculate from the start time and 
		 half the specified exposure length.
		"""
	
		self.date_obs = get_current_UTC_time_in_isot_format()
		self.mjd_obs = self.date_obs.mjd

		self.mid_exp = self.date_obs + time.TimeDelta(self.exptime/2.0, format='sec')
		self.mjd_mid = self.mid_exp.mjd

def get_current_weather(logfile_loc = 'logfiles/weather.log'):

	"""
	If the weather goes to a weather.log file on tcs, will want this script just to read the last line of the
		weather log file. Will have to come up with something incase the the weather info cannot be retrieved
		- although not getting weather info would be a safety issue
		
	Uses python's subproccess to run a tail command to find the last line (of 107 bytes) in the log file. The
		input is reversed by the -r flag, so it actually takes the first 107 bytes
		
	
	Will assume the weather info is retrive as a string in the following format...
	
	2454144.18988  12 187  23.8  23  826.0   2 DRY  -44.5 DRY ------------ 14.70 -99.99 -99.99  41 -99 -99 1.61
	
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
	
		logfile_loc = directory to where the weather log file is. Will need to update once file structure
			is sorted
	
	RETURN
	
		retreived_line =  list of weather values, with each value stored as a string
	
	
	"""

	# use tail to find the last 107 bytes of the weather log file. The -c means it searches bytes, and
	#  -r means the input is reversed -hopefully this will make it quicker for larger files, but not tested
	sub1 = subprocess.Popen(['tail','-r','-c','107',logfile_loc], stdout=subprocess.PIPE,
		stderr=subprocess.PIPE)
	outp = sub1.communicate()
	if len(outp[0]) > 2:
		retrieved_line = outp[0].decode('utf-8')
	else:
		print('INFO: Error reading weather log file')
	
	retrieved_line = retrieved_line.split()

	return retrieved_line


def get_fits_header_info(focuser_config,focuser_position, weather_list, expose_info, target_info):

	"""
	This function would get all the info required for an entry into for the fits header. Most of this
	 info is also used in the observing log database entry.
	 
	 ** Not worked out all the details yet ** 
	Some strings used as place holders, most are from the target infomation
	 
	 
	 PARAMETERS:
	 
		focuser_config = a dictionary construction from the configuration settings retrived from the focuser
			(not the config file)
			
		focuser_pos = number passed from elsewhere (or could endup being the full dictionary)
		
		weather_list = list containing values for different weather observations. See get_current_weather()
			for more info in what each represents
			
		expose_info = An exposure_obj, contain infomation such as the exposure time, filter, and exposure
			start time.
			
		target_info = ***NOT USED YET*** will pass the required target infomation.
		
	RETURN:
	
		fits_info_dict = the dictionary that is formed from all the infomation.
	
	"""
	
	# FOR FITS HEADER...
	fits_info_dict ={'OBSERVAT': ('SAAO', 'Observatory name'),
					'TELESCOP': ('Xamidimura', 'Telescope name'),
					'INSTRUME': (expose_info.CCD, 'CCD1-South/CCD2-North'),
					'FILTRWHL': (expose_info.filter_wheel_name, 'ifw1-South/ifw2-North'),
					'FOCUSER' : (focuser_config['Nickname'], 'focuser1-south/focuser2-north'),
					'DATE'    : (get_current_UTC_time_in_isot_format().value, 'File creation date/time (UTC)'),
					'OBJECT'  : ("FROM TARGET INFO?", 'Target name'),
					'IMAGETYP': (expose_info.image_type, 'Flat/bias/dark/science/other'),
					
					'OBJ-RA'  : ("From TARGET INFO", 'Expected Target RA'),
					'OBJ-DEC' : ("From TARGET INFO", 'Expected Target DEC'),
					'TEL-RA'  : ("Function from teles", 'Telescope RA'),
					'TEL-DEC' : ("Function from teles", 'Telescope DEC'),
					'IMAG-RA' : ("Calculate", 'Nominal image position, pxl (1024,1024) J2000'),
					'IMAG-DEC': ("Calculate", 'Nominal image position, pxl (1024,1024) J2000'),
	
					'EQUINOX' :(2000, 'Used coordinate system'),
					'DATE-OBS': (expose_info.date_obs.value, 'Exp start CCYY-MM-DDTHH:MM:SS.sss(UTC)'),
					'MID_EXP' : (expose_info.mid_exp.value, 'Exp middle CCYY-MM-DDTHH:MM:SS.sss(UTC)'),
					'MJD_OBS' : (expose_info.mjd_obs, 'MJD at start'),
					'MJD_MID' : (expose_info.mjd_mid, 'MJD at mid-point'),
					'EXPTIME' : (expose_info.exptime, 'Integration time (s)'),
	
					'FILT_NAM': (expose_info.filter, 'Rx/Gx/Bx/Wx/Ix'),
					#'FILT_POS': ("FROM GET POS FUNCTION", 'Filter wheel position from 1-5'),
					'FOCU_POS': (focuser_position, 'Position of focuser at exp. start'),
	
					'LATITUDE': ('-32:22:51', 'Site Latitude, degrees +N'),
					'LONGITUD': ('20:48:38', 'Site Longitude, degrees +E'),
					'ALTITUDE': ('1.8E+03', 'Site elevation (meters) above sea level'),
	
	"**CHECK**"		'BIASSEC' : ('[2068:2148,1:2048]', 'Bias section'), # Don't know if these are correct
	"**CHECK**"		'TRIMSEC' : ('[6:2053,1:2048]',	'Illuminated section'), # Taken from WASP fits file.
					'GAIN'    : ("NOT SURE", '???'),
					'CCD_TEMP': ("????", '????'),
	
					#"From focuser config -- Run get config everytime, or run once before hand??"
					'TEMP_COM':	(focuser_config['TComp ON'], 'Temperature compensation (ON=1/OFF=0)'),
					'TCOMSTRT':	(focuser_config['TC@Start'], 'Temperature compensation @ start (ON=1/OFF=0)'),
					'TCOMMODE': (focuser_config['TCMode']  , 'Temperature compensation mode'),
					'TCOM_COA': (focuser_config['TempCo A'], 'Temperature compensation coefficient A'),
					'TCOM_COB': (focuser_config['TempCo B'], 'Temperature compensation coefficient B'),
					'TCOM_COC':	(focuser_config['TempCo C'], 'Temperature compensation coefficient C'),
					'TCOM_COD':	(focuser_config['TempCo D'], 'Temperature compensation coefficient D'),
					'TCOM_COE':	(focuser_config['TempCo E'], 'Temperature compensation coefficient E'),
					'BCK_LASH':	(focuser_config['BLC En']  ,'Backlash compensation (ON =1/OFF=0)'),
					'BCK_STEP':	(focuser_config['BLC Stps'], 'Steps used for backlash compensation'),
					'COMMENT' : ('Weather log from: '+weather_list[0]+', '+time.Time(float(weather_list[0]), format='jd').isot),

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


def get_obslog_info(fits_info_dict, CCDno, IMAGE_ID,status):

	"""
	This function will gather all the info needed for the entry into the observation log
	
	***  Status info, and target type to be completed  ***
	
	PARAMETERS:
	
		fits_info_dict = This is the gather info for the fits header. Most of the information is used in
			there so don't want to repeat the gathering process
					
	RETURN:
	
		obslog_dict = Dictionary containing the information to go into the observing log table.
	
	
	"""
	#IMAGE_ID = '{0:>010}'.format(IMAGE_ID)
	obslog_dict = {'IMAGE_ID': IMAGE_ID,
	'CCD_ID'     : str(CCDno),
	'FILE'    : 'CCD'+str(CCDno)+'_'+'{0:>010}'.format(IMAGE_ID)+'.fits',
	'TAR_NAME': fits_info_dict['OBJECT'][0],#"OBJECT from FITS header", Need the [0] to get value not comment
	'TAR_TYPE': "From target DB EB, planet, etc.",
	'DATE_OBS': fits_info_dict['DATE-OBS'][0],#"FITS header",
	'MJD_OBS' : fits_info_dict['MJD_OBS'][0],#"FITS header",
	'IMAGETYP': fits_info_dict['IMAGETYP'][0],#"FITS header",
	'FILT_NAM': fits_info_dict['FILT_NAM'][0],#"FITS header",
	'EXPTIME' : fits_info_dict['EXPTIME'][0],#"FITS header",
	'OBJ_RA'  : fits_info_dict['OBJ-RA'][0],#"FITS header",
	'OBJ_DEC' : fits_info_dict['OBJ-DEC'][0],#"FITS header",
	'TEL_RA'  : fits_info_dict['TEL-RA'][0],#"FITS header",
	'TEL_DEC' : fits_info_dict['TEL-DEC'][0],#"FITS header",
	'IMAG_RA'  : fits_info_dict['IMAG-RA'][0],#"FITS header",
	'IMAG_DEC' : fits_info_dict['IMAG-DEC'][0],#"FITS header",
	'INSTRUME': fits_info_dict['INSTRUME'][0],#"FITS header",
	'FOCUSER' : fits_info_dict['FOCUSER'][0],#"FITS header",
	'STATUS'  : status
	}

	return obslog_dict


def sort_all_logging_info(exposure_class, target_class, focuser_info, conn, curs,status):

	"""
	
	Will gather status info, weather info, telescope RA/Dec etc to be pass to the function that create
		the dictonaries for the fits header and observing log record. Creates the fits header and
	
	
	PARAMETERS:
		target_class = contains things such as target name, position, requested filters and exposures.
		exposure_class = contains info for the current exposure, e.g. exposure length, filter, image_type, start time?
		focuser_info = [no, port, config]
		filter_port = active port for filter wheel
	
		conn = sqlite3 connection to the database
		curs = sqlite cursor object to send sql strings to query/control table in database
	
	
	"""
	#focus_status_dict = fc.get_focuser_status(focuser_info[0],focuser_info[1],return_dict=True)
	focus_status_dict = {'Temp(C)': '+21.7', 'Curr Pos': '108085', 'Targ Pos': '000000', 'IsMoving': '1', 'IsHoming': '1', 'IsHomed': '0', 'FFDetect': '0', 'TmpProbe': '1', 'RemoteIO': '0', 'Hnd Ctlr': '0'}
	
	telescope_RA_DEC = '???','???' """Eventually function to get RA/DEC from telescope"""
	
	
	# Get weather
	current_weather = get_current_weather()
	# Fetch
	fits_dict = get_fits_header_info(focuser_info[2],focus_status_dict['Curr Pos'], current_weather,
			exposure_class, target_class)
	
	#turn the dictionary into a fits header
	image_header = fits.Header()
	for i in fits_dict:
		image_header[i] = fits_dict[i]
	primaryHDU = fits.PrimaryHDU(header =image_header)
	
	# Fetch Observing log info
	obs_dict = get_obslog_info(fits_dict,exposure_class.CCD, IMAGE_ID=exposure_class.file_num,status=status)

	# these format the dictionary keys and value to put into the SQL request..
	aa = ','.join(obs_dict.keys())
	values_place_holder = len(obs_dict.keys())*'?,'
	#Set up SQL request
	sql ='''INSERT INTO '''+str(observe_log_DBtable)+'''('''+aa+''') VALUES('''+(values_place_holder)[:-1]+')'
	curs.execute(sql,tuple(obs_dict.values()))
	conn.commit()

	#save fits header
	primaryHDU.writeto('fits_file_tests/'+obs_dict['FILE'], overwrite=True)

	return exposure_class.file_num + 1

def get_next_file_number(CCDno, fits_file_dir = 'fits_file_tests/'):

	"""
	Will get a list of fits files that match the CCD number. Take the last file, extract the file number.
	 if the
	
	PARAMETERS:
	
		CCDno = 1 or 2, to represent which CCD you want the file number for.
	
	RETURN
	
		next_file_no = The number of the last file for a particular CCD. If no files present,
			will return 1
	"""
	
	if CCDno not in [1,2]:
		logging.error('Invalid CCD number')
	
	else:

		file_list = os.listdir(fits_file_dir)#
		matched = fnmatch.filter(file_list, 'CCD'+str(CCDno)+'_*.fits')
	
		try:
			last_file = matched[-1]
			next_file_no = int(last_file[5:-5]) + 1
	
		except:
			print('No file in current directory. Starting from File No: 1')
			next_file_no =  1


		return next_file_no

def main():

	"""
	main function to run all the observing stuff, but is very much work in progress.
	"""
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set up all the instruments, i.e. focuser and filter wheel
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
	
	#Load focuserNo and open port communication to the focusers - the homing can take up 20s to
	#  complete
#	focuser_no1, focuser1_port = fc.startup('focuser1-south.cfg') #proper
#	focuser_no2, focuser2_port = fc.startup('focuser2-north.cfg') #proper
	focuser_no1, focuser1_port = 1, 'port' #Just temporary
	
	# Want to load the current focuser configuration settings so don't have to
	#  check it everytime we need to write a fits header or output to observing log
	#  Might need to update this if the config setting get updated during the night
	#  but this probably unlikely

#	focuser1_config_dict = fc.get_focuser_stored_config(1, port, return_dict = False) #proper
#	focuser2_config_dict = fc.get_focuser_stored_config(2, port, return_dict = False) #proper
	focuser1_config_dict = {'Nickname': 'FocusLynx Foc2', 'Max Pos': '125440', 'DevTyp': 'OE', 'TComp ON': '0', 'TempCo A': '+0086', 'TempCo B': '+0086', 'TempCo C': '+0086', 'TempCo D': '+0000', 'TempCo E': '+0000', 'TCMode': 'A', 'BLC En': '0', 'BLC Stps': '+40', 'LED Brt': '075', 'TC@Start': '0'} #Just temporary
	
	# Run startup for filterwheels
	#ifw1_port, ifw1_config = fwc.filter_wheel_startup('ifw1-south.cfg') #proper
	#ifw2_port, ifw2_config = fwc.filter_wheel_startup('ifw2-north.cfg') #proper
	ifw1_port, ifw1_config = 'port_ifw1', common.load_config('ifw1-south.cfg', path='configs/') #Just temporary
	ifw2_port, ifw2_config = 'port_ifw2', common.load_config('ifw2-north.cfg', path='configs/')
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	#Connect to table in the database, so that an observing log can bee stored
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	dbconn, dbcurs = connect_database.connect_to()
	#Not permenant, just here while testing so dont end up with a huge database with pointless rows
	connect_database.remove_table_if_exists(dbcurs, 'obslog2')
	dbcurs.execute('CREATE TABLE obslog2 (IMAGE_ID INTEGER, CCD_ID INTERGER, FILE text, TAR_NAME text, TAR_TYPE text, DATE_OBS text, MJD_OBS real, IMAGETYP text, FILT_NAM text, EXPTIME real, OBJ_RA text, OBJ_DEC text, TEL_RA text, TEL_DEC text, IMAG_RA text, IMAG_DEC text, INSTRUME text, FOCUSER text, STATUS INTEGER);')
	dbconn.commit()
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	#Get next file number for each ccd
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	next_no1 = get_next_file_number(1)
	next_no2 = get_next_file_number(2)


	"""
	Run Scheduler to find target - return target info from target list database
	
		- Target info should provide:
			RA/DEC of target
			Name
			List of filters
			List of exposure times in sec
			image_type
			
	"""
	filter_list = ['RX','GX','BX']
	exposure_times = [2,4,6]
	image_type ='SCIENCE'
	
	
	for j in range(len(filter_list)):
	

		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		#THen this will be part of the loop that runs when taking exposures
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
		#create exposure object
		exp_obj1 = exposure_obj(exposure_times[j],filter_list[j],image_type,1, ifw1_config['name'], next_no1)
		#exp_obj2 = exposure_obj(4,'RX','SCIENCE',2, ifw2_config['name'], next_no2)
	
		#change filter wheel to appropriate filter if need be:
		# uncomment when open port available
		#fwc.change_filter(exp_obj1, ifw1_port, ifw1_config)

		# Set start time and set exposure command
		exp_obj1.set_start_time()
		"""
		SEND EXPOSURE COMMAND TO TCS - get status depending on response
		
		"""
		status = 0 #FUNCTION return appropriate response??

		#Do observing log and fits header
		next_no1 = sort_all_logging_info(exp_obj1,'target_class',[focuser_no1,focuser1_port,focuser1_config_dict],
		 dbconn,dbcurs,status)
	
	
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	#This is testing stuff to show all the rows in the obslog2 table
	connect_database.show_all_rows_in_table(observe_log_DBtable,dbcurs)
	connect_database.close_connection(dbconn,dbcurs)
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""
def main()
if __name__ == '__main__':
	main()

"""