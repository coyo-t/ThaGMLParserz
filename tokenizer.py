from pathlib import Path

import mth
from gml_keywords import gml_keywords
from strreader import StringReader
from tokens import *


class ParseError(Exception):
	pass


class ParseNumberError(ParseError):
	pass


class DigestStringError(ParseError):
	pass


KINDA_WHITESPACE = lambda ch: ch in ' \t\v\f'
"""
dont use skip whitespace bc we need newlines (including \\r, since
windows loves to do \\r\\n instead of just \\n -_-
"""

def digest_string (s: str):
	# gurgle -v-"
	f = StringReader(s)
	def read_esc_num (length: int, base: int, typeof: str):
		try:
			t = f.tell()
			chars = f.text[t:t+length]
			if len(chars) < length:
				raise DigestStringError(f'Not enough chars for {typeof} esc seq: "{chars}"')
			v = int(chars, base)
			f.seek(t + length)
			return chr(v)
		except Exception as e:
			raise DigestStringError(f'problem digesting string {typeof} escape seq: {e}')

	outs = ''
	while f.can_read():
		ch = f.read()
		if ch == '\\':
			if f.vore('\\'): pass
			elif f.vore('"'): ch = '"'
			elif f.vore('r'): ch = '\x0D'
			elif f.vore('n'): ch = '\n'
			elif f.vore('b'): ch = '\x08'
			elif f.vore('f'): ch = '\x0c'
			elif f.vore('t'): ch = '\t'
			elif f.vore('v'): ch = '\x0b'
			elif f.vore('a'): ch = '\x07'
			elif f.vore('u'): ch = read_esc_num(4, 16, 'unicode')
			elif f.vore('x'): ch = read_esc_num(2, 16, 'hex')
			elif '0' <= f.peek() <= '7': ch = read_esc_num(1, 8, 'octal')
			elif f.peek() == '':
				raise DigestStringError(f'Hit end of string before finding escape sequence type!')
			else:
				raise DigestStringError(f'Unknown string escape sequence \\{ch}!')
		outs += ch
	return outs


def read_multiline_comment (f: StringReader):
	depth = 0
	while True:
		if f.vore('*', '/'):
			if depth > 0:
				depth -= 1
				continue
			else:
				return
		# nested multi-line comments
		# GML doesnt suppourt them, but I Will Fuck You.
		# here its considered an error to have an unclosed multiline
		# comment inside another multiline comment. This is far more permissive
		# for multicomming out other blocks of text that may or may not have multiline
		# comments in them already.
		# That, or i could do something stupid like have the first pass of the tokenizer
		# do *just* comments and determine whether or not shits nested by whether it reaches
		# the end of the file and finds the depth is still greater than 0. that would
		# work I Guess, but damn if that isnt fucking stupid -_-
		elif f.vore('/', '*'):
			depth += 1
			continue
		elif f.peek() == '':
			raise ParseError('Unclosed multiline comment!')
		f.skip()


def read_hex_number (f: StringReader) -> Token:
	name = f.take_while(mth.is_allowed_number_hex)
	return NumberLiteralToken(int(name.replace('_', ''), 16))


def read_css_colour (f: StringReader) -> Token:
	name = f.take_while(mth.is_allowed_number_hex).replace('_', '')
	if (l:=len(name)) > 6:
		raise ParseNumberError(f'Too many digits for hex colour code #{name}!')
	elif l < 6:
		raise ParseNumberError(f'Not enough digits for hex colour code #{name}!')
	value = int(name, 16)
	return NumberLiteralToken(((value>>16)&0xFF)|(value&0x00FF00)|((value&0xFF)<<16))


def handle_macro (f: StringReader) -> Token:
	# So, the #macro x:y syntax is actually config:name,
	# not name:config. Why? i dont know! this is stupid! but okay

	def try_read_id ():
		if mth.is_number(ch:=f.peek()):
			raise ParseError(f'Macro parse error: ident started with number!')
		elif not mth.is_identifier(ch):
			if f.vore_newline():
				raise ParseError(f'Macro parse error: Unexpected newline in ident!')
			else:
				raise ParseError(f'Macro parse error: Unexpected symbol {ch} in ident!')
		else:
			return f.take_while(mth.is_identifier)

	f.take_while(KINDA_WHITESPACE)
	ident1 = try_read_id()
	if f.vore(':'):
		macrotoken = MacroToken(name=try_read_id(), configuration=ident1)
	else:
		macrotoken = MacroToken(name=ident1)

	f.take_while(KINDA_WHITESPACE)

	# this is dumb
	def pred (ch: str) -> bool:
		if ch == '\\':
			f.skip()
			if f.vore_newline():
				return True
			else:
				raise ParseError('Expected newline after continuator symbol in macro!')
		elif ch == '\r':
			if f.peek(1) == '\n':
				return False
		elif ch == '\n' or ch == '':
			return False
		return True

	body = f.take_while(pred)
	if body.endswith('\\'):
		body += '\n'
	macrotoken.body = tokenize(body, True)
	return macrotoken


def handle_number (f: StringReader) -> Token:
	start = f.tell()
	ch = f.read()

	is_float = False
	if ch == '.':
		# number is a float that omits the leading 0
		is_float = True

	# dont bother checking for the non-base 10 literals if we
	# already know we're parsing a float
	if not is_float and ch == '0':
		# might be parsing a hex or binary literal
		if f.vore('xX'): # hexliteral
			return read_hex_number(f)
		elif f.vore('bB'): # binliteral
			start = f.tell()
			f.take_while(mth.is_allowed_number_bin)
			return NumberLiteralToken(int(f.substr_from(start).replace('_', ''), 2))
	f.take_while(mth.is_allowed_number_lit)

	if f.peek() == '.':
		if is_float:
			# extra dot, not suppourted!
			raise ParseNumberError('Extra dot in numeric literal!')
		else:
			is_float = True
			f.skip()
	# still try to take more regardless of whether we know the number
	# is a float or not, as the numeric literal might leave off the
	# trailing dot; IE, `1.`
	f.take_while(mth.is_allowed_number_lit)
	if is_float:
		return NumberLiteralToken(float(f.substr_from(start).replace('_', '')))
	else:
		return NumberLiteralToken(int(f.substr_from(start).replace('_', '')))


def handle_string (f: StringReader, is_multiline: bool):
	start = f.tell()
	if is_multiline:
		while (ch:=f.peek()) != '':
			if ch == '"':
				tk = StringLiteralToken(f.substr_from(start))
				f.skip() # trailing "
				return tk
			f.skip()
		raise ParseError('Unclosed string')
	else:
		# im not actually sure why newlines arent fine in GML. theyd have
		# to explicitly check and stop parsing a string if they encounter a newline.
		# maybe their tokenizer works on individual lines hrm.
		while f.can_read():
			if f.vore_newline():
				raise ParseError('String broken by newline')
			elif f.peek() == '"':
				if f.prev() == '\\':
					f.skip()
					continue
				tk = StringLiteralToken(digest_string(f.substr_from(start)))
				f.skip() # trailing "
				return tk
			f.skip()
		raise ParseError('Unclosed string')

#TODO:
#	do string templ have escape seqs for { and }?
#	how does it handled unclosed {?
def handle_string_template (f: StringReader):
	# Maybe a little silly to duplicate code like this but uh.
	# ._. i dont care its easier
	start = f.tell()
	depth = 0
	mark = -1
	bracket_slices = list[slice]()
	while f.can_read():
		if f.vore_newline():
			if depth == 0:
				raise ParseError('String broken by newline')
			continue
		elif f.vore('\\', '"'):
			pass
		elif f.vore('{'):
			if depth == 0:
				mark = f.tell()-start
			depth += 1
			continue
		elif f.vore('}'):
			depth -= 1
			if depth < 0:
				depth = 0
			elif depth == 0:
				bracket_slices.append(slice(mark, f.tell()-1-start))
			continue
		elif f.peek() == '"':
			if depth != 0:
				f.skip()
				continue
			if len(bracket_slices) == 0:
				# string contains no expression blocks, treat it
				# as a regular str literal
				tk = StringLiteralToken(digest_string(f.substr_from(start)))
				f.skip() # trailing "
				return tk
			# operate on the string backwards, so that
			# slices dont have to be recalculated
			text = list(f.substr_from(start))
			f.skip() # trailing "
			tk = StringTemplateToken()
			i = len(bracket_slices) - 1
			for body in reversed(bracket_slices):
				tk.bodies.insert(0, tokenize(''.join(text[body])))
				text[body] = str(i)
				i -= 1
			tk.string = digest_string(''.join(text))
			return tk
		f.skip()
	raise ParseError('Unclosed string')


def tokenize (src: str, handle_whack_as_newline=False) -> Tokens:
	f = StringReader(src)
	tokens = Tokens()

	while f.can_read():
		f.take_while(KINDA_WHITESPACE)
		ch = f.read()

		match ch:
			case '':
				break
			#TODO:
			#	these two should RLE encode how many newlines in a row there were
			#	mostly because the *number* of newlines doesnt rlly matter ._.
			case '\r':
				if f.vore('\n'):
					tokens += NewlineToken()
				else:
					continue
			case '\n':
				tokens += NewlineToken()
			case '\\':
				if not handle_whack_as_newline:
					raise ParseError('Unexpected backslash in stream!')
				if f.vore_newline():
					tokens += NewlineToken()
				else:
					raise ParseError('Expected newline after backslash continuator!')
			case '/':
				if f.vore('/'):
					tokens += CommentToken(f.take_while(lambda c: c != '\n'), False)
					f.skip() # ending newline
				elif f.vore('*'):
					start = f.tell()
					read_multiline_comment(f)
					tokens += CommentToken(f.text[start : f.tell()-2], True)
				elif f.vore('='):
					tokens += InplaceOpToken(InplaceKind.DIV)
				else:
					tokens += SlashToken()
			case '.':
				# might be reading a decimal number that omits the leading 0
				if mth.is_number(f.peek()):
					f.rewind()
					tokens += handle_number(f)
				else:
					tokens += DotToken()
			case '"':
				tokens += handle_string(f, False)
			case '@':
				if f.vore('"'):
					tokens += handle_string(f, True)
				else:
					raise ParseError('Unexpected @ in stream!')
					# tokens += AtToken()
			case '$':
				if f.vore('"'):
					tokens += handle_string_template(f)
					# raise NotImplementedError('I HAVENT DONE FSTRINGS AAAAAAAAAA!!!!!!!!')
				else:
					if mth.is_allowed_number_hex(f.peek()):
						tokens += read_hex_number(f)
					else:
						raise ParseError('Unexpected midas hotkey in stream!')
			case '?':
				if f.vore('?'):
					if f.vore('='):
						tokens += InplaceOpToken(InplaceKind.NULL)
					else:
						tokens += NullishToken()
				else:
					tokens += QuestoToken()
			case '~': tokens += SquiggleToken()
			case '!':
				if f.vore('='):
					tokens += BangEqualsToken()
				else:
					tokens += LogicNotToken(False)
			case '=':
				if f.vore('='):
					tokens += DoubleEqualsToken()
				else:
					tokens += EqualsToken()
			case '{': tokens += LBraceToken()
			case '}': tokens += RBraceToken()
			case '(': tokens += LWhiffleToken()
			case ')': tokens += RWhiffleToken()
			case '[':
				if   f.vore('|'): tokens += SpecialAccessorToken(AccessorKind.DS_LIST)
				elif f.vore('?'): tokens += SpecialAccessorToken(AccessorKind.DS_MAP)
				elif f.vore('#'): tokens += SpecialAccessorToken(AccessorKind.DS_GRID)
				elif f.vore('@'): tokens += SpecialAccessorToken(AccessorKind.ARRAY)
				elif f.vore('$'): tokens += SpecialAccessorToken(AccessorKind.STRUCT)
				else: tokens += LBracketToken()
			case ']': tokens += RBracketToken()
			case ',': tokens += CommaToken()
			case ':': tokens += ColonToken()
			case ';': tokens += SemiColonToken()
			case '+':
				if   f.vore('='): tokens += InplaceOpToken(InplaceKind.ADD)
				elif f.vore('+'): tokens += IncrToken()
				else: tokens += PlusToken()
			case '-':
				if   f.vore('='): tokens += InplaceOpToken(InplaceKind.SUB)
				elif f.vore('-'): tokens += DecrToken()
				else: tokens += MinusToken()
			case '*':
				if f.vore('='): tokens += InplaceOpToken(InplaceKind.MUL)
				else:           tokens += StarToken()
			case '%':
				if f.vore('='): tokens += InplaceOpToken(InplaceKind.MOD)
				else:           tokens += PercToken()
			case '&':
				if   f.vore('&'): tokens += AndToken(False)
				elif f.vore('='): tokens += InplaceOpToken(InplaceKind.AND)
				else: tokens += AmpersandToken()
			case '|':
				if   f.vore('|'): tokens += OrToken(False)
				elif f.vore('='): tokens += InplaceOpToken(InplaceKind.OR)
				else: tokens += PipeToken()
			case '^':
				if   f.vore('^'): tokens += XorToken(False)
				elif f.vore('='): tokens += InplaceOpToken(InplaceKind.XOR)
				else: tokens += CarrotToken()
			case '<':
				if f.vore('='):
					tokens += LequalToken()
				elif f.vore('<'):
					if f.vore('='):
						tokens += InplaceOpToken(InplaceKind.LSH)
					else:
						tokens += LShiftToken()
				else:
					tokens += LessToken()
			case '>':
				if f.vore('='):
					tokens += GequalToken()
				elif f.vore('>'):
					if f.vore('='):
						tokens += InplaceOpToken(InplaceKind.RSH)
					else:
						tokens += RShiftToken()
				else:
					tokens += GreaterToken()
			case '#':
				# this isnt particuarly efficient -_- but whatever
				#TODO: This method is sort of complicated, im not sure how to
				#	report an error between an unknown preproc directive or a
				#	problem with parsing a hex colour
				begin = f.tell() - 1
				name = f.take_while(mth.is_identifier)
				if name == 'macro':
					tokens += handle_macro(f)
				elif name == 'region':
					f.take_while(KINDA_WHITESPACE)
					tokens += RegionToken(False, f.take_while(lambda c: c != '\n'))
					f.skip() # trailing newline
				elif name == 'endregion':
					f.take_while(KINDA_WHITESPACE)
					tokens += RegionToken(True, f.take_while(lambda c: c != '\n'))
					f.skip() # trailing newline
				elif name == '':
					raise ParseError(f'Unexpected # in stream @{begin}!')
				elif all(map(mth.is_allowed_number_hex, name)):
					f.seek(begin + 1)
					tokens += read_css_colour(f)
				else:
					raise ParseError(f'Unknown preprocessor directive "#{name}" @ {begin}!')
			case _:
				if mth.is_letter(ch) or ch == '_':
					f.rewind()
					name = f.take_while(mth.is_identifier)
					if name in gml_keywords:
						if (func:=gml_keywords[name]) is not None:
							tokens += func(name)
						else:
							tokens += KeywordToken(name)
					else:
						if name.startswith('argument'):
							idx = name.lstrip('argument')
							if len(idx) == 0:
								tokens += ScriptArgumentToken(-1)
								continue
							try:
								idx = int(idx)
								if idx in range(0, 16):
									tokens += ScriptArgumentToken(idx)
									continue
							except ValueError:
								pass
						tokens += IdentifierToken(name)
				elif mth.is_number(ch):
					f.rewind()
					tokens += handle_number(f)
				else:
					raise ParseError(f'Unexpected character in stream "{ch}"')
	return tokens


def main (targ: str|Path):
	tokens = tokenize(Path(targ).read_text('utf8'))
	tokens += EOFToken()
	return tokens
