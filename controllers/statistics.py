# -*- coding: utf-8 -*-

import __init__
import db
from sets import Set

class statistics():

	mongo = db.mongoAdapter()

	dungeons_count = mongo.count('dungeons')

	player_stat_col = 'statistics'
	base_stat_col = 'statistics_static'

	stats_array = {}
	updated_records = Set()

	def __init__(self):
		pass

	def update(self, data, params):
		changed = False
		if params:
			for param in params:
				if param in data['stats']:
					if param == 'lvl':
						data['stats'][param] = params[param]
					else:
						data['stats'][param] += params[param]

					changed = True

		return changed
