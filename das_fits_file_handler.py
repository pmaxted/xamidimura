""" 
das_fits_file_handle.py

 An attempt to create something that will take the fits files stored on the
  DAS machines, combine them with the fits header files on the observer
  machine and store them safely on the observer machine

"""

import os
import subprocess
import settings_and_error_codes as set_err_codes
from astropy.io import fits
from astropy.time import Time
import time

def check_file_process(fits_type, das):

	ok_das = [1,2,'1','2']
	
	if das not in ok_das:
		raise ValueError('Invalid number supplied for DAS machine, use '\
			'1 or 2')


	else:
		das = str(das)
		fits_dir_dict = dict({'FLAT':'FLAT/DAS'+das+'_Flat*.fts',
							'BIAS':'BIAS/DAS'+das+'_Bias*.fts',
						'THERMAL':'THERMAL/DAS'+das+'_Therm*.fts',
						'DARK':'THERMAL/DAS'+das+'_Therm*.fts',
						'OBJECT':'NORMAL/DAS'+das+'_*.fts'})
						#'normal':'NORMAL/DAS'+das+'_*.fts'})
	
		try:
			fits_dir = fits_dir_dict[fits_type]
	
		except KeyError:
			raise ValueError('Invalid fits type supplied. Use "FLAT", "BIAS", "THERMAL", '\
				'"DARK" or "OBJECT"')
		else:
			out = subprocess.run(['ssh','wasp@das'+das,'ls',
				'/data/das'+das+'/'+fits_dir], capture_output = True)

			if len(out.stdout) == 0 and out.stderr == b'ls: No match.\n':
				file_path = None
				return file_path#,file_no]
			#file_no = None
			elif len(out.stdout) !=0:
				file_path = out.stdout.decode('utf-8').strip().split('\n')[-1]
				#file_no = file_path.split('/')[-1]
				return file_path#,file_no]
			else:
				raise RuntimeError('Unexpected response when running ls '\
					'command: '+str(out.stderr))
			

def get_last_fits_header(das,dir = set_err_codes.DATA_FILE_DIRECTORY):

	ok_das = [1,2,'1','2']

	if das not in ok_das:
		raise ValueError('Invalid number supplied for DAS machine, use '\
			'1 or 2')

	else:
		das = str(das)
		date_folder = max(os.listdir(dir))
		out = subprocess.run('ls CCD'+das+'*.fits',cwd = dir+date_folder,
			capture_output=True, shell=True)
		
		if len(out.stdout) == 0:
			file = None
		
		else:
			file = max(out.stdout.decode('utf-8').strip().split('\n'))
			#print(file)
		
		return file, date_folder
		
		
def get_last_files(das):

	print('Fetching last files for DAS'+str(das))
	last_flat = check_file_process('FLAT',das)
	last_bias = check_file_process('BIAS',das)
	last_thermal = check_file_process('THERMAL',das)
	last_dark = check_file_process('DARK',das)
	last_normal = check_file_process('OBJECT',das)

	last_file_dict = dict({"FLAT":last_flat,"BIAS":last_bias,
		"THERMAL":last_thermal, "DARK":last_dark,"OBJECT":last_normal})

	return last_file_dict

def new_header_dict(das_header):

	new_header_info = dict({
		'XFACTOR' : (das_header['XFACTOR'],'Camera x binning factor'),
		'YFACTOR' : (das_header['YFACTOR'],'Camera y binning factor'),
		'LST'  : (das_header['LST'], 'Local sidereal time'),
		'DASSTART':(Time(das_header['DATE-OBS']+'T'+das_header['UTSTART'],
			 format='isot').value, 'Start time from DAS machine'),
		'DASMIDD':(Time(das_header['DATE-OBS']+'T'+das_header['UTMIDDLE'], 
				format='isot').value, 'Exposure midpoint from DAS machine'),
		'IMAG-RA':(das_header['RA'], 'Nominal image center J2000 RA'),
		'IMAG-DEC': (das_header['DEC'], 'Nominal image center J2000 Dec'),
		'CCDSPDH' : (das_header['CCDSPDH'],'CCD Readout time / pixel (usecs)'),
		'CCDSPDV' : (das_header['CCDSPDV'], 'CCD Access time / row (usecs)'),
		'ZENDIST' : (das_header['ZENDIST'],'Zenith Distance, degrees'),
		'AIRMASS' : (das_header['AIRMASS'],'Airmass calculation'),
		'MOONPHAS': (das_header['MOONPHAS'],'Percentage of full'),
		'MOONALT' : (das_header['MOONALT'], 'Degrees above horizon'),
		'MOONDIST': (das_header['MOONDIST'], 'Degrees from image center')
		})
		
	return new_header_info

def sort_data_output_dir(imagetype, dir = set_err_codes.FINAL_DATA_DIRECTORY):
		
	if imagetype == 'FLAT':
		if os.path.isdir(dir+'/'+'flats') == False:	
			out4 = subprocess.run(['mkdir','flats'], cwd = dir, 
				capture_output =True)
			if out4.returncode !=0:
				raise RuntimeError('Unable to create directory: '+out4.stderr)		
		path = dir+'/'+'flats/'
					
	elif imagetype == 'BIAS':		
		if os.path.isdir(dir+'/'+'bias') == False:
			out4 = subprocess.run(['mkdir','bias'], cwd = dir,
				capture_output=True)
			if out4.returncode !=0:
				raise RuntimeError('Unable to create directory: '+out4.stderr)
		path = dir+'/'+'bias/'
					
	elif imagetype == 'THERMAL':
		if os.path.isdir(dir+'/'+'thermal') == False:
			out4 = subprocess.run(['mkdir','thermal'], cwd = dir,
				capture_output=True)
			if out4.returncode !=0:
				raise RuntimeError('Unable to create directory: '+out4.stderr)
		path = dir+'/'+'thermal/'

	elif imagetype == 'DARK':
		if os.path.isdir(dir+'/'+'dark') == False:
			out4 = subprocess.run(['mkdir','dark'], cwd = dir)
			if out4.returncode !=0:
				raise RuntimeError('Unable to create directory: '+out4.stderr)
		path = dir+'/'+'dark/'

	elif imagetype == 'OBJECT':
		#assume the image is an object file
		if os.path.isdir(dir+'/'+'normal') == False:
			out4 = subprocess.run(['mkdir','normal'], cwd = dir)
			if out4.returncode !=0:
				raise RuntimeError('Unable to create directory: '+out4.stderr)
			
		path = dir+'/'+'normal/'

	else:
		raise ValueError('Invalid image type supplied')

	return path

def copy_over_file(das_no,new_header_file,new_date_folder,last_file_dict, 
	attempt_count_limit =10):
	
	ok_das = [1,2,'1','2']

	if das_no in ok_das == False:
		raise ValueError('Invalid number supplied for DAS machine, use '\
			'1 or 2')

	else:
		das_no = str(das_no)

		#open the header to see what type of image (flat/bias/object)
		with fits.open(set_err_codes.DATA_FILE_DIRECTORY+new_date_folder \
				+'/'+new_header_file) as hdu1:
			fits_header = hdu1[0].header

		imagetyp = fits_header['IMAGETYP']
		
		#use the image type to look for new files in the appropriate
		#  directory on the das machine
		attempt_count = 0
		new_das_file = check_file_process(imagetyp, das_no)
		#print(new_das_file)
		while new_das_file == last_file_dict[imagetyp] and \
								attempt_count<attempt_count_limit:
			print('Waiting for new das file')
			time.sleep(1)
			new_das_file = check_file_process(imagetyp, das_no)
			attempt_count += 1

		
		if attempt_count >= attempt_count_limit:
			raise RuntimeError('Waited '+str(attempt_count_limit)+' secs, and'\
				' no new file appeared')
		
		else:
			#only executed if while condition become false
#			print('Copying file to tempory location to access header')
			out3 = subprocess.run(["scp","wasp@das"+das_no+":"\
				+new_das_file,"."], capture_output=True,
					cwd=set_err_codes.FINAL_DATA_DIRECTORY+'/temporary')
			#data/das1/NORMAL/DAS1_001651075.fts","."],capture_output=True)
			if out3.returncode != 0:
				raise RuntimeError('Could not copy file: '+out3.stderr)
		
			else:
				das_file = new_das_file.split('/')[-1]
				#Open the newly copied fits
				with fits.open(set_err_codes.FINAL_DATA_DIRECTORY+'/temporary/'\
					+das_file) as das_hdu:
					image_data = das_hdu[0].data
					das_header = das_hdu[0].header
					
				new_header_info_to_add = new_header_dict(das_header)
				
				for i in new_header_info_to_add:
					fits_header[i] = new_header_info_to_add[i]
				primaryHDU =fits.PrimaryHDU(header=fits_header, data= image_data)	
			
				path = sort_data_output_dir(imagetyp, 
					dir = set_err_codes.FINAL_DATA_DIRECTORY)
				
				if os.path.isdir(path+new_date_folder) == False \
						and os.path.isdir(path) == True:
					
					print('Creating new date directory')
					out4 = subprocess.run(['mkdir',new_date_folder], cwd = path)
						
				primaryHDU.writeto(path+new_date_folder	+'/'+\
					new_header_file)
				print('File Transfered...')

				#print('Removing temporary...')
				out4 = subprocess.run(['rm',
					 set_err_codes.FINAL_DATA_DIRECTORY+'/temporary/'+das_file],
					 capture_output=True)
				
				if out4.returncode !=0:
					print('Issue removing temporary file:', dasfile)

def do_the_comparisons(das_no, last_fits_header, last_date_folder,
	last_dict_file):


	# Check the fits header files again to see if there is a new file
	new_header_file, new_date_folder = get_last_fits_header(das_no)
	if new_header_file != last_fits_header and last_fits_header != None:
		
		#print('option1')
		copy_over_file(das_no,new_header_file,new_date_folder,last_dict_file)
		last_fits_header = new_header_file
		last_date_folder = new_date_folder
		return 0,last_fits_header, last_date_folder, last_dict_file

	elif new_header_file != last_fits_header and last_fits_header == None:
		#print('option2')
		last_fits_header = new_header_file
		last_date_folder = new_date_folder
		return 0, last_fits_header, last_date_folder, last_dict_file

	else:
		#print('no new file')
		return 5, last_fits_header, last_date_folder, last_dict_file

def main():


#	print('Running main()')
	# Find out what was the fits header file to be saved on the observer
	#  machine and then find out what were the names of the last files to be 
	# store in the data directory of the das machine. Checks all bias, flat,
	# thermal and normal images
	last_fits_header1, last_date_folder1 = get_last_fits_header(1)
	last_file_dict1 = get_last_files(1)
	last_fits_header2, last_date_folder2 = get_last_fits_header(2)
	last_file_dict2 = get_last_files(2)

	while 1:#i<2:

		print('1:', last_fits_header1, last_date_folder1)
		print('2:', last_fits_header2, last_date_folder2)

		return1, last_fits_header1, last_date_folder1, last_file_dict1 \
			= do_the_comparisons(1, last_fits_header1,last_date_folder1,
				last_file_dict1)
		return2, last_fits_header2, last_date_folder2, last_file_dict2 \
			= do_the_comparisons(2, last_fits_header2, last_date_folder2,
				last_file_dict2)

		if return1 == 5 or return2 == 5:	
			time.sleep(1)


if __name__ == '__main__':
	main()
