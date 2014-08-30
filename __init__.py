# -*- coding: UTF-8 -*-

import os, sys, inspect

for dir in ['controllers','system','web','tools','models', 'system/parser_modules']:
	cmd_folder = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])+'/'+dir
	if cmd_folder not in sys.path:
		sys.path.insert(0, cmd_folder)