from enum import Enum

class TK(Enum):
	LBRACE = () # {
	RBRACE = () # }

	LBRACKET = () # [
	RBRACKET = () # ]

	LWHIFFLE = () # (
	RWHIFFLE = () # )

	EQUALS = () # =
	PLUS   = () # +
	MINUS  = () # -
	STAR   = () # *
	SLASH  = () # /
	MOD    = () # %

	INCR = () # ++
	DECR = () # --

	COMMA     = () # ,
	DOT       = () # .
	SEMICOLON = () # ;
	COLON     = () # :

	QUESTO     = () # ?
	NULLISH    = () # ??

	WHACK     = () # \
	AT        = () # @
	MIDAS     = () # $
	FONG      = () # #
	SQUIGGLE  = () # ~

	EQUALITY   = () # ==
	INEQUALITY = () # !=
	LESS      = () # <
	GREATER   = () # >
	LESSEQ    = () # <=
	GREATEREQ = () # >=

	BANG = () # !  not
	AND  = () # && and
	OR   = () # || or
	XOR  = () # ^^ xor

	AMPERSAND = () # &
	PIPE      = () # |
	CARROT    = () # ^
	LSHIFT    = () # <<
	RSHIFT    = () # >>

	IDIV = () # div
	IMOD = () # mod

	INPLACE_OP = () # detr by InplaceKind
	SPECIAL_ACCESSOR = () # detr by accessorkind

	SCRIPT_ARG = ()

	COMMENT = ()
	NEWLINE = ()
	EOF = ()
