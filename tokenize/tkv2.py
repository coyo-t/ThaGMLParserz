from enum import Enum, auto
from .reader import Reader
from .types import TMP_TK

gml_kinda_ws = ' \t\v\f'
gml_all_ws = '\r\n'+gml_kinda_ws

class TokenType(Enum):
	PLUS  = auto()
	MINUS = auto()
	STAR  = auto()
	SLASH = auto()

	LINE_COMMENT  = auto()
	BLOCK_COMMENT = auto()

	NEWLINE = auto()
	EOF = auto()

class TokenizeError(Exception):
	pass

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

	def add (self, token, *metadata):
		# self.tokens.append(token)
		nn = token.name if isinstance(token, TokenType) else str(token)
		sl = slice(self.begin, self.f.tell())
		print(f'{nn} {sl} {metadata}')

	def new_line (self):
		"""
		Assumes the cursor is after the newline char
		"""
		self.line_index = self.f.tell()
		self.line_number += 1

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
				case '/':
					if f.vore('/'):
						# Single-line comment
						# If you think about it, single line comments are just
						# really big newline characters
						com_begin = f.tell()
						f.skip_until('\n', True)
						# dont include newline in comment body
						add(TokenType.LINE_COMMENT, f.text[com_begin:f.tell()-1])
						self.new_line()
					elif f.vore('*'):
						# Multi-line comment
						com_begin = f.tell()
						self.handle_multiline_comment()
						# dont include trailing */ in body
						add(TokenType.BLOCK_COMMENT, f.text[com_begin:f.tell()-2])
					else:
						add(TokenType.SLASH)


	def act (self):
		self.tokenize()

