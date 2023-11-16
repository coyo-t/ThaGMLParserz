from pathlib import Path
import logging

ASSETS  = Path('./assets')
FPWGMS2 = Path('D:/_projects/parallel2shit/gml')
SCRIPTS = FPWGMS2/'__parallel/fnaf1 recreation/scripts'
GMS2PROJ = Path('D:/_projects/xGamemakerStudio2')

def script_name (name:str,root=SCRIPTS):
	return root/name/f'{name}.gml'

def to_exec ():
	return (
		# script_name('__scr_ai_oldStep')
		# script_name('scr_menu_night6')
		# ASSETS/'draw_rout_cctv.gml'
		# script_name('scr_lz4', GMS2PROJ/'grimdawnfdumpforcazey/scripts')
		# script_name('scr_macro', GMS2PROJ/'grimdawnfdumpforcazey/scripts')
		# script_name('_debug', FPWGMS2/'FPW_beta_conv/scripts')
		# FPWGMS2/'__parallel/paramk6/objects/obj_panorama/Draw_0.gml'
		# script_name('script_listener', GMS2PROJ/'mc adiobussy tesst2/scripts')
		script_name('player_camera_update', GMS2PROJ/'__old/Popgoes 1 Repainted/scripts')
		# ASSETS/'multiline_macro_test.gml'
		# ASSETS/'strings_test.gml'
		# ASSETS/'comments_test.gml'
		# ASSETS/'number_literal_tests.gml'
	)

def mm2 ():
	from tokenize import tkv2
	fname = to_exec()
	print(f'Tokenizing "{fname}"')
	source = fname.read_text('utf8').replace('\r\n', '\n').replace('\r', '\n')
	tokenizer = tkv2.Tokenizer(source)

	tokens = tokenizer.act()
	depth = 0
	def fuckfuckfuck (tk: list[tkv2.Token]):
		nonlocal depth
		for token in tk:
			if token.type.debug_indent_decr(): depth = max(depth - 1, 0)
			print(f'{'\t' * depth}{token}')
			if token.type.debug_indent_incr(): depth += 1
			if token.type is tkv2.TKType.MACRO:
				print('==== BEGIN MACRO ====')
				meta = token.macro_get_metadata()
				print(repr(meta.lexeme))
				depth += 1
				fuckfuckfuck(meta.tokens)
				depth -= 1
				print('====  END MACRO  ====')

	fuckfuckfuck(tokens)

	# try:
	# 	tokenizer.act()
	# except Exception as e:
	# 	logging.error(
	# 		f'{type(e).__name__} when tokenizing source file: {e.args[0]}\n'
	# 		f'@Line: {tokenizer.line_index+1}, Char: {tokenizer.char_index-1}',
	# 	)

# from tokens import *
# import tokenizer
# def mm ():
# 	print('---- BEGIN ----')
# 	result = tokenizer.main(to_exec())
# 	return
#
# 	depth = 0
# 	scope_incr = False
# 	scope_decr = False
# 	for token in result:
# 		match token:
# 			case TK() if token.is_special_accessor():
# 				scope_incr = True
# 			case LBraceToken() | TK.L_BRACKET | TK.L_WHIFFLE | TK.SPECIAL_ACCESSOR:
# 				scope_incr = True
# 			case RBraceToken() | TK.R_BRACKET | TK.R_WHIFFLE:
# 				scope_decr = True
# 			case RegionToken():
# 				(scope_decr:=True) if token.is_end else (scope_incr:=True)
# 		depth -= scope_decr
# 		ident = '\t' * depth
# 		depth += scope_incr
# 		scope_incr = scope_decr = False
# 		match token:
# 			case TK() as tk:
# 				outs = tk.value
# 			case _:
# 				outs = token
# 		print(f'{ident}{outs}')
# 	print('----  END  ----')

if __name__ == '__main__':
	mm2()
	# mm()
