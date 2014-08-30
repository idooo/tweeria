#!/usr/bin/python
# -*- coding: utf-8 -*-

import __init__
import settings
import random
from bson import ObjectId

class Guild(settings.BaseObj):

	data = {
		'name': '',
		'search_name': '',
		'link_name': '',
		'description':'',
		'people':[],
		'creator': '',
		'img': 'none',
		'score': 0,
		'open': 1,
		'people_count':0,
		'request': [],
		'site_link': '',
		'pvp_score' : 0,
		'faction': -1,
	    'guild_points': 0
	}

class GuildNews(settings.BaseObj):

	data = {
		'guild_id': 0,
	    'news': []
	}

class ModelGuilds():

	col_guilds = settings.database.cols['guilds']
	col_players = settings.database.cols['players']
	col_gmessages = settings.database.cols['col_guild_messages']
	col_gnews = settings.database.cols['col_guilds_news']

	def __init__(self, connection):
		self.mongo = connection
		self.balance = settings.balance

	# GET

	def getPlayersGuild(self, user_id):
		return self.mongo.find(self.col_guilds, {'people':{'$all':[user_id]}})

	def getTopGuildsByPeopleCount(self, count = 10):
		return self.mongo.getu(self.col_guilds, {}, fields = {'name':1, 'people_count':1, 'img':1, 'pvp_score':1}, limit = count, sort = {'people_count': -1})

	def getGuildByName(self, name, type_of_name='search_name'):
		if type_of_name == 'search_name':
			name = name.upper()

		return self.mongo.find(self.col_guilds, {type_of_name: name})

	def getGuildMembers(self, guild, field = 'people', sort_query = {}):
		if not field in guild or not guild[field]:
			return []

		players = self.mongo.findSomeIDs(self.col_players, guild[field], sort=sort_query, fields={
			'_id': 1,
			'name': 1,
			'class': 1,
			'lvl':1,
		    #'stat':1,
			'avatar': 1,
			'achv_points': 1,
			'pvp_score': 1,
			'race': 1,
		    'faction': 1,
		    'user_id': 1,
		    'stat.lead.current': 1
		})

		return players

	def getGuildNews(self, guild_id):
		return self.mongo.find(self.col_gnews, {'guild_id': guild_id})

	def getGuildToWarList(self, my_guild_name, limit = 10):
		return self.mongo.getu(self.col_guilds, search={'name': {'$ne': my_guild_name}}, limit=limit)

	def getGuildByID(self, id):
		return self.mongo.find(self.col_guilds, {'_id': id})

	def getGuildsByIDs(self, ids):
		return self.mongo.findSomeIDs(self.col_guilds, ids, fields={
			'_id': 1,
			'name': 1,
		})

	def getGuildMessages(self, guild_name):
		return self.mongo.find(self.col_gmessages, {'name': guild_name})

	def getGuilds(self):
		return self.mongo.getu(self.col_guilds, fields={
			"pvp_score": 1,
			"people": 1,
			"faction": 1,
			"score": 1,
			"people_count": 1,
			"name": 1
		})

	def getTrendingGuilds(self, limit = 10):

		people_count = random.randint(5, 35)
		pvp_score = random.randint(1,1000)
		gte = random.randint(0,1)

		return self.mongo.getu(
			self.col_guilds,
			search={
				'people_count': {['$gte','$lte'][gte]: people_count},
			    'pvp_score': {'$gte':pvp_score},
			},
			fields={'name':1, 'people_count':1, 'img':1, 'link_name':1, 'pvp_score':1},
			limit=limit
		)

	def getGuildsListFiltered(self, count = 10, search_query = {}, page = 1, field = False, sort = -1):
		if field:
			sort_query = {field: sort}
		else:
			sort_query = {}

		fields = {'name':1, 'img':1, 'people_count':1, 'pvp_score':1, 'guild_points': 1}

		return self.mongo.getu(self.col_guilds, search = search_query, fields = fields, skip = count*(page-1), limit = count, sort = sort_query)

	def getGuildsListSearch(self, search_query):
		return self.mongo.getu(self.col_guilds, search_query, {'name': 1, '_id': 0}, limit=10)

	def getGuildsCount(self):
		return self.mongo.count(self.col_guilds)

	def getTopPvPGuildPlayers(self, guild_id, min_pvp_score = 0, count = 5):
		guild_people = self.mongo.find(self.col_guilds, {'_id': guild_id}, {'people': 1})
		if guild_people:
			query = []
			for id in guild_people['people']:
				query.append({'_id':id})

			if query:
				return self.mongo.getu(
					self.col_players,
					search={"$or" : query},
					fields={'_id': 1, 'name': 1},
					sort={'pvp_score': -1},
					limit=count
				)

		return False

	# ADD

	def addGuild(self, guild):
		player_id = guild['creator']

		if self.mongo.find(self.col_guilds, {'search_name': guild['search_name']}):
			return False

		self.mongo.insert(self.col_guilds, guild)
		self.mongo.update(self.col_players, {'_id': player_id}, {'_guild_name': guild['name']})

		history = [self.balance.guild_message]
		record = {'name': guild['name'], 'history': history}
		self.mongo.insert(self.col_gmessages, record)

		guild_id = self.mongo.find(self.col_guilds, {'name': guild['name']}, {'_id':1})['_id']

		self.mongo.insert(self.col_gnews, {
			'guild_id': guild_id,
		    'news': []
		})

		return True

	# MISC

	def rawUpdateGuild(self, guild_name, fields):
		self.mongo.raw_update(self.col_guilds, {'name': guild_name}, fields)

	def setGuildMessages(self, guild_name, messages):
		self.mongo.update(self.col_gmessages, {'name': guild_name}, {'history': messages})

	def clearGuildSettings(self, player_id):
		self.mongo.update(self.col_players, {'_id': player_id}, {'_guild_name': ''})

	def changeSettings(self, guild_id, settings):
		self.mongo.update(self.col_guilds, {'_id': guild_id}, settings)

	def leaveGuild(self, guild_id, player_id):
		self.mongo.raw_update(self.col_guilds, {'_id': guild_id}, {'$inc':{'people_count': -1}, "$pull":{'people': player_id}})
		self.clearGuildSettings(player_id)

	def joinGuild(self, guild_id, player_id, guild_name = ''):
		self.mongo.update(self.col_players, {'_id': player_id}, {'_guild_name': guild_name})
		self.mongo.raw_update(self.col_guilds, {'_id': guild_id}, {'$inc':{'people_count': 1}, "$push":{'people': player_id}})

	def isGuildExist(self, search_name):
		return self.mongo.find(self.col_guilds, {'search_name': search_name})

	def promoteLeadership(self, guild_id, player_name):
		player = self.mongo.find(self.col_players, {'name': player_name}, {'_id':1})
		if player:
			self.mongo.update(self.col_guilds, {'_id': guild_id}, {'creator':player['_id']})

	def removeGuild(self, guild_id, player_id):
		self.mongo.remove(self.col_guilds, {'_id': guild_id})
		self.mongo.remove(self.col_gnews, {'guild_id': guild_id})
		self.clearGuildSettings(player_id)

	def askInvite(self, guild_id, player_id):
		self.mongo.raw_update(self.col_guilds, {'_id': guild_id}, {"$push":{'request': player_id}})

	def rejectInvite(self, guild_id, player_id):
		self.mongo.raw_update(self.col_guilds, {'_id': guild_id}, {"$pull":{'request': player_id}})

	def removeAllRequests(self, player_id):
		guilds = self.mongo.getu(self.col_guilds, { 'request': {'$all': [player_id]}}, {'_id':1})
		for guild in guilds:
			self.mongo.raw_update(self.col_guilds, {'_id': guild['_id']}, {"$pull":{'request': player_id}})

	# NEWS

	def getGuildNews(self, guild_id):
		return self.mongo.find(self.col_gnews, {'guild_id': guild_id})

	def addNewsToBase(self, guild_id, news_body):
		self.mongo.raw_update(self.col_gnews, {'guild_id': guild_id}, {'$push': {'news': news_body}})
		print self.mongo.getLastError()

	def removeNewsFromBase(self, guild_id, news_uid):
		self.mongo.raw_update(self.col_gnews, {'guild_id': guild_id}, {'$pull': {'news': {'UID': news_uid} }})
