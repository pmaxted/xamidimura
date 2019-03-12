"""
getAlmanac.py
Jessica A. Evans

 A script to get the important times regarding sunrise, sunset, twilight etc
  so the telescope now the best time to be taking things like
 

"""

import settings_and_error_codes as set_err_codes
#from astroplan import Observer
#from astroplan import OldEarthOrientationDataWarning
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation
from math import pi
import numpy
import warnings
import math

# After 14 days the timings used for the Observer object becomes out of date and
# raises a OldEarthOrientationDataWarning. In which case a new IRES bulletin
# table should be downloaded

with warnings.catch_warnings(record=True) as w:
	from astroplan import Observer
	from astroplan import OldEarthOrientationDataWarning
	warnings.simplefilter("once")
	#logger.warning('Updating IERS bulletin table')
	for i in w:
		if i.category == OldEarthOrientationDataWarning:
			new_mess = '.'.join(str(i.message).split('.')[:3])
			print('WARNING:',new_mess)
			print('INFO: Updating IERS bulletin table...')
			from astroplan import download_IERS_A
			download_IERS_A()

def deg2str(degs):
	"""
	Takes a decimal value and converts it back to the string format
	
		Note the transfer of the '-' sign has not been checked.
	
	"""

	hh = math.floor(degs)
	mm = (degs % 1)*60
	ss = (mm % 1)*60

	str_ans = format(hh, '02n')+':'+format(math.floor(mm),'02n')+':'+format(ss, '03.3f')

	return str_ans

def str2deg(val, to_split_on = ':'):

	"""
	Takes a value of the form 23:43:23.55 and converts it to decimal 
	 degrees and then radians
	 
	 PARAMETERS:
	 
		val = A string representing a sexagesimal value separated by colons
		
	 RETURN:
	 
		degs = The decimal value of the sexagesimal value, will not be a string
	 
	"""
	if isinstance(val, str) == False:
		raise ValueError('Please supply string to convert to decimal'\
			' degrees')
	
	if to_split_on in val:
		if val[0] == '-':
			val_arr = val[1:].split(to_split_on)
		else:
			val_arr = val.split(to_split_on)

		degs = float(val_arr[0])+(float(val_arr[1])/60.0)+(
									float(val_arr[2])/(60*60.0))

		if val[0] == '-':
			degs = degs * -1

		return degs
	else:
		raise ValueError('Expecting "'+to_split_on+'" in the input value')

def set_up_observer():

	"""
	Will need to convert the longitude and latitude from the settings in to 
	 decimal degrees from their string format. Then create the observer
	 object
	 
	RETURN:
		
		saao = An observer object with the location set to SAAO. It take the 
			longitude, latitude and altitude from the settings and error code
			python file. It is expecting them to be strings in sexagesimal
			format, and will use the str2deg function to convert them to 
			decimal format.
	 
	"""

	long = str2deg(set_err_codes.LONGITUDE)
	lat = str2deg(set_err_codes.LATITUDE)

	saao = Observer(longitude = long*u.deg, latitude = lat*u.deg,
		elevation = set_err_codes.ALTITUDE*u.m, name = 'SAAO',
		timezone='Etc/GMT+2')


	return saao

def convert_time(jd_time, out_format='iso'):

	"""
	The observer module contain lots of useful functions to get the times
	 of sunset/sunrise etc... but all the times are returned in Julian date.
	 want to convert that before returning it
	 
	PARAMETERS:
	
		jd_time = An astropy time object. It's expecting the format to be 'jd'
			but it doesn't really matter.
			
		out_format = The format you would like the time to be in. The 'iso' 
			format is useful for easy reading and interpretting.
			
	RETURN:
	
		jd_time = Astropy time object with the format that was specified by
			'out_format'
	
	"""

	jd_time.format = out_format
	return jd_time


def get_timingsISO(observer_obj, current_time):

	"""
	For a location as specified by the observer object 'observer_obj', work out
	 when the next astro,nautical, civil twilight times are (both morning and 
	 evening), sunset, sunrise and moonrise/set.
	 
	PARAMETERS:
	
		observer_obj = An observer object from the astroplan module. The 
			longitude, latitude and altitude of the object should be set to 
			where you what the the times for.
			
		current_time =  An astropy time object, containing the current time.
			Don't think it minds what format because astroplan converts it
			anyway.
			
	RETURN
	
		times_arr = A numpy array of astropy time objects, where each object
			contains the time of a key time. The array time are structured as
			follows:
			
			0 - sunset
			1 - civil_even_twilight
			2 - nauti_even_twilight
			3 - astro_even_twilight
			4 - astro_morn_twilight
			5 - nauti_morn_twilight
			6 - civil_morn_twilight
			7 - sunrise
			8 - moonrise
			9 - moonset
	"""

	#night_bool = observer_obj.is_night(current_time) #based on horizon being at 0 deg
	#ls_time = observer_obj.local_sidereal_time(current_time, kind='mean')

	sunset = convert_time(observer_obj.sun_set_time(
			current_time, which = 'next'))
			
	astro_even_twilight = convert_time(observer_obj.twilight_evening_astronomical(
			current_time, which = 'next'))
	nauti_even_twilight = convert_time(observer_obj.twilight_evening_nautical(
			current_time, which = 'next'))
	civil_even_twilight = convert_time(observer_obj.twilight_evening_civil(
			current_time, which = 'next'))

	
	sunrise = convert_time(observer_obj.sun_rise_time(
			current_time, which = 'next'))
			
	astro_morn_twilight = convert_time(observer_obj.twilight_morning_astronomical(
			current_time, which = 'next'))
	nauti_morn_twilight = convert_time(observer_obj.twilight_morning_nautical(
			current_time, which = 'next'))
	civil_morn_twilight = convert_time(observer_obj.twilight_morning_civil(
			current_time, which = 'next'))
	
	
	moonrise = convert_time(observer_obj.moon_rise_time(
			current_time, which = 'next'))
	moonset = convert_time(observer_obj.moon_set_time(
			current_time, which = 'next'))
			
	times_arr = numpy.array([sunset,civil_even_twilight, nauti_even_twilight,
		astro_even_twilight, astro_morn_twilight, nauti_morn_twilight,
		civil_morn_twilight, sunrise, moonrise, moonset])
	
	#current_time.format = 'jd'
	#sa_local_time = Time(current_time.value+(2/24.0), format = 'jd')
	#sa_local_time.format = 'iso'
	
	#times_dict['Current(SAST)'] = sa_local_time
	
	return times_arr


def calc_time_differences(time_arr):

	"""
	After supplying an array containing the time of sunset, sunrise, twilight
	 etc, this function will calculate the difference between these times and
	 the current time. It will decide which one is closest based on the smallest
	 time difference.
	 
	 Currently it will return a string with the result and the time unitl then 
	 in days.
	 
	PARAMETERS:
	
		time_arr = the output array from the get_timingsISO function. Assume it 
		 has the values in a specific order, and is laid out as follows:
		0	- sunset
		1	- civil_evening
		2	- nautical_evening
		3	- astro_evening
		4	- astro_morning
		5	- nautical_morning
		6	- civil_evening
		7	- sunrise
		8	- moonrise
		9	- moonset
			
		The moon times are removed before continuing with the time difference
		 calculations
		 
	RETURN:
	
		mess = A str representing what time of day it is. Valid values include
			'daytime','afterSunset','afterCivil', night, beforeCivil and
			beforeSunset
			
		t_remain = the time between the current time and the end of the current
			time of day. Value is in days.
			
		key_time =  one of the astropy time objects from time_arr. Have chosen
			ones that might be useful.
	"""

	current_time = Time.now()
	current_time.format = 'iso'
	
	key_times = time_arr[:-2]

	#Works out the difference between the key times and the current times
	diffs = numpy.array([(i - current_time).value for i in key_times])
	#print (diffs)
	positive_condition_arr = diffs[diffs > 0]
	# Find which one is closest so we know what time of day it is
	time_ele = numpy.where(numpy.min(positive_condition_arr) == diffs)[0][0]

	# This provides a visual for what time of day it is and then return useful
	#  information.
	if time_ele == 0:
		t_remain = diffs[0]
		print("It's daytime! " +format(t_remain*24, '2.2f')+"h until sunset.")
		mess = 'daytime'
		return mess, t_remain, key_times[0] # sunset

	elif time_ele == 1:
		t_remain = diffs[1]
		print("Sun has set, "+ format(t_remain*24, '2.2f')+"h until "\
				"civil twilight (evening)") # Take bias then open
		mess = 'afterSunset'
		return mess, t_remain, key_times[0] # sunset
	
	elif time_ele == 2:
		t_remain = diffs[2]
		print("Civil twilight (evening),  "+ format(t_remain*24, '2.2f')+"h until "\
				"nautical twilight (evening)") # take flats
	
		mess = 'afterCivil'
		return mess, t_remain, key_times[3] #evening astro
	
	elif time_ele == 3 or time_ele == 4 or time_ele == 5:
		t_remain = diffs[5]
		print("Night time, " +format(t_remain*24, '2.2f')+"h until "\
				"nautical twilight (morning)") #Do night observations
		mess = 'night'
		return mess, t_remain, key_times[4] #morning astro

	elif time_ele == 6:
		t_remain = diffs[6]
		print("Nautical twilight (morning), " +format(t_remain*24, '2.2f')+"h until "\
				"civil twilight (morning)") # take morning flats
		mess = 'beforeCivil'
		return mess, t_remain, key_times[4] #morning astro

	elif time_ele == 7:
		t_remain = diffs[7]
		print("Civil twilight (morning), " +format(t_remain*24, '2.2f')+"h until "\
				"sunrise") #close up
		mess = 'beforeSunrise'
		return mess, t_remain, key_times[7] # sunrise
	
	else:
		logger.error('Could find closest time event')



def decide_observing_time():

	"""
	Combines all of the functions described above to work out what time of day
	 it is.
	 
	RETURN:
	
		t_mess = A str representing what time of day it is. Valid values include
			'daytime','afterSunset','afterCivil', night, beforeCivil and
			beforeSunset
			
		t_left = the time between the current time and the end of the current
			time of day. Value is in days.
			
		k_time =  one of the astropy time objects from time_arr. Have chosen
			ones that might be useful.
	
	"""

	saao = set_up_observer()
	current_time = Time.now()
	current_time.format = 'iso'
	
	times = get_timingsISO(saao, current_time)
	t_mess, t_left, k_time = calc_time_differences(times)


	return t_mess, t_left, k_time

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
		height = ALT*u.m)

	return earth_loc

def main():

	"""
	If this script is run rom the command line, it will print the current 
	 sunset, sunrise, twilight timings in UTC.
	"""

	saao = set_up_observer()
	current_time = Time.now()
	current_time.format = 'iso'
	
	times = get_timingsISO(saao, current_time)
	
	#times_dict['Current(SAST)'] = sa_local_time

	print('~~~~~~~~~~~~~~~~~~~~~~~~~')
	print('Times are UTC')
	print('~~~~~~~~~~~~~~~~~~~~~~~~~')
	print('Next Sunset\t\t', times[0])
	print('Civil twilight\t\t', times[1])
	print('Nautical twilight\t', times[2])
	print('Astronomical twilight\t',times[3])
	print('~~~~~~~~~~~~~~~~~~~~~~~~~')
	print('Next Sunrise\t\t', times[7])
	print('Civil twilight\t\t', times[6])
	print('Nautical twilight\t', times[5])
	print('Astronomical twilight\t',times[4])
	print('~~~~~~~~~~~~~~~~~~~~~~~~~')
	print('Moonrise\t\t', times[8])
	print('Moonset\t\t\t',times[9])
	print('~~~~~~~~~~~~~~~~~~~~~~~~~')
	print('Current (UTC):\t\t',current_time)
	current_time.format = 'jd'
	sa_local_time = Time(current_time.value+(2/24.0), format = 'jd')
	sa_local_time.format = 'iso'
	print('Current (SAST):\t\t', sa_local_time)
	
	current_time.location = create_earth_loc()
	sid_time = current_time.sidereal_time(kind ='mean').value
	print('Current ST:\t\t', deg2str(sid_time))

	
if __name__ == '__main__':
    main()
	





