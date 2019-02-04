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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CHANGE TABLE DATA
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def target_already_in_table(target_name, curs, conn,
		table_name = set_err_codes.TARGET_INFORMATION_TABLE):

	rows = match_target_name(target_name, table_name,curs)
	if len(rows) == 0:
		ok_to_add = True
	elif len(rows) >=2:
		print('WARNING! Name found multiple times already.')
		ok_to_add = False
	else:
		print('Target name already found')
		ok_to_add = False

	return ok_to_add

def update_target_info(target_name, column_name, value, curs,conn):

	table_col_headers = get_column_headers('target_info', conn)

	if column_name not in table_col_headers:
		raise ValueError('Not a valid column name')

	else:
		sql = "UPDATE "+table_name+" SET "+column_name+" ? WHERE TAR_NAME=?"
		curs.execute(sql,tuple(value, target_name))

def add_target_to_database(info_list, curs, conn,
		table_name = set_err_codes.TARGET_INFORMATION_TABLE,
		overwrite_exsiting = False):
	
	table_col_headers = get_column_headers('target_info', conn)
	if len(table_col_headers) != len(info_list):
		raise ValueError('List of new information does not match number of '\
			'columns in database.')
	else:
		#check to see target name already in table
		ok_to_add_bool = target_already_in_table(info_list[0],curs,conn)
	
		if ok_to_add_bool == False:
		
			if overwrite_exsiting == True:
				set_string = ' = ?, '.join(table_col_headers[1:])+' = ?'
				info_to_update = info_list[1:]
				info_to_update.append(info_list[0])

				sql_update ="UPDATE "+table_name+" SET "+set_string+" WHERE TAR_NAME=?"
				print('Going to overwrite the stored values')
				curs.execute(sql_update,tuple(info_to_update))

				conn.commit()

			else:
				print('New target:',str(info_list[0]), 'not added as it is '\
					'already in the table')
			
	
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

	targets_tab = ascii.read('database/new_targets.txt', delimiter = ',',
		data_start=1,header_start=0)
	for new_info in targets_tab:
		add_target_to_database(list(new_info), curs, conn,
			overwrite_exsiting=overwrite)


def remove_target(target_name, curs, conn,
	table_name = set_err_codes.TARGET_INFORMATION_TABLE):

		rows = match_target_name(target_name, table_name,curs)
		print(rows)
		

		if len(rows) < 1:
			raise ValueError('No target found with that name')
		if len(rows) >2:
			print('Removing multiple rows')

		curs.execute("DELETE FROM "+str(table_name)+" WHERE TAR_NAME=?",(
		target_name,))
		#sql = "DELETE FROM "+table_name+" WHERE TAR_NAME = ?"
		#print(sql)
		#curs.execute(sql,target_name)
		conn.commit()

#create table obslog.tb (IMAGE_ID INTEGER, CCD_ID INTERGER, TAR_NAME text, TAR_TYPE text, DATE_OBS text, MJD_OBS real, IMAGTYP text, FILT_NAM text, EXPTIME real, OBJ_RA text, OBJ_DEC text, TEL_RA text, TEL_DEC text, IMAG_RA text, IMAG_DEC text, INSTRUME text, FOCUSER text, STATUS INTEGER)

#cur.execute('CREATE TABLE obslog2 (IMAGE_ID INTEGER, CCD_ID INTERGER, FILE text, TAR_NAME text, TAR_TYPE text, DATE_OBS text, MJD_OBS real, IMAGETYP text, FILT_NAM text, EXPTIME real, OBJ_RA text, OBJ_DEC text, TEL_RA text, TEL_DEC text, IMAG_RA text, IMAG_DEC text, INSTRUME text, FOCUSER text, STATUS INTEGER);')


# create target_info_table....
"""
dbcurs.execute('CREATE TABLE '+set_err_codes.TARGET_INFORMATION_TABLE+' (TAR_NAME text, RA text, DEC text, TAR_TYPE text, T_0 real, Period real);')
dbconn.commit()


connect_database.remove_table_if_exists(dbcurs, set_err_codes.OBSERVING_LOG_DATABASE_TABLE )

testVals = ['WASP0411-39', '04:11:16.67', '-39:24:40.1', 5379.288, 14.80612]
test2 = ['WASP0419-41', '04:19:49.22', '-41:23:28.7', 6129.02177,14.88678]
test3 = ['WASP0426-38', '04:26:03.78', '-38:32:13.9', 6144.4344, 13.243062]
"""