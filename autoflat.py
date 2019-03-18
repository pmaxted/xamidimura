"""
autoflat.py
Jessica A Evans

 This script contains functions that will handle taking morning and evening 
  flat field images. The main functions for doing this are the 
  'do_flats_evening' and 'do_flats_morning' functions.
  
 The order in which it cycles through filters is set by the parameters at the
  top of the script. For each filter, the filter change is requested and test
  images are taken (with scratchmode on) until the sky brightness has reached
  a suitable level for taking flats. For evening flats this is when the 
  average sky count from the two cameras is less than the saturation level. It
  will wait 5 second before trying again if they are too bright. For the morning
  the level is set by the min_count value. In both cases, an estimate of the
  next exposure length is done by calculating what factor would be needed to
  get the average count to the ideal level. In the evening this is rounded up to
  the next integer, in the morning it is round up to the nearest 0.1.
  
 The code will contiune taking flat for a filter until the max number of flats
  has been reached, the max exposure time is reached or the min exposure time
  is reached. A offset is applied between each exposure. It logs how many flats
  are taken for each filter, and how many of the flats have counts between 
  min_count and saturation. Note currently, the bias level is not taken into
  consideration.
 
  
 **Eventually will want to update the method it uses to guess the next exposure
  time. Use flats in different filts to see how the brightness changes with
  time after sunset - And use this infomation and readout time to estimate the 
  best exposure time. Is need to improve the effiecency of the flat field and
  increase the number of flats obtained.

"""
import observing
import logging
import settings_and_error_codes as set_err_codes
import time
import numpy as np
from astropy.time import Time


logger_flat = logging.getLogger(__name__)
logger_flat.setLevel(logging.INFO)
fileHand = logging.FileHandler(filename = \
	set_err_codes.LOGFILES_DIRECTORY+'observingScript.log', mode = 'a')
fileHand.setLevel(logging.INFO)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s - '\
		'%(message)s','%Y-%m-%d_%H:%M:%S_UTC')
fileHand.setFormatter(formatter)
logger_flat.addHandler(fileHand)
"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 FLAT FIELD CONFIG PARAMS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
max_flats = 10
max_time_filter_change = 20 #secs
min_exp = 1 #secs
max_exp = 20 #secs
approx_readout = 10 #secs
quick_test = 0.1

saturation = 40000#60000
ideal_counts= 10000#20000
min_count = 10000 #18000
bias_level = 1000

exposure_attempts = 3

evening_filter_order = ['BX','GX','WX','RX','IX']
morning_filter_order = ['IX','RX','WX','GX','BX']


ra_off = np.array([15,15,15,0,-15,-15,-15,0,15,15,15,0,-15,-15,-15,-15,0,0,0,15])
dec_off = np.array([0, 0, 0, 15, 0, 0, 0, 15, 0, 0, 0, 15, 0, 0, 0, 0,-15, -15, -15,0])

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def create_flat_obs_recipe(filter_choice, exptime, tar_name = 'FLAT',
	focus=50000):

	"""
	The exposure function in the observing script requires an 'observing recipe'
	 so it now whan combination of filter, exposure length etc is required.
	 This is something that normally get loaded from a file. To take a FLAT
	 image, the observing recipe is still needed, but rather than waste time
	 reading/writing this information from file, as it will change every few
	 seconds, this function will just create a dictionary that contains the
	 same information as the observing recipe.
	 
	PARAMETERS:
	
		filter_choice = String represent which filter the flat will be taken 
			with. Valid choice are currently 'RX,'GX','BX','WX','IX'
			
		exptime = the exposure time in seconds for the flat field.
		
		tar_name = Something to put in the target name field in the headers.
			'FLAT' will allow it to standout.
		focus = A value to set the focus to. [Not currently implemented]
		
	RETURN:
	
		recipe_dict = If a valid filter is supplied, a dictionary containing
		 the infomation required for an observing recipe.
	
	"""

	if filter_choice not in evening_filter_order or filter_choice not in morning_filter_order:
	
		logger_flat.error('Invalid filter supplied')
	else:

		recipe_dict = dict({'TAR_NAME':tar_name,
			'IMG-RA':'N/A', 'IMG-DEC': 'N/A', 'FILTERS':filter_choice,
			'FOCUS_POS':focus, 'EXPTIME':np.array(exptime),
			'N_PATT':np.array([0]), 'S_PATT':np.array([0]),
			'N_FILT':np.array([filter_choice]), 'S_FILT':np.array([filter_choice]),
			'N_EXPO':np.array([exptime]), 'S_EXPO':np.array([exptime]),
			'N_FOCUS':np.array([focus]), 'S_FOCUS':np.array([focus])})

		return recipe_dict

def take_flat(exp = quick_test):

	"""
	This function can be used to quickly take a flat image, by sending a request 
	 to the TCS machine. Note using this function will not log the image in
	 the observing log, or create a local fits file header. If scratchmode is 
	 disabled it will still create a file on the DAS machines. Intended to be
	 be used with scratchmode enabled.
	 
	It will make a number of attempts of taking an exposure (the number is
	 specified by the 'exposure_attempts' paramter at the top of the script.
	 
	 
	PARAMETERS:
	
		exp =  the exposure length of the flat to be taken.
		
	RETURN:
	
		exp_success = True/False. Will return true if the code successfully
		managed to take an exposure. If not it will return false.
	
	"""

	exp_attempts = 0
	exp_success = False
	while exp_attempts < exposure_attempts and exp_success == False:
		status = observing.tcs.tcs_exposure_request('FLAT', quick_test)

		if status <0:
			logger_flat.error('Error taking test image')
			exp_attempts+=1
			exp_success = False
		else:
			#observing.tcs.wait_till_read_out()
			exp_success = True

	return exp_success

def get_sky_outcome(exp = quick_test):

	"""
	This function will use the 'take_flat' function to request a test exposure,
	 and will then handle the output (i.e. whether the request was successful 
	 or not). If the request was unsuccessful, it will log an error message
	 and then close up [NEED CODE FOR THIS]. If the request was successful, then
	 it will use the 'get_sky_count' function to get the average sky background
	 from the flats (using the 'lasksky' command on the TCS). It will then 
	 estimate the counts for a minimum exposure length, by scaling up the values
	 achieve for the test exposure.
	 
	** THIS FUNCTION IS FOR EVENING FLATS **
	
	PARAMETERS:
	
		exp = The exposure time for the test exposure. This is passed to the 
			'take_flat' function.
			
	RETURN:
		
		one_sec_count_est = if the flat request was successful, the function 
		 return the count estimate for minimum exposure time. It is a direct
		 scaling of the test counts, and doesn't take into account that the
		 sky will have dimmed between the two exposures, or that the sky
		 will be dimmer in the last second of the 10s compared with the first
		 second. Will generally be an overestimate.
	"""

	exp_success = take_flat(exp=exp)
	if exp_success == False:
		logger_flat.error('Unable to take test image after 3 attempts..'\
			'.Giving up')
		print('PUT IN CODE TO HANDLE THIS..give up after three exp attempts')


	else:
		av_sky = get_sky_count()
		# Estimate the counts from a 1s exposure
		one_sec_count_est = av_sky * (min_exp/quick_test)

		return one_sec_count_est

def get_sky_outcome_morning(exp = quick_test):
	"""
	This function will use the 'take_flat' function to request a test exposure,
	 and will then handle the output (i.e. whether the request was successful 
	 or not). If the request was unsuccessful, it will log an error message
	 and then close up [NEED CODE FOR THIS]. If the request was successful, then
	 it will use the 'get_sky_count' function to get the average sky background
	 from the flats (using the 'lasksky' command on the TCS). It will then 
	 estimate the counts for a max exposure length, by scaling up the values
	 achieve for the test exposure.
	 
	** THIS FUNCTION IS FOR MORNING FLATS **
	
	PARAMETERS:
	
		exp = The exposure time for the test exposure. This is passed to the 
			'take_flat' function.
			
	RETURN:
		
		one_sec_count_est = if the flat request was successful, the function 
		 return the count estimate for MAX exposure time. It is a direct
		 scaling of the test counts, and doesn't take into account that the
		 sky will have brighten between the two exposures, or that the sky
		 will be brighter in the last bit of the exposure compared with the 
		 first part. Will generally be an underestimate.
	"""

	exp_success = take_flat(exp=exp)
	if exp_success == False:
		logger_flat.error('Unable to take test image after 3 attempts..'\
			'.Giving up')
		print('PUT IN CODE TO HANDLE THIS..give up after three exp attempts')


	else:
		av_sky = get_sky_count()
		# Estimate the counts from a 20s exposure
		one_sec_count_est = av_sky * (max_exp/quick_test)

		return one_sec_count_est

def get_sky_count():
	"""
	This function will run the lasksky command on the TCS, to get the sky
	 brightness of the last images that were taken. It will then average the
	 values from the two cameras.
	 
	RETURN:

		av_sky = The average sky brightness across the last images taken
			with the two cameras
	
	"""
	# Get the sky count estimate for the last image taken
	sky_count_arr = observing.tcs.lastsky().split(' ')
	sky_count_arr = np.array([float(i.strip()) for i in sky_count_arr])
	# average the values from the two cameras
	print(sky_count_arr)
	
	av_sky = np.mean([sky_count_arr[0],sky_count_arr[2]])
	return av_sky

def get_filter_sequence(morning=False):

	"""
	Will load in the filter order required depending on if it's morning or
	 evening (as defined by the morning bool). In the evening the filters
	 should go from bluest to reddest. In the morning the filter should go from
	 reddest to bluest.
	 
	PARAMETERS:
	
		morning = True/False. If true function will get the list with the 
			morning filter order. If false, it will get the evening list
			
	RETURN:
	
		filters = the filters in the correct order for flats
	"""

	if morning == True:
		filters = morning_filter_order
	else:
		filters = evening_filter_order

	return filters

def wait_for_right_count_evening(count_no):
	"""
	This function will repeatedly take test exposures until the average
	 sky brightness estimate for the minimum exposure length is below the 
	 saturation point of the CCD (set by a parameter at the start of the 
	 script).
	
	** THIS FUNCTION IS FOR EVENING FLATS **
	
	PARAMETERS:
		
		count_no = The sky-brightness count from the last images. This is the
		 value that will be checked.
		 
	RETURN:
		
		count_no = Same as the input value if it was below the saturation, or 
		 the most recent sky brightness counts if the function had to wait for
		 the brightness to be ok.

	"""
	# If the estimate count is higher than the saturation point, wait 5
		# seconds and take another test exposure until it fall below
	while count_no > saturation:
		time.sleep(5)
		count_no = get_sky_outcome()

	return count_no

def wait_for_right_count_morning(count_no):
	"""
	This function will repeatedly take test exposures until the average
	 sky brightness estimate for the maximum exposure length is above the
	 minimum count level (set by a parameter at the start of the
	 script).
	
	** THIS FUNCTION IS FOR MORNING FLATS **
	
	PARAMETERS:
		
		count_no = The sky-brightness count from the last images. This is the
		 value that will be checked.
		 
	RETURN:
		
		count_no = Same as the input value if it was above the minimum, or
		 the most recent sky brightness counts if the function had to wait for
		 the brightness to be ok.

	"""
	# If the estimate count is higher than the saturation point, wait 5
	# seconds and take another test exposure until it fall below
	while count_no < min_count:
		time.sleep(5)
		count_no = get_sky_outcome()

	return count_no

def get_exposure_estimate(count_no):
	"""
	This function will estimate an exposure time for the next flat image based
	 on the average counts from the last image from each camera. If the counts
	 are less than the ideal value, then a factor will be calculated to increase
	 the counts to the required level (useful if the flats were started late
	 and the quick_test exposure is not long enough to get a reasonable first
	 flat image). If the average counts fall in the valid range (less than
	 saturation, greater than ideal), the quick_test will just be scale to make
	 it to the minimum exposure time. Finally if the counts don't fit either
	 of these cases (e.g. a count that is too high), a error will be logged.
	
	** THIS FUNCTION IS FOR EVENING FLATS **
	
	PARAMETER:
	
		count_no =  The average sky brightness count that is going to be 
		 checked.
		
	"""
	if	count_no < ideal_counts:
		min_factor = observing.math.ceil((ideal_counts/count_no)*10)/10
		exp_est = quick_test * min_factor * (min_exp/quick_test)
		return exp_est

	elif count_no > ideal_counts and count_no < saturation:

		exp_est = quick_test * (min_exp/quick_test)
		return exp_est

	else:
		logger_flat.error('Invalid count for estimating flat exposure length: '+str(count_no))

def get_exposure_estimate_morning(count_no):
	"""
	This function will estimate an exposure time for the next flat image based
	 on the average counts from the last image from each camera. If the counts
	 are less than the ideal value, then a factor will be calculated to increase
	 the counts to the required level (useful if the flats were started late
	 and the quick_test exposure is not long enough to get a reasonable first
	 flat image). If the average counts fall in the valid range (less than
	 saturation, greater than ideal), the quick_test will just be scale to make
	 it to the minimum exposure time. Finally if the counts don't fit either
	 of these cases (e.g. a count that is too high), a error will be logged.
	
	** THIS FUNCTION IS FOR MORNING FLATS **
	
	PARAMETER:
	
		count_no =  The average sky brightness count that is going to be 
		 checked.
		
	"""
	if	count_no > saturation:
		min_factor = (observing.math.ceil((ideal_counts/count_no)*10))/10
		print(min_factor)
		exp_est = quick_test * min_factor * (max_exp/quick_test)
		print(exp_est, (max_exp/quick_test))
		return exp_est

	elif count_no > ideal_counts and count_no < saturation:

		exp_est = quick_test * (max_exp/quick_test)
		return exp_est

	else:
		logger_flat.error('Invalid count for estimating flat exposure length: '+str(count_no))

def do_telescope_offset():
	"""
	This function will take a offset for ra/dec and send the request to the
	 telescope mount. The code will always pick the first value from the
	 array that is defined at the top of the script, but the np.roll functions 
	 effectively shift each by one element. This means each time the function
	 is called you get a different shift. The pattern will eventually repeat 
	 after 20 calls
	"""
	global ra_off
	global dec_off

	try:
		observing.tcs.apply_offset_to_tele(ra_off,dec_off)
		logger_flat.info('Applying telescope offset: ('+str(ra_off[0]
			)+','+str(dec_off[0])+') in arcsec')

	except:
		logger_flat.warning('Unable to apply offset to telescope between flats')

	else:
		ra_off = np.roll(ra_off,1)
		dec_off = np.roll(dec_off,1)

def do_flats_evening(key_time, best_field_row, datestr,
	fits_folder):
	"""
	 This is one of the main function to carry out the flats. This one will
	  carry out EVENING flats.
	  
	It will first get a list containing filter names in the order the flats 
	 should be taken.
	
	For each filter, a filter change will be requested. Initially scratchmode
	 will be turned on and a test exposure will be taken. If the average sky
	 brightness from this test exposure is greater than the saturation level
	 then the code will wait until the brightness fall. If or once the
	 brightness has fallen, an estimate of the exposure length will be made.
	 Scratchmode will then be turned off. An observing target_object will 
	 be generated (containing the ra_dec of the blank field etc).
	 
	It will then enter a loop to create a temporary observing recipe, take an
	 exposure and then check the counts on the image (adjusting the exposure
	 time as required). An offset is applied after each exposure. The loop will
	 continue until the maximum number of exposures for that filter is reached,
	 or maximum exposure time is reached.
	 
	A log of the number of flats, number of good flats (those with counts 
	 between the min count and saturation) are made.
	 
	PARAMETERS:
	
		key_time = [not currently used] space to pass an important time e.g.
		 sunset. Might be useful for calculating the amount of twilight is
		 left, or time since sunset. Important for when the exposure updates
		 are made
		 
		best_field_row = the row from the blank_sky_field table that was 
		 picked for the flat fields. The information is used to generate the
		 fits headers.
		 
		datestr = a string represent the date folder for the fits header to be
		 saved. 
		
		fits_folder = the full directory for where the fits files wil be saved
	
	"""

	filters = get_filter_sequence(morning=False)

	total_flats = 0
	# For each filter
	for i in filters:

		# Will want to change to the first filter
		statusN, statusS = observing.change_filter_loop(i,i)


		#With scratchmode on, will want to take short test images to see how
		#  bright the sky is. Once the brightness is OK, turn off scratchmode
		# then create observing recipe and take exposes.
		observing.tcs.scratchmode('on')
	
		#do test exposures and get average sky count from two images
		one_sec_count_est = get_sky_outcome(exp=quick_test)

	
		# If evening and already into flat taking region, estimate time needed
		#  for a suitable count
		if one_sec_count_est > saturation:
		
			# If the estimate count is higher than the saturation point, wait 5
			# seconds and take another test exposure until it fall below
			one_sec_count_est = wait_for_right_count_evening(one_sec_count_est)

		# If the count estimate is less than the ideal counts (for example if
		#  we were later starting flats), we'll need to increase the initial
		# exposure time to account for the later start. Can still start flats
		if one_sec_count_est < saturation:
			est_exp = get_exposure_estimate(one_sec_count_est)

		# At this point can assume we have a rough estimate of how long an
		# exposure needs to be for it to be in the optimum window, so turn off
		#  scratchmode
		observing.tcs.scratchmode('off')

		# Create a target object ready
		targ_ob = observing.target_obj(name = 'FLAT_'+i,
			coords = [best_field_row['RA(hms)'],best_field_row['DEC(dms)']],
			type = 'FLAT')
		# keep track of how many flats are being taken
		no_of_flats_for_filter = 0
		no_of_good_flats = 0
		logger_flat.info('Doing flats for filter: ' + i)
		
		# the exposure time is less that the higher limit and the max
		# number of flats for a filter has not been reached
		while est_exp <= max_exp and no_of_flats_for_filter <= max_flats:
			
			# create an observing recipe in memory (no point wasting time
			# creating an actual file, because it will change again in a minute
			recipe = create_flat_obs_recipe(i,est_exp)
		
			# Use the 'observing.py' script to take an FLAT exposure so
			# it logs stuff in the observing log and creates a fits header
			observing.take_exposure(recipe, 'FLAT', targ_ob, datestr,
				fits_folder)
			
			# Get the sky count, to be used to estimate the next exposure time
			av_sky = get_sky_count()
			# only want to count the flat if it has reasonable counts
			if av_sky >min_count and av_sky < saturation:
				no_of_good_flats +=1
			no_of_flats_for_filter +=1
		
			time_for_flat = est_exp + approx_readout
			min_factor = observing.math.ceil(ideal_counts/av_sky)
			est_exp = est_exp * min_factor
			logger_flat.info('Exposure time for next image: '+str(est_exp))
			# Offset the telescope
			#do_telescope_offset()
		
		if est_exp > max_exp:
			logger_flat.info('Next exposure longer than maximum allowed '\
				'exposure')
		if no_of_flats_for_filter> max_flats:
			logger_flat.info('Taken the max number of flats for this filter')
		
		logger_flat.info(str(no_of_good_flats)+'/'+str(no_of_flats_for_filter)\
			+' good flats (with counts between '+str(min_count)+' and ' \
			+str(saturation)+') taken for filter: '+ i)
		
		total_flats += no_of_flats_for_filter



def do_flats_morning(key_time, best_field_row, datestr,
	fits_folder):

	"""
	 This is one of the main function to carry out the flats. This one will
	  carry out EVENING flats.
	  
	It will first get a list containing filter names in the order the flats 
	 should be taken.
	
	For each filter, a filter change will be requested. Initially scratchmode
	 will be turned on and a test exposure will be taken. If the average sky
	 brightness from this test exposure is greater than the saturation level
	 then the code will wait until the brightness fall. If or once the
	 brightness has fallen, an estimate of the exposure length will be made.
	 Scratchmode will then be turned off. An observing target_object will 
	 be generated (containing the ra_dec of the blank field etc).
	 
	It will then enter a loop to create a temporary observing recipe, take an
	 exposure and then check the counts on the image (adjusting the exposure
	 time as required). An offset is applied after each exposure. The loop will
	 continue until the maximum number of exposures for that filter is reached,
	 or maximum exposure time is reached.
	 
	A log of the number of flats, number of good flats (those with counts 
	 between the min count and saturation) are made.
	 
	PARAMETERS:
	
		key_time = [not currently used] space to pass an important time e.g.
		 sunset. Might be useful for calculating the amount of twilight is
		 left, or time since sunset. Important for when the exposure updates
		 are made
		 
		best_field_row = the row from the blank_sky_field table that was 
		 picked for the flat fields. The information is used to generate the
		 fits headers.
		 
		datestr = a string represent the date folder for the fits header to be
		 saved. 
		
		fits_folder = the full directory for where the fits files wil be saved
	
	"""

	filters = get_filter_sequence(morning=True)

	total_flats = 0
	# For each filter
	for i in filters:

		# Will want to change to the first filter
		statusN, statusS = observing.change_filter_loop(i,i)


		#With scratchmode on, will want to take short test images to see how
		#  bright the sky is. Once the brightness is OK, turn off scratchmode
		# then create observing recipe and take exposes.
		observing.tcs.scratchmode('on')
	
		#do test exposures and get average sky count from two images
		one_sec_count_est = get_sky_outcome_morning(exp=max_exp)

	
		# If evening and already into flat taking region, estimate time needed
		#  for a suitable count
		if one_sec_count_est < min_count:
		
			# If the estimate count is higher than the saturation point, wait 5
			# seconds and take another test exposure until it fall below
			one_sec_count_est = wait_for_right_count_morning(one_sec_count_est)

		# If the count estimate is less than the ideal counts (for example if
		#  we were later starting flats), we'll need to increase the initial
		# exposure time to account for the later start. Can still start flats
		if one_sec_count_est > min_count:
			est_exp = get_exposure_estimate_morning(one_sec_count_est)

		# At this point can assume we have a rough estimate of how long an
		# exposure needs to be for it to be in the optimum window, so turn off
		#  scratchmode
		observing.tcs.scratchmode('off')

		# Create a target object ready
		targ_ob = observing.target_obj(name = 'FLAT_'+i,
			coords = [best_field_row['RA(hms)'],best_field_row['DEC(dms)']],
			type = 'FLAT')
		# keep track of how many flats are being taken
		no_of_flats_for_filter = 0
		no_of_good_flats = 0
		logger_flat.info('Doing flats for filter: ' + i)
		
		# the exposure time is less that the higher limit and the max
		# number of flats for a filter has not been reached
		while est_exp >= min_exp and est_exp <= max_exp and no_of_flats_for_filter <= max_flats:
			
			# create an observing recipe in memory (no point wasting time
			# creating an actual file, because it will change again in a minute
			recipe = create_flat_obs_recipe(i,est_exp)
		
			# Use the 'observing.py' script to take an FLAT exposure so
			# it logs stuff in the observing log and creates a fits header
			observing.take_exposure(recipe, 'FLAT', targ_ob, datestr,
				fits_folder)
			
			# Get the sky count, to be used to estimate the next exposure time
			av_sky = get_sky_count()
			# only want to count the flat if it has reasonable counts
			if av_sky > min_count and av_sky < saturation:
				no_of_good_flats +=1
			no_of_flats_for_filter +=1
		
			time_for_flat = est_exp + approx_readout
			min_factor = observing.math.ceil((ideal_counts/av_sky)*10)/10
			est_exp = est_exp * min_factor
			logger_flat.info('Exposure time for next image: '+str(est_exp))
			# Offset the telescope
			#do_telescope_offset()
		

		if est_exp < min_exp:
			logger_flat.info('Next exposure shorter than minimum allowed '\
				'exposure')
		if est_exp > max_exp:
			logger_flat.info('Next exposure longer than maximum allowed '\
				'exposure')
		if no_of_flats_for_filter> max_flats:
			logger_flat.info('Taken the max number of flats for this filter')
		
		logger_flat.info(str(no_of_good_flats)+'/'+str(no_of_flats_for_filter)\
			+' good flats (with counts between '+str(min_count)+' and ' \
			+str(saturation)+') taken for filter: '+ i)
		
		total_flats += no_of_flats_for_filter

