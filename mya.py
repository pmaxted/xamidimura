#!/usr/bin/env python
import ctypes
import mmap
import os
import struct


def main():
	# Create new empty file to back memory map on disk
	#
	fd = os.open('/tmp/mmaptest', os.O_CREAT | os.O_RDWR)


	try:
		# Create the mmap instance with the following params:
		# fd: File descriptor which backs the mapping or -1 for anonymous
		# mapping length: Must in multiples of PAGESIZE (usually 4 KB)
		# flags: MAP_SHARED means other processes can share this mmap
		# prot: PROT_WRITE means this process can write to this mmap
		buf = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED, mmap.PROT_WRITE)
	except ValueError:
		print('Got ValueError')
		# Zero out the file to insure it's the right size
		assert os.write(fd, b'\x00' * mmap.PAGESIZE) == mmap.PAGESIZE
		buf = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED, mmap.PROT_WRITE)


	# Now create an int in the memory mapping
	#i = ctypes.c_int.from_buffer(buf)
	s_type = ctypes.c_char * len('c')
	s = s_type.from_buffer(buf)

	print('First 10 bytes of memory mapping: ', buf[:10])
	
	#new_i = input('Enter a new value for i: ')
	#i.value = int(new_i)

	s.raw = bytes(input('Enter a value for s:'), 'utf-8')




if __name__ == '__main__':
    main()