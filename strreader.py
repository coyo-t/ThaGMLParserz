from typing import Callable, TypeAlias
import string

Predicate: TypeAlias = Callable[[str], bool]

class StringReader:
	def __init__ (self, text: str):
		self._txt = text
		self._ptr = 0

	def __len__ (self):
		return len(self._txt)

	@property
	def text (self):
		return self._txt

	def tell (self):
		return self._ptr

	def peek (self, offset=0):
		if (self._ptr + offset) >= len(self):
			return ''
		return self._txt[self._ptr]

	def read (self):
		ch = self.peek()
		self.skip()
		return ch

	def prev (self):
		if 0 > (ofs:=self.tell()-1) >= len(self):
			return ''
		return self._txt[ofs]

	def can_read (self, count=1):
		return (self._ptr + count) <= len(self)

	def at_end (self):
		return self._ptr >= len(self)

	def skip (self, offset=1):
		self._ptr += offset

	def rewind (self):
		self._ptr -= 1

	def seek (self, offset: int):
		self._ptr += offset

	def skip_while (self, predicate: Predicate):
		while True:
			if self.can_read() and predicate(self.peek()):
				self.skip()
				continue
			return

	def skip_whitespace (self):
		self.skip_while(lambda ch: ch in string.whitespace)

	def vore_substr (self, substr: str):
		l = len(substr)
		if self._txt[self._ptr:self._ptr+l] == substr:
			self._ptr += l
			return True
		return False

	def take_while (self, predicate: Predicate) -> str:
		start = self.tell()
		while predicate(self.peek()) and self.can_read():
			self.skip()
		return self.text[start : self.tell()]

	def vore (self, *whats: str):
		for what in whats:
			if self.peek() not in what:
				return False
			self.skip()
		return True

	# GOD FUCKING DAMMIT WINDOWS AAAAAAAAAAAAAAAAAAAA
	def vore_newline (self):
		"""
		Consumes either the newline sequence `/r/n`, or just
		a `/n` character, whichever is found

		Thanks Windows -_-
		"""
		if self.peek() == '\r':
			if self.peek(1) == '\n':
				self.skip(2)
				return True
		if self.peek() == '\n':
			self.skip()
			return True
		return False

	def substr_from (self, begin:int):
		return self._txt[begin: self.tell()]
