from enum import Enum, auto
from .reader import Reader
from .types import TMP_TK
import string

gml_kinda_ws = ' \t\v\f'
gml_all_ws = '\r\n'+gml_kinda_ws

char_is_hex_number = lambda ch: ch == '_' or (ch in string.hexdigits)

is_identifier_start = lambda ch: (ch in string.ascii_letters) or ch == '_'
is_identifier = lambda ch: (ch in string.digits) or is_identifier_start(ch)

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

class KeywordType(Enum):
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

class TokenType(Enum):
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

	COMMENT = auto()

	IDENTIFIER = auto()
	LITERAL = auto()
	KEYWORD = auto()

	NEWLINE = auto()
	EOF = auto()

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
		# This is silly
		match name:
			case 'begin': return TokenType.LCURLY, DualTokenType.WORD
			case   'end': return TokenType.RCURLY, DualTokenType.WORD
			case   'div': return (TokenType.INT_DIV,)
			case   'mod': return (TokenType.INT_MOD,)
			case   'not': return TokenType.LOGIC_NOT, DualTokenType.WORD
			case   'and': return TokenType.LOGIC_AND, DualTokenType.WORD
			case    'or': return TokenType.LOGIC_OR,  DualTokenType.WORD
			case   'xor': return TokenType.LOGIC_XOR, DualTokenType.WORD

			case       'all': return TokenType.LITERAL, LiteralType.ALL
			case      'self': return TokenType.LITERAL, LiteralType.SELF
			case      'true': return TokenType.LITERAL, LiteralType.BOOLEAN, True
			case     'false': return TokenType.LITERAL, LiteralType.BOOLEAN, False
			case     'other': return TokenType.LITERAL, LiteralType.OTHER
			case     'noone': return TokenType.LITERAL, LiteralType.NOONE
			case    'global': return TokenType.LITERAL, LiteralType.GLOBAL
			case 'undefined': return TokenType.LITERAL, LiteralType.UNDEFINED

			case      'if': return TokenType.KEYWORD, KeywordType.IF
			case    'then': return TokenType.KEYWORD, KeywordType.THEN
			case    'else': return TokenType.KEYWORD, KeywordType.ELSE
			case    'case': return TokenType.KEYWORD, KeywordType.CASE
			case  'switch': return TokenType.KEYWORD, KeywordType.SWITCH
			case 'default': return TokenType.KEYWORD, KeywordType.DEFAULT

			case       'do': return TokenType.KEYWORD, KeywordType.DO
			case      'for': return TokenType.KEYWORD, KeywordType.FOR
			case     'with': return TokenType.KEYWORD, KeywordType.WITH
			case    'while': return TokenType.KEYWORD, KeywordType.WHILE
			case    'until': return TokenType.KEYWORD, KeywordType.UNTIL
			case    'break': return TokenType.KEYWORD, KeywordType.BREAK
			case   'repeat': return TokenType.KEYWORD, KeywordType.REPEAT
			case 'continue': return TokenType.KEYWORD, KeywordType.CONTINUE

			case         'var': return TokenType.KEYWORD, KeywordType.VAR
			case        'enum': return TokenType.KEYWORD, KeywordType.ENUM
			case      'static': return TokenType.KEYWORD, KeywordType.STATIC
			case    'function': return TokenType.KEYWORD, KeywordType.FUNCTION
			case   'globalvar': return TokenType.KEYWORD, KeywordType.GLOBALVAR
			case 'constructor': return TokenType.KEYWORD, KeywordType.CONSTRUCTOR

			case   'exit': return TokenType.KEYWORD, KeywordType.EXIT
			case 'return': return TokenType.KEYWORD, KeywordType.RETURN
			case 'delete': return TokenType.KEYWORD, KeywordType.DELETE

			case     'try': return TokenType.KEYWORD, KeywordType.TRY
			case   'catch': return TokenType.KEYWORD, KeywordType.CATCH
			case   'throw': return TokenType.KEYWORD, KeywordType.THROW
			case 'finally': return TokenType.KEYWORD, KeywordType.FINALLY

		return TokenType.IDENTIFIER, name

	def add (self, token, *metadata):
		# self.tokens.append(token)
		nn = token.name if isinstance(token, TokenType) else str(token)
		sl = slice(self.begin, self.f.tell())
		print(f'{nn} {metadata}')

	def new_line (self):
		"""
		Assumes the cursor is after the newline char
		"""
		self.line_index = self.f.tell()
		self.line_number += 1

	def inplace_quick (self, cbasetype: TokenType):
		if self.f.vore('='):
			self.add(TokenType.IN_PLACE_OP, cbasetype)
		self.add(cbasetype)

	def tokenize (self):
		f = self.f
		add = self.add
		while f.has_remaining:
			f.skip_while(gml_kinda_ws)
			self.begin = f.tell()
			ch = f.read()
			match ch:
				case '\n':
					self.new_line(); add(TokenType.NEWLINE)
				case '\\':
					if not self.do_line_continues:
						raise TokenizeError('Unexpected whack (\\) in stream!')
					if f.vore('\n'):
						self.new_line(); add(TokenType.NEWLINE)
					else:
						raise TokenizeError('Expected newline after continuator (\\)!')
				case '"':
					raise NotImplementedError('String')
				case '@' if f.vore('"'):
					raise NotImplementedError('Multi-line string literal')
				case '$' if f.vore('"'):
					raise NotImplementedError('String template')
				case '$' if f.peek_is(char_is_hex_number):
					add(TokenType.LITERAL, LiteralType.NUMBER, self.handle_hexadecimal_literal(), NumberLiteralSrc.HEX)
				case '0' if f.vore('xX'):
					add(TokenType.LITERAL, LiteralType.NUMBER, self.handle_hexadecimal_literal(), NumberLiteralSrc.HEX)
				case '0' if f.vore('bB'):
					add(TokenType.LITERAL, LiteralType.NUMBER, self.handle_binary_literal(), NumberLiteralSrc.BIN)
				case '{': add(TokenType.LCURLY, DualTokenType.SYMBOL)
				case '}': add(TokenType.RCURLY, DualTokenType.SYMBOL)
				case '(': add(TokenType.LWHIFFLE)
				case ')': add(TokenType.RWHIFFLE)
				case '[':
					if   f.vore('|'): add(TokenType.ACCESSOR, AccessorType.LIST)
					elif f.vore('?'): add(TokenType.ACCESSOR, AccessorType.MAP)
					elif f.vore('#'): add(TokenType.ACCESSOR, AccessorType.GRID)
					elif f.vore('@'): add(TokenType.ACCESSOR, AccessorType.ARRAY)
					elif f.vore('$'): add(TokenType.ACCESSOR, AccessorType.STRUCT)
					else: add(TokenType.LBRACKET)
				case ']':
					add(TokenType.RBRACKET)
				case '~':
					add(TokenType.BIT_NOT)
				case '&':
					if f.vore(ch):
						add(TokenType.LOGIC_AND, False)
					else:
						self.inplace_quick(TokenType.BIT_AND)
				case '|':
					if f.vore(ch):
						add(TokenType.LOGIC_OR, False)
					else:
						self.inplace_quick(TokenType.BIT_OR)
				case '^':
					if f.vore(ch):
						add(TokenType.LOGIC_XOR, False)
					else:
						self.inplace_quick(TokenType.BIT_XOR)
				case '=':
					if f.vore('='):
						add(TokenType.EQUALITY)
					else:
						add(TokenType.EQUALS)
				case '!':
					if f.vore('='):
						add(TokenType.INEQUALITY)
					else:
						add(TokenType.LOGIC_NOT)
				case '<':
					if f.vore('<'):
						self.inplace_quick(TokenType.BIT_LSHIFT)
					elif f.vore('='):
						add(TokenType.LESS_EQUAL)
					else:
						add(TokenType.LESS_THAN)
				case '>':
					if f.vore('>'):
						self.inplace_quick(TokenType.BIT_RSHIFT)
					elif f.vore('='):
						add(TokenType.GREATER_EQUAL)
					else:
						add(TokenType.GREATER_THAN)
				case '+':
					if f.vore('+'):
						add(TokenType.INCR)
					else:
						self.inplace_quick(TokenType.PLUS)
				case '-':
					if f.vore('-'):
						add(TokenType.DECR)
					else:
						self.inplace_quick(TokenType.MINUS)
				case '*':
					self.inplace_quick(TokenType.MUL)
				case '%':
					self.inplace_quick(TokenType.MOD)
				case '/':
					if f.vore('/'):
						# Single-line comment
						# If you think about it, single line comments are just
						# really big newline characters
						com_begin = f.tell()
						f.skip_until('\n', True)
						# dont include newline in comment body
						add(TokenType.COMMENT, f.text[com_begin:f.tell()-1], CommentType.LINE)
						self.new_line()
					elif f.vore('*'):
						# Multi-line comment
						com_begin = f.tell()
						self.handle_multiline_comment()
						# dont include trailing */ in body
						add(TokenType.COMMENT, f.text[com_begin:f.tell()-2], CommentType.BLOCK)
					else:
						self.inplace_quick(TokenType.DIV)
				case _ if is_identifier_start(ch):
					f.rewind()
					add(*self.handle_identifier())
				case _:
					...

	def act (self):
		self.tokenize()

