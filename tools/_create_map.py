#!/usr/bin/python
# -*- coding: utf-8 -*-

# author: Alex Shteinikov

import __init__
import settings
tweenk_core = settings.core()
tweenk_balance = settings.balance()

import optparse
import os, inspect, sys
import re
import codecs
import db

def readMap(mapname):

	lines = []

	with codecs.open(mapname, "r", "utf-16") as sourceFile:
		while True:
			contents = sourceFile.readline()
			if not contents:
				break

			lines.append(contents)

	mongo = db.mongoAdapter()
	mongo.cleanUp('map')

	width = 60 #filelines[0].split(',')[0][2:]
	height = 50 #filelines[0].split(',')[1]

	RE_MAP_KEY = re.compile('end-map-key')

	state = 0
	x = 0
	y = 0

	line_number = 0

	features = []

	for line in lines:

		if state == 0:
			if re.search(RE_MAP_KEY,line):
				state = 1

		elif state == 1:
			state = 2

		elif state == 2:
			if x == height and y < width:
				x = 0
				y += 1

			if y < width:

				buff = line.split('\t')
				if buff[0] == 'feature':
					type_of_object = buff[3].split(':')[1]
					features.append({'y':x-1, 'x':y, 'type': type_of_object})
				else:
					data = {'y':x, 'x':y, 'tile': buff[0], 'elevation': int(buff[1].split(':')[1]) }
					x += 1
					mongo.insert('map', data)

		line_number += 1

if __name__ == '__main__':
	readMap(os.path.dirname(os.path.realpath(__file__))+'/map/map.hxm')
