#!/usr/bin/env python
import ctypes
import mmap
import os
import struct
import sys
import settings_and_error_codes as set_err_codes
from astropy import time as astro_time
import time
import logging

logger1 = logging.getLogger('pointing_offset')
logger1.setLevel(logging.INFO)
fileHand = logging.FileHandler(filename = \
	set_err_codes.LOGFILES_DIRECTORY+'observingScript.log', mode = 'a')
fileHand.setLevel(logging.INFO)
logging.Formatter.converter = time.gmtime
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s - '\
		'%(message)s','%Y-%m-%d_%H:%M:%S_UTC')
fileHand.setFormatter(formatter)
logger1.addHandler(fileHand)

#def set_a_time(x):

#	global a_time
#	a_time = x


def old_pointing_off_check(
		time_lim = set_err_codes.time_limit_since_last_pointing_update):
	"""
	This function checks the last time the memory map file was accessed, and
	compare that time to the current time. If the time difference is greater
	than the appropriate setting in 'settings_and_error_codes.py' then 
	the function returns True to indicate that it is a old pointing offset.
	
	Is used in conjunction with the read_offset_values function, because we
	 don't want to return a really old offset. It could be from a previous
	 nights observation or for the last target. The time limit setting will
	 need to be adjusted to suit.
	
	"""

	try:
		# The last mosified time is in unix time
		t_last_modified = os.path.getctime(set_err_codes.POINT_OFF_MEM_MAP_FILE_LOC)
	except:
		return False
	
	else:

		t_now = astro_time.Time.now()
		t_now.format = 'unix'

		#print('Now:',t_now)
		#print('last:',t_last_modified)

		t_delta = t_now.value - t_last_modified # in seconds
		#print(t_delta)
		


		if t_delta > time_lim:

			#set_a_time(t_last_modified)
			logger1.warning('Last pointing update is too old (>'\
				+str(time_lim)+'s)')
			logger1.warning('Time since last pointing update: '+str(t_delta)+'s')

			return True

		else:
			#set_a_time(0)
			return False




def read_offset_values():
	"""
	This function will be called by the obsering script when it wants to 
	 check want the later pointing offset it
	 
	 RETURN:
	 
	 new_ra or ra_val = the new read in offset for ra, or zero if there was a 
		problem reading in a value
	"""
	ra_val = 0.0
	dec_val = 0.0

	old_bool = old_pointing_off_check()
	if old_bool == False:
		try:
			# Open the file for reading
			fd = os.open(set_err_codes.POINT_OFF_MEM_MAP_FILE_LOC, os.O_RDONLY)

			# Memory map the file
			buf = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED, access=mmap.ACCESS_READ)#mmap.PROT_READ)


			#get the size of each value in bytes
			val_size = ctypes.sizeof(ctypes.c_double)
	
			# ra is first
			new_ra, = struct.unpack('d', buf[:val_size]) #d is format code for
				#double has 8 bytes
		
			#dec offset is second
			new_dec, = struct.unpack('d', buf[val_size:(val_size*2)])

		except:
			logger1.error('Error retrieving new offsets, returning (0.0, 0.0) instead')
			return ra_val,dec_val
		else:
			os.close(fd)
			return new_ra, new_dec

	else:
		return ra_val,dec_val


def update_offset_values(ra_off,dec_off):
	"""
	This function is used to create a memory map, which will store the
	 pointing offsets in ra and dec.
	
	The values are stored as c_type doubles (8 bytes) with 15 decimal place
	precision and can do signed values
	"""
	# Create new empty file to back memory map on disk
	#
	fd = os.open(set_err_codes.POINT_OFF_MEM_MAP_FILE_LOC,
			os.O_CREAT | os.O_RDWR)


	try:
		# Create the mmap instance with the following params:
		# fd: File descriptor which backs the mapping or -1 for anonymous
		# mapping length: Must in multiples of PAGESIZE (usually 4 KB)
		# flags: MAP_SHARED means other processes can share this mmap
		# prot: PROT_WRITE means this process can write to this mmap
		buf = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED, mmap.PROT_WRITE)
	except ValueError:
		# Zero out the file to insure it's the right size
		assert os.write(fd, b'\x00' * mmap.PAGESIZE) == mmap.PAGESIZE
		buf = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED, mmap.PROT_WRITE)


	# Now create an c_double in the memory mapping
	
	ra_val = ctypes.c_double.from_buffer(buf)
	#print('Size of x_val', ctypes.sizeof(ctypes.c_double))

	#assign a number to the mapped bytes
	ra_val.value = ra_off

	# Before we create a new value, we need to find the offset of the next free
	# memory address within the mmap
	offset = struct.calcsize(ra_val._type_)
	assert buf[offset] == 0#'\x00'
	
	#Now create stuff for y
	dec_val = ctypes.c_double.from_buffer(buf, offset)
	dec_val.value = dec_off

	#print('Offset_values:',ra_val.value, dec_val.value)
	buf.flush()
	os.close(fd)

def main():

	"""
	This function will run if the script is called from a terminal. Pass it 
	two floats when called (representing the offsets in ra and dec) and 
	they will be stored in the memory mapped file.
	
	This function will not run if the module is imported, without it explicitly 
	 being called.
	"""

	try:
		new_ra_off = float(sys.argv[1])
		new_dec_off = float(sys.argv[2])
	except:
		print('Offset values must be floats')
		logger1.error('Offset values must be floats')
	else:
		update_offset_values(new_ra_off, new_dec_off)

if __name__ == '__main__':
    main()