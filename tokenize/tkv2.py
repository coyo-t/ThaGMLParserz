from enum import Enum, auto
from .reader import Reader
from .types import TMP_TK
import string

gml_kinda_ws = ' \t\v\f'
gml_all_ws = '\r\n'+gml_kinda_ws

char_is_hex_number = lambda ch: ch == '_' or (ch in string.hexdigits)

is_identifier_start = lambda ch: (ch in string.ascii_letters) or ch == '_'
is_identifier = lambda ch: (ch in string.digits) or is_identifier_start(ch)
is_number_lit = lambda ch: (ch in string.digits) or ch == '_'

class DualTokenType(Enum):
	SYMBOL = False
	WORD = True

class CommentType(Enum):
	LINE  = auto()
	BLOCK = auto()

class NumberLiteralSrc(Enum):
	FLOAT  = auto()
	INT    = auto()
	HEX    = auto()
	BIN    = auto()
	COLOUR = auto()

class AccessorType(Enum):
	LIST   = ('|',)
	MAP    = ('?',)
	GRID   = ('#',)
	ARRAY  = ('@',)
	STRUCT = ('$',)

class KWType(Enum):
	IF = auto()
	THEN = auto()
	ELSE = auto()
	WHILE = auto()
	DO = auto()
	FOR = auto()
	BREAK = auto()
	CONTINUE = auto()
	WITH = auto()
	UNTIL = auto()
	REPEAT = auto()
	EXIT = auto()
	RETURN = auto()
	SWITCH = auto()
	CASE = auto()
	DEFAULT = auto()
	VAR = auto()
	GLOBALVAR = auto()
	ENUM = auto()
	FUNCTION = auto()
	TRY = auto()
	CATCH = auto()
	FINALLY = auto()
	THROW = auto()
	STATIC = auto()
	DELETE = auto()
	CONSTRUCTOR = auto()

class LiteralType(Enum):
	NUMBER  = auto()
	STRING  = auto()
	BOOLEAN = auto()
	UNDEFINED = auto()
	SELF   = auto()
	OTHER  = auto()
	ALL    = auto()
	NOONE  = auto()
	GLOBAL = auto()

class TKType(Enum):
	LCURLY = auto()
	RCURLY = auto()
	LBRACKET = auto()
	RBRACKET = auto()
	LWHIFFLE = auto()
	RWHIFFLE = auto()

	PLUS  = auto()
	MINUS = auto()
	MUL  = auto()
	DIV = auto()
	MOD = auto()

	INT_DIV = auto()
	INT_MOD = auto()

	INCR = auto()
	DECR = auto()

	EQUALS = auto()

	DOT       = auto()
	COMMA     = auto()
	SEMICOLON = auto()
	COLON     = auto()

	QUESTION = auto()
	NULLISH  = auto()

	EQUALITY      = auto()
	INEQUALITY    = auto()
	LESS_THAN     = auto()
	LESS_EQUAL    = auto()
	GREATER_THAN  = auto()
	GREATER_EQUAL = auto()

	LOGIC_NOT = auto()
	LOGIC_AND = auto()
	LOGIC_OR  = auto()
	LOGIC_XOR = auto()

	BIT_LSHIFT = auto()
	BIT_RSHIFT = auto()
	BIT_NOT    = auto()
	BIT_AND    = auto()
	BIT_OR     = auto()
	BIT_XOR    = auto()

	IN_PLACE_OP = auto()

	ACCESSOR = auto()

	COMMENT   = auto()
	REGION    = auto()
	ENDREGION = auto()

	IDENTIFIER = auto()
	LITERAL = auto()
	KEYWORD = auto()

	NEWLINE = auto()
	EOF = auto()

# TODO: this works, right? TEST IT WHEN YOU HAVE STR TEMPLATES DONE MORON
def digest_string (s: str):
	# gurgle glorp glrr uvu
	class DigestStringError(Exception): pass

	# this isnt very efficient. -_-
	if (i:=len(s)) == 0:
		return ''
	elif i == 1:
		if s == '\\':
			raise DigestStringError('Empty escape sequence at end of string!')
		return s
	chars = list(s)
	if chars[-1] == '\\':
		if chars[-2] != '\\':
			raise DigestStringError('Empty escape sequence at end of string!')
		else:
			i -= 1
	simple_seqs = {
		'r': '\x0D', 'n': '\x0A', 'b': '\x08', 'f': '\x0C',
		't': '\x09', 'v': '\x0B', 'a': '\x07',
	}
	def method_name (limit:int, typeof:str):
		k = i + 2
		j = k
		while (chars[j] in string.hexdigits) and (j - k) < limit: j += 1
		digits = chars[k:j]
		if len(digits) < limit:
			raise DigestStringError(f'Not enough digits for {typeof} escape sequence!')
		chars[i:j] = chr(int(''.join(digits), 16))

	while (i:=i-1) >= 0:
		ch = chars[i]
		if ch != '\\':
			continue
		ch = chars[i+1]
		match ch:
			case '\\' | '"':
				del chars[i] # the character escaped is the same as the esc seq
			case _ if ch in simple_seqs:
				chars[i:i+2] = simple_seqs[ch]
			case 'u':
				method_name(4, 'unicode')
			case 'x':
				method_name(2, 'hex')
			case _ if '0' <= ch <= '7':
				chars[i:i+2] = chr(int(ch, 8))
			case _:
				raise DigestStringError(f'Unknown string escape sequence \\{ch}!')
	return ''.join(chars)


class TokenizeError(Exception): pass

class Tokenizer:
	def __init__ (self, source:str):
		"""
		Assumes input source string has had all windows-style line endings
		and carriage returns replaced with singular newline characters.
		if not, bad things might happen! uh oh!

		"""
		self.text = source
		self.f = Reader(self.text)
		self.line_number = 0
		self.line_index = 0
		self.begin = 0
		self.do_line_continues = False

		self.tokens = []

	@property
	def char_index (self):
		""":return: The current character index in the current line"""
		return self.f.tell() - self.line_index

	def handle_multiline_comment (self):
		"""Assumes the beginning /* has been skipped"""
		f = self.f
		while True:
			ch = f.read()
			match ch:
				case '':
					raise TokenizeError('Unclosed multi-line comment!')
				case '\n':
					self.new_line()
				case '/' if f.vore('*'):
					# I don't particuarly like recursion but whatever
					# this should just incr & decr a depth count
					self.handle_multiline_comment()
				case '*' if f.vore('/'):
					return

	def handle_binary_literal (self):
		digits = self.f.vore_while('_01').replace('_', '')
		return int(digits, 2)

	def handle_hexadecimal_literal (self):
		digits = self.f.vore_while(char_is_hex_number).replace('_', '')
		return int(digits, 16)

	def handle_identifier (self):
		name = self.f.vore_while(is_identifier)
		# TODO: This is very silly
		match name:
			case 'begin': return TKType.LCURLY, DualTokenType.WORD
			case   'end': return TKType.RCURLY, DualTokenType.WORD
			case   'div': return (TKType.INT_DIV,)
			case   'mod': return (TKType.INT_MOD,)
			case   'not': return TKType.LOGIC_NOT, DualTokenType.WORD
			case   'and': return TKType.LOGIC_AND, DualTokenType.WORD
			case    'or': return TKType.LOGIC_OR,  DualTokenType.WORD
			case   'xor': return TKType.LOGIC_XOR, DualTokenType.WORD

			case       'all': return TKType.LITERAL, LiteralType.ALL
			case      'self': return TKType.LITERAL, LiteralType.SELF
			case      'true': return TKType.LITERAL, LiteralType.BOOLEAN, True
			case     'false': return TKType.LITERAL, LiteralType.BOOLEAN, False
			case     'other': return TKType.LITERAL, LiteralType.OTHER
			case     'noone': return TKType.LITERAL, LiteralType.NOONE
			case    'global': return TKType.LITERAL, LiteralType.GLOBAL
			case 'undefined': return TKType.LITERAL, LiteralType.UNDEFINED

			case      'if': return TKType.KEYWORD, KWType.IF
			case    'then': return TKType.KEYWORD, KWType.THEN
			case    'else': return TKType.KEYWORD, KWType.ELSE
			case    'case': return TKType.KEYWORD, KWType.CASE
			case  'switch': return TKType.KEYWORD, KWType.SWITCH
			case 'default': return TKType.KEYWORD, KWType.DEFAULT

			case       'do': return TKType.KEYWORD, KWType.DO
			case      'for': return TKType.KEYWORD, KWType.FOR
			case     'with': return TKType.KEYWORD, KWType.WITH
			case    'while': return TKType.KEYWORD, KWType.WHILE
			case    'until': return TKType.KEYWORD, KWType.UNTIL
			case    'break': return TKType.KEYWORD, KWType.BREAK
			case   'repeat': return TKType.KEYWORD, KWType.REPEAT
			case 'continue': return TKType.KEYWORD, KWType.CONTINUE

			case         'var': return TKType.KEYWORD, KWType.VAR
			case        'enum': return TKType.KEYWORD, KWType.ENUM
			case      'static': return TKType.KEYWORD, KWType.STATIC
			case    'function': return TKType.KEYWORD, KWType.FUNCTION
			case   'globalvar': return TKType.KEYWORD, KWType.GLOBALVAR
			case 'constructor': return TKType.KEYWORD, KWType.CONSTRUCTOR

			case   'exit': return TKType.KEYWORD, KWType.EXIT
			case 'return': return TKType.KEYWORD, KWType.RETURN
			case 'delete': return TKType.KEYWORD, KWType.DELETE

			case     'try': return TKType.KEYWORD, KWType.TRY
			case   'catch': return TKType.KEYWORD, KWType.CATCH
			case   'throw': return TKType.KEYWORD, KWType.THROW
			case 'finally': return TKType.KEYWORD, KWType.FINALLY

		return TKType.IDENTIFIER, name

	def handle_multiline_string_literal (self):
		"""Assumes beginning @" was vored"""
		# cant just use `f.vore_until`, have to check for EOF
		# and report back an error that the string is unclosed
		f = self.f
		begin = f.tell()
		while True:
			ch = f.read()
			if ch == '':
				raise TokenizeError('Unclosed @string!')
			elif ch == '"':
				break
		# trailing " already skiped due to the way the loop works
		return f.text[begin:f.tell()-1]

	def handle_string_literal (self):
		"""Assumes beginning " was vored"""
		f = self.f
		begin = f.tell()
		while True:
			ch = f.read()
			if ch == '"':
				if f.peek(-1) == '\\':
					continue
				break
			elif ch == '\n':
				raise TokenizeError('Newline in string literal!')
			elif ch == '':
				raise TokenizeError('Unclosed string!')
		# trailing " already skiped due to the way the loop works
		return digest_string(f.text[begin:f.tell()-1])

	def handle_number_literal (self):
		f = self.f
		start = f.tell()
		f.skip_while(is_number_lit)
		is_float = f.vore('.')
		f.skip_while(is_number_lit)
		return (
			TKType.LITERAL,
			LiteralType.NUMBER,
			(float if is_float else int)(f.substr_from(start)),
			NumberLiteralSrc.FLOAT if is_float else NumberLiteralSrc.INT
		)


	def add (self, token, *metadata):
		# self.tokens.append(token)
		nn = token.name if isinstance(token, TKType) else str(token)
		sl = slice(self.begin, self.f.tell())
		print(f'{nn} {metadata}')

	def new_line (self):
		"""
		Assumes the cursor is after the newline char
		"""
		self.line_index = self.f.tell()
		self.line_number += 1

	def inplace_quick (self, cbasetype: TKType):
		if self.f.vore('='):
			self.add(TKType.IN_PLACE_OP, cbasetype)
		self.add(cbasetype)

	def region_quick (self, cbasetype: TKType):
		com_begin = self.f.tell()
		self.f.skip_until('\n', True)
		# dont include newline in comment body
		self.add(cbasetype, self.f.text[com_begin:self.f.tell() - 1])

	def tokenize (self):
		f = self.f
		add = self.add
		while f.has_remaining:
			f.skip_while(gml_kinda_ws)
			self.begin = f.tell()
			ch = f.read()
			match ch:
				case '\n':
					self.new_line(); add(TKType.NEWLINE)
				case '\\':
					if not self.do_line_continues:
						raise TokenizeError('Unexpected whack (\\) in stream!')
					if f.vore('\n'):
						self.new_line(); add(TKType.NEWLINE)
					else:
						raise TokenizeError('Expected newline after continuator (\\)!')
				case '"':
					add(TKType.LITERAL, LiteralType.STRING, self.handle_string_literal())
				case '@' if f.vore('"'):
					add(TKType.LITERAL, LiteralType.STRING, self.handle_multiline_string_literal())
				case '$' if f.vore('"'):
					raise NotImplementedError('String template')
				case '$' if f.peek_is(char_is_hex_number):
					add(TKType.LITERAL, LiteralType.NUMBER, self.handle_hexadecimal_literal(), NumberLiteralSrc.HEX)
				case '0' if f.vore('xX'):
					add(TKType.LITERAL, LiteralType.NUMBER, self.handle_hexadecimal_literal(), NumberLiteralSrc.HEX)
				case '0' if f.vore('bB'):
					add(TKType.LITERAL, LiteralType.NUMBER, self.handle_binary_literal(), NumberLiteralSrc.BIN)
				case '#':
					mk_begin = f.tell()
					name = f.vore_while(is_identifier)
					if name == 'region':
						self.region_quick(TKType.REGION)
					elif name == 'endregion':
						self.region_quick(TKType.ENDREGION)
					elif name == 'macro':
						raise NotImplementedError('MACRO')
					else:
						f.seek(mk_begin)
						name = f.vore_while(char_is_hex_number).replace('_', '')
						if len(name) < 6:
							raise TokenizeError(f'Not enough digits for colour constant {name}!')
						elif len(name) > 6:
							raise TokenizeError(f'Too many digits for colour constant {name}!')
						col = int(name, 16)
						col = ((col>>16)&0xFF)|(col&0xFF00)|((col&0xFF)<<16)
						add(TKType.LITERAL, LiteralType.NUMBER, col, NumberLiteralSrc.COLOUR)
				case ',': add(TKType.COMMA)
				case ';': add(TKType.SEMICOLON)
				case ':': add(TKType.COLON)
				case '.':
					# float literal might leave off the leading 0
					if f.peek_is(string.digits):
						f.rewind()
						add(*self.handle_number_literal())
					else:
						add(TKType.DOT)
				case '{': add(TKType.LCURLY, DualTokenType.SYMBOL)
				case '}': add(TKType.RCURLY, DualTokenType.SYMBOL)
				case '(': add(TKType.LWHIFFLE)
				case ')': add(TKType.RWHIFFLE)
				case '[':
					if   f.vore('|'): add(TKType.ACCESSOR, AccessorType.LIST)
					elif f.vore('?'): add(TKType.ACCESSOR, AccessorType.MAP)
					elif f.vore('#'): add(TKType.ACCESSOR, AccessorType.GRID)
					elif f.vore('@'): add(TKType.ACCESSOR, AccessorType.ARRAY)
					elif f.vore('$'): add(TKType.ACCESSOR, AccessorType.STRUCT)
					else: add(TKType.LBRACKET)
				case ']':
					add(TKType.RBRACKET)
				case '~':
					add(TKType.BIT_NOT)
				case '?':
					if f.vore('?'):
						self.inplace_quick(TKType.NULLISH)
					else:
						add(TKType.QUESTION)
				case '&':
					if f.vore(ch):
						add(TKType.LOGIC_AND, False)
					else:
						self.inplace_quick(TKType.BIT_AND)
				case '|':
					if f.vore(ch):
						add(TKType.LOGIC_OR, False)
					else:
						self.inplace_quick(TKType.BIT_OR)
				case '^':
					if f.vore(ch):
						add(TKType.LOGIC_XOR, False)
					else:
						self.inplace_quick(TKType.BIT_XOR)
				case '=':
					if f.vore('='):
						add(TKType.EQUALITY)
					else:
						add(TKType.EQUALS)
				case '!':
					if f.vore('='):
						add(TKType.INEQUALITY)
					else:
						add(TKType.LOGIC_NOT)
				case '<':
					if f.vore('<'):
						self.inplace_quick(TKType.BIT_LSHIFT)
					elif f.vore('='):
						add(TKType.LESS_EQUAL)
					else:
						add(TKType.LESS_THAN)
				case '>':
					if f.vore('>'):
						self.inplace_quick(TKType.BIT_RSHIFT)
					elif f.vore('='):
						add(TKType.GREATER_EQUAL)
					else:
						add(TKType.GREATER_THAN)
				case '+':
					if f.vore('+'):
						add(TKType.INCR)
					else:
						self.inplace_quick(TKType.PLUS)
				case '-':
					if f.vore('-'):
						add(TKType.DECR)
					else:
						self.inplace_quick(TKType.MINUS)
				case '*':
					self.inplace_quick(TKType.MUL)
				case '%':
					self.inplace_quick(TKType.MOD)
				case '/':
					if f.vore('/'):
						# Single-line comment
						# If you think about it, single line comments are just
						# really big newline characters
						com_begin = f.tell()
						f.skip_until('\n', True)
						# dont include newline in comment body
						add(TKType.COMMENT, f.text[com_begin:f.tell() - 1], CommentType.LINE)
						self.new_line()
					elif f.vore('*'):
						# Multi-line comment
						com_begin = f.tell()
						self.handle_multiline_comment()
						# dont include trailing */ in body
						add(TKType.COMMENT, f.text[com_begin:f.tell() - 2], CommentType.BLOCK)
					else:
						self.inplace_quick(TKType.DIV)
				case _ if is_identifier_start(ch):
					f.rewind()
					add(*self.handle_identifier())
				case _ if ch in string.digits:
					f.rewind()
					add(*self.handle_number_literal())
				case _:
					...

	def act (self):
		self.tokenize()

