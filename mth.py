import string

def is_letter (ch: str):
	return ch in string.ascii_letters

def is_number (ch: str):
	return ch in string.digits

def is_identifier (ch: str):
	return is_letter(ch) or is_number(ch) or ch == '_'

def is_allowed_number_hex (ch: str):
	return ch in string.hexdigits or ch == '_'

def is_allowed_number_bin (ch: str):
	return ch in '_01'

def is_allowed_number_lit (ch: str):
	return is_number(ch) or ch == '_'
