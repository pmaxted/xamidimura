"""
test_roof_control_functions.py
Jessica A. Evans
03/01/2019

Contains unit tests for the roof_control_function script. All the command/response strings here
	are what I believe are accurate strings that could come from the PLC based on my
	understanding of the manual, but I have not checked explicitly. The exceptions are those that are
	designed to test failures.
	
	Currently tests:
		- plc_string_is_valid
		- plc_insert_fcs
		- plc_mode
		- plc_status_request_response_plc
		- plc_tilt_status
		- plc_status_comms_timeout
		- plc_status_power_timeout
		- plc_status_status_code
		- plc_status_end_code
		- plc_status_write_response_end_code
		- plc_status_write_error_message
		- plc_status_error_message
		- plc_data_error_message
		- int_bit_is_set
		- set_hex_bit
		- unset_hex_bit
		- hex_bit_is_set
	
	
"""

import unittest
import roof_control_functions
import settings_and_error_codes as set_err_codes


class test_command_response(unittest.TestCase):

	def test_not_valid_string(self):

		with self.assertRaises(ValueError):
			roof_control_functions.plc_command_response('Hi')

class test_string_is_valid(unittest.TestCase):

	#Things we know are valid
	#	"@00RD0150000351*\r" - (request roof status)
	#	"@00MS5E*\r" - (request plc status)

	#Things that are not valid...
	# - missing the @
	# - missing node number (00)
	# - missing the *\r terminator
	# - missing a header code
	# incorrect frame check sequence (FCS)
	def test_ok_string_request_roof_status(self):
		#	"@00RD0150000351*\r" - (request roof status)
		expected = True
		actual = roof_control_functions.plc_string_is_valid("@00RD0150000351*\r")
	
		self.assertEqual(expected,actual)
	
	def test_ok_string_request_plc_status(self):
		#	"@00MS5E*\r" - (request plc status)
		expected = True
		actual = roof_control_functions.plc_string_is_valid("@00MS5E*\r")
	
		self.assertEqual(expected,actual)

	def test_check_leading_symbol(self):
		# - missing the @
		expected = False
		actual = roof_control_functions.plc_string_is_valid("00RD0150000351*\r")

		self.assertEqual(expected,actual)

	def test_check_terminator(self):
		# - missing the *\r
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@00RD0150000351")

		self.assertEqual(expected,actual)

	def test_check_node_number_missing_one_zero(self):
		# - missing the 00 after @
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@0RD0150000351*\r")
		self.assertEqual(expected,actual)

	def test_check_node_number_missing_two_zero(self):
		# - missing the 00 after @
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@RD0150000351*\r")
		self.assertEqual(expected,actual)

	def test_check_node_number_wrong_numbers(self):
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@12RD0150000351*\r")
		self.assertEqual(expected,actual)

	def test_wrong_fcs(self):
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@00RD0150000352*\r")
	
		self.assertEqual(expected,actual)

	def test_number_header_code(self):
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@00120150000351*\r")
	
		self.assertEqual(expected,actual)

	def test_no_content(self):
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@00M5E*\r")
	
		self.assertEqual(expected,actual)


class test_insert_fcs(unittest.TestCase):

	def test_has_no_trailing_00(self):
		expected = False
		actual = roof_control_functions.plc_insert_fcs("@00RD0150000351*\r")
	
		self.assertEqual(expected,actual)

	def test_should_be_ok(self):
		expected = "@00RD0150000351*\r"
		actual = roof_control_functions.plc_insert_fcs("@00RD0150000300*\r")
	
		self.assertEqual(expected,actual)

	def test_check_leading_symbol(self):
		# - missing the @
		expected = False
		actual = roof_control_functions.plc_string_is_valid("00RD0150000300*\r")

		self.assertEqual(expected,actual)

	def test_check_terminator(self):
		# - missing the *\r
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@00RD0150000300")

		self.assertEqual(expected,actual)

	def test_check_node_number_missing_one_zero(self):
		# - missing the 00 after @
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@0RD0150000300*\r")
		self.assertEqual(expected,actual)

	def test_check_node_number_missing_two_zero(self):
		# - missing the 00 after @
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@RD0150000300*\r")
		self.assertEqual(expected,actual)

	def test_check_node_number_wrong_numbers(self):
		expected = False
		actual = roof_control_functions.plc_string_is_valid("@12RD0150000300*\r")
		self.assertEqual(expected,actual)

class test_plc_mode(unittest.TestCase):

	def test_program_mode(self):
		expected = set_err_codes.PLC_STATUS_MODE['0']
		actual = roof_control_functions.plc_mode("@00MS0000A827*\r")
		self.assertEqual(expected,actual)

	def test_run_mode(self):
		expected = set_err_codes.PLC_STATUS_MODE['2']
		actual = roof_control_functions.plc_mode("@00MS0002A825*\r")
		self.assertEqual(expected,actual)

	def test_monitor_mode(self):
		expected = set_err_codes.PLC_STATUS_MODE['3']
		actual = roof_control_functions.plc_mode("@00MS0003A824*\r")
		self.assertEqual(expected,actual)
	
	def test_unknown_mode(self):
		expected = set_err_codes.PLC_STATUS_UNKNOWN_MODE
		actual = roof_control_functions.plc_mode("@00MS0004A823*\r")
		self.assertEqual(expected,actual)

	def test_bad_fcs(self):
		expected = set_err_codes.PLC_STATUS_INVALID_RESPONSE
		actual = roof_control_functions.plc_mode("@00MS0003A825*\r")
		self.assertEqual(expected,actual)

	def test_bad_in_string(self):
		expected = set_err_codes.PLC_STATUS_INVALID_RESPONSE
		actual = roof_control_functions.plc_mode("00MS0003A825*\r")
		self.assertEqual(expected,actual)


class test_plc_status_request_response_plc(unittest.TestCase):

	def test_normal_status(self):
		expected = set_err_codes.PLC_STATUS_STATUS['0']
		actual = roof_control_functions.plc_status_request_response_plc("@00MS0000A827*\r")
		self.assertEqual(expected,actual)
	
	def test_fatal_error(self):
		expected = set_err_codes.PLC_STATUS_STATUS['1']
		actual = roof_control_functions.plc_status_request_response_plc("@00MS0010A826*\r")
		self.assertEqual(expected,actual)

	def test_FALS_error(self):
		expected = set_err_codes.PLC_STATUS_STATUS['8']
		actual = roof_control_functions.plc_status_request_response_plc("@00MS0080A82F*\r")
		self.assertEqual(expected,actual)

	def test_unknown_error(self):
		expected = set_err_codes.PLC_STATUS_UNKNOWN_STATUS
		actual = roof_control_functions.plc_status_request_response_plc("@00MS0040A823*\r")[:20]
		self.assertEqual(expected,actual)
	
	def test_bad_fcs(self):
		expected = set_err_codes.PLC_STATUS_INVALID_RESPONSE
		actual = roof_control_functions.plc_status_request_response_plc("@00MS0003A825*\r")
		self.assertEqual(expected,actual)

	def test_bad_string_no_symbol(self):
		expected = set_err_codes.expected = set_err_codes.PLC_STATUS_INVALID_RESPONSE
		actual = roof_control_functions.plc_status_request_response_plc("00MS0000A827*\r")
		self.assertEqual(expected,actual)

	def test_bad_string_no_terminator(self):
		expected = set_err_codes.expected = set_err_codes.PLC_STATUS_INVALID_RESPONSE
		actual = roof_control_functions.plc_status_request_response_plc("@00MS0000A827")
		self.assertEqual(expected,actual)



class test_plc_status_tilt_status(unittest.TestCase):
	# * NOTE the 0150 hex code representing the set bit for the status is not a valid status
	# but tests don't care about that part of the response
	def test_tilt_tel_drive_control_east_limit(self):
		expected = 27136 # tel drive control set and reach east limit (110101000000000)
		actual = roof_control_functions.plc_status_tilt_status("@00RD0001500000270F6A0056*\r")
		self.assertEqual(expected,actual)
	
	def test_tilt_west_1hr(self):
		expected = 512 # between 1hor west and 6hour west (000001000000000)
		actual = roof_control_functions.plc_status_tilt_status("@00RD0001500000270F020023*\r")
		self.assertEqual(expected,actual)

	def test_tilt_wrong_fcs(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_tilt_status("@00RD0001500000270F200022*\r")
		self.assertEqual(expected,actual)

	def test_tilt_no_symbol(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_tilt_status("00RD0001500000270F200023*\r")
		self.assertEqual(expected,actual)

	def test_tilt_no_terminator(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_tilt_status("@00RD0001500000270F200023\r")
		self.assertEqual(expected,actual)


class test_plc_status_comms_timeout(unittest.TestCase):
	# * NOTE the 0150 hex code representing the set bit for the status is not a valid status
	# but tests don't care about that part of the response
	def test_comms_high_limit(self):
		expected = 9999
		actual = roof_control_functions.plc_status_comms_timeout("@00RD0001500000270F21*\r")
		self.assertEqual(expected,actual)
	
	def test_comms_low_limit(self):
		expected = 0
		actual = roof_control_functions.plc_status_comms_timeout("@00RD0001500000000052*\r")
		self.assertEqual(expected,actual)
	
	def test_comms_too_high_limit(self):
		expected = 43690
		actual = roof_control_functions.plc_status_comms_timeout("@00RD0001500000AAAA52*\r")
		self.assertEqual(expected,actual)

	def test_comms_wrong_fcs(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_comms_timeout("@00RD0001500000000051*\r")
		self.assertEqual(expected,actual)

	def test_comms_no_symbol(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_comms_timeout("00RD0001500000000052*\r")
		self.assertEqual(expected,actual)

	def test_comms_no_terminator(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_comms_timeout("@00RD0001500000000052\r")
		self.assertEqual(expected,actual)



class test_plc_status_power_timeout(unittest.TestCase):
	# * NOTE the 0150 hex code representing the set bit for the status is not a valid status
	# but tests don't care about that part of the response
	def test_power_high_limit(self):
		expected = 9999
		actual = roof_control_functions.plc_status_power_timeout("@00RD000150270F000021*\r")
		self.assertEqual(expected,actual)
	
	def test_power_low_limit(self):
		expected = 0
		actual = roof_control_functions.plc_status_power_timeout("@00RD0001500000000052*\r")
		self.assertEqual(expected,actual)
	
	def test_power_too_high_limit(self):
		expected = 43690
		actual = roof_control_functions.plc_status_power_timeout("@00RD000150AAAA000052*\r")
		self.assertEqual(expected,actual)

	def test_power_wrong_fcs(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_power_timeout("@00RD0001500000000051*\r")
		self.assertEqual(expected,actual)

	def test_power_no_symbol(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_power_timeout("00RD0001500000000052*\r")
		self.assertEqual(expected,actual)

	def test_power_no_terminator(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_power_timeout("@00RD0001500000000052")
		self.assertEqual(expected,actual)



class test_plc_status_status_code(unittest.TestCase):
	
	def test_status_ok_code_1(self):
		expected = 45061 #(represents '1011000000000101', i.e. closed, mains, no rain, no control req,
						 # accept both delays, not request telescope control, watchdog reset)
		actual = roof_control_functions.plc_status_status_code("@00RD00B005270F000052*\r")
		self.assertEqual(expected,actual)
	
	def test_status_ok_code_2(self):
		expected = 40973 #(represents '1010000000001101', in case I got the bits in the one above
						 #  around the wrong way
		actual = roof_control_functions.plc_status_status_code("@00RD00A00D270F000020*\r")
		self.assertEqual(expected,actual)
	
	def test_status_too_many_bits(self):
		expected = 90123 #(represents 10110000000001011', 17 bits
		actual = roof_control_functions.plc_status_status_code("@00RD001600B270F000060*\r")
		self.assertNotEqual(expected,actual)
	
	def test_status_wrong_fcs(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_status_code("@00RD00B005270F000051*\r")
		self.assertEqual(expected,actual)
	
	def test_status_no_symbol(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_status_code("00RD00B005270F000052*\r")
		self.assertEqual(expected,actual)

	def test_status_no_terminator(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_status_code("@00RD00B005270F000052*")
		self.assertEqual(expected,actual)

	def test_status_RANDOM_TEST(self):
		expected = 3
		actual = roof_control_functions.plc_status_status_code("@00RD000003270F000026*\r")
		self.assertEqual(expected,actual)



class test_plc_status_end_code(unittest.TestCase):

	def test_status_normal_code(self):
		expected = 0
		actual = roof_control_functions.plc_status_end_code("@00RD00B005270F000052*\r")
		self.assertEqual(expected,actual)

	def test_status_FCS_error_code(self):
		expected = 13 #13 in hexcode = 0D
		actual = roof_control_functions.plc_status_end_code("@00RD0DB005270F000026*\r")
		self.assertEqual(expected,actual)

	def test_status_Format_error_code(self):
		expected = 14 #14 in hexcode = 0E
		actual = roof_control_functions.plc_status_end_code("@00RD0EB005270F000027*\r")
		self.assertEqual(expected,actual)

	def test_status_entry_no_data_error_code(self):
		expected = 15 #15 in hexcode = 0F
		actual = roof_control_functions.plc_status_end_code("@00RD0FB005270F000024*\r")
		self.assertEqual(expected,actual)

	def test_status_frame_length_error_code(self):
		expected = 18 #15 in hexcode = 12
		actual = roof_control_functions.plc_status_end_code("@00RD12B005270F000051*\r")
		self.assertEqual(expected,actual)

	def test_status_CPU_error_code(self):
		expected = 21 #21 in hexcode = 15
		actual = roof_control_functions.plc_status_end_code("@00RD15B005270F000056*\r")
		self.assertEqual(expected,actual)

	def test_status_code_wrong_fcs(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_end_code("@00RD00B005270F000051*\r")
		self.assertEqual(expected,actual)

	def test_status_code_no_symbol(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_end_code("00RD00B005270F000052*\r")
		self.assertEqual(expected,actual)

	def test_status_code_no_terminator(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_end_code("@00RD00B005270F000052")
		self.assertEqual(expected,actual)

class test_plc_status_write_response_end_code(unittest.TestCase):

	def test_WR_normal_endcode(self):
		expected = 0
		actual = roof_control_functions.plc_status_write_response_end_code("@00SC0050*\r")
		self.assertEqual(expected,actual)

	def test_WR_FCS_error_endcode(self):
		expected = 13
		actual = roof_control_functions.plc_status_write_response_end_code("@00SC0D24*\r")
		self.assertEqual(expected,actual)

	def test_WR_format_error_endcode(self):
		expected = 14
		actual = roof_control_functions.plc_status_write_response_end_code("@00SC0E25*\r")
		self.assertEqual(expected,actual)

	def test_WR_entry_number_data_error_endcode(self):
		expected = 15
		actual = roof_control_functions.plc_status_write_response_end_code("@00SC0F26*\r")
		self.assertEqual(expected,actual)

	def test_WR_frame_length_error_endcode(self):
		expected = 18
		actual = roof_control_functions.plc_status_write_response_end_code("@00SC1253*\r")
		self.assertEqual(expected,actual)

	def test_WR_not_executable_endcode(self):
		expected = 19
		actual = roof_control_functions.plc_status_write_response_end_code("@00SC1352*\r")
		self.assertEqual(expected,actual)

	def test_WR_CPU_error_endcode(self):
		expected = 21
		actual = roof_control_functions.plc_status_write_response_end_code("@00SC1554*\r")
		self.assertEqual(expected,actual)

	def test_WR_endcode_no_symbol(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_write_response_end_code("00SC0050*\r")
		self.assertEqual(expected,actual)

	def test_WR_endcode_no_terminator(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_write_response_end_code("@00SC0050")
		self.assertEqual(expected,actual)

	def test_WR_endcode_wrong_fcs(self):
		expected = set_err_codes.PLC_STATUS_FAIL_TO_DECODE_RESPONSE
		actual = roof_control_functions.plc_status_write_response_end_code("@00SC0051*\r")
		self.assertEqual(expected,actual)


class test_plc_status_write_error_message(unittest.TestCase):

	def test_write_error_message_normal(self):
		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['00']
		actual = roof_control_functions.plc_status_write_error_message(0)
		self.assertEqual(expected,actual)

	def test_write_error_message_normal_with_full_response(self):
		#the dict key has to be a string, this would fail if it not
		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['00']
		actual = roof_control_functions.plc_status_write_error_message(roof_control_functions.plc_status_write_response_end_code("@00SC0050*\r"))
		self.assertEqual(expected,actual)
	
	def test_write_error_message_19_with_full_response(self):
		#the dict key has to be a string, this would fail if it not
		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['19']
		actual = roof_control_functions.plc_status_write_error_message(roof_control_functions.plc_status_write_response_end_code("@00SC1958*\r"))
		self.assertEqual(expected,actual)

	def test_write_error_messages_valid_codes(self):

		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['13']
		actual = roof_control_functions.plc_status_write_error_message(19)
		self.assertEqual(expected,actual)

		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['14']
		actual = roof_control_functions.plc_status_write_error_message(20)
		self.assertEqual(expected,actual)

		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['15']
		actual = roof_control_functions.plc_status_write_error_message(21)
		self.assertEqual(expected,actual)

		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['18']
		actual = roof_control_functions.plc_status_write_error_message(24)
		self.assertEqual(expected,actual)

		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['19']
		actual = roof_control_functions.plc_status_write_error_message(25)
		self.assertEqual(expected,actual)

		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['21']
		actual = roof_control_functions.plc_status_write_error_message(33)
		self.assertEqual(expected,actual)


	def test_write_error_messages_invalid_codes(self):
	
		invalid_codes = [23,-1]
		for i in invalid_codes:
			expected = set_err_codes.PLC_STATUS_UNKNOWN_STATUS
			actual = roof_control_functions.plc_status_write_error_message(i)[:20]
			self.assertEqual(expected,actual)

class test_plc_status_error_message(unittest.TestCase):
	
	def test_error_message_normal(self):
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['00']
		actual = roof_control_functions.plc_status_error_message(0)
		self.assertEqual(expected,actual)
	
	def test_error_messages_valid_codes(self):
	
		#valid_codes = [1,2,4,'08','13','14','15','18','19','23','A3','A4','A5','A8']
		
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['01']
		actual = roof_control_functions.plc_status_error_message(1)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['02']
		actual = roof_control_functions.plc_status_error_message(2)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['04']
		actual = roof_control_functions.plc_status_error_message(4)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['08']
		actual = roof_control_functions.plc_status_error_message(8)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['13']
		actual = roof_control_functions.plc_status_error_message(19)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['14']
		actual = roof_control_functions.plc_status_error_message(20)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['15']
		actual = roof_control_functions.plc_status_error_message(21)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['18']
		actual = roof_control_functions.plc_status_error_message(24)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['19']
		actual = roof_control_functions.plc_status_error_message(25)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['23']
		actual = roof_control_functions.plc_status_error_message(35)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['A3']
		actual = roof_control_functions.plc_status_error_message(163)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['A4']
		actual = roof_control_functions.plc_status_error_message(164)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['A5']
		actual = roof_control_functions.plc_status_error_message(165)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['A8']
		actual = roof_control_functions.plc_status_error_message(168)
		self.assertEqual(expected,actual)
	
	
	def test_error_message_A3_with_full_response(self):
		#the dict key has to be a string, this would fail if it not
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['A3']
		actual = roof_control_functions.plc_status_error_message(roof_control_functions.plc_status_write_response_end_code('@00SCA322*\r'))
		self.assertEqual(expected,actual)

	def test_error_message_01_with_full_response(self):
		#the dict key has to be a string, this would fail if it not
		expected = set_err_codes.PLC_STATUS_ERROR_MESSAGE['01']
		actual = roof_control_functions.plc_status_error_message(roof_control_functions.plc_status_write_response_end_code('@00SC0151*\r'))
		self.assertEqual(expected,actual)

	def test_get_key_error(self):

		expected = set_err_codes.PLC_STATUS_UNKNOWN_STATUS #38 represents an error code of 26, which is not valid
		actual = roof_control_functions.plc_status_error_message(38)[:20]
		self.assertEqual(expected,actual)


class test_plc_status_data_error_message(unittest.TestCase):

	def test_data_error_message_normal(self):
		expected = set_err_codes.PLC_STATUS_DATA_ERROR_MESSAGE['00']
		actual = roof_control_functions.plc_data_error_message(0)
		self.assertEqual(expected,actual)

	def test_data_error_message_normal_with_full_response(self):
		#the dict key has to be a string, this would fail if it not
		expected = set_err_codes.PLC_STATUS_DATA_ERROR_MESSAGE['00']
		actual = roof_control_functions.plc_data_error_message(roof_control_functions.plc_status_end_code("@00RD00B005270F000052*\r"))
		self.assertEqual(expected,actual)
	
	def test_data_error_message_18_with_full_response(self):
		#the dict key has to be a string, this would fail if it not
		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['18']
		actual = roof_control_functions.plc_data_error_message(roof_control_functions.plc_status_end_code("@00RD18B005270F00005B*\r"))
		self.assertEqual(expected,actual)
	
	def test_data_error_message_21_with_full_response(self):
		#the dict key has to be a string, this would fail if it not
		expected = set_err_codes.PLC_STATUS_WRITE_ERROR_MESSAGE['21']
		actual = roof_control_functions.plc_data_error_message(roof_control_functions.plc_status_end_code("@00RD21B005270F000051*\r"))
		self.assertEqual(expected,actual)

	def test_data_error_messages_valid_codes(self):

		expected = set_err_codes.PLC_STATUS_DATA_ERROR_MESSAGE['13']
		actual = roof_control_functions.plc_data_error_message(19)
		self.assertEqual(expected,actual)

		expected = set_err_codes.PLC_STATUS_DATA_ERROR_MESSAGE['14']
		actual = roof_control_functions.plc_data_error_message(20)
		self.assertEqual(expected,actual)

		expected = set_err_codes.PLC_STATUS_DATA_ERROR_MESSAGE['15']
		actual = roof_control_functions.plc_data_error_message(21)
		self.assertEqual(expected,actual)

		expected = set_err_codes.PLC_STATUS_DATA_ERROR_MESSAGE['18']
		actual = roof_control_functions.plc_data_error_message(24)
		self.assertEqual(expected,actual)
	
		expected = set_err_codes.PLC_STATUS_DATA_ERROR_MESSAGE['21']
		actual = roof_control_functions.plc_data_error_message(33)
		self.assertEqual(expected,actual)
	
	def test_data_error_messages_invalid_codes(self):
	
		invalid_codes = [23,-1]
		for i in invalid_codes:
			expected = set_err_codes.PLC_STATUS_UNKNOWN_STATUS
			actual = roof_control_functions.plc_data_error_message(i)[:20]
			self.assertEqual(expected,actual)

class test_int_bit_is_set(unittest.TestCase):

	def test_bits_0_and_4(self):

		test_int = 17 # represents status 0011, a closed roof and raining, everything else not set
		expected_0 = True
		expected_4 = True
		expected_other = False

		actual_0 = roof_control_functions.int_bit_is_set(test_int, 0)
		actual_4 = roof_control_functions.int_bit_is_set(test_int, 4)
		self.assertEqual(expected_0,actual_0)
		self.assertEqual(expected_4,actual_4)
		
		other_bits = [1,2,3,5,6,7,8,9,10,11,12,13,14,15]
		for i in other_bits:
			actual = roof_control_functions.int_bit_is_set(test_int,i)
			self.assertEqual(expected_other,actual)

	def test_negative_intNo(self):
		
		with self.assertRaises(ValueError):
			roof_control_functions.int_bit_is_set(-1,0)

	def test_non_integer_intNo(self):

		with self.assertRaises(ValueError):
			roof_control_functions.int_bit_is_set(1.345,0)

		with self.assertRaises(ValueError):
			roof_control_functions.int_bit_is_set('dsfs',0)

	def test_non_integer_offset(self):
	
		with self.assertRaises(ValueError):
			roof_control_functions.int_bit_is_set(17,0.2424)

		with self.assertRaises(ValueError):
			roof_control_functions.int_bit_is_set(17,'gdsfjs')

	def test_high_limit_offset(self):

		with self.assertRaises(ValueError):
			roof_control_functions.int_bit_is_set(17,16)

		#Check that 15 is ok
		expected = False
		actual = roof_control_functions.int_bit_is_set(17,15)
		self.assertEqual(expected,actual)

	def test_low_limit_offset(self):

		with self.assertRaises(ValueError):
			roof_control_functions.int_bit_is_set(17,-1)

		#Check that 0 is ok
		expected = True
		actual = roof_control_functions.int_bit_is_set(17,0)
		self.assertEqual(expected,actual)

class test_set_hex_bit(unittest.TestCase):

	def test_set_bit_5(self):
		test_hex = '0001'
		expected = '0021'

		actual = roof_control_functions.set_hex_bit(test_hex,5)
		self.assertEqual(expected,actual)

	def test_set_bit_1(self):
		test_hex = '0020'
		expected = '0021'

		actual = roof_control_functions.set_hex_bit(test_hex,0)
		self.assertEqual(expected,actual)

	def test_set_hex_high_limit_offset(self):

		with self.assertRaises(ValueError):
			roof_control_functions.set_hex_bit('0021',16)

		#Check that 15 is ok
		expected = '8001'
		actual = roof_control_functions.set_hex_bit('0001',15)
		self.assertEqual(expected,actual)

	def test_low_limit_offset(self):

		with self.assertRaises(ValueError):
			roof_control_functions.set_hex_bit('0020',-1)

	def test_non_integer_offset(self):
	
		with self.assertRaises(ValueError):
			roof_control_functions.set_hex_bit('0020',0.2424)

		with self.assertRaises(ValueError):
			roof_control_functions.set_hex_bit('0020','gdsfjs')

class test_unset_hex(unittest.TestCase):

	def test_unset_bit_5(self):
		test_hex = '0021' #Repesents number 33 in hex, which is 10001 in binary, meaning bit 5 and 0 are set
		expected = '0001' # Once bit 5 is unset, expecting to get 1, or 00001 in binary

		actual = roof_control_functions.unset_hex_bit(test_hex,5)
		self.assertEqual(expected,actual)

	def test_unset_bit_1(self):
		test_hex = '0021' #Repesents number 33 in hex, which is 10001 in binary, meaning bit 5 and 0 are set
		expected = '0020' # Once bit 0 is unset, expecting to get 32, or 10000 in binary

		actual = roof_control_functions.unset_hex_bit(test_hex,0)
		self.assertEqual(expected,actual)

	def test_high_limit_offset(self):

		with self.assertRaises(ValueError):
			roof_control_functions.unset_hex_bit('0021',16)

		#Check that 15 is ok
		expected = '0021'
		actual = roof_control_functions.unset_hex_bit('0021',15)
		self.assertEqual(expected,actual)

	def test_low_limit_offset(self):

		with self.assertRaises(ValueError):
			roof_control_functions.unset_hex_bit('0021',-1)

	def test_non_integer_offset(self):
	
		with self.assertRaises(ValueError):
			roof_control_functions.unset_hex_bit('0021',0.2424)

		with self.assertRaises(ValueError):
			roof_control_functions.unset_hex_bit('0021','gdsfjs')


class test_hex_bit_is_set(unittest.TestCase):

	def test_hex_bits_0_and_5(self):

		test_hex = 33 # represents status 0011, a closed roof and raining, everything else not set
		expected_0 = True
		expected_5 = True
		expected_other = False

		actual_0 = roof_control_functions.hex_bit_is_set(test_hex, 0)
		actual_5 = roof_control_functions.hex_bit_is_set(test_hex, 5)
		self.assertEqual(expected_0,actual_0)
		self.assertEqual(expected_5,actual_5)
		
		other_bits = [1,2,3,4,6,7,8,9,10,11,12,13,14,15]
		for i in other_bits:
			actual = roof_control_functions.hex_bit_is_set(test_hex,i)
			self.assertEqual(expected_other,actual)


	def test_non_integer_hex_offset(self):
	
		with self.assertRaises(ValueError):
			roof_control_functions.hex_bit_is_set(33,0.2424)

		with self.assertRaises(ValueError):
			roof_control_functions.hex_bit_is_set(33,'gdsfjs')

	def test_high_limit_hex_offset(self):

		with self.assertRaises(ValueError):
			roof_control_functions.hex_bit_is_set(33,16)

		#Check that 15 is ok
		expected = False
		actual = roof_control_functions.hex_bit_is_set(33,15)
		self.assertEqual(expected,actual)

	def test_low_limit_offset(self):

		with self.assertRaises(ValueError):
			roof_control_functions.hex_bit_is_set(33,-1)

		#Check that 0 is ok
		expected = True
		actual = roof_control_functions.hex_bit_is_set(33,0)
		self.assertEqual(expected,actual)


if __name__ =='__main__':
	unittest.main()