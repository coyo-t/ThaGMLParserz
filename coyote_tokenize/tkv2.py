from __future__ import annotations
import string
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from .reader import Reader

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

	# Undocumenteds (act as normal array access, doesnt
	# syntax highlight correctly, *does* compile fine)
	U8     = ('B:',)
	S8     = ('b:',)
	U16    = ('X:',)
	S16    = ('x:',)
	U32    = ('I:',)
	S32    = ('i:',)
	F32    = ('f:',)
	F64    = ('d:',)


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
	FSTRING = auto()
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
	MACRO = auto()

	IDENTIFIER = auto()
	LITERAL = auto()
	KEYWORD = auto()

	NEWLINE = auto()
	EOF = auto()

	def debug_indent_incr (self):
		return self in (
			self.LCURLY,
			self.LBRACKET,
			self.LWHIFFLE,
			self.REGION,
			self.ACCESSOR,
		)

	def debug_indent_decr (self):
		return self in (
			self.RCURLY,
			self.RBRACKET,
			self.RWHIFFLE,
			self.ENDREGION,
		)

@dataclass
class MacroData:
	name: str = ''
	configuration: str|None = None
	tokens: list[Token] = field(default_factory=list)
	lexeme: str = ''
	name_begin: PositionInfo = None
	name_end:   PositionInfo = None

	@property
	def keyword_length (self):
		return len('#macro ')

	@property
	def has_config (self):
		return self.configuration is not None

@dataclass
class LiteralData:
	literal_type: LiteralType

@dataclass
class FStringData(LiteralData):
	class Section:
		def __init__ (self, sect_begin:int, sect_end:int,fstr_begin:int):
			self.absolute=slice(sect_begin,sect_end)
			self.relative=slice(sect_begin-fstr_begin,sect_end-fstr_begin)
	lexeme:       str = ''
	fixed_up_str: str = ''
	sections: list[Section] = field(default_factory=list)
	section_contents: list[list['Token']] = field(default_factory=list)
	@classmethod
	def create (cls):
		return cls(LiteralType.FSTRING)

@dataclass
class NumberLiteralData(LiteralData):
	value: float
	number_src: NumberLiteralSrc
	@classmethod
	def create (cls, value: float, src: NumberLiteralSrc):
		return cls(LiteralType.NUMBER, value, src)
	@classmethod
	def create_hex (cls, value: float):
		return cls.create(value, NumberLiteralSrc.HEX)
	@classmethod
	def create_bin (cls, value: float):
		return cls.create(value, NumberLiteralSrc.BIN)
	def __str__ (self):
		match self.number_src:
			case NumberLiteralSrc.HEX:
				return f'0x{int(self.value):X}'
			case NumberLiteralSrc.BIN:
				return f'0b{int(self.value):B}'
			case NumberLiteralSrc.COLOUR:
				return f'#{int(self.value):X}'
			case NumberLiteralSrc.INT:
				return f'{int(self.value)}'
			case NumberLiteralSrc.FLOAT:
				return f'{self.value:.4f}'
		raise ValueError(f'Incorrect number source {self.number_src}')

@dataclass
class StringLiteralData(LiteralData):
	text: str
	@classmethod
	def create (cls, text: str):
		return cls(LiteralType.STRING, text)

@dataclass
class CommentData:
	type: CommentType
	text: str
	@classmethod
	def create (cls, text:str, is_multiline=False):
		return cls(CommentType.BLOCK if is_multiline else CommentType.LINE, text)

# TODO: this works, right? TEST IT WHEN YOU HAVE STR TEMPLATES DONE MORON
def digest_string (s: str):
	class DigestStringError(Exception): pass # gurgle glorp glrr uvu
	# this isnt very efficient. -_-
	# also, technically, the open escape sequence at the end of a string
	# would be caught by the tokenizer, as it'd cause an unclosed string.
	# but might as well check it here anyway
	if (i:=len(s)) == 0:
		return ''
	elif i == 1:
		if s == '\\':
			raise DigestStringError('Empty escape sequence at end of string!')
		return s
	# i could also call it "Slurry" if that'd squick people out more òvó
	chyme = list(s)
	if chyme[-1] == '\\':
		if chyme[-2] != '\\':
			raise DigestStringError('Empty escape sequence at end of string!')
		i -= 1 # prevent indigestion later
	simple_seqs = {'r':'\x0D','n':'\x0A','b':'\x08','f':'\x0C','t':'\x09','v':'\x0B','a':'\x07'}
	def method_name (limit:int, typeof:str):
		k = i + 2
		j = k
		while (chyme[j] in string.hexdigits) and (j - k) < limit: j += 1
		digits = chyme[k:j]
		if len(digits) < limit:
			raise DigestStringError(f'Not enough digits for {typeof} escape sequence!')
		chyme[i:j] = chr(int(''.join(digits), 16))
	# Work backwards rather than forwards in the string. A classic trick that
	# prevents us from having to recalculate any indices or bounds checks
	# Tee Hee, thanks dad.
	while (i:=i-1) >= 0:
		ch = chyme[i]
		if ch != '\\':
			continue
		ch = chyme[i+1]
		match ch:
			case '\\' | '"' | "'":
				del chyme[i] # the character escaped is the same as the esc seq
			case _ if ch in simple_seqs:
				chyme[i:i+2] = simple_seqs[ch]
			case 'u':
				method_name(4, 'unicode')
			case 'x':
				method_name(2, 'hex')
			case _ if '0' <= ch <= '7':
				chyme[i:i+2] = chr(int(ch, 8))
			case _:
				raise DigestStringError(f"Unknown string escape sequence '\\{ch}'!")
	return ''.join(chyme)

# This is a little silly
identifiers_r_keywords = {
	'begin': (TKType.LCURLY, DualTokenType.WORD),
	  'end': (TKType.RCURLY, DualTokenType.WORD),
	  'div': (TKType.INT_DIV,),
	  'mod': (TKType.INT_MOD,),
	  'not': (TKType.LOGIC_NOT, DualTokenType.WORD),
	  'and': (TKType.LOGIC_AND, DualTokenType.WORD),
	   'or': (TKType.LOGIC_OR,  DualTokenType.WORD),
	  'xor': (TKType.LOGIC_XOR, DualTokenType.WORD),

	      'all': (TKType.LITERAL, LiteralType.ALL),
	     'self': (TKType.LITERAL, LiteralType.SELF),
	     'true': (TKType.LITERAL, LiteralType.BOOLEAN, True),
	    'false': (TKType.LITERAL, LiteralType.BOOLEAN, False),
	    'other': (TKType.LITERAL, LiteralType.OTHER),
	    'noone': (TKType.LITERAL, LiteralType.NOONE),
	   'global': (TKType.LITERAL, LiteralType.GLOBAL),
	'undefined': (TKType.LITERAL, LiteralType.UNDEFINED),

	     'if': (TKType.KEYWORD, KWType.IF),
	   'then': (TKType.KEYWORD, KWType.THEN),
	   'else': (TKType.KEYWORD, KWType.ELSE),
	   'case': (TKType.KEYWORD, KWType.CASE),
	 'switch': (TKType.KEYWORD, KWType.SWITCH),
	'default': (TKType.KEYWORD, KWType.DEFAULT),

	      'do': (TKType.KEYWORD, KWType.DO),
	     'for': (TKType.KEYWORD, KWType.FOR),
	    'with': (TKType.KEYWORD, KWType.WITH),
	   'while': (TKType.KEYWORD, KWType.WHILE),
	   'until': (TKType.KEYWORD, KWType.UNTIL),
	   'break': (TKType.KEYWORD, KWType.BREAK),
	  'repeat': (TKType.KEYWORD, KWType.REPEAT),
	'continue': (TKType.KEYWORD, KWType.CONTINUE),

	        'var': (TKType.KEYWORD, KWType.VAR),
	       'enum': (TKType.KEYWORD, KWType.ENUM),
	     'static': (TKType.KEYWORD, KWType.STATIC),
	   'function': (TKType.KEYWORD, KWType.FUNCTION),
	  'globalvar': (TKType.KEYWORD, KWType.GLOBALVAR),
	'constructor': (TKType.KEYWORD, KWType.CONSTRUCTOR),

	  'exit': (TKType.KEYWORD, KWType.EXIT),
	'return': (TKType.KEYWORD, KWType.RETURN),
	'delete': (TKType.KEYWORD, KWType.DELETE),

	    'try': (TKType.KEYWORD, KWType.TRY),
	  'catch': (TKType.KEYWORD, KWType.CATCH),
	  'throw': (TKType.KEYWORD, KWType.THROW),
	'finally': (TKType.KEYWORD, KWType.FINALLY),
}

@dataclass
class PositionInfo:
	cursor: int
	line_number: int
	line_index: int
	@property
	def char_on_line (self):
		return self.cursor - self.line_index
	def clone (self):
		return PositionInfo(self.cursor, self.line_number, self.line_index)

@dataclass
class Token:
	type: TKType
	begin: PositionInfo = None
	end: PositionInfo = None
	metadata: tuple[Any] = field(default_factory=tuple)

	def macro_get_metadata (self) -> MacroData:
		if self.type is not TKType.MACRO:
			raise AttributeError('Tried to get macro metadata for a non-macro token!')
		return self.metadata[0]

	def literal_get (self) -> LiteralData:
		if self.type is not TKType.LITERAL:
			raise AttributeError('Tried to get literal data for a non-literal token!')
		return self.metadata[0]

class TokenizeError(Exception): pass

class Tokenizer:
	class Gender(Enum):
		NONE = auto()
		MACRO = auto()
		FSTRING = auto()

	def __init__ (self, source:str, gender=Gender.NONE):
		"""
		Assumes input source string has had all windows-style line endings
		and carriage returns replaced with singular newline characters.
		if not, bad things might happen! uh oh!

		"""
		self.text = source
		self.f = Reader(self.text)
		self._line_number = 0
		self._line_index = 0
		self.begin = PositionInfo(0, 0, 0)
		self.gender = gender
		self.tokens: list[Token] = []
		self.token_stack: list[list[Token]] = []
		self.limit = len(self.f)

	def token_stack_push (self, clear=True):
		self.token_stack.append(old:=self.tokens)
		if clear:
			self.tokens = []
		else:
			self.tokens = old.copy()
		return old

	def token_stack_pop (self):
		old = self.tokens
		if len(self.token_stack) == 0:
			self.tokens = []
		else:
			self.tokens = self.token_stack.pop()
		return old

	@property
	def position_info (self):
		""":returns: A copy"""
		return PositionInfo(self.f.tell(), self.line_number, self.line_index)

	@property
	def line_number (self):
		return self._line_number

	@property
	def line_index (self):
		return self._line_index

	@property
	def char_index (self):
		""":return: The current character index in the current line"""
		return self.f.tell() - self._line_index

	def _begin_sub_tokenize (self, new_gender=Gender.NONE):
		pev = (self.gender, self.begin)
		self.gender = new_gender
		self.token_stack_push()
		return pev

	def _end_sub_tokenize (self, pev):
		self.token_stack_pop()
		self.gender, self.begin = pev

	def handle_multiline_comment (self):
		"""Assumes the beginning /* has been skipped"""
		f = self.f
		depth = 0
		while True:
			ch = f.read()
			match ch:
				case '':
					raise TokenizeError('Unclosed multi-line comment!')
				case '\n':
					self.new_line()
				case '/' if f.vore('*'):
					depth += 1
				case '*' if f.vore('/'):
					if depth == 0:
						return
					depth -= 1

	def handle_binary_literal (self):
		return int(self.f.vore_while('_01').replace('_', ''), 2)

	def handle_hexadecimal_literal (self):
		digits = self.f.vore_while(char_is_hex_number).replace('_', '')
		return int(digits, 16)

	def handle_identifier (self):
		name = self.f.vore_while(is_identifier)
		if name in identifiers_r_keywords:
			return identifiers_r_keywords[name]
		return TKType.IDENTIFIER, name

	def handle_multiline_string_literal (self, matching_kind='"'):
		"""Assumes beginning @" was vored"""
		# cant just use `f.vore_until`, have to check for EOF
		# and report back an error that the string is unclosed,
		# as well as counting new lines
		f = self.f
		if f.vore(matching_kind):
			return ''
		begin = f.tell()
		while True:
			ch = f.read()
			if ch == '':
				raise TokenizeError('Unclosed @string!')
			elif ch == '\n':
				self.new_line()
			elif ch == matching_kind:
				break
		# trailing " already skiped due to the way the loop works
		return f.text[begin:f.tell()-1]

	def handle_string_literal (self, matching='"'):
		"""Assumes beginning " was vored"""
		f = self.f
		if f.vore(matching):
			return ''

		begin = f.tell()
		while True:
			ch = f.read()
			if ch == matching:
				# -2. -1 will just give back the '"' we just read
				if f.peek(-2) == '\\':
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
			NumberLiteralData.create(
				(float if is_float else int)(f.substr_from(start)),
				NumberLiteralSrc.FLOAT if is_float else NumberLiteralSrc.INT
			),
		)

	# TODO: not here but later there needs to be a check for recursive macros
	def handle_macro (self):
		# assumes the intermediary whitespace has been skipped
		f = self.f
		def vore_name ():
			if f.peek_isnt(is_identifier_start):
				raise TokenizeError('Unexpected symbol at beginning of macro identifier!')
			name = f.vore_while(is_identifier)
			if len(name) == 0:
				raise TokenizeError('Macro identifier empty!')
			return name
		# the syntax is either #macro {name} {tokens}
		# or                   #macro {config}:{name} {tokens}
		# This is stupid! I dont know why its like this -_-
		# But its on purpose, i know that
		outm = MacroData()
		outm.name_begin = self.position_info
		id1 = vore_name()
		if f.vore(':'):
			outm.name, outm.configuration = vore_name(), id1
		else:
			outm.name, outm.configuration = id1, None
		outm.name_end = self.position_info

		mdatbegin = f.tell()
		pev = self._begin_sub_tokenize(self.Gender.MACRO)
		outm.tokens = self.tokenize()
		self._end_sub_tokenize(pev)
		outm.lexeme = f.text[mdatbegin:f.tell()]
		return outm

	def handle_fstring (self, matching='"'):
		f = self.f
		begin = f.tell()
		outs = FStringData.create()
		while True:
			ch = f.read()
			if ch == matching:
				# -2 instead of -1, the latter just gets the " we just read
				if f.peek(-2) == '\\':
					continue
				break
			elif ch == '\n':
				raise TokenizeError('Newline in string template literal')
			elif ch == '':
				raise TokenizeError('Unclosed string literal')
			elif ch == '{':
				split_begin = f.tell()
				pev = self._begin_sub_tokenize(self.Gender.FSTRING)
				tokens = self.tokenize()
				self._end_sub_tokenize(pev)
				outs.sections.append(FStringData.Section(split_begin, f.tell()-1, begin)) # exclude ending }
				outs.section_contents.append(tokens)
		# trailing " already skiped due to the way the loop works
		# also, need to digest string before.. digesting it again.
		# like a cow, i guess. not very efficient though v_v
		outs.lexeme = f.text[begin:f.tell()-1]
		outb = list(outs.lexeme)
		i = len(outs.sections) - 1
		for sect in reversed(outs.sections):
			outb[sect.relative] = str(i)
			i -= 1
		outs.fixed_up_str = digest_string(''.join(outb))
		return outs

	def new_line (self):
		"""
		Assumes the cursor is after the newline char
		"""
		self._line_index = self.f.tell()
		self._line_number += 1

	def add (self, token:TKType, *metadata):
		# self.tokens.append(token)
		# nn = token.name if isinstance(token, TKType) else str(token)
		# print(f'{self.line_number}: {nn} {metadata}')
		tk = Token(token, self.begin, self.position_info, metadata)
		self.tokens.append(tk)

	def inplace_quick (self, cbasetype: TKType):
		if self.f.vore('='):
			self.add(TKType.IN_PLACE_OP, cbasetype)
		self.add(cbasetype)

	def region_quick (self, cbasetype: TKType):
		com_begin = self.f.tell()
		self.f.skip_until('\n', True)
		# dont include newline in comment body
		self.add(cbasetype, CommentData.create(self.f.text[com_begin:self.f.tell() - 1]))
		self.new_line()

	def newline_quick (self, cbasetype: TKType, *metadata):
		self.add(cbasetype, *metadata)
		self.new_line()

	def tokenize (self):
		f = self.f
		add = self.add
		depth = 0
		is_fstring = self.gender is self.Gender.FSTRING
		is_macro = self.gender is self.Gender.MACRO
		while f.has_remaining and f.tell() < self.limit:
			f.skip_while(gml_kinda_ws)
			self.begin = self.position_info
			ch = f.read()
			match ch:
				case '\n':
					if is_macro:
						break
					self.newline_quick(TKType.NEWLINE)
				case '\\':
					if is_macro:
						if f.vore('\n'):
							self.newline_quick(TKType.NEWLINE)
						else:
							raise TokenizeError('Expected newline after continuator (\\)!')
					else:
						raise TokenizeError('Unexpected whack (\\) in stream!')
				case '"':
					if is_fstring and depth == 0:
						raise TokenizeError('Unclosed string template section')
					add(TKType.LITERAL, StringLiteralData.create(self.handle_string_literal()))
				case '@' if f.vore('"'):
					add(TKType.LITERAL, StringLiteralData.create(self.handle_multiline_string_literal()))
				case '@' if f.vore("'"):
					add(TKType.LITERAL, StringLiteralData.create(self.handle_multiline_string_literal("'")))
				case '$' if f.vore('"'):
					add(TKType.LITERAL, self.handle_fstring())
					# raise NotImplementedError('String template')
				case '$' if f.peek_is(char_is_hex_number):
					add(TKType.LITERAL, NumberLiteralData.create_hex(self.handle_hexadecimal_literal()))
				case '0' if f.vore('xX'):
					add(TKType.LITERAL, NumberLiteralData.create_hex(self.handle_hexadecimal_literal()))
				case '0' if f.vore('bB'):
					add(TKType.LITERAL, NumberLiteralData.create_bin(self.handle_binary_literal()))
				case '#':
					mk_begin = f.tell()
					name = f.vore_while(is_identifier)
					if name == 'region':
						self.region_quick(TKType.REGION)
					elif name == 'endregion':
						self.region_quick(TKType.ENDREGION)
					elif name == 'macro':
						if is_macro:
							raise TokenizeError('Cant create a macro inside a macro!')
						f.skip_while(gml_kinda_ws)
						if f.peek_is('\n'):
							raise TokenizeError('Unexpected newline where macro name shouldve been!')
						add(TKType.MACRO, self.handle_macro())
						self.new_line()
					else:
						f.seek(mk_begin)
						name = f.vore_while(char_is_hex_number).replace('_', '')
						if len(name) < 6:
							raise TokenizeError(f'Not enough digits for colour constant {name}!')
						elif len(name) > 6:
							raise TokenizeError(f'Too many digits for colour constant {name}!')
						col = int(name, 16)
						col = ((col>>16)&0xFF)|(col&0xFF00)|((col&0xFF)<<16)
						add(TKType.LITERAL, NumberLiteralData.create(col, NumberLiteralSrc.COLOUR))
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
				case '{':
					if is_fstring:
						depth += 1
					add(TKType.LCURLY, DualTokenType.SYMBOL)
				case '}':
					if is_fstring:
						if depth == 0:
							break
						depth -= 1
					add(TKType.RCURLY, DualTokenType.SYMBOL)
				case '(': add(TKType.LWHIFFLE)
				case ')': add(TKType.RWHIFFLE)
				case '[':
					if   f.vore('|'): add(TKType.ACCESSOR, AccessorType.LIST)
					elif f.vore('?'): add(TKType.ACCESSOR, AccessorType.MAP)
					elif f.vore('#'): add(TKType.ACCESSOR, AccessorType.GRID)
					elif f.vore('@'): add(TKType.ACCESSOR, AccessorType.ARRAY)
					elif f.vore('$'): add(TKType.ACCESSOR, AccessorType.STRUCT)
					else: add(TKType.LBRACKET)
				# these are silly v_v but we need to
				# fallthrough to identifiers if they dont pass
				case '[' if f.v2re('B:'): add(TKType.ACCESSOR, AccessorType.U8)
				case '[' if f.v2re('b:'): add(TKType.ACCESSOR, AccessorType.S8)
				case '[' if f.v2re('X:'): add(TKType.ACCESSOR, AccessorType.U16)
				case '[' if f.v2re('x:'): add(TKType.ACCESSOR, AccessorType.S16)
				case '[' if f.v2re('I:'): add(TKType.ACCESSOR, AccessorType.U32)
				case '[' if f.v2re('i:'): add(TKType.ACCESSOR, AccessorType.S32)
				case '[' if f.v2re('f:'): add(TKType.ACCESSOR, AccessorType.F32)
				case '[' if f.v2re('d:'): add(TKType.ACCESSOR, AccessorType.F64)
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
					elif f.vore('>'):
						add(TKType.INEQUALITY) # apparently gml supports `<>` for `!=`. Undocumented.
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
						self.newline_quick(TKType.COMMENT, CommentData.create(f.text[com_begin:f.tell() - 1]))
						if is_macro: break
					elif f.vore('*'):
						# Multi-line comment
						com_begin = f.tell()
						self.handle_multiline_comment()
						# dont include trailing */ in body
						add(TKType.COMMENT, CommentData.create(f.text[com_begin:f.tell() - 2], True))
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
		if is_fstring and depth != 0:
			raise TokenizeError('Unclosed string template section')
		return self.tokens

	def act (self):
		self.tokenize()
		self.add(TKType.EOF)
		return self.tokens

