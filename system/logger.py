# -*- coding: utf-8 -*-

# Log module
#
# author: Alex Shteinikov

from time import strftime
import os

class logger():

	fp = file

	def __init__(self, filename = ''):
		if filename != '':
			self.openFile(os.path.dirname(os.path.realpath(__file__))+'/../'+filename)

	def openFile(self, filename):
		self.fp = open(filename, 'a')

	def write(self, message, tp = 0):
		str = strftime("%d.%m.%Y %H:%M:%S")

		if tp == 0:
			str = 'INFO  '+str

		str += '  '+message+'\n'

		self.fp.write(str)

	def closeFile(self):
		self.fp.close()