import sqlite3
import pandas as pd
import settings_and_error_codes as set_err_codes

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


	curs.execute("SELECT * FROM "+str(table_name)+" WHERE TAR_NAME="+str(
		target_name))
	rows = curs.fetchall()

	return rows

def get_table_into_pandas(table_name, connection_name):

	dat_frame = pd.read_sql_query('SELECT * FROM '+str(table_name),
		connection_name)
	return dat_frame

def remove_table_if_exists(curs, table_name):

	curs.execute('DROP TABLE IF EXISTS '+ str(table_name))


#create table obslog.tb (IMAGE_ID INTEGER, CCD_ID INTERGER, TAR_NAME text, TAR_TYPE text, DATE_OBS text, MJD_OBS real, IMAGTYP text, FILT_NAM text, EXPTIME real, OBJ_RA text, OBJ_DEC text, TEL_RA text, TEL_DEC text, IMAG_RA text, IMAG_DEC text, INSTRUME text, FOCUSER text, STATUS INTEGER)

#cur.execute('CREATE TABLE obslog2 (IMAGE_ID INTEGER, CCD_ID INTERGER, FILE text, TAR_NAME text, TAR_TYPE text, DATE_OBS text, MJD_OBS real, IMAGETYP text, FILT_NAM text, EXPTIME real, OBJ_RA text, OBJ_DEC text, TEL_RA text, TEL_DEC text, IMAG_RA text, IMAG_DEC text, INSTRUME text, FOCUSER text, STATUS INTEGER);')


# create target_info_table....
"""
dbcurs.execute('CREATE TABLE '+set_err_codes.TARGET_INFORMATION_TABLE+' (TARGET_ID INTEGER, TARGET_NAME text, RA text, DEC text, T_0 real, Period real);')
dbconn.commit()
a = [TARGET_ID, TAR_NAME, RA, DEC, T_0, Period]
aaa = ','.join(a)

sql = '''INSERT INTO '''+str(obs.set_err_codes.TARGET_INFORMATION_TABLE )+'''('''+aaa+''') VALUES('''+(values_place_holder)+')'

curs.execute(sql,tuple(testVals))
conn.commit()

connect_database.remove_table_if_exists(dbcurs, set_err_codes.OBSERVING_LOG_DATABASE_TABLE )

testVals = [1,'WASP0411-39', '04:11:16.67', '-39:24:40.1', 5379.288, 14.80612]
test2 = ['WASP0419-41', '04:19:49.22', '-41:23:28.7', 6129.02177,14.88678]
test3 = ['WASP0426-38', '04:26:03.78', '-38:32:13.9', 6144.4344, 13.243062]
"""