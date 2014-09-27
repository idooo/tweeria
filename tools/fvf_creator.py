#!/usr/bin/python
# -*- coding: utf-8 -*-

# This is automated system to create new faction vs faction events
# author: Alex Shteinikov

import __init__
import settings
import time
from sets import Set
import random

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import db
import logger

class FVFCreator:

	mongo = db.mongoAdapter()
	balance = settings.balance()
	core = settings.core()
	log = logger.logger('logs/system_events.log')

	def __init__(self):
		pass

	def checkAndCreateFvF(self, FORCE = False):

		need_to_create_new = True

		last_fvf = self.mongo.getu('events', search={'type': 'fvf'}, sort={'create_date': -1}, limit=1)
		if last_fvf:
			if last_fvf[0]['create_date'] + self.balance.FVF_CREATE_TIME > time.time():
				need_to_create_new = False

		if need_to_create_new or self.core.debug['always_create_fvf'] or FORCE:
			if last_fvf:
				not_side = last_fvf[0]['sides'][random.randint(0,1)]
				sides = [0,1,2]
				del sides[not_side]
				side_1, side_2 = sides

			else:
				side_1 = random.sample([0,1,2], 1)[0]
				side_2 = Set([0,1,2])
				side_2.remove(side_1)
				side_2 = random.sample(side_2, 1)[0]

			self.createFvF(side_1, side_2)

	def createFvF(self, side_1, side_2):

		start_time = time.time() + random.randint(self.balance.FVF_START_TIME_MIN, self.balance.FVF_START_TIME_MAX)

		desc = ''

		event = {
			'type': 'fvf',
			'guild_run': False,
			'desc': desc,
		    'activity': [],
			'start_date': start_time,
			'create_date': time.time(),
		    'finish_date': start_time + self.balance.LENGTH_OF_FVF,
			'status': 'active',
			'promoted_hashtag': [self.balance.FVF_HASHES[side_1], self.balance.FVF_HASHES[side_2]],
			'sides': [side_1, side_2],
		    'sides_names': [self.balance.faction[side_1], self.balance.faction[side_2]],
			'people': []
		}

		self.mongo.insert('events', event)

		message = 'FvF event was created: '+event['sides_names'][0]+' vs. '+event['sides_names'][0]
		self.log.write(message)
		print message

if __name__ == "__main__":

	fvf = FVFCreator()
	fvf.checkAndCreateFvF()
