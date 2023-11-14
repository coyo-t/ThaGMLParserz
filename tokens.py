from dataclasses import dataclass, field
from enum import Enum

class Token:
	pass


class Tokens(list[Token]):
	def __iadd__(self, other):
		if isinstance(other, Token):
			self.append(other)
			return self
		return super().__iadd__(other)


class ScopeKind(Enum):
	SELF   = ('self',  -1)
	OTHER  = ('other', -2)
	ALL    = ('all',   -3)
	NOONE  = ('noone', -4)

	@property
	def name (self) -> str:
		return self.value[0]

	@property
	def id (self) -> int:
		return self.value[1]

	def __str__ (self): return self.name


class AccessorKind(Enum):
	DS_LIST = ('|',)
	DS_MAP  = ('?',)
	DS_GRID = ('#',)
	ARRAY   = ('@',)
	STRUCT  = ('$',)

	@property
	def symbol (self) -> str:
		return self.value[0]

	def __str__ (self): return f'[{self.symbol}'


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


class EOFToken(Token):
	def __str__ (self): return '--< EOF >--'


class CommentToken(Token):
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


class NewlineToken(Token):
	"""
	this is needed bc semicolons are not required terminators
	for statements. Im not 100% on how GML handles
	implicit semicolons though. -_-
	"""
	def __str__(self): return '< \\n >'


@dataclass
class LBraceToken(Token): # {, begin
	was_word: bool = False
	def __str__ (self): return f'< {'begin' if self.was_word else '{'} >'


@dataclass
class RBraceToken(Token): # }, end
	was_word: bool = False
	def __str__ (self): return f'< {'end' if self.was_word else '}'} >'


@dataclass
class AndToken(Token):
	was_word:bool = False
	def __str__ (self): return f'< {'and' if self.was_word else '&&'} >'


@dataclass
class OrToken(Token):
	was_word:bool = False
	def __str__ (self): return f'< {'or' if self.was_word else '||'} >'


@dataclass
class XorToken(Token):
	was_word:bool = False
	def __str__ (self): return f'< {'xor' if self.was_word else '^^'} >'


class LWhiffleToken(Token):
	def __str__ (self): return '< ( >'
class RWhiffleToken(Token):
	def __str__ (self): return '< ) >'
class LBracketToken(Token):
	def __str__ (self): return '< [ >'
class RBracketToken(Token):
	def __str__ (self): return '< ] >'
class SlashToken(Token):
	def __str__ (self): return '< / >'
class WhackToken(Token):
	def __str__ (self): return '< \\ >'
class DotToken(Token):
	def __str__ (self): return '< . >'
class CommaToken(Token):
	def __str__ (self): return '< , >'
class AtToken(Token):
	def __str__ (self): return '< @ >'
class MidasToken(Token): # The Dollar $ymbol
	def __str__ (self): return '< $ >'
class ColonToken(Token):
	def __str__ (self): return '< : >'
class SemiColonToken(Token):
	def __str__ (self): return '< ; >'
class SquiggleToken(Token):
	def __str__ (self): return '< ~ >'
class IntDivToken(Token):
	def __str__ (self): return '< div >'
class IntModToken(Token):
	def __str__ (self): return '< mod >'
class AmpersandToken(Token):
	def __str__ (self): return '< & >'
class PipeToken(Token):
	def __str__ (self): return '< | >'
class CarrotToken(Token):
	def __str__ (self): return '< ^ >'
class PlusToken(Token):
	def __str__ (self): return '< + >'
class MinusToken(Token):
	def __str__ (self): return '< - >'
class StarToken(Token):
	def __str__ (self): return '< * >'
class PercToken(Token):
	def __str__ (self): return '< % >'
class IncrToken(Token):
	def __str__ (self): return '< ++ >'
class DecrToken(Token):
	def __str__ (self): return '< -- >'
class NewObjectToken(Token):
	def __str__ (self): return '< new >'
class BangEqualsToken(Token):
	def __str__ (self): return '< != >'
class EqualsToken(Token):
	def __str__ (self): return '< = >'
class DoubleEqualsToken(Token):
	def __str__ (self): return '< == >'
class LShiftToken(Token):
	def __str__ (self): return '< << >'
class LessToken(Token):
	def __str__ (self): return '< < >'
class LequalToken(Token):
	def __str__ (self): return '< <= >'
class RShiftToken(Token):
	def __str__ (self): return '< >> >'
class GreaterToken(Token):
	def __str__ (self): return '< > >'
class GequalToken(Token):
	def __str__ (self): return '< >= >'
class UndefinedToken(Token):
	def __str__ (self): return '< undefined >'
class GlobalToken(Token):
	def __str__ (self): return '< global >'
class QuestoToken(Token):
	def __str__ (self): return '< ? >'
class NullishToken(Token):
	def __str__ (self): return '< ?? >'


@dataclass
class InplaceOpToken(Token):
	kind: InplaceKind
	def __str__ (self): return f'< {self.kind.value} >'


@dataclass
class LogicNotToken(Token):
	was_word: bool = False
	def __str__ (self): return f'< {'not' if self.was_word else '!'} >'


@dataclass
class SpecialAccessorToken(Token):
	kind: AccessorKind
	def __str__ (self): return f'< {self.kind} >'


@dataclass
class ScriptArgumentToken(Token):
	index: int
	def __str__ (self): return f'< argument{'' if self.index < 0 else self.index} >'


@dataclass
class IdentifierToken(Token):
	name: str
	def __str__ (self): return f'< Ident: {self.name} >'


@dataclass
class BoolLiteralToken(Token):
	value: bool
	def __str__ (self): return f'< {'true' if self.value else 'false'} >'


@dataclass
class RegionToken(Token):
	is_end: bool
	contents: str = field(default='')
	def __str__ (self):
		name = f'#{'end' if self.is_end else ''}region'
		return f'< {name}{' '+repr(self.contents) if len(self.contents) > 0 else ''} >'


@dataclass
class MacroToken(Token):
	name: str
	configuration: str = field(default=None)
	body: list[Token] = field(default_factory=list)

	def __str__ (self):
		main = f'#macro {self.name}' + (f', cfg:{self.configuration}' if self.has_config else '')
		if len(self.body) != 0:
			main += f', ({', '.join(map(str, self.body))})'
		return f'< {main} >'

	@property
	def has_config (self):
		return self.configuration is not None


@dataclass
class ScopeToken(Token):
	kind: ScopeKind
	def __str__ (self): return f'< {self.kind.value}. >'


@dataclass
class KeywordToken(Token):
	keyword: str
	def __str__ (self): return f'< {self.keyword} >'


@dataclass
class NumberLiteralToken(Token):
	value: float
	def __str__ (self): return f'< Val: {self.value} >'


@dataclass
class StringLiteralToken(Token):
	string: str
	def __str__ (self): return f'< Str: {repr(self.string)} >'


@dataclass
class StringTemplateToken(Token):
	string:str         =field(default='')
	bodies:list[Tokens]=field(default_factory=list)

	def __str__ (self):
		main = f'${repr(self.string)}'
		for body in self.bodies:
			main += f', {{{', '.join(map(str, body))}}}'
		return f'< {main} >'




