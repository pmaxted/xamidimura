import sqlite3
import pandas as pd
import settings_and_error_codes as set_err_codes
from astropy.io import ascii

def connect_to(database_name = set_err_codes.DATABASE_NAME,
		path_to_database= set_err_codes.DATABASE_PATH):
	
	conn = sqlite3.connect(path_to_database+database_name)
	curs_obj = conn.cursor() # need a cursor object to send stuff to DB

	return conn, curs_obj

def commit_changes(connection_name):

	connection_name.commit()
	
def close_connection(connection_name, curs_obj):

	curs_obj.close()
	connection_name.close()
	
def commit_and_close(connection_name):

	commit_change(connection_name)
	close_connection(connection_name)

def show_table_names(conn):

	curs_obj = conn.cursor()
	for row in curs_obj.execute(
		'SELECT name FROM sqlite_master WHERE type="table";'):
		print(row)

	curs_obj.close()
		
def show_all_rows_in_table(table_name, curs_obj):
	for row in curs_obj.execute('SELECT * FROM '+str(table_name)):
		print(row)

def match_target_name(target_name, table_name, curs):


	curs.execute("SELECT * FROM "+str(table_name)+" WHERE TAR_NAME=?",(
		target_name,))
	rows = curs.fetchall()

	return rows

def match_target_id(target_id, table_name, curs):


	curs.execute("SELECT * FROM "+str(table_name)+" WHERE TAR_ID=?",(
		target_id,))
	rows = curs.fetchall()

	return rows

def get_table_into_pandas(table_name, connection_name):

	dat_frame = pd.read_sql_query('SELECT * FROM '+str(table_name),
		connection_name)
	return dat_frame

def remove_table_if_exists(curs, table_name):

	curs.execute('DROP TABLE IF EXISTS '+ str(table_name))


def get_column_headers(table_name, conn):

	curs2 = conn.execute('select * from '+table_name)
	list_column_name = [description[0] for description in curs2.description]

	return list_column_name


def create_unique_target_id(target_info_list):

	"""
	Will check that elements 1 and 2 in the list/array have the expected format 
	 for ra and dec - Both have two ':'...
	
	"""

	# Split the values on the ':'
	ra_split = target_info_list[1].split(':')
	dec_split = target_info_list[2].split(':')
	if len(ra_split) != 3:
		raise ValueError('Check format of RA, second value in list. Expecting '\
				'2 ":"')
	if len(dec_split) != 3:
		raise ValueError('Check format of DEC, second value in list. Expecting '\
				'2 ":"')

	ra_str = '{:02}{:02}{:05.2f}'.format(int(ra_split[0]),int(ra_split[1]),
			float(ra_split[2]))
	dec_str = '{:+03}{:02}{:04.1f}'.format(int(dec_split[0]),int(dec_split[1]),
			float(dec_split[2]))
			
	uniq_id = 'XAMI'+ra_str+dec_str

	return uniq_id




# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CHANGE TABLE DATA FOR TARGET INFO
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def target_name_already_in_table(target_name, curs, conn,
		table_name = set_err_codes.TARGET_INFORMATION_TABLE):

	rows = match_target_name(target_name, table_name,curs)
	if len(rows) == 0:
		ok_to_add = True
	else:
		print(target_name,'- target name already found')
		ok_to_add = False

	return ok_to_add

def target_id_already_in_table(target_id, curs, conn,
		table_name = set_err_codes.TARGET_INFORMATION_TABLE):

	rows = match_target_id(target_id, table_name,curs)
	if len(rows) == 0:
		ok_to_add = True
	else:
		print(target_id,'- target id already found')
		ok_to_add = False

	return ok_to_add


def update_target_info(target_id, column_name, value, curs,conn):

	table_col_headers = get_column_headers('target_info', conn)

	if column_name not in table_col_headers:
		raise ValueError('Not a valid column name')

	else:
		sql = "UPDATE "+table_name+" SET "+column_name+" ? WHERE TAR_ID=?"
		curs.execute(sql,tuple(value, target_id))


def add_target_to_database(info_list, curs, conn,
		table_name = set_err_codes.TARGET_INFORMATION_TABLE,
		overwrite_exsiting = False):
	"""
	
	PARAMETERS:
	
		info_list = a list of parameters to form a row of information in the
			target information database. Note RA should be the second value in
			the list and DEC should be the 3rd. Both off these should be in
			typical hh:mm:ss.ss or +dd:mm:ss.s format. TAR_ID will be generated
			from the RA and DEC values. List should have a format similar to 
			
		['WASP0419-41', '04:19:49.22', '-41:23:28.7', 'EB', 11.2, 'F9', 
				6129.02177, 14.88678, 0.36, 0.11, 0.014, 0.022, 0.483, 'Total']

		This example has been split over two line to make it easier to read.
		
		curs = cursor object linked to the database
		conn = connection object connected to the database
		
		table_name = name of the table to which to add the info
		
		overwrite_exisiting = True/False, if True and the target information
			yields a target id that already exists, the information for that
			id will be overwritten.
	"""
	
	
	table_col_headers = get_column_headers(table_name, conn)
	
	#-1 because the info_list at this point doesn't contain the tar_id
	if len(table_col_headers)-1 != len(info_list):
		raise ValueError('List of new information does not match number of '\
			'columns in database.')
	else:
		#check to see target name already in table
		id = create_unique_target_id(info_list)
		info_list.insert(0,id)
		target_name_not_found = target_name_already_in_table(info_list[1],curs,
			conn)
		target_id_not_found = target_id_already_in_table(id,curs,conn)
		ok_to_add_bool = target_id_not_found == True and \
			target_name_not_found == True
	
		if ok_to_add_bool == False:
		
			if overwrite_exsiting == True:
				set_string = ' = ?, '.join(table_col_headers[1:])+' = ?'
				info_to_update = info_list[1:]
				info_to_update.append(info_list[0])

				sql_update ="UPDATE "+table_name+" SET "+set_string+" WHERE TAR_ID=?"
				print('Going to overwrite the stored values')
				curs.execute(sql_update,tuple(info_to_update))

				conn.commit()

			else:
				print('New target:',str(info_list[1]), 'not added as it is '\
					'already in the table.\n')
			
	
		else:

			col_header_string = ','.join(table_col_headers)
			value_place_holder = len(table_col_headers)*'?,'

			sql = '''INSERT INTO '''+str(table_name)+'''('''+col_header_string+\
				''') VALUES('''+(value_place_holder)[:-1]+')'

			curs.execute(sql,tuple(info_list))
			conn.commit()

def add_multiple_targets_from_file(curs, conn, overwrite = False,
	table_name = set_err_codes.TARGET_INFORMATION_TABLE,
	filename='new_targets.txt', filedir=set_err_codes.DATABASE_PATH):
	
	"""
	Open a file with target info and read in as table. Go through each row
	 in the table and attempt to add it tot the database using the 
	 add_target_to_database function.
	 
	 PARAMETERS
	 
		curs = a cursor object linked to the database
		conn = a connection object linked to the database
		overwrite = True/False, if true will update information when repeat
			target ids are found.
		table_name = the name of the table for the information to be added
		filename = the name of the file that contains the new info
		filedir = path to the folder that contains 'filename'

	"""

	targets_tab = ascii.read(filedir+filename, delimiter = ',',
		data_start=0,header_start=0)
	for new_info in targets_tab:
		add_target_to_database(list(new_info), curs, conn,
			overwrite_exsiting=overwrite)


def remove_target(target_name, curs, conn,
	table_name = set_err_codes.TARGET_INFORMATION_TABLE):
	"""
	Search a table for a target name, and remove any rows that match. Will
	 through exception if no matches are found.
	 
	 PARMAETERS:
	 
		target_name = the NAME to search for.
		curs = cursor object linked to the database
		conn = connection to the database
		table_name = the name of the table to search for the target id
	"""
	rows = match_target_name(target_name, table_name,curs)
	print(rows)
		

	if len(rows) < 1:
		raise ValueError('No target found with that name')
	if len(rows) >2:
		print('Removing multiple rows')
		
	curs.execute("DELETE FROM "+str(table_name)+" WHERE TAR_NAME=?",(
		target_name,))

	conn.commit()

def remove_target_id(target_id, curs, conn,
	table_name = set_err_codes.TARGET_INFORMATION_TABLE):
	"""
	Search a table for a target id, and remove any rows that match. Will 
	 through exception if no matches are found.
	 
	 PARMAETERS:
	 
		target_id = the ID to search for.
		curs = cursor object linked to the database
		conn = connection to the database
		table_name = the name of the table to search for the target id
	"""

	rows = match_target_id(target_id, table_name,curs)
	print('Rows matched:')
	print(rows)
		

	if len(rows) < 1:
		raise ValueError('No target found with that ID')
	if len(rows) >2:
		print('Removing multiple rows')

	curs.execute("DELETE FROM "+str(table_name)+" WHERE TAR_ID=?",(
		target_id,))

	conn.commit()


"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 PRIORITY TABLE MANIPULATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def add_priority_to_database(info_list, curs, conn,
		table_name = set_err_codes.PRIORITY_TABLE,
		overwrite_exsiting = False):
	"""
	
	PARAMETERS:
	
		info_list = a list of parameters to form a row of information in the
			target information database. Note RA should be the second value in
			the list and DEC should be the 3rd. Both off these should be in
			typical hh:mm:ss.ss or +dd:mm:ss.s format. TAR_ID will be generated
			from the RA and DEC values. List should have a format similar to 
			
		['XAMI041116.67-392440.1',0,2,2,2,2]

		This example has been split over two line to make it easier to read.
		
		curs = cursor object linked to the database
		conn = connection object connected to the database
		
		table_name = name of the table to which to add the info
		
		overwrite_exisiting = True/False, if True and the target information
			yields a target id that already exists, the information for that
			id will be overwritten.
	"""
	
	
	table_col_headers = get_column_headers(table_name, conn)
	
	#-1 because the info_list at this point doesn't contain the priority_id
	print(table_col_headers)
	if len(table_col_headers)-1 != len(info_list):
		raise ValueError('List of new information does not match number of '\
			'columns in database.')
	else:

		target_id_not_found = target_id_already_in_table(info_list[0],curs,conn,
			table_name = set_err_codes.PRIORITY_TABLE)
		ok_to_add_bool = target_id_not_found #== True #and \target_name_not_found == True
	
		if ok_to_add_bool == False:
		
			if overwrite_exsiting == True:
				set_string = ' = ?, '.join(table_col_headers[1:])+' = ?'
				info_to_update = info_list[1:]
				info_to_update.append(info_list[0])

				sql_update ="UPDATE "+table_name+" SET "+set_string+" WHERE TAR_ID=?"
				print('Going to overwrite the stored values')
				curs.execute(sql_update,tuple(info_to_update))

				conn.commit()

			else:
				print('New target:',str(info_list[0]), 'not added as it is '\
					'already in the table.\n')
			
	
		else:

			col_header_string = ','.join(table_col_headers[1:])
			value_place_holder = len(table_col_headers[1:])*'?,'

			sql = '''INSERT INTO '''+str(table_name)+'''('''+col_header_string+\
				''') VALUES('''+(value_place_holder)[:-1]+')'

			curs.execute(sql,tuple(info_list))
			conn.commit()

def add_multiple_priorities_from_file(curs, conn, overwrite = False,
	table_name = set_err_codes.PRIORITY_TABLE,
	filename='new_priority_rows.txt', filedir=set_err_codes.DATABASE_PATH):
	
	"""
	Open a file with target info and read in as table. Go through each row
	 in the table and attempt to add it tot the database using the 
	 add_target_to_database function.
	 
	 PARAMETERS
	 
		curs = a cursor object linked to the database
		conn = a connection object linked to the database
		overwrite = True/False, if true will update information when repeat
			target ids are found.
		table_name = the name of the table for the information to be added
		filename = the name of the file that contains the new info
		filedir = path to the folder that contains 'filename'

	"""

	targets_tab = ascii.read(filedir+filename, delimiter = ',',
		data_start=0,header_start=0)
	for new_info in targets_tab:
		add_target_to_database(list(new_info), curs, conn,
			overwrite_exsiting=overwrite)

def update_priority_info(target_id, column_name, value, curs, conn):

	"""
	will update a value in a specific column based on a supplied target id.
	 The target id column should contain unique values
	"""

	table_col_headers = get_column_headers(set_err_codes.PRIORITY_TABLE, conn)

	if column_name not in table_col_headers:
		raise ValueError('Not a valid column name')

	else:
		sql = "UPDATE "+table_name+" SET "+column_name+" ? WHERE TAR_ID=?"
		curs.execute(sql,tuple(value, target_id))

def remove_priority_id(priority_id, curs, conn,
	table_name = set_err_codes.PRIORITY_TABLE):
	"""
	Search a table for a priority id, and remove any rows that match. Will
	 through exception if no matches are found.
	 
	 PARMAETERS:
	 
		priority_id = the ID to search for.
		curs = cursor object linked to the database
		conn = connection to the database
		table_name = the name of the table to search for the priority id
	"""

	rows = match_target_id(priority_id, table_name,curs)
	print('Rows matched:')
	print(rows)
		

	if len(rows) < 1:
		raise ValueError('No priority found with that ID')
	if len(rows) >2:
		print('Removing multiple rows')

	curs.execute("DELETE FROM "+str(table_name)+" WHERE PRIORITY_ID=?",(
		priority_id,))

	conn.commit()


#create table obslog.tb (IMAGE_ID INTEGER, CCD_ID INTERGER, TAR_NAME text, TAR_TYPE text, DATE_OBS text, MJD_OBS real, IMAGTYP text, FILT_NAM text, EXPTIME real, OBJ_RA text, OBJ_DEC text, TEL_RA text, TEL_DEC text, IMAG_RA text, IMAG_DEC text, INSTRUME text, FOCUSER text, STATUS INTEGER)

#cur.execute('CREATE TABLE obslog2 (IMAGE_ID INTEGER, CCD_ID INTERGER, FILE text, TAR_NAME text, TAR_TYPE text, DATE_OBS text, MJD_OBS real, IMAGETYP text, FILT_NAM text, EXPTIME real, OBJ_RA text, OBJ_DEC text, TEL_RA text, TEL_DEC text, IMAG_RA text, IMAG_DEC text, INSTRUME text, FOCUSER text, STATUS INTEGER);')


# create target_info_table....
"""
dbcurs.execute('CREATE TABLE '+set_err_codes.TARGET_INFORMATION_TABLE+' (TAR_ID text, TAR_NAME text NOT NULL, RA text, DEC text NOT NULL, TAR_TYPE text, MAGNITUDE real, SPEC_TYPE text,T_0 real, PERIOD real, DEPTH1 real, DEPTH2 real, WIDTH1 real, WIDTH2 real, PHASE2 real, NOTES text, PRIMARY KEY (TAR_ID ASC));')
dbconn.commit()
"""
#create priority_database table
"""
dbcurs.execute('CREATE TABLE '+set_err_codes.PRIORITY_TABLE+' (PRIORITY_ID INTEGER, TAR_ID text UNIQUE NOT NULL, COMPLETENESS real, OVERALL_PRIORITY real, PRIORITY1 real, PRIORITY2 real, URGENCY INTEGER, PRIMARY KEY (PRIORITY_ID), FOREIGN KEY(TAR_ID) REFERENCES '+set_err_codes.TARGET_INFORMATION_TABLE+'(TAR_ID));')
dbconn.commit()
"""
#other random stuff..
"""
connect_database.remove_table_if_exists(dbcurs, set_err_codes.TARGET_INFORMATION_TABLE)

testVals = ['WASP0426-38', '04:26:03.78', '-38:32:13.9', 'EB', 10.9, 'F9', 6144.4344, 13.243062, 0.13, 0.04, 0.016,0.014,0.223,'Total']
test2 = ['WASP0411-39', '04:11:16.67', '-39:24:40.1', 'EB', 11.9, 'F1', 5379.28800, 14.806120, 0.48, 0.34,0.025, 0.033, 0.49, 'Dbl*']
test3 = ['WASP0419-41', '04:19:49.22', '-41:23:28.7', 'EB', 11.2, 'F9', 6129.02177, 14.88678, 0.36, 0.11, 0.014, 0.022, 0.483, 'Total']

Name, RA, Dec, T_0, P, depth_1, width_1, phase_2,  depth_2, width_2, mag, SpType,Notes
WASP0411-39, 04:11:16.67, -39:24:40.1,5379.288,14.80612,0.48,0.025,0.49,0.34,0.033,11.9, F1,Dbl*
WASP0419-41, 04:19:49.22, -41:23:28.7,6129.02177,14.88678,0.36,0.014,0.483,0.11,0.022,11.2, F9,Total
WASP0426-38, 04:26:03.78, -38:32:13.9,6144.4344,13.243062,0.13,0.016,0.223,0.04,0.014,10.9, F9,Total
test_target_single_Texp, 10:46:04, -46:08:06, TEST, 20, G, 5805.28800, 24.600000, , , , , , Test

"""
