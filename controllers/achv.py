# -*- coding: utf-8 -*-

import __init__
import db
from sets import Set

class achievements():

	mongo = db.mongoAdapter()

	updated_records = Set()

	player_achv_col = 'achievements'
	base_achv_col = 'achievements_static'

	static = []
	achvs_array = {}

	def __init__(self, load_static = True):
		if load_static:
			self.static = self.loadStatic()

	def loadStatic(self):
		return self.mongo.getu(self.base_achv_col, {'type': { '$gt': 0 }}, fields={
			"condition": 1,
			"UID": 1
		})

	def update(self, data, statistic):

		new_achvs = Set()

		for achv in self.static:
			if not data['achvs'][str(achv['UID'])]:
				earn_it = True
				for condition in achv['condition']:
					if condition in statistic['stats']:
						earn_it = earn_it and (statistic['stats'][condition] >= achv['condition'][condition])
					else:
						earn_it = False

				if earn_it:
					data['achvs'][str(achv['UID'])] = True
					new_achvs.add(achv['UID'])

		return new_achvs
