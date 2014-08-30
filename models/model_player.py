#!/usr/bin/python
# -*- coding: utf-8 -*-

import __init__
import __main__
import settings
from time import time
import random
from sets import Set
from model_spells import SpellBook
import tweepy
from bson import ObjectId

class PlayerInstance(settings.BaseObj):

	data = {
		'achv_points' : 0,

		'token1' : '',
		'token2' : '',

		'name' : '',
		'avatar' : '',
		'class' : 0,
		'race' : -1,
		'faction': -1,
		'sex': 0, # 0 - Female, 1 — Male
		'exp' : 0,
		'lvl' : 1,
		'last_id' : 0,
		'last_login': 0,
		'pvp' : False,
		'pvp_score' : 0,

		'artworks': [],
		'titles': [],

		'stat': {},
		'user_id' : 0,

		# geo coords
		'position': {
			"x": 0,
			"y": 0,
			"last": []
		},

		'resources': {
			"prg": 5,
			"ore": 5,
			"eore": 1,
			"gold": 100
		},

		'resistance': {
			'fire': 0,
			'air': 0,
			'water': 0,
			'earth': 0,
			'poison': 0,
			'arcane': 0,
			},

		'buffs': [],

		# backlinks
		# Информация сохраненная здесь может быть неактуальной
		# используется лишь для увеличения скорости отображения
		# и оптимизации
		'_guild_name': '',

		# system hidden
		'activity': [],
		'metrics': {},
		'ratings': [],

		'utc_offset': 0,

	    'invited': []
	}

class ModelPlayers():

	col_players = settings.database.cols['players']
	col_created = settings.database.cols['col_created']
	col_spellbooks = settings.database.cols['col_spellbooks']
	col_messages_created = settings.database.cols['col_messages_created']
	col_stats_static = settings.database.cols['col_stats_static']
	col_stats = settings.database.cols['col_stats']
	col_achvs_static = settings.database.cols['col_achv_static']
	col_achvs = settings.database.cols['col_achvs']
	col_invites = settings.database.cols['col_invites']
	col_beta_users = settings.database.cols['col_beta_players']
	col_created = settings.database.cols['col_created']
	col_crafted = settings.database.cols['col_crafted']
	col_gamestats = settings.database.cols['col_gamestats']
	col_items_deleted = settings.database.cols['col_items_deleted']
	col_bad_people = settings.database.cols['col_admin_bad_people']
	col_artworks = settings.database.cols['col_artworks']
	col_spells_pattern = settings.database.cols['col_spells_crafted_patterns']
	col_guilds = settings.database.cols['guilds']

	def __init__(self, connection):
		self.mongo = connection
		self.balance = settings.balance
		self.core = settings.core

	# GET

	def getStaticAchievements(self):
		return self.mongo.getu(self.col_achvs_static)

	def getPlayersList(self, _ids = False, fields_names = False):
		if fields_names:
			fields = {}
			for field_name in fields_names:
				fields.update({field_name: 1})
		else:
			fields = {}

		if not _ids:
			return self.mongo.getu(self.col_players, fields = fields)
		else:
			people = Set()
			for _id in _ids:
				people.add(_id)

			query = {'_id': {'$in': list(people)}}
			return self.mongo.getu(self.col_players, search=query, fields=fields)

	def getPlayersList2(self, _ids, fields = {}):
		query = {'_id': {'$in': list(_ids)}}
		return self.mongo.getu(self.col_players, search=query, fields=fields)

	def getPlayer_ID(self, name):
		player = self.mongo.find(self.col_players, {'name': name}, {'_id': 1})
		if player:
			return player['_id']

	def getPlayer(self, something, fields = False, flags = []):

		search_field = 'user_id'
		try:
			criteria = int(something)
		except Exception:
			search_field = 'name'
			criteria = something

		need_messages = False

		if not fields:
			fields = {'name':1, 'user_id':1, 'avatar':1, 'token1':1, 'token2':1, 'utc_offcet': 1}
		elif fields == 'all':
			fields = {}
			need_messages = True
		elif fields == 'game':
			need_messages = True
			fields = {'activity':0, 'metrics':0}
		elif fields == 'map':
			need_messages = False
			fields = {'name':1, '_id':1, 'position':1, 'class':1, 'faction':1, 'race':1}
		elif fields == 'other_map_player':
			need_messages = False
			fields = {'name':1, '_id':1, 'position':1, 'class':1, 'faction':1, 'race':1, 'lvl':1, 'avatar':1}

		if 'no_messages' in flags:
			need_messages = False


		player = self.mongo.find(self.col_players, {search_field:criteria}, fields)

		if player and need_messages:
			messages = self.mongo.find('messages_created', {'user_id': player['user_id']})
			if not messages:
				messages = []

			player.update({'messages': messages['last']})

		return player

	def getPlayerRaw(self, user_id, fields):
		return self.mongo.find(self.col_players, {'user_id': user_id}, fields)

	def getPlayerBy_ID(self, _id, fields = {}):
		if not isinstance(_id, ObjectId):
			try:
				_id = ObjectId(_id)
			except Exception:
				return False

		return self.mongo.find(self.col_players, {'_id': _id}, fields)

	def getPlayerRawByName(self, name, fields = {}):
		return self.mongo.find(self.col_players, {'name': name}, fields)

	def getPlayersRaw(self, query = {}, fields = {}):
		return self.mongo.getu(self.col_players, query, fields)

	def getBannedPlayers(self):
		players = self.mongo.getu(self.col_players, {'banned': {'$exists':1}}, {'name':1, 'ban_reason': 1, 'banned_by': 1})
		return players

	def getUGCEnabledPlayers(self, fields = {'_id': 1, 'name': 1, 'ugc_enabled': 1}):
		return self.mongo.getu(self.col_players, {'ugc_enabled': True}, fields)

	def getStatsByUserID(self, name):
		return self.mongo.find(self.col_players, {'user_id': name}, {'stat':1, 'lvl':1})

	def getTrendingPlayers(self, limit = 10):

		lvl = random.randint(2,30)
		pvp_score = random.randint(0,1000)
		achv_points = random.randint(0, 20)

		return self.mongo.getu(
			self.col_players,
			search={
				'lvl': {'$gte': lvl},
			    'pvp_score': {'$gte': pvp_score},
			    'achv_points': {'$gte': achv_points},
			    'last_login': {'$gte': time() - self.core.MAX_TIME_TO_SLEEP}
			},
			fields={'name':1, 'class':1, 'lvl':1, 'avatar':1, 'race':1, 'faction':1, 'pvp_score':1, 'achv_points': 1},
			limit=limit,
		)

	def getPlayerHaveItems(self, player_id):
		return self.mongo.getu('items_created', {'player_id': player_id})

	def getPlayerItems(self, player_id, criteria = None):
		if not criteria:
			return self.mongo.getu('items_created', {'player_id': player_id, 'sell': False})
		else:
			if criteria == 'equipped': # написать выбор для инвентария
				return self.mongo.getu('items_created', {'player_id': player_id, 'equipped': False})

	def getPlayerMessages(self, user_id):
		return self.mongo.find(self.col_messages_created, {'user_id': user_id}, fields={'_id':0})

	def getStatisticStaticForPrint(self):
		return self.mongo.getu(self.col_stats_static, fields={"text": 1, "visibility": 1, 'name': 1, 'type': 1}, sort={'order': 1})

	def getPlayerStatistics(self, user_id):
		return self.mongo.find(self.col_stats, {'user_id': user_id})

	def getAchvStaticForPrint(self):
		return self.mongo.getu(self.col_achvs_static, fields={'UID':1, "type": 1, "name": 1, "visibility": 1,'img': 1, 'text':1 }, sort={'order': 1})

	def getPlayerAchvs(self, user_id):
		return self.mongo.find(self.col_achvs, {'user_id': user_id})

	def getModerators(self):
		return self.mongo.getu(self.col_players, {'moderator': {'$exists': True}}, {
			'name': 1,
			'user_id': 1,
			'moderator_rights': 1,
		    'moderator_stats': 1
		})

	def getInvitedList(self):
		return self.mongo.getu(self.col_invites)

	def isUserAdmin(self, name):
		return self.mongo.find(self.col_players, {'name': name,'admin': {'$exists': True}}, {'name':1, 'user_id':1})

	def getEnemyPlayerData(self, player_name):
		return self.mongo.find(self.col_players, {'name': player_name}, {
			'_id':1,
		    'class':1,
		    'stat':1,
		    'buffs':1,
		    'lvl':1,
		    'pvp':1,
		    'user_id':1,
		    'name':1
		})

	def getNearPlayers(self, x, y, pvp = -1, name = '', lvl = 0, additional = False, all_map = False):
		if all_map:
			rad = 10
		else:
			rad = 3

		lvl_pvp_diff = self.balance.PVP_LVL_DIFF

		query = {
			'position.x': {'$gte': x-rad, '$lte':x+rad},
			'position.y': {'$gte': y-rad, '$lte':y+rad},
		    'name': {'$ne': name}
		}

		if lvl > 0:
			query.update({'lvl':{'$gte': lvl-lvl_pvp_diff, '$lte': lvl+lvl_pvp_diff}})

		if pvp == -1:
			pass
		elif pvp:
			query.update({'pvp': 1})
		else:
			query.update({'pvp': 0})

		need_fields = {'name': 1, 'user_id':1, 'lvl':1}
		if additional:
			need_fields.update({'position':1, 'class':1, 'faction':1, 'race':1, 'pvp':1, 'avatar':1})

		return self.mongo.getu(self.col_players, query , need_fields)

	def getNearPlayersCount(self, x, y, rad, name):

		query = {
			'position.x': {'$gte': x-rad, '$lte':x+rad},
			'position.y': {'$gte': y-rad, '$lte':y+rad},
			'name': {'$ne': name}
		}

		return self.mongo.count(self.col_players, query)

	def getNearEnemies(self, rad, player):
		query = {
			'position.x': {'$gte': player['position']['x']-rad, '$lte':player['position']['x']+rad},
			'position.y': {'$gte': player['position']['y']-rad, '$lte':player['position']['y']+rad},
		    'faction': {'$ne': player['faction']},
		    '_guild_name': {'$ne': player['_guild_name']},
		    'lvl': {'$gte': player['lvl']-10, '$lte': player['lvl']+10},
		    'pvp': 1
		}

		return self.mongo.getu(self.col_players, query, {
			'name': 1,
			'_guild_name': 1,
			'race': 1,
		    'class': 1,
		    'faction': 1,
		    'lvl': 1,
		    'avatar': 1
		}, limit=10)

	def getNearFriends(self, rad, player):
		if player['_guild_name']:
			query = {
				'position.x': {'$gte': player['position']['x']-rad, '$lte':player['position']['x']+rad},
				'position.y': {'$gte': player['position']['y']-rad, '$lte':player['position']['y']+rad},
				'_guild_name': player['_guild_name'],
			    'name': {'$ne': player['name']}
			}

			return self.mongo.getu(self.col_players, query, {
				'name': 1,
				'race': 1,
				'class': 1,
				'faction': 1,
				'lvl': 1,
				'avatar': 1
			}, limit=10)

		return []

	def getAllPlayerCoords(self):
		return self.mongo.getu(self.col_players, {}, {'name':1, 'position':1})

	def getPlayersListFiltered(self, count = 10, search_query = {}, page = 1, field = False, sort = -1):
		if field:
			sort_query = {field: sort}
		else:
			sort_query = {}

		fields = {'name':1, 'avatar':1, 'lvl':1, 'class':1, 'faction':1, 'race':1, '_guild_name':1, 'achv_points':1, 'pvp_score':1}

		return self.mongo.getu(self.col_players, search = search_query, fields = fields, skip = count*(page-1), limit = count, sort = sort_query)

	def getPlayersCount(self):
		return self.mongo.count(self.col_players)

	def updatePlayerBuffs(self, player_id, buffs):
		self.mongo.update(self.col_players, {'_id': player_id}, {'buffs': buffs})

	def getFriends(self, player_id):
		if isinstance(player_id, str):
			player_id = ObjectId(player_id)

		player = self.mongo.find(self.col_players, {'_id': player_id}, {'token1':1, 'token2':1, 'user_id':1})

		p_key = __main__.tweenk_core.loaded_data['p_key']
		p_secret = __main__.tweenk_core.loaded_data['p_secret']

		if player:
			auth = tweepy.OAuthHandler(p_key, p_secret)
			auth.set_access_token(player['token1'], player['token2'])
			api = tweepy.API(auth)
			return api.friends(user_id = player['user_id'])
		else:
			return False

	def getRejectInfo(self):
		return self.mongo.getu(self.col_bad_people, fields={'_id': 0}, sort={'total': -1})

	def getUGCDisabled(self):
		return self.mongo.getu(self.col_players, {'ugc_disabled': {'$exists': True}}, fields={'_id': 1})

	# ADD

	def addNewPlayer(self, player_info, starter_items_UIDs = [], join_guild = False):

		def createStatRecord(user_id):
			stats = self.mongo.getu('statistics_static', fields={'_id':0})
			record = {}
			for stat in stats:
				if stat['type'] != 'none':
					record[stat['name']] = stat['amount']

			self.mongo.insert('statistics',{'user_id': user_id, 'stats': record})

		def createAchvRecord(user_id):
			achvs = self.mongo.getu('achievements_static', fields={'_id':0})
			record = {}
			for achv in achvs:
				record[str(achv['UID'])] = False

			self.mongo.insert('achievements',{'user_id': user_id, 'achvs': record})

		def getStartedItems(player_id):
			for item in starter_items_UIDs:
				item = self.mongo.find('items',{'UID':item})

				item_record = {
					'player_id'   : player_id,
					'UID'         : item['UID'],
					'name'		  : item['name'],
					'type'		  : item['type'],
					'view'		  : item['view'],
					'color'		  : item['color'],
					'lvl_min'	  : item['lvl_min'],
					'bonus'		  : item['bonus'],
					'cost'		  : item['cost'],
					'img'		  : item['img'],
					'equipped'    : True
				}

				self.mongo.insert('items_created',item_record)

		def addMessageRecord(user_id):
			last = [self.balance.welcome_message]
			record = {'user_id': user_id, 'last': last, 'history': last}
			self.mongo.insert(self.col_messages_created, record)

		def addSpellBook(player_id):

			spellbook = SpellBook()

			spellbook.data.update({
				'player_id': player_id
			})

			self.mongo.insert(self.col_spellbooks, spellbook.data.copy())

		self.mongo.insert(self.col_players, player_info)
		player_id = self.mongo.find('players',{'user_id':player_info['user_id']},{'_id':1})['_id']

		if not self.mongo.getLastError() and player_id:
			createStatRecord(player_info['user_id'])
			createAchvRecord(player_info['user_id'])
			getStartedItems(player_id)
			addMessageRecord(player_info['user_id'])
			addSpellBook(player_id)

			if join_guild:
				guild = self.mongo.find(self.col_guilds, {'search_name': join_guild.upper()}, {'_id': 1, 'name': 1})
				if guild:
					self.mongo.update(self.col_players, {'_id': player_id}, {'_guild_name': guild['name']})
					self.mongo.raw_update(self.col_guilds, {'_id': guild['_id']}, {'$inc':{'people_count': 1}, "$push":{'people': player_id}})

			return player_id

		return False

	# MISC

	def isPlayerAdmin(self, player_id):
		return self.mongo.find(self.col_players, {'_id': player_id, 'admin':{'$exists': True}})

	def isPlayerModerator(self, player_id):
		return self.mongo.find(self.col_players, {'_id': player_id, 'moderator':{'$exists': True}}, {
			'_id':1,
		    'moderator_rights': 1
		})

	def isBetaPlayer(self, user_id):
		return self.mongo.find(self.col_beta_users, {'user_id': user_id})

	def setPlayerMessages(self, user_id, messages):
		self.mongo.update(self.col_messages_created, {'user_id': user_id}, {'last': messages})

	def getCurrentStats(self, stats):
		current_stats = {}
		for stat_name in stats:
			current_stats.update({stat_name: stats[stat_name]['current']})

		return current_stats

	def recalculateStats(self, player_id, items = None, player_stats = None, update = True):

		if not items:
			items = self.mongo.getu(self.col_created, {'player_id': player_id, 'equipped': True}, {'bonus': 1})

		if not player_stats:
			player = self.mongo.find(self.col_players, {'_id': player_id}, {'stat':1})

			if player:
				stats = player['stat']
			else:
				return False
		else:
			stats = player_stats

		new_stats = {}

		for stat_name in stats:
			new_stats.update({stat_name: stats[stat_name]['max']})

		for item in items:
			for stat_name in item['bonus']:
				new_stats[stat_name] += item['bonus'][stat_name]

		for stat_name in stats:
			diff = stats[stat_name]['max_dirty'] - stats[stat_name]['current']
			stats[stat_name]['max_dirty'] = new_stats[stat_name]
			stats[stat_name]['current'] = new_stats[stat_name] - diff

			if stat_name == 'MP' and stats[stat_name]['current'] == 0:
				pass
			elif stats[stat_name]['current'] <= 0:
				stats[stat_name]['current'] = 1

		if update:
			self.mongo.update(self.col_players, {'_id': player_id}, {'stat': stats})

		return stats

	def increaseModeratorStats(self, player_id, action_type, thing_type, action_time):
		if action_type == 'approve':
			modifier = 'a'
		else:
			modifier = 'r'

		self.mongo.raw_update(self.col_players, {'_id': player_id}, {
			'$inc': {'moderator_stats.'+modifier+'_'+thing_type: 1},
		    '$set': {'moderator_stats.time': action_time}
		})

		print self.mongo.getLastError()

	def promoteToModerator(self, player_name, rights):
		self.mongo.update(self.col_players, {'name': player_name}, {
			'moderator': True,
			'moderator_rights': rights,
		    'moderator_stats' : {
			    'a_items': 0,
		        'a_spells': 0,
		        'a_artworks': 0,
		        'r_items': 0,
		        'r_spells': 0,
		        'r_artworks': 0,
		        'time': 0
		    }
		})

	def rejectFromModerator(self, player_name):
		self.mongo.raw_update(self.col_players, {'name': player_name}, {
			'$unset': {'moderator': 1, 'moderator_rights': 1, 'moderator_stats': 1}
		})

	def invitePlayer(self, player_name):
		self.mongo.update(self.col_invites, {'name': player_name}, {'name': player_name}, True)

	def rejectInvite(self, player_name):
		self.mongo.remove(self.col_invites, {'name': player_name})

	def banPlayer(self, player_name, banned_by, reason = 'Not a human'):

		if not reason.strip():
			reason = 'Not a human'

		player = self.mongo.find(self.col_players, {'name':player_name}, {'token1': 1, 'token2':1, '_id':1})
		if not player:
			return False

		player_id = player['_id']
		del player['_id']

		player.update({
			'achv_points': 0,
		    'pvp_score': 0,
			'lvl': 1,
			'exp': 0,
		    'resources': {'gold': 0, 'ore':0, 'prg':0, 'eore': 0},
			'token1': '__'+player['token1'],
			'token2': '__'+player['token2'],
		    'banned': True,
		    'ratings': {'trending_position': 100500},
		    'ban_reason': reason,
		    'banned_by': banned_by
		})

		self.mongo.update(self.col_players, {'_id':player_id}, player)

		self.mongo.remove(self.col_created, {'player_id': player_id})
		self.mongo.update(self.col_crafted, {'author': player_id}, {'sale_info.active': False})

		return True

	def changeLevelByName(self, player_name, level, reason, author = False, author_name = False):
		player = self.mongo.find(self.col_players, {'name':player_name}, {'_id': 1})

		if not player:
			return False

		self.mongo.update(self.col_players, {'_id': player['_id']}, {
			'lvl': level,
		    'exp': 0,
		    'lvl_reduce_reason': reason
		})

		data = {
			'player_id': player['_id'],
		    'player_name': player_name,
		    'level': level,
		    'reason': reason,
		    'author': author,
		    'author_name': author_name,
		    'time': time()
		}

		is_info_about_reduces = self.mongo.find(self.col_gamestats, {'type': 'levels'}, {'_id': 1})
		if is_info_about_reduces:
			self.mongo.raw_update(self.col_gamestats, {'type': 'levels'}, {'$push': {'info': data}})
		else:
			self.mongo.insert(self.col_gamestats, {
				'type': 'levels',
			    'info': [data]
			})

		return True

	def updatePlayerData(self, player_id, data):
		try:
			if not isinstance(player_id, ObjectId):
				player_id = ObjectId(player_id)

			self.mongo.update(self.col_players, {'_id': player_id}, data)
		except Exception:
			self.mongo.update(self.col_players, {'name': player_id}, data)

	def rawUpdatePlayerData(self, player_id, data):
		try:
			if not isinstance(player_id, ObjectId):
				player_id = ObjectId(player_id)

			self.mongo.raw_update(self.col_players, {'_id': player_id}, data)
		except Exception:
			return False

	def resetPlayerData(self, player_id, data):
		self.updatePlayerData(player_id, data)

		self.mongo.remove(self.col_created, {'player_id': player_id})

	def giveBonusToReferal(self, refer_name, user_id, user_name):
		self.mongo.raw_update(self.col_players, {'name': refer_name},{
			'$inc': {
				'stat.fame.max': 1,
				'stat.fame.max_dirty': 1,
				'stat.fame.current': 1,
				'stat.luck.max': 1,
				'stat.luck.max_dirty': 1,
				'stat.luck.current': 1
			},
			'$push': {'invited': {user_name: user_id}}
		})

	def recalculateAchvPoints(self, user_id, achv_points = -1):

		achv = self.mongo.find(self.col_achvs, {'user_id':user_id})

		count = 0
		for a in achv['achvs']:
			if achv['achvs'][a]:
				count += 1

		if count != achv_points:
			self.mongo.update(self.col_players, {'user_id': user_id}, {'achv_points': count})

	def takeAchv(self, player_name, achv_UID):
		player = self.mongo.find(self.col_players, {'name': player_name}, {'user_id':1, 'achv_points': 1})

		if player:
			self.mongo.update(self.col_achvs, {'user_id': player['user_id']}, {'achvs.'+str(achv_UID): True})
			self.recalculateAchvPoints(player['user_id'], player['achv_points'])
			return True

		else:
			return False

	def updateRejectInfo(self, obj_id, tp):

		# tp = type of thing (0 - item, 1 - spell, 2 - artwork)

		if not isinstance(obj_id, ObjectId):
			obj_id = ObjectId(obj_id)

		if tp == 0:
			collection = self.col_crafted
			inc = 'items'

		elif tp == 1:
			collection = self.col_spells_pattern
			inc = 'artworks'

		elif tp == 2:
			collection = self.col_artworks
			inc = 'spells'

		else:
			return False

		thing = self.mongo.find(collection, {'_id': obj_id}, {'author': 1})

		self.mongo.raw_update(self.col_bad_people, {'player_id': thing['author']}, {
			'$inc': {'r_'+inc: 1, 'total': 1},
			'$set': {'player_id': thing['author']}
		}, True)

	# Twitter API

	def postMentionInvite(self, from_player_id, text):
		player = self.mongo.find(self.col_players, {'_id': from_player_id}, {'token1':1, 'token2':1, 'user_id':1, 'name':1})

		p_key = __main__.tweenk_core.loaded_data['p_key']
		p_secret = __main__.tweenk_core.loaded_data['p_secret']

		if player:
			auth = tweepy.OAuthHandler(p_key, p_secret)
			auth.set_access_token(player['token1'], player['token2'])
			api = tweepy.API(auth)
			api.update_status(text)
			return True
		else:
			return False

	def getUserTimeline(self, player_name):
		player = self.mongo.find(self.col_players, {'name': player_name}, {'token1':1, 'token2':1, 'user_id':1, 'name':1})

		if not player:
			return (False, False)

		p_key = __main__.tweenk_core.loaded_data['p_key']
		p_secret = __main__.tweenk_core.loaded_data['p_secret']

		try:
			auth = tweepy.OAuthHandler(p_key, p_secret)
			auth.set_access_token(player['token1'], player['token2'])
			api = tweepy.API(auth)
			return (True, api.user_timeline(include_entities=1, include_rts=True))

		except Exception, e:
			return (False, str(e))

