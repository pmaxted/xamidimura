import unittest
import focuser_control

class test_start_end_command_char(unittest.TestCase):

	def test_add_chars_letters(self):

		expected = '<Hello>'
		actual = focuser_control.get_start_end_char('Hello')

		self.assertEqual(expected, actual)

	def test_add_chars_numbers(self):

		expected = '<00421>'
		actual = focuser_control.get_start_end_char('00421')

		self.assertEqual(expected,actual)

	def test_add_char_param(self):
		expected = '<123>'
		test_param = 123
		actual = focuser_control.get_start_end_char(test_param)
		
		self.assertEqual(expected,actual)


if __name__=="__main__":
	unittest.main()