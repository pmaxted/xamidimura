"""
settings_and_error_codes.py

Contains a list of all the various error codes from the various scripts, and also the various settings such as timeouts and connection attempts.

"""

# Status code for taking exposure
STATUS_CODE_OK = 0
STATUS_CODE_CCD_WARM = 1
STATUS_CODE_WEATHER_INTERRUPT = -1
STATUS_CODE_OTHER_INTERRUPT = -2
STATUS_CODE_EXPOSURE_NOT_STARTED = -3
STATUS_CODE_UNEXPECTED_RESPONSE = -4
STATUS_CODE_NO_RESPONSE = -5
STATUS_CODE_FILTER_WHEEL_TIMEOUT = -6




# Timeouts in seconds
plc_serial_port_timeout =30
plc_comms_timeout = 60
plc_power_timeout = 60

roof_moving_timeout = 600
telescope_coms_timeout = 30
tcs_coms_timeout = 60


#Other parameters
pass_coord_attempts = 2
tcs_conn_tries_total = 3

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#              DATABASE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DATABASE_NAME = 'xamidimura.db'
DATABASE_PATH = 'database/'

TARGET_INFORMATION_TABLE = 'target_info'
OBSERVING_LOG_DATABASE_TABLE = 'obslog2'



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#              PLC
# -As taken from the original manual
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PLC_CODE_OK = 0

# PLC status modes:
PLC_STATUS_MODE = dict({'0': 'Program mode',
						'2':'Run mode',
						'3': 'Monitor mode'})
PLC_STATUS_UNKNOWN_MODE = 'Unknown mode'
PLC_STATUS_INVALID_RESPONSE = 'Invalid PLC status request response string'

PLC_STATUS_STATUS = dict({	'0': 'Normal',
							'1':'Fatal Error',
							'8':'FALS Error'})
PLC_STATUS_UNKNOWN_STATUS = 'Unknown error code: '

PLC_STATUS_WRITE_ERROR_MESSAGE = dict({	'00': "Normal Completion",
										'13': "FCS error",
										'14': "Format error",
										'15': "Entry number data error",
										'18': "Frame length error",
										'19': "Not executable",
										'21': "Not executable due to CPU Unit CPU error"
										})

PLC_STATUS_ERROR_MESSAGE = dict({	'00': "Normal Completion",
									'01': "Not executable in RUN mode",
									'02': "Not executable in MONITOR mode",
									'04': "Address Over",
									'08': "Not executable in PROGRAM mode",
									'13': "FCS error",
									'14': "Format error",
									'15': "Entry number data error",
									'18': "Frame length error",
									'19': "Not executable",
									'23': "Memory write protected",
									'A3': "FCS Error in transmit data",
									'A4': "Format Error in transmit data",
									'A5': "Data Error in transmit data",
									'A8': "Frame Length Error in transmit data"
										})

PLC_STATUS_DATA_ERROR_MESSAGE = dict({	'00': "Normal Completion",
										'13': "FCS error",
										'14': "Format error",
										'15': "Entry number data error",
										'18': "Frame length error",
										'21': "Not executable due to CPU Unit CPU error"
										})
PLC_STATUS_FAIL_TO_DECODE_RESPONSE = 255