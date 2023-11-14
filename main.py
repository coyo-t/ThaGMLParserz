from pathlib import Path
import tokenizer
from tokens import *

ASSETS  = Path('./assets')
FPWGMS2 = Path('D:/_projects/parallel2shit/gml')
SCRIPTS = FPWGMS2/'__parallel/fnaf1 recreation/scripts'
GMS2PROJ = Path('D:/_projects/xGamemakerStudio2')

def script_name (name:str,root=SCRIPTS):
	return root/name/f'{name}.gml'

def mm ():
	print('---- BEGIN ----')
	result = tokenizer.main(
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
	)
	depth = 0
	for tk in result:
		ident = '\t' * depth
		if isinstance(tk, (LBraceToken, LBracketToken, LWhiffleToken)):
			depth += 1
			print(f'{ident}{tk}')
			continue
		elif isinstance(tk, (RBraceToken, RBracketToken, RWhiffleToken)):
			depth -= 1
			ident = '\t' * depth
		elif isinstance(tk, RegionToken):
			if tk.is_end:
				depth -= 1
				ident = '\t' * depth
			else:
				depth += 1
			print(f'{ident}{tk}')
			continue
		print(f'{ident}{tk}')
	print('----  END  ----')

if __name__ == '__main__':
	mm()
