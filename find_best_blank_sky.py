"""
find_best_blank_sky.py
Jessica A. Evans


	Based on a list of blank sky regions as specified by the path set in
	 settings_and_error_codes.py script, this script will load in the table 
	 in that file and calculate the zenith distance for each field. The
	 field with the smallest zenith distance will be chosen.
	 
	

"""

import math
import numpy
from astropy.io import ascii
from astropy.time import Time
import settings_and_error_codes as set_err_codes
from astropy.coordinates import EarthLocation
import astropy.units as units
import logging
import time

logger_bsky = logging.getLogger('find_blank_sky')

logger_bsky.setLevel(logging.INFO)
fileHand = logging.FileHandler(filename = \
	set_err_codes.LOGFILES_DIRECTORY+'observingScript.log', mode = 'a')
fileHand.setLevel(logging.INFO)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s - '\
		'%(message)s','%Y-%m-%d_%H:%M:%S_UTC')
fileHand.setFormatter(formatter)
logger_bsky.addHandler(fileHand)


def str2deg(val):

	"""
	Takes a value of the form 23:43:23.55 and converts it to decimal 
	 degrees and then radians
	"""
	if isinstance(val, str) == False:
		raise ValueError('Please supply string to convert to decimal'\
			' degrees')
	
	if val[0] == '-':
		val_arr = val[1:].split(':')
	else:
		val_arr = val.split(':')

	degs = float(val_arr[0])+(float(val_arr[1])/60.0)+(
								float(val_arr[2])/(60*60.0))

	if val[0] == '-':
		degs = degs * -1

	return degs

def convert_RAs_DECs(tab):

	"""
	Loop through the table and create two array with the ra and dec of each 
	 field converted to decimal.
	 
	PARAMTERS:
	
		tab = the table of blank fields as loaded from the csv file
		
	RETURN
	
		ra_arr = numpy array containing the decimal values for ra
		de_arr - numpy array contain the decimal values for dec
	"""

	ra_arr = numpy.array([])
	dec_arr = numpy.array([])
	for i in range(len(tab)):
		converted_ra = str2deg(tab['RA(hms)'][i])
		converted_dec = str2deg(tab['DEC(dms)'][i])
		
		ra_arr = numpy.append(converted_ra, ra_arr)
		dec_arr = numpy.append(converted_dec, dec_arr)

	return ra_arr, dec_arr


def deg2str(degs):
	"""
	Takes a decimal value and converts it back to the string format
	
		Note the transfer of the '-' sign has not been checked.
	
	"""

	hh = math.floor(degs)
	mm = (degs % 1)*60
	ss = (mm % 1)*60

	str_ans = str(hh)+':'+str(math.floor(mm))+':'+str(ss)

	return str_ans

def create_earth_loc(LONG = set_err_codes.LONGITUDE,
		LAT = set_err_codes.LATITUDE, ALT = set_err_codes.ALTITUDE):

	"""
	Take the longitude, latitude and altitude values and creates a EarthLocation
	 object.
	"""

	long_split = LONG.split(':')
	long_str = long_split[0]+'d'+long_split[1]+'m'+long_split[2]+'s'

	lat_split = LAT.split(':')
	lat_str = lat_split[0]+'d'+lat_split[1]+'m'+lat_split[2]+'s'

	earth_loc = EarthLocation(lat = lat_str, lon = long_str,
		height = ALT*units.m)

	return earth_loc



def get_sidereal_time():
	"""
	Obtain the current time and convert it to a sidereal time. Might need to 
	 check the time zones eventually. The observer machine is set to use UTC
	 time? the sidereal time will need to be local...
	
	"""


	#Need to create a EarthLocation object to pass the longitude to the
	#  time object.

	current_time =  Time.now()
	#print(current_time)
	current_time.location = create_earth_loc()
	sid_time = current_time.sidereal_time(kind ='mean').value

	return sid_time#, deg2str(sid_time)

def calc_HA(ra, sidereal_time):

	HA = (sidereal_time - ra)%24

	return HA

def calc_zenith_distance(lat,dec,ha):

	""" 
	Based on the equation 23 on page 57 of "The CCD photometric calibration
		cookbook" http://starlink.rl.ac.uk/star/docs/sc6.pdf
		
		sec(z) = 1/(sin(phi)*sin(delta) + cos(phi)*cos(delta)*cos(h)
		
	where:
	phi = latitude of observation,
	delta = declination of observation
	h = Hour angle
	
	then as sec(z) = 1/cos(z), cos(z) = 1/sec(z) and
	
	cos(z) = (sin(phi)*sin(delta) + cos(phi)*cos(delta)*cos(h)
	
	PARAMETERS:
	
		lat = single latitude value in decimal degrees
		dec = array of declination value in decimal degrees
		ha = array of Hour Angle values in decimal degrees

	"""

	sinPhi = numpy.sin(numpy.radians(lat))
	sinDelta = numpy.sin(numpy.radians(dec))

	cosPhi = numpy.cos(numpy.radians(lat))
	cosDelta = numpy.cos(numpy.radians(dec))
	cosH = numpy.cos(numpy.radians(ha))

	denom = (sinPhi*sinDelta + cosPhi*cosDelta*cosH)

	z = numpy.arccos(denom)

	return z

def one_row_cal(row):

	print(row['RA(hms)'],row['DEC(dms)'])
	ra_deg = str2deg(row['RA(hms)'])
	dec_deg = str2deg2rad(row['DEC(dms)'])

	sid = get_sidereal_time()
	ha = calc_HA (ra_deg, sid)

	print(ha)

def find_best_field():

	# Get the csv file as a table
	tab = ascii.read(set_err_codes.BLANK_SKY_REGION_CSV, format='csv',
		header_start=7)
		
	ra, dec = convert_RAs_DECs(tab)
	sid = get_sidereal_time()
	
	ha_arr = numpy.remainder((sid - ra), 20)
	lat = str2deg(set_err_codes.LATITUDE)
	
	zen_dist_rad = calc_zenith_distance(lat, dec, ha_arr)

	zen_dist_ang = numpy.degrees(zen_dist_rad)
	min_dist_ele = numpy.where(zen_dist_ang == min(zen_dist_ang))[0][0]
	
	best_field = tab[min_dist_ele]
	
	logger_bsky.info('Best blank sky field: RA = '+best_field['RA(hms)']+\
		', DEC = '+best_field['DEC(dms)']+', with limit ='+\
		' '+str(best_field['Limit']))

	return best_field

def main():
	
	print('Finding blank field near zenith....\n')
	small_zen_dist_field = find_best_field()
	print('Best blank sky field: RA = '+small_zen_dist_field['RA(hms)']+\
		', DEC = '+small_zen_dist_field['DEC(dms)']+', with limit ='+\
		' '+str(small_zen_dist_field['Limit']))
	
	#return tab[min_dist_ele]


	#return tab


if __name__ == '__main__':
    main()