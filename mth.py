import string
from strreader import StringReader
import io

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


def digest_string (s: str):
	# gurgle -v-"
	class DigestStringError(Exception):
		pass

	# i would use newline=None, but that brings up questions
	# relating to slicing and seek position. oh well. guess ill have
	# to handle windows style newlines myself anyways -_-
	f = io.StringIO(s)
	def read_esc_num (length: int, base: int, typeof: str):
		try:
			t = f.tell()
			chars = s[t:t+length]
			if len(chars) < length:
				raise DigestStringError(f'Not enough chars for {typeof} esc seq: "{chars}"')
			v = int(chars, base)
			f.seek(t + length)
			return chr(v)
		except Exception as e:
			raise DigestStringError(f'Problem digesting string {typeof} escape seq: {e}')

	outs = ''
	while (ch:=f.read(1)) != '':
		if ch == '\\':
			ch = f.read(1)
			match ch:
				case '\\': pass
				case '"':  ch = '"'
				case 'r':  ch = '\x0D'
				case 'n':  ch = '\x0A'
				case 'b':  ch = '\x08'
				case 'f':  ch = '\x0C'
				case 't':  ch = '\x09'
				case 'v':  ch = '\x0B'
				case 'a':  ch = '\x07'
				case 'u':  ch = read_esc_num(4, 16, 'unicode')
				case 'x':  ch = read_esc_num(2, 16, 'hex')
				case ch if '0' <= ch <= '7':
					f.seek(-1, io.SEEK_CUR)
					ch = read_esc_num(1, 8, 'octal')
				case '':
					raise DigestStringError(f'Hit end of string before finding escape sequence type!')
				case _:
					raise DigestStringError(f'Unknown string escape sequence \\{ch}!')
		outs += ch
	return outs
	# _f = StringReader(s)
	# def read_esc_num (length: int, base: int, typeof: str):
	# 	try:
	# 		t = _f.tell()
	# 		chars = _f.text[t:t+length]
	# 		if len(chars) < length:
	# 			raise DigestStringError(f'Not enough chars for {typeof} esc seq: "{chars}"')
	# 		v = int(chars, base)
	# 		_f.seek(t + length)
	# 		return chr(v)
	# 	except Exception as e:
	# 		raise DigestStringError(f'problem digesting string {typeof} escape seq: {e}')
	#
	# outs = ''
	# while _f.can_read():
	# 	ch = _f.read()
	# 	if ch == '\\':
	# 		if _f.vore('\\'): pass
	# 		elif _f.vore('"'): ch = '"'
	# 		elif _f.vore('r'): ch = '\x0D'
	# 		elif _f.vore('n'): ch = '\n'
	# 		elif _f.vore('b'): ch = '\x08'
	# 		elif _f.vore('f'): ch = '\x0c'
	# 		elif _f.vore('t'): ch = '\t'
	# 		elif _f.vore('v'): ch = '\x0b'
	# 		elif _f.vore('a'): ch = '\x07'
	# 		elif _f.vore('u'): ch = read_esc_num(4, 16, 'unicode')
	# 		elif _f.vore('x'): ch = read_esc_num(2, 16, 'hex')
	# 		elif '0' <= _f.peek() <= '7': ch = read_esc_num(1, 8, 'octal')
	# 		elif _f.peek() == '':
	# 			raise DigestStringError(f'Hit end of string before finding escape sequence type!')
	# 		else:
	# 			raise DigestStringError(f'Unknown string escape sequence \\{ch}!')
	# 	outs += ch
	# return outs
