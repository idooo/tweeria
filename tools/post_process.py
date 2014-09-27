#!/usr/bin/python
# -*- coding: utf-8 -*-

# author: Alex Shteinikov

import __init__
import settings
tweenk_core = settings.core()
tweenk_balance = settings.balance()

import db
import random
import logger

class postProcess():

	mongo = db.mongoAdapter()
	log = logger.logger('logs/system_events.log')

	def __init__(self):
		pass

	def guildInfoUpdate(self):

		buff_players = self.mongo.getu('players', fields={'_guild_name':1, '_id':1})
		guilds = self.mongo.getu('guilds', fields={'name':1, 'people':1, '_id':1, 'people_count': 1})

		players = {}

		for buff in buff_players:
			players.update({str(buff['_id']): buff})

		for guild in guilds:
			for player_id in guild['people']:
				player_str_id = str(player_id)
				if player_str_id in players:
					if players[player_str_id]['_guild_name'] != guild['name']:
						self.mongo.update('players', {'_id': player_id}, {'_guild_name': guild['name']})
				else:
					guild['people_count'] -= 1
					self.mongo.update('guilds', {'_id': guild['_id']},{'people': filter (lambda x: x != player_id, guild['people']), 'people_count': guild['people_count']})

	def achvUpdate(self):
		buff_players = self.mongo.getu('players', fields={'achv_points':1, '_id':1, 'user_id':1})

		players = {}

		for buff in buff_players:
			players.update({
				str(buff['user_id']): buff['achv_points']
			})

		achievements = self.mongo.getu('achievements')

		for achv in achievements:
			count = 0
			for a in achv['achvs']:
				if achv['achvs'][a]:
					count += 1

			str_user_id = str(achv['user_id'])

			if str_user_id in players and players[str_user_id] != count:
				self.mongo.update('players', {'user_id': achv['user_id']}, {'achv_points': count})

	def goldCorrect(self):
		players = self.mongo.getu('players', {'resources.gold':{'$lt': 0}}, {'_id': 1})
		for player in players:
			self.mongo.update('players', {'_id': player['_id']}, {'resources.gold': int(random.randint(100, 200))})

	def process(self):
		self.guildInfoUpdate()
		self.achvUpdate()
		self.goldCorrect()

		message = 'Post process finished'
		self.log.write(message)
		print message

if __name__ == "__main__":

	pp = postProcess()
	pp.process()
