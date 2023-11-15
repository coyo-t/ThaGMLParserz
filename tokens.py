from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class InplaceKind(Enum):
	ADD  = '+'
	SUB  = '-'
	MUL  = '*'
	DIV  = '/'
	MOD  = '%'
	NULL = '??'
	AND  = '&'
	OR   = '|'
	XOR  = '^'
	LSH  = '<<'
	RSH  = '>>'

	def __str__ (self): return f'{self.value}='

class WordSymbolKind(Enum):
	SYMBOL = False
	WORD   = True

class TokenType:
	pass

@dataclass
class Token:
	type: TokenType
	sub_type: Enum = None
	location: slice = None
	metadata: Any = None


class EOF(TokenType):
	def __str__ (self): return '--< EOF >--'

class Literal(TokenType):
	pass

@dataclass
class Accessor:
	class Kind(Enum):
		DS_LIST = ('|',)
		DS_MAP  = ('?',)
		DS_GRID = ('#',)
		ARRAY   = ('@',)
		STRUCT  = ('$',)
		@property
		def symbol (self) -> str:
			return self.value[0]
		def __str__ (self):
			return f'[{self.symbol}'

	kind: Kind
	def __str__ (self):
		return f'< {self.kind} >'

@dataclass
class Scope(TokenType):
	class Kind(Enum):
		SELF  = ('self',  -1)
		OTHER = ('other', -2)
		ALL   = ('all',   -3)
		NOONE = ('noone', -4)

		@property
		def name (self) -> str:
			return self.value[0]
		@property
		def id (self) -> int:
			return self.value[1]
		def __str__ (self):
			return self.name

	kind: Kind

	def __str__ (self):
		return f'< {self.kind.name}. >'

@dataclass
class DualWordSymbolToken(TokenType):
	was_word: bool = False

def simple_token (symbol: str):
	class SimpleToken(TokenType):
		def __str__ (self): return f'< {symbol} >'
	return SimpleToken()

def bool_literal (state: bool):
	class BoolLiteral(Literal):
		def __str__ (self): return f'< {'true' if state else 'false'} >'
	return BoolLiteral()

def self_literal (kind: Scope.Kind):
	return Scope(kind)

def accessor_token (kind: Accessor.Kind):
	return Accessor(kind)

class Tokens(list[TokenType]):
	def __iadd__(self, other):
		if isinstance(other, (TokenType, TK)):
			self.append(other)
			return self
		return super().__iadd__(other)


class TK(Enum):
	L_BRACE = ()
	R_BRACE = ()

	L_BRACKET = simple_token('[')
	R_BRACKET = simple_token(']')

	L_WHIFFLE = simple_token('(')
	R_WHIFFLE = simple_token(')')

	COMMA = simple_token(',')
	DOT   = simple_token('.')
	SEMICOLON = simple_token(';')
	COLON     = simple_token(':')

	PLUS    = simple_token('+')
	MINUS   = simple_token('-')
	STAR    = simple_token('*')
	SLASH   = simple_token('/')
	PERCENT = simple_token('%')
	EQUALS  = simple_token('=')

	L_SHIFT = simple_token('<<')
	R_SHIFT = simple_token('>>')

	LOGIC_NOT = ()
	LOGIC_AND = ()
	LOGIC_OR  = ()
	LOGIC_XOR = ()

	INT_DIV = simple_token('div')
	INT_MOD = simple_token('mod')

	EQUALITY      = simple_token('==')
	INEQUALITY    = simple_token('!=')
	LESS_THAN     = simple_token('<')
	GREATER_THAN  = simple_token('>')
	LESS_EQUAL    = simple_token('<=')
	GREATER_EQUAL = simple_token('>=')

	BITWISE_NOT = simple_token('~')
	BITWISE_AND = simple_token('&')
	BITWISE_OR  = simple_token('|')
	BITWISE_XOR = simple_token('^')

	INCR = simple_token('++')
	DECR = simple_token('--')

	COMMENT = ()

	QUESTO = simple_token('?')
	NULLISH = simple_token('??')

	OP_ASSIGN = ()
	SPECIAL_ACCESSOR = ()

	KEYWORD = ()
	NEW_OBJECT = simple_token('new')
	SCOPE_NAME = ()
	GLOBAL = simple_token('global')
	UNDEFINED = simple_token('undefined')
	SCRIPT_ARGUMENT = ()

	ACCESS_DS_LIST = accessor_token(Accessor.Kind.DS_LIST)
	ACCESS_DS_MAP  = accessor_token(Accessor.Kind.DS_MAP)
	ACCESS_DS_GRID = accessor_token(Accessor.Kind.DS_GRID)
	ACCESS_ARRAY   = accessor_token(Accessor.Kind.ARRAY)
	ACCESS_STRUCT  = accessor_token(Accessor.Kind.STRUCT)

	FOLD_REGION = ()
	MACRO = ()

	IDENTIFIER = ()
	BOOLEAN_LITERAL = ()
	NUMBER_LITERAL  = ()
	STRING_LITERAL  = ()
	FSTRING_LITERAL = ()

	TRUE  = bool_literal(True)
	FALSE = bool_literal(False)

	SELF  = self_literal(Scope.Kind.SELF)
	OTHER = self_literal(Scope.Kind.OTHER)
	ALL   = self_literal(Scope.Kind.ALL)
	NOONE = self_literal(Scope.Kind.NOONE)

	NEWLINE = simple_token('\\n')
	"""
	this is needed bc semicolons are not required terminators
	for statements. Im not 100% on how GML handles
	implicit semicolons though. -_-
	"""

	EOF = EOF()

	def is_special_accessor (self):
		return isinstance(self.value, Accessor)


class CommentToken(TokenType):
	"""
	Comments are kept as tokens despite not being
	syntactically meaningful. They are however used
	for functor documentation & typing
	"""
	def __init__ (self, contents:str, was_multiline:bool):
		self.contents = contents
		self.multiline = was_multiline
	def __str__ (self):
		if self.multiline:
			return f'< /* {repr(self.contents)} */ >'
		return f'< // {repr(self.contents)} >'

@dataclass
class LBraceToken(DualWordSymbolToken): # {, begin
	def __str__ (self): return f'< {'begin' if self.was_word else '{'} >'


@dataclass
class RBraceToken(DualWordSymbolToken): # }, end
	def __str__ (self): return f'< {'end' if self.was_word else '}'} >'


@dataclass
class AndToken(DualWordSymbolToken):
	def __str__ (self): return f'< {'and' if self.was_word else '&&'} >'


@dataclass
class OrToken(DualWordSymbolToken):
	def __str__ (self): return f'< {'or' if self.was_word else '||'} >'


@dataclass
class XorToken(DualWordSymbolToken):
	def __str__ (self): return f'< {'xor' if self.was_word else '^^'} >'


@dataclass
class InplaceOpToken(TokenType):
	kind: InplaceKind
	def __str__ (self): return f'< {self.kind.value} >'


@dataclass
class LogicNotToken(DualWordSymbolToken):
	def __str__ (self): return f'< {'not' if self.was_word else '!'} >'


@dataclass
class ScriptArgumentToken(TokenType):
	index: int
	def __str__ (self): return f'< argument{'' if self.index < 0 else self.index} >'


@dataclass
class IdentifierToken(TokenType):
	name: str
	def __str__ (self): return f'< Ident: {self.name} >'


@dataclass
class RegionToken(TokenType):
	is_end: bool
	contents: str = field(default='')
	def __str__ (self):
		name = f'#{'end' if self.is_end else ''}region'
		return f'< {name}{' '+repr(self.contents) if len(self.contents) > 0 else ''} >'

	@staticmethod
	def pred (ch: str): return ch != '\n'


@dataclass
class MacroToken(TokenType):
	name: str
	configuration: str = field(default=None)
	body: list[TokenType] = field(default_factory=list)

	def __str__ (self):
		main = f'#macro {self.name}' + (f', cfg:{self.configuration}' if self.has_config else '')
		if len(self.body) != 0:
			main += f', ({', '.join(map(str, self.body))})'
		return f'< {main} >'

	@property
	def has_config (self):
		return self.configuration is not None


@dataclass
class KeywordToken(TokenType):
	keyword: str
	def __str__ (self): return f'< {self.keyword} >'


@dataclass
class NumberLiteralToken(Literal):
	value: float
	def __str__ (self): return f'< Val: {self.value} >'


@dataclass
class StringLiteralToken(Literal):
	string: str
	def __str__ (self): return f'< Str: {repr(self.string)} >'


@dataclass
class StringTemplateToken(Literal):
	string:str         =field(default='')
	bodies:list[Tokens]=field(default_factory=list)

	def __str__ (self):
		main = f'${repr(self.string)}'
		for body in self.bodies:
			main += f', {{{', '.join(map(str, body))}}}'
		return f'< {main} >'


