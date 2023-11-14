import string
import io

kinda_gml_whitespace = (
	' \t\v\f'
	'\u0085\u00A0\u1680\u180E\u2000\u2001\u2002\u2003'
	'\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u200B'
	'\u200C\u200D\u2028\u2029\u202F\u205F\u2060\u3000'
	'\uFEFF'
)
"""
dont use skip whitespace bc we need newlines (including \\r, since
windows loves to do \\r\\n instead of just \\n -_-

otherwise taken from:

https://manual.yoyogames.com/#t=Additional_Information%2FWhitespace_Characters.htm
"""

all_gml_whitespace = '\r\n'+kinda_gml_whitespace
"https://manual.yoyogames.com/#t=Additional_Information%2FWhitespace_Characters.htm"


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
	for ch in iter(lambda: f.read(1), ''):
		if ch == '\\':
			ch = f.read(1)
			match ch:
				case '\\' | '"': pass # the character escaped is the same as the seq
				case 'r': ch = '\x0D'
				case 'n': ch = '\x0A'
				case 'b': ch = '\x08'
				case 'f': ch = '\x0C'
				case 't': ch = '\x09'
				case 'v': ch = '\x0B'
				case 'a': ch = '\x07'
				case 'u': ch = read_esc_num(4, 16, 'unicode')
				case 'x': ch = read_esc_num(2, 16, 'hex')
				case _ if '0' <= ch <= '7':
					f.seek(-1, io.SEEK_CUR)
					ch = read_esc_num(1, 8, 'octal')
				case '':
					raise DigestStringError(f'Hit end of string before finding escape sequence type!')
				case _:
					raise DigestStringError(f'Unknown string escape sequence \\{ch}!')
		outs += ch
	return outs

