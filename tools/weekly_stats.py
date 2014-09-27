#!/usr/bin/python
# -*- coding: utf-8 -*-

# This is a weekly stats module
# author: Alex Shteinikov

import __init__
import settings

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import db

class WeeklyStats:

	mongo = db.mongoAdapter()
	balance = settings.balance()
	core = settings.core()

	def __init__(self):
		pass

	def updateStats(self):

		collection = 'weekly_stats'

		if not self.mongo.collectionExist(collection):
			self.mongo.createCollection(collection)

		stats = self.mongo.getu('statistics', {'user_id': 12164662})
		prev_weekly = self.mongo.getu(collection)

		if not prev_weekly:
			prev_weekly = []

		str_prev_weekly = {}
		for stat in prev_weekly:
			str_prev_weekly.update({str(stat['user_id']): stat['stats']})

		to_update = []

		for stat in stats:
			str_id = str(stat['user_id'])
			if str_id in str_prev_weekly:
				diff = {
					'monsters': stat['stats']['kills_monster'] - str_prev_weekly[str_id]['monsters'],
					'players': stat['stats']['pvp_kills_player'] - str_prev_weekly[str_id]['players'],
					'lvl': stat['stats']['lvl'] - str_prev_weekly[str_id]['lvl']
				}

				record = {'user_id': stat['user_id'], 'stats': diff}

				if diff['monsters'] + diff['players'] + diff['lvl'] > 0:
					to_update.append(record)

					normal = {
						'monsters': stat['stats']['kills_monster'],
						'players': stat['stats']['pvp_kills_player'],
						'lvl': stat['stats']['lvl']
					}

					self.mongo.update(collection, {'user_id': stat['user_id']}, {'stats': normal})

			else:
				diff = {
					'monsters': stat['stats']['kills_monster'],
				    'players': stat['stats']['pvp_kills_player'],
				    'lvl': stat['stats']['lvl']
				}

				record = {'user_id': stat['user_id'], 'stats': diff}

				if diff['monsters'] + diff['players'] + diff['lvl'] > 1:
					to_update.append(record)

				self.mongo.insert(collection, record)

		for item in to_update:
			print item

if __name__ == "__main__":

	ws = WeeklyStats()
	ws.updateStats()