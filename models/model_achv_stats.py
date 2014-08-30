#!/usr/bin/python
# -*- coding: utf-8 -*-

import __init__
import settings

class ModelSA():

	col_achv_static = settings.database.cols['col_achv_static']
	col_achvs = settings.database.cols['col_achvs']
	col_stats_static = settings.database.cols['col_stats_static']
	col_stats = settings.database.cols['col_stats']
	col_players = settings.database.cols['players']

	def __init__(self, connection):
		self.mongo = connection
		self.balance = settings.balance


	# GET

	def getAchvForPlayer(self, username):
		player = self.mongo.find(self.col_players, {'name': username}, {'user_id'})
		if player:
			player_achvs = self.mongo.find(self.col_achvs, {'user_id': player['user_id']}, {'achvs':1})['achvs']

			static_achvs = self.mongo.getu(self.col_achv_static, fields={'_id':0, 'condition':0})

			achvs = [None] * len(static_achvs)

			for achv in static_achvs:
				achv.update({'complete': player_achvs[str(achv['UID'])]})
				achvs[achv['order']-1] = achv

			return achvs