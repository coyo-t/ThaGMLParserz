from pathlib import Path

ASSETS  = Path('./assets')
DEGEN_CASES = ASSETS/'degenerate cases'
FPWGMS2 = Path('D:/_projects/parallel2shit/gml')
SCRIPTS = FPWGMS2/'__parallel/fnaf1 recreation/scripts'
GMS2PROJ = Path('D:/_projects/xGamemakerStudio2')

def script_name (name:str,root=SCRIPTS):
	return root/name/f'{name}.gml'

def to_exec ():
	return (
		# script_name('__scr_ai_oldStep')
		# script_name('scr_menu_night6')
		# script_name('scr_lz4', GMS2PROJ/'grimdawnfdumpforcazey/scripts')
		# script_name('scr_macro', GMS2PROJ/'grimdawnfdumpforcazey/scripts')
		# script_name('_debug', FPWGMS2/'FPW_beta_conv/scripts')
		# script_name('script_listener', GMS2PROJ/'mc adiobussy tesst2/scripts')
		# script_name('player_camera_update', GMS2PROJ/'__old/Popgoes 1 Repainted/scripts')

		# GMS2PROJ/'QoI THing/objects/Object1/Create_0.gml'
		# FPWGMS2/'__parallel/paramk6/objects/obj_panorama/Draw_0.gml'

		# ASSETS/'draw_rout_cctv.gml'
		# ASSETS/'multiline_macro_test.gml'
		ASSETS/'strings_test.gml'
		# ASSETS/'comments_test.gml'
		# ASSETS/'number_literal_tests.gml'

		# DEGEN_CASES/'macro in macro.gml'
	)

def mm2 ():
	import logging
	from coyote_tokenize import tkv2
	fname = to_exec()
	print(f'Tokenizing "{fname}"')
	source = fname.read_text('utf8').replace('\r\n', '\n').replace('\r', '\n')
	tokenizer = tkv2.Tokenizer(source)

	tokens = tokenizer.act()
	depth = 0
	def fuckfuckfuck (tk: list[tkv2.Token]):
		nonlocal depth
		for token in tk:
			if token.type.debug_indent_decr():
				depth = max(depth - 1, 0)
			indent = '\t' * depth
			print(f'{indent}{token.begin.line_number+1:04d} {token}')
			if token.type.debug_indent_incr():
				depth += 1
			if token.type is tkv2.TKType.MACRO:
				print(f'{indent}==== BEGIN MACRO ====')
				meta = token.macro_get_metadata()
				print(repr(meta.lexeme))
				depth += 1
				fuckfuckfuck(meta.tokens)
				depth -= 1
				print(f'{indent}====  END MACRO  ====')
			if token.type is tkv2.TKType.LITERAL:
				data = token.literal_get()
				if isinstance(data, tkv2.FStringData):
					print(f'{indent}==== BEGIN FSTRING {repr(data.fixed_up_str)} ====')
					for sect in data.section_contents:
						depth += 1
						fuckfuckfuck(sect)
						depth -= 1
					print(f'{indent}====  END FSTRING  ====')


	fuckfuckfuck(tokens)

	# try:
	# 	tokenizer.act()
	# except Exception as e:
	# 	logging.error(
	# 		f'{type(e).__name__} when tokenizing source file: {e.args[0]}\n'
	# 		f'@Line: {tokenizer.line_index+1}, Char: {tokenizer.char_index-1}',
	# 	)


if __name__ == '__main__':
	mm2()
	# mm()
