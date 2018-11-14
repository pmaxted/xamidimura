import sqlite3
import pandas as pd

def connect_to(database_name = 'xamidimura.db', path_to_database= 'database/'):
	
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
	for row in curs_obj.execute('SELECT name FROM sqlite_master WHERE type="table";'):
		print(row)

	curs_obj.close()
		
def show_all_rows_in_table(table_name, curs_obj):
	for row in curs_obj.execute('SELECT * FROM '+str(table_name)):
		print(row)

def get_table_into_pandas(table_name, connection_name):

	dat_frame = pd.read_sql_query('SELECT * FROM '+str(table_name), connection_name)
	return dat_frame

def remove_table_if_exists(curs, table_name):

	curs.execute('DROP TABLE IF EXISTS '+ str(table_name))


#create table obslog.tb (IMAGE_ID INTEGER, CCD_ID INTERGER, TAR_NAME text, TAR_TYPE text, DATE_OBS text, MJD_OBS real, IMAGTYP text, FILT_NAM text, EXPTIME real, OBJ_RA text, OBJ_DEC text, TEL_RA text, TEL_DEC text, IMAG_RA text, IMAG_DEC text, INSTRUME text, FOCUSER text, STATUS INTEGER)

#cur.execute('CREATE TABLE obslog2 (IMAGE_ID INTEGER, CCD_ID INTERGER, FILE text, TAR_NAME text, TAR_TYPE text, DATE_OBS text, MJD_OBS real, IMAGETYP text, FILT_NAM text, EXPTIME real, OBJ_RA text, OBJ_DEC text, TEL_RA text, TEL_DEC text, IMAG_RA text, IMAG_DEC text, INSTRUME text, FOCUSER text, STATUS INTEGER);')
