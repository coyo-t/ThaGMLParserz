from dataclasses import dataclass, field
from typing import TypeAlias, Callable
import itertools

Predicate: TypeAlias = Callable[[str], bool]

@dataclass
class Reader:
	_str: str = field(default='')
	_ptr: int = 0

	def __len__ (self):
		return len(self._str)

	def tell (self):
		return self._ptr

	def seek (self, position: int):
		self._ptr = position

	@property
	def cursor (self):
		return self.tell()

	@cursor.setter
	def cursor (self, value:int):
		self.seek(value)

	@property
	def text (self):
		return self._str

	@property
	def has_remaining (self):
		return 0 <= self._ptr < len(self)

	@property
	def remaining (self):
		l = len(self)
		return max(0, min(l - self._ptr, l))

	def can_read (self, amount=1):
		return self._ptr >= 0 and self._ptr + amount <= len(self)

	def change_text (self, new_text:str):
		self._str = new_text
		self._ptr = 0

	def peek_at (self, index:int):
		# this is formatted weirdly, i might want to do "on encounter char" callback
		if 0 <= index < len(self._str):
			ch = self._str[index]
		else:
			ch = ''
		return ch

	def peek (self, offset:int=0):
		return self.peek_at(self._ptr + offset)

	def skip (self, count:int=1):
		self._ptr += count

	def rewind (self):
		"""Move the cursor back by one"""
		self._ptr -= 1

	def read (self):
		ch = self.peek()
		self.skip()
		return ch

	def v2re (self, seq: str):
		"""
		Checks a sequence of characters. Only advances if all pass.
		This is silly
		"""
		if all(self.peek(i) == ch for i, ch in enumerate(seq)):
			self.skip(len(seq))
			return True
		return False

	def vore (self, pred: str|Predicate):
		"""
		Advance the cursor if the current char matches any chars in the input string,
		or the predicate returns `True` for the current char, otherwise do nothing.
		:returns: Whether or not the cursor advanced
		"""
		match pred:
			case str():
				if self.peek() in pred:
					self.skip()
					return True
			case Predicate():
				if pred(self.peek()):
					self.skip()
					return True
		return False

	def __iter__ (self):
		"""
		Return characters from the current cursor
		position up until the end of the string
		"""
		# return iter(self.read, '')
		return self.iter()

	def peek_is (self, pred:str|Predicate, offset=0):
		return (self._digest_predicate(pred))(self.peek(offset))

	def peek_isnt (self, pred:str|Predicate, offset=0):
		return not self.peek_is(pred, offset)

	@staticmethod
	def _digest_predicate(pred:str|Predicate)->Predicate:
		if isinstance(pred,str):
			return pred.__contains__
		return pred

	def skip_while (self, pred:str|Predicate, inclusive=False):
		"""
		Skip until `False`
		:arg pred: A predicate which returns `True` to continue, or a string
		that contains the characters to continue skipping on
		:arg inclusive: Also skip the character that stopped the loop if `True`
		"""
		predicate = self._digest_predicate(pred)
		while predicate(self.peek()) and self.has_remaining:
			self.skip()
		if inclusive: self.skip()

	def skip_until (self, pred:str|Predicate, inclusive=False):
		"""
		Skip chars until `True`
		:arg pred: A predicate which returns `True` to break, or a string
		that contains the characters to break on
		:arg inclusive: Also skip the character that stopped the loop if `True`
		"""
		predicate = pred.__contains__ if isinstance(pred, str) else pred
		while not predicate(self.peek()) and self.has_remaining:
			self.skip()
		if inclusive: self.skip()

	#TODO:
	# There should be a few states to "inclusive". non-inclusive,
	# which doesnt include or skip the character that stopped the loop
	# inclusive, which both includes it in the result & skips it,
	# and skip_inclusive, which doesnt include it in the result but *does*
	# skip it anyway
	def vore_while (self, pred:str|Predicate, inclusive=False):
		"""
		Read & return a string from the current cursor position up until
		`pred` returns `False`. if `inclusive` is `True`, the character
		that caused `pred` to return `False` will be included in the result and
		advance the cursor position.
		"""
		begin = self.cursor
		self.skip_while(pred, inclusive=inclusive)
		return self._str[begin:self.cursor]

	def vore_until (self, pred:str|Predicate, inclusive=False):
		"""
		Read & return a string from the current cursor position up until
		`pred` returns `True`. if `inclusive` is `True`, the character
		that caused `pred` to return `True` will be included in the result and
		advance the cursor position.
		"""
		begin = self.cursor
		self.skip_until(pred, inclusive=inclusive)
		return self._str[begin:self.cursor]

	def iter (self):
		# return (self._str[i] for i in range(self.cursor, len(self)))
		while (ch:=self.read()) != '':
			yield ch

	def iter_while (self, pred:str|Predicate):
		return itertools.takewhile(self._digest_predicate(pred), self)

	def substr_from (self, substr_begin: int):
		"""
		:return: A slice of the string from `substr_begin` up to the cursor position
		"""
		return self._str[substr_begin:self.cursor]
