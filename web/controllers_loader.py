# -*- coding: UTF-8 -*-

import __init__
import settings
import os, inspect

class controllersLoader():

	def __init__(self):
		self._loadModules()
		self._getAlias()

	def _loadModules(self):
		modules_folder = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])+'/../controllers'

		self.modules = {}
		for item in os.listdir(modules_folder):
			if item[-2:] == 'py':
				self.modules.update({item[:-3:]:__import__(item[:-3:])})

	def _getAlias(self):
		self.alias = []
		self.controllers = {}
		for item in self.modules:
			try:
				self.controllers.update({item: self.modules[item].data['class']()})
				self.modules[item].data.update({'name': item})
				self.alias.append(self.modules[item].data)
			except Exception:
				pass


