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

PLC_CODE_OK = 0


# Timeouts in seconds
plc_serial_port_timeout =30
roof_moving_timeout = 120
telescope_coms_timeout = 30
tcs_coms_timeout = 60


#Other parameters
pass_coord_attempts = 2
tcs_conn_tries_total =3