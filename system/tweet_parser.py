# -*- coding: utf-8 -*-

import __init__
import settings

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import random
from model_basic import DataModel
import re
import db
import os, inspect
import time
from sets import Set
import statistics, achv
from functions import getReadbleTime, getMessages, inCircle

def _profile(method_to_decorate):
	def wrapper(*args, **kwargs):
		t_start = time.time()
		result = method_to_decorate(*args, **kwargs)
		t_all = time.time() - t_start
		print '@'+method_to_decorate.__name__,'\t', t_all
		return result

	return wrapper

class tweetParser():

	balance = tweenk_balance
	core = tweenk_core
	mongo = db.mongoAdapter()

	items = {}
	player = {}
	lvls = {}

	tweet_vars = {}

	ratings_metrics = {}

	interactions = []
	reverse_interactions = []

	notable_messages = []
	meganotable_messages = []

	updated_fields = Set()
	updated_events = Set()

	def __init__(self, debug = False):
		self.DEBUG = debug
		self._loadModules()
		self.model = DataModel()

		# clear 1 week pool items
		clear_time = time.time() - self.balance.POOLED_MAX_TIME
		self.mongo.remove('items_pool', {'pooled_date': {'$lt': clear_time}})

		self.getGameObjects()


	# -------------------------
	# Modules

	def _loadModules(self):
		modules_folder = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])+'/parser_modules'

		self.modules = {}
		for item in os.listdir(modules_folder):
			if item[-2:] == 'py':
				self.modules.update({item[:-3:]:__import__(item[:-3:])})

	def isModule(self, name):
		return name in self.modules

	# -------------------------
	# Events

	def _processPvPGroupWarMechanics(self, event):

		query = []
		for id in event['people']:
			query.append({'_id': id})

		players_info = self.mongo.getu(
			'players',
			search = {'$or' : query},
			fields = {'stat': 1, 'class': 1, '_guild_name': 1, 'faction': 1, '_id': 1, 'name': 1}
		)

		if event['type'] == 'war':
			sides = {
			'side_1': {
			'name': event['guild_side_name'],
			'id': event['guild_side'],
			},
			'side_2': {
			'name': event['target_name'],
			'id': event['target']
			}
			}

		elif event['type'] == 'fvf':
			sides = {
			'side_1': {
			'name': event['sides_names'][0],
			'id': event['sides'][0]
			},
			'side_2': {
			'name': event['sides_names'][1],
			'id': event['sides'][1]
			}
			}

		fight_result = self.modules['fight'].fightBetweenGroups(
			sides, players_info, self.balance, event
		)

		return fight_result

	def processRaid(self, event):

		def processRaidMechanics(event, dungeon):

			def getChances(activity, author_leaderhip):

				MAGIC_BONUS = 0.2
				MAX_TWEETS = 10

				players = {}
				for active in activity:
					player_id = str(active['player_id'])

					if player_id in players:
						players[player_id]['count'] += 1
					else:
						players[player_id] = {
						'count': 1,
						'lvl': active['player_lvl'],
						'magic': 0,
						}

					if active['is_spell']:
						players[player_id]['magic'] += 1

				points = 0

				for player_id in players:
					if players[player_id]['count'] > MAX_TWEETS:
						players[player_id]['count'] = MAX_TWEETS

					number = players[player_id]['count']

					if players[player_id]['magic'] > MAX_TWEETS:
						players[player_id]['magic'] = MAX_TWEETS

					magic = players[player_id]['magic']

					points += players[player_id]['lvl']*(number+magic*MAGIC_BONUS)


				points = int(points + float(points)*float(author_leaderhip*self.balance.AUTHOR_EVENT_BONUS)/100)
				return {'points': points, 'combat': players}

			def getAuthorLeadshipBonus(event):
				if event['author'] in event['people']:
					author_stat = self.mongo.find('players', {'_id': event['author']}, {'stat':1})
					if author_stat:
						return author_stat['stat']['lead']['current']

				return 0

			author_leaderhip = getAuthorLeadshipBonus(event)

			result = getChances(event['activity'], author_leaderhip)
			is_complete = dungeon['power'] <= result['points']

			# find ignored lazy players
			ignored = []
			for player_id in event['people']:
				if not str(player_id) in result['combat']:
					ignored.append(player_id)

			return {
			'is_complete': is_complete,
			'result_points': result['points'],
			'combat': result['combat'],
			'is_ignored': ignored
			}

		dungeon = self.getRaidByUID(event['target'])
		monster = self.getRandomMonster(dungeon_UID = event['target'], must_be_boss = True)

		result = processRaidMechanics(event, dungeon)

		is_event_complete = result['is_complete']

		for player_id in event['people']:
			self.changePlayer(player_id)
			is_ignored = player_id in result['is_ignored']
			self.parse({
				'is_event': True,
				'event_type': 'raid',
				'is_complete': is_event_complete,
				'people': len(event['people']),
				'dungeon': dungeon,
				'is_ignored': is_ignored,
				'boss': monster
			})
			try:
				self.savePlayerData()
			except:
				pass

		if is_event_complete:
			status = 'complete'
		else:
			status = 'fail'

		return {
			'status': status,
			'result_points': result['result_points'],
			'combat': result['combat']
		}

	def processGuildWar(self, event):

		result = self._processPvPGroupWarMechanics(event)

		if not result:
			event.update( {
				'status': 'fail',
				'winner': False,
				'winner_id': False,
				'combat': []
			})
			return False

		event.update({
			'status': 'complete',
			'winner': result['winner_name'],
			'winner_id': result['winner_id'],
			'combat': result['combat']
		})

		for player_id in event['people']:
			is_ignored = player_id in result['combat']['ignored']
			self.changePlayer(player_id)
			self.parse({
			'is_event': True,
			'is_complete': True,
			'event': event,
			'is_ignored': is_ignored,
			'event_type': 'war'
			})

			self.savePlayerData()

		return True

	def processFvF(self, event):

		result = self._processPvPGroupWarMechanics(event)

		if not result:
			return False

		event.update({
		'status': 'complete',
		'winner': result['winner_name'],
		'winner_id': result['winner_id'],
		'combat': result['combat']
		})

		for player_id in event['people']:
			is_ignored = player_id in result['combat']['ignored']
			self.changePlayer(player_id)
			self.parse({
			'is_event': True,
			'is_complete': True,
			'event': event,
			'is_ignored': is_ignored,
			'event_type': 'fvf'
			})

			self.savePlayerData()

		return True

	def processEvents(self):
		events = self.model.events.getJustFinishedEvents()

		for event in events:
			if event['type'] == 'raid':
				combat_result = self.processRaid(event)
				event.update(combat_result)

			elif event['type'] == 'war':
				combat_result = self.processGuildWar(event)

				if combat_result:
					if 'ignored' in event['combat']:
						del event['combat']['ignored']

					if event['target'] != event['winner_id']:
						looser_id = event['target']
					else:
						looser_id = event['guild_side']

					self.mongo.raw_update('guilds', {'_id': looser_id}, {'$inc': {'guild_points': self.balance.GVG_GUILD_LOOSE_REWARD}})
					self.mongo.raw_update('guilds', {'_id': event['winner_id']}, {'$inc': {'guild_points': self.balance.GVG_GUILD_WIN_REWARD}})

			elif event['type'] == 'fvf':
				combat_result = self.processFvF(event)

				if combat_result:
					if 'ignored' in event['combat']:
						del event['combat']['ignored']

					if event['sides'][0] == event['winner_id']:
						str_looser_id = str(event['sides'][1])
					else:
						str_looser_id = str(event['sides'][0])

					str_winner_id = str(event['winner_id'])

					self.mongo.raw_update('game_statistics', {'type': 'pvp_faction_stats'}, {
						'$inc': {
						'points.'+str_winner_id: self.balance.PVP_FVF_REWARD,
						'points.'+str_looser_id: self.balance.PVP_FVF_LOOSE_REWARD,
						'battles'+str_winner_id: 1,
						'battles'+str_looser_id: 1,
						'wins'+str_winner_id: 1,
					}
				})

		self.model.events.markJustFinishedAsFinished(events)

	def saveCurrentEvents(self):
		for event_id in self.updated_events:
			self.model.events.updateEvent(self.all_events[event_id]['_id'], {
				'status': self.all_events[event_id]['status'],
				'activity': self.all_events[event_id]['activity']
			})

	# -------------------------

	def finalDataSave(self):

		def saveGuildsMessages():

			for guild_name in self.gmessages:
				over = len(self.gmessages[guild_name]['history']) - self.core.max_guild_stored_messages
				for i in xrange(0, over):
					self.gmessages[guild_name]['history'].pop(0)

				self.model.guilds.setGuildMessages(guild_name, self.gmessages[guild_name]['history'])

		def notableSave():
			existing_messages = self.model.misc.getNotableMessages()

			count_notable = len(self.notable_messages)
			if count_notable <= self.core.max_notable_messages:
				new_messages = existing_messages + self.notable_messages
				for i in range(0, len(existing_messages)+ count_notable - self.core.max_notable_messages):
					new_messages.pop(0)
			else:
				new_messages = []
				for i in range(0, self.core.max_notable_messages):
					new_messages.append(self.notable_messages[random.randint(0, count_notable-1)])

			getMessages(new_messages, with_time=False)
			for message in new_messages:
				if 'data' in message:
					message['time'] = message['data']['time']
					del message['data']

			self.model.misc.saveNotableMessages(new_messages)

		def updateGuilds():
			for guild_name in self.guilds_updates:
				self.model.guilds.rawUpdateGuild(guild_name,
					{'$inc':{'pvp_score': self.guilds_updates[guild_name]['pvp_score']}}
				)

		saveGuildsMessages()
		notableSave()
		updateGuilds()

		# remove 2 weeks old finished events
		self.mongo.remove('events', {'finish_date': {'$lte': time.time() - self.core.FINISHED_EVENTS_LIFETIME}})

	def getGameObjects(self):

		def getMonstersByClass():

			def getDungeonByID(id):
				for dungeon in self.dungeons:
					if dungeon['UID'] == id:
						return dungeon

				for dungeon in self.raids:
					if dungeon['UID'] == id:
						return dungeon

			buff = self.model.misc.getMonsters()

			self.monsters = []

			for monster in buff:
				if monster['area']['area_normal']:
					self.monsters.append(monster)
				if monster['area']['area_dungeon']:
					if monster['boss']:
						monster_type = 'bosses'
					else:
						monster_type = 'monsters'

					getDungeonByID(monster['dungeon'])[monster_type].append(monster)

		def getDungeons():
			all_dungeons = self.model.misc.getDungeons()

			self.dungeons = []
			self._hash_dungeons = {}
			self.raids = []

			for dungeon in all_dungeons:
				dungeon.update({'bosses': [], 'monsters': []})
				if not dungeon['type']:
					self.dungeons.append(dungeon)
					self._hash_dungeons.update({dungeon['hashtag'].upper(): dungeon})
				else:
					self.raids.append(dungeon)

		def getAchvs():
			buff = self.mongo.getu('achievements_static', fields={'UID':1, 'name':1})
			achvs = {}
			for achv in buff:
				achvs.update({str(achv['UID']): achv['name']})

			return achvs

		def getLocationsMatrix():

			def getStrCoords(position):
				return str(position['x']), str(position['y'])

			location_matrix = {}
			location_tags = {}
			all_locations = self.model.misc.getLocations() + self.model.misc.getDungeons()

			for location in all_locations:
				str_x, str_y = getStrCoords(location['position'])
				record = {
				'name': location['name'],
				'type': location['type'],
				'UID': location['UID'],
				}

				location_tags.update({
				location['hashtag']: {
				'position': location['position'],
				'name': location['name'],
				'type': location['type'],
				'UID': location['UID']
				}
				})

				if str_x in location_matrix:
					if str_y in location_matrix[str_x]:
						location_matrix[str_x][str_y].append(record)
					else:
						location_matrix[str_x].update({str_y: [record]})
				else:
					location_matrix.update({str_x: {str_y: [record]}})

			self.location_matrix = location_matrix
			self.location_tags = location_tags

		def getParsedEvents():

			def getPlayerByID(players, _id):
				for player in players:
					if player['_id'] == _id:
						return player['name']

			buff_events = self.model.events.getEvents({'only_active': True})
			events = {}
			for event in buff_events:
				events.update({
				str(event['_id']): event
				})

			return events

		def getQuestsData():
			buff_quests = self.mongo.getu('quests')
			self.quests = []
			for quest in buff_quests:
				if quest['type'] == 1:
					found = False
					for dungeon in self.dungeons:
						if dungeon['UID'] == quest['dungeon_UID']:
							found = True
							quest.update({'dungeon': dungeon})

					if not found:
						for dungeon in self.raids:
							if dungeon['UID'] == quest['dungeon_UID']:
								found = True
								quest.update({'dungeon': dungeon})

				self.quests.append(quest)

		def getFasterStructures():

			if self.DEBUG:
				debug_limits = 100
			else:
				debug_limits = 0

			players = self.mongo.getu('players', fields = {'name':1, '_id':0})
			self._fast_all_players = Set()

			for player in players:
				self._fast_all_players.add(player['name'].upper())

			spellbooks = self.model.spells.getALLSpellbooks(debug_limits)

			self._fast_spellbooks = {}

			for spellbook in spellbooks:
				self._fast_spellbooks.update({str(spellbook['player_id']): spellbook})

			spells_created = self.model.spells.getALLSpellsCreated(debug_limits)
			spells = self.model.spells.getALLSpells(debug_limits)

			self._fast_spells_created = {}
			for spell in spells_created:
				self._fast_spells_created.update({str(spell['_id']): spell})

			self._fast_spells = {}
			for spell in spells:
				self._fast_spells.update({str(spell['UID']): spell})

		def getNewMechanics():
			_buff = self.mongo.find('actions',{} ,{'_id': 0})

			self.actions = {}

			for _id in _buff:
				key = str(_buff[_id]['tweet_data']['mention'])+str(_buff[_id]['tweet_data']['rt'])+str(_buff[_id]['tweet_data']['hashtag'])+'#'
				key += str(_buff[_id]['player']['pvp'])+'#'
				key += str(_buff[_id]['target']['np'])+str(_buff[_id]['target']['enemy'])+str(_buff[_id]['target']['friend'])

				self.actions.update({
					key: _buff[_id]['actions']
				})

		def getMessages():

			self.messages = {}
			self.p_messages = {}

			all_messages = self.model.misc.getMessages()
			for message in all_messages:
				str_type_id = str(message['type'])
				str_id = str(message['UID'])

				if not str_type_id in self.p_messages:
					self.p_messages.update({str_type_id: []})

				self.messages.update({str_id: message})

				self.p_messages[str_type_id] += [str(message['UID'])]*message['p']

		getNewMechanics()

		self.RE_SPELLS = {}

		self.all_events = getParsedEvents()

		self.map = self.core.getMap()

		getMessages()

		getDungeons()
		getMonstersByClass()

		getLocationsMatrix()

		getQuestsData()

		pvp_rewards = self.mongo.getu('pvp_rewards')
		self.pvp_rewards = {}
		for record in pvp_rewards:
			self.pvp_rewards.update({str(record['lvl']): record['exp']})

		self.pool_items = self.mongo.getu('items_pool')


		self.stats = statistics.statistics()
		self.achvs = achv.achievements()
		self.static_achvs = getAchvs()

		self.guilds = self.model.guilds.getGuilds()
		self.guilds_updates = {}
		self.gmessages = {}

		self.lvls = self.mongo.find('lvls', fields = {'_id':0})

		self.items = [[],[],[],[]]
		for i in [0,2,3]:
			self.items[i] = self.mongo.getu('items', {'color': i,'holidays': 0})

		getFasterStructures()

	def isParam(self, param):
		return param in self.tweet_vars and self.tweet_vars[param]

	def getExceptionText(self, e):
		text = str(e)
		line = ''
		for i in range(0, len(text)+12):
			line += '-'

		print line
		print '|    ', text, '    |'
		print line

	def getRecordsByLvl(self,records,lvl, search = {}):
		output = []
		for record in records:
			if (record['lvl_min']<=lvl)and(record['lvl_max']>=lvl):
				if search != {} and search.keys()[0] in record and search[search.keys()[0]] == record[search.keys()[0]] or not search:
					output.append(record)

		return output

	def getRecordsBetweenLvls(self, records, lvl_min, lvl_max):
		output = []
		for record in records:
			if lvl_min <= record['lvl_min'] <= lvl_max or lvl_min <= record['lvl_max'] <= lvl_max or lvl_min > record['lvl_min'] and lvl_max < record['lvl_max']:
				output.append(record)

		return output

	def getRandomRecord(self, records):
		result = records[random.randint(0,len(records)-1)]
		return result

	def getRandomRecordPop(self, records):
		n = random.randint(0,len(records)-1)
		result = records[n].copy()
		del records[n]

		return result

	def countMetrics(self):
		if self.isParam('is_monster_kill'):
			if not 'monster_kill' in self.metrics:
				self.metrics.update({'monster_kill': 0 })

			self.metrics['monster_kill'] += 1

	# --------------------------------------------------------------------------------------

	def addInteraction(self, from_id, from_name, to_id, to_name, action, result, data = False):

		record = {
			'from': {
				'id': from_id,
			    'name': from_name
			},
			'to': {
				'id': to_id,
			    'name': to_name
			},
		    'result': result,
			'action': action
		}

		if data:
			record.update(data)

		self.interactions.append(record)

	# --------------------------------------------------------------------------------------
	# Notifications

	def getNotifications(self):

		if 'post_to_twitter' in self.player and self.player['post_to_twitter']:
			if self.isParam('achvs'):
				for achv in self.tweet_vars['achvs']:
					self.notifications.append({
					'type': 'achv',
					'data': achv['achv_name'],
					})

			if self.isParam('new_lvl'):
				self.notifications.append({
				'type': 'lvl',
				'data': self.tweet_vars['new_lvl'],
				})

	# --------------------------------------------------------------------------------------

	def countRatingsMetrics(self):

		def updateRatingMetric(param, field_name, add = 1):
			if self.isParam(param):
				if not field_name in self.ratings_metrics:
					self.ratings_metrics.update({field_name: 0 })

				self.ratings_metrics[field_name] += add

		if self.isParam('exp_gain'):
			updateRatingMetric('exp_gain', 'exp', self.tweet_vars['exp_gain'])

	def _getPlayerItems(self, player_id = None):
		if not player_id:
			player_id = self.player['_id']


		all_items = self.model.items.getPlayerBuyedItems(player_id,  {
			'bonus': 1,
			'type':1,
			'cost': 1,
			'name': 1,
			'UID': 1,
			'color': 1,
			'_id':1,
			'equipped':1
		} )

		equipped = []
		inventory = []
		for item in all_items:

			if 'equipped' in item:
				if item['equipped']:
					equipped.append(item)
				else:
					inventory.append(item)

		self.player_items = equipped
		self.inventory_items = inventory

	def _getPlayerEquippedItems(self, player_id = None, fields = 'parser'):
		if not player_id:
			player_id = self.player['_id']

		return self.model.items.getEquippedItems(player_id, fields_filter=fields)

	def changePlayer(self, user_id, restore_health = False):

		def getSpells():

			str_player_id = str(self.player['_id'])
			if str_player_id in self._fast_spellbooks:
				spellbook_spells = self._fast_spellbooks[str_player_id]['spells']
			else:
				spellbook_spells = False

			if spellbook_spells:
				spellbook_ids = []
				spellbook_str_ids = Set()
				for spell in spellbook_spells:
					spellbook_ids.append(spell['spell_id'])
					spellbook_str_ids.add(str(spell['spell_id']))

				founded = []
				spellbook = []
				for str_spell_id in spellbook_str_ids:
					if str_spell_id in self._fast_spells:
						spellbook.append(self._fast_spells[str_spell_id])
						founded.append(self._fast_spells[str_spell_id]['_id'])

				not_founded = set(spellbook_ids) - set(founded)


				for str_spell_id in spellbook_str_ids:
					if str_spell_id in self._fast_spells_created:
						if self._fast_spells_created[str_spell_id]['_id'] in not_founded:
							not_founded.remove(self._fast_spells_created[str_spell_id]['_id'])
							spellbook.append(self._fast_spells_created[str_spell_id])

				return spellbook

			else:
				return []

		def getProtoBuff():
			for buff in self.player['buffs']:
				if 'buff_uid' in buff and buff['buff_uid'] == 1000:
					self.player['exp_protobuff'] = True
					self.player['gold_protobuff'] = True

		self.updated_fields = set()

		try:
			self.player = self.model.players.getPlayer(int(user_id), fields='all', flags={'no_messages': True})
		except Exception:
			self.player = self.model.players.getPlayerBy_ID(user_id)

		self.metrics_stats = {}
		if not self.player:
			return False

		all_player_messages = self.model.players.getPlayerMessages(self.player['user_id'])
		if not (all_player_messages and 'last' in all_player_messages):
			return False

		self.player_messages = all_player_messages['last']

		self.player_stats = self.mongo.find('statistics', {'user_id': self.player['user_id']})
		self.player_achvs = self.mongo.find('achievements', {'user_id': self.player['user_id']})

		self._getPlayerItems()

		self.spellbook = getSpells()

		self.player_events = self.mongo.getu('events', {
				'people': {'$all':[self.player['_id']]},
				'$or': [{'status':'progress'}, {'status': 'active'}]
			},
			{
				'start_date': 1,
			    'finish_date': 1,
			    '_id': 1,
			    'type': 1,
			    'position': 1
			}
		)

		self.notifications = []

		if restore_health:
			self.player['stat']['HP']['current'] = self.player['stat']['HP']['max_dirty']
			self.player['stat']['MP']['current'] = self.player['stat']['MP']['max_dirty']
			self.updated_fields.add('stat')

		self.metrics = {'monster_kill':0}
		getProtoBuff()

		return True

	def savePlayerData(self, last_id = 0):

		def getNewMetrics():
			hour = str(time.gmtime().tm_hour)
			result = {}
			for metric_name in self.metrics.keys():
				result.update({'metrics.'+metric_name+'.'+hour : {'value':self.metrics[metric_name], 'lvl':self.player['lvl']}})

			return result

		def buffClear():

			if self.player['buffs']:
				current_time = time.time()
				new_buffs = []
				for buff in self.player['buffs']:
					if buff['start_time'] + buff['length'] > current_time:
						new_buffs.append(buff)

				if not len(new_buffs) == len(self.player['buffs']):
					self.player['buffs'] = new_buffs
					self.updated_fields.add('buffs')

		record = {}

		if not self.player:
			return False

		buffClear()

		if 'stat' in self.updated_fields:
			self.recalculateFinalPlayerStats()

		if 'statistics' in self.updated_fields:
			self.mongo.update('statistics', {'_id': self.player_stats['_id']}, {'stats': self.player_stats['stats']})

		if 'achvs' in self.updated_fields:
			self.mongo.update('achievements', {'_id': self.player_achvs['_id']}, {'achvs': self.player_achvs['achvs']})

		if 'messages' in self.updated_fields:
			over = len(self.player_messages) - self.core.max_stored_messages
			for i in xrange(0, over):
				self.player_messages.pop(0)

			self.model.players.setPlayerMessages(self.player['user_id'], self.player_messages)
			self.updated_fields.remove('messages')

		for field in self.updated_fields:
			if field in self.player:
				record.update({field:self.player[field]})

		metrics = getNewMetrics()
		if metrics:
			record.update(metrics)

		if last_id:
			record.update({'last_id': last_id})

		if self.notifications:
			self.mongo.update('notification_queue', {'player_id': self.player['_id']}, {
				'player_id': self.player['_id'],
				'name': self.player['name'],
				'token1': self.player['token1'],
				'token2': self.player['token2'],
				'notifications': self.notifications
			}, True)

		if record:
			self.mongo.update('players',{'user_id':self.player['user_id']}, record)

	def setActivity(self, activity_name):

		if not 'activity' in self.player:
			self.player.update({'activity': {}})
		elif isinstance(self.player['activity'], list):
			self.player['activity'] = dict()

		if not activity_name in self.player['activity']:
			self.player['activity'].update({activity_name: 1})
		else:
			self.player['activity'][activity_name] += 1

		self.updated_fields.add('activity')

	def recalculateFinalPlayerStats(self):

		self.player['stat'] = self.model.players.recalculateStats(
			self.player['_id'],
			items = self.player_items,
			player_stats = self.player['stat'],
			update = False
		)

	# --------------------------------------------------------------------------------------

	def composeMessage(self):

		def getMessagesByP(str_type_of_message):
			str_message_id = self.p_messages[str_type_of_message][random.randint(0, len(self.p_messages[str_type_of_message])-1)]
			return self.messages[str_message_id]

		def getMessageBody(type_of_message, additional_type = -1, pre = False):
			if type_of_message <= 0:
				return {'text':'', 'UID':-1, 'no_message': True}

			message = getMessagesByP(str(type_of_message)).copy()

			if additional_type > 0:
				if pre:
					message['message'] = str(getMessagesByP(str(additional_type))['message']) + '. ' + message['message']
				else:
					message['message'] += '. '+ str(getMessagesByP(str(additional_type))['message'])

			return {'text':message['message'], 'UID': message['UID']}

		def getMessageData():
			data = {}
			if self.isParam('is_monster'):
				data.update({
					'monster': self.tweet_vars['monster']['name'],
					'monster_UID': self.tweet_vars['monster']['UID']
				})

			if self.isParam('is_mention'):
				data.update({
					'party': self.tweet_vars['mention_player'],
					'party_UID': self.tweet_vars['mention_player_user_id'],
					'is_player': self.tweet_vars['is_mention_player']
				})

			if self.isParam('is_retweet'):
				data.update({
					'party': self.tweet_vars['retweeted_user'],
					'party_UID': self.tweet_vars['retweeted_user_id'],
					'is_player': self.tweet_vars['is_retweeted_player']
				})

			if self.isParam('from_name'):
				data.update({
					'party': self.tweet_vars['from_name'],
					'party_UID': self.tweet_vars['from_id'],
					'is_player': True
				})

			if self.isParam('dungeon'):
				data.update({
					'dungeon': self.tweet_vars['dungeon']['name'],
					'dungeon_UID': self.tweet_vars['dungeon']['UID']
				})

			if self.isParam('is_spell'):
				data.update({
					'spell': self.tweet_vars['spell']['name'],
					'spell_UID': self.tweet_vars['spell']['_id']
				})

			if self.isParam('is_event'):
				if self.tweet_vars['event_type'] == 'war':
					data.update({
						'winner_guild': self.tweet_vars['winner_guild'],
						'winner_guild_name': self.tweet_vars['winner_guild_name'],
						'looser_guild': self.tweet_vars['looser_guild'],
						'looser_guild_name': self.tweet_vars['looser_guild_name'],
						'event_id': self.tweet_vars['event']['_id']
					})

				elif self.tweet_vars['event_type'] == 'fvf':
					data.update({
						'winner_faction': self.tweet_vars['winner_faction'],
						'winner_faction_name': self.tweet_vars['winner_faction_name'],
						'looser_faction': self.tweet_vars['looser_faction'],
						'looser_faction_name': self.tweet_vars['looser_faction_name'],
						'event_id': self.tweet_vars['event']['_id']
					})

			return data

		def checkPoI():
			if self.isParam('is_poi') and not self.isParam('already_visited'):
				data = ({
					        'poi': self.tweet_vars['poi']['name'],
					        'poi_UID': self.tweet_vars['poi']['UID'],
					        'poi_type': self.tweet_vars['poi']['type'],
				        })

				message = getMessageBody(23)
				self.insertMessage(message, data)

		def checkQuests():

			if 'quest_finished' in self.tweet_vars:
				data = ({
					        'quest': self.tweet_vars['quest']['name'],
					        'quest_UID': self.tweet_vars['quest']['UID']
				        })

				if self.tweet_vars['quest_finished']:
					message_type = 25
				else:
					message_type = 26

				if 'quest_gold' in self.tweet_vars:
					self.tweet_vars['gold'] = self.tweet_vars['quest_gold']

				if 'quest_exp' in self.tweet_vars:
					self.tweet_vars['exp'] = self.tweet_vars['quest_exp']

				self.insertMessage(getMessageBody(message_type), data)

			if self.isParam('is_quest'):
				data = ({
					        'quest': self.tweet_vars['quest']['name'],
					        'quest_UID': self.tweet_vars['quest']['UID']
				        })

				if self.tweet_vars['quest']['type'] == 1:
					if 'monster' in self.tweet_vars:
						data.update({
							'monster': self.tweet_vars['quest']['dungeon']['bosses'][0]['name'],
							'monster_UID': self.tweet_vars['quest']['kill_boss_UID']
						})

					else:
						data.update({
							'monster': 'Unknown Monster',
							'monster_UID': -1
						})

				self.insertMessage(getMessageBody(24), data)

		type_of_message = -1
		additional_type = -1
		pre = False
		data = {}

		checkPoI()

		if self.isParam('action') and self.isParam('action_result'):
			data = getMessageData()

			if not self.isParam('interaction'):
				type_of_message = self.tweet_vars['action']['messages_'+self.tweet_vars['action_result']]
			else:
				type_of_message = self.tweet_vars['action']['callback_'+self.tweet_vars['action_result']]

		if self.isParam('is_self_buff'):
			pre = True
			additional_type = 16

		if self.isParam('is_spell') and not self.isParam('is_buff'):
			additional_type = 15

		message = getMessageBody(type_of_message, additional_type, pre)
		#print 'message>', type_of_message, additional_type, message

		self.insertMessage(message, data)

		checkQuests()

		if self.isParam('new_lvl'):
			self.insertMessage(getMessageBody(3), {'lvl': self.tweet_vars['new_lvl']})

		if self.isParam('achvs'):
			for achv in self.tweet_vars['achvs']:
				data = ({
				        'achv': achv['achv_name'],
				        'achv_UID': achv['achv_UID']
				        })

				message = getMessageBody(5)
				self.insertMessage(message, data)

		if self.isParam('is_drop') and self.isParam('drop_item'):
			data = ({
			        'item': self.tweet_vars['drop_item']['name']
			        })

			if 'UID' in self.tweet_vars['drop_item']:
				data.update({'item_UID': self.tweet_vars['drop_item']['UID']})
			else:
				data.update({'item_id': self.tweet_vars['drop_item']['_id']})

			message = getMessageBody(9)
			self.insertMessage(message, data)


		if self.isParam('dropout_item'):
			data = ({
			        'item': self.tweet_vars['dropout_item']['name']
			        })

			if 'UID' in self.tweet_vars['dropout_item']:
				data.update({'item_UID': self.tweet_vars['dropout_item']['UID']})
			else:
				data.update({'item_id': self.tweet_vars['dropout_item']['_id']})

			message = getMessageBody(22)
			self.insertMessage(message, data)

		elif self.isParam('sell_item'):
			data = ({
				        'item': self.tweet_vars['sell_item']['name'],
				        'gold': self.tweet_vars['sell_item']['cost'],
			        })

			if 'UID' in self.tweet_vars['sell_item']:
				data.update({'item_UID': self.tweet_vars['sell_item']['UID']})
			else:
				data.update({'item_id': self.tweet_vars['sell_item']['_id']})

			message = getMessageBody(10)
			self.insertMessage(message, data)

	def insertMessage(self, message, data = {}):

		def insertGuildMessage(guild, record):
			try:
				pass
			except Exception:
				pass

			if not guild in self.gmessages:
				self.gmessages.update({guild: self.model.guilds.getGuildMessages(guild)})
			self.gmessages[guild]['history'].append(record)

		if 'no_message' in message or message['text'] == "0":
			return False

		data.update({
			'player':self.tweet_vars['player'],
			'time': time.time(),
			'message_UID': message['UID']
		})

		if self.isParam('gold') and not 'gold' in data:
			data.update({'gold': self.tweet_vars['gold']})
			del self.tweet_vars['gold']

		if self.isParam('pvp_score') and not 'pvp_score' in data:
			data.update({'pvp_score': self.tweet_vars['pvp_score']})
			del self.tweet_vars['pvp_score']

		if self.isParam('exp') and not 'exp' in data:
			data.update({'exp': self.tweet_vars['exp']})
			del self.tweet_vars['exp']

		record = {'message': message['text'], 'data': data}

		self.player_messages.append(record)
		self.updated_fields.add('messages')

		if 'notable' in data or 'meganotable' in data:
			if 'notable' in data:
				self.notable_messages.append(record)
			else:
				self.meganotable_messages.append(record)

			if len(self.player['_guild_name']):
				insertGuildMessage(self.player['_guild_name'], record)

	# --------------------------------------------------------------------------------------

	def isMention(self, tweet):
		self.tweet_vars['is_mention'] = False

		if 'user_mentions' in tweet.entities and tweet.entities['user_mentions']:
			self.tweet_vars['is_mention']  = True

			name = tweet.entities['user_mentions'][0]['screen_name']
			self.tweet_vars['mention_player'] = name
			self.tweet_vars['mention_player_user_id'] = tweet.entities['user_mentions'][0]['id']

			if name == self.player['name']:
				self.tweet_vars.update({
					'is_mention_self': True,
					'is_mention': False,
					'is_self_target': True
				})
			else:

				if name.upper() in self._fast_all_players:
					self.tweet_vars.update({
						'is_mention_player': True,
						'_to': {
							'user_id': self.tweet_vars['mention_player_user_id'],
						    'name': name
						}
					})

				if not 'is_mention_player' in self.tweet_vars:
					self.tweet_vars.update({'is_mention_player': False})

	def isHashtag(self, tweet):
		self.tweet_vars['is_hashtag'] = False

		if 'hashtags' in tweet.entities and tweet.entities['hashtags']:
			self.tweet_vars['is_hashtag'] = True
			hashtags = []
			for hashtag in tweet.entities['hashtags']:
				hashtags.append(hashtag['text'])

			self.tweet_vars['hashtags'] = hashtags

			for hashtag in hashtags:
				if hashtag in self.location_tags:
					self.tweet_vars['is_move_order'] = True
					self.tweet_vars['move_order'] = self.location_tags[hashtag]
					break

			if not self.isParam('is_move_order'):
				if not ('direction' in self.player and self.player['direction']):
					dungeon = self.getRandomDungeon()
					self.tweet_vars['is_move_order'] = True
					self.tweet_vars['move_order'] = self.location_tags[dungeon['hashtag']]

	def isRetweet(self, tweet):

		try:
			self.tweet_vars.update({'retweeted_user': tweet.retweeted_status.user.screen_name})
			is_retweet = True
		except Exception, e:
			is_retweet = False

		if is_retweet:
			self.tweet_vars['retweeted_user_id'] = tweet.retweeted_status.user.id

			if self.tweet_vars['retweeted_user'].upper() in self._fast_all_players:
				self.tweet_vars.update({
					'is_retweeted_player': True,
					'_to': {
						'user_id': self.tweet_vars['retweeted_user_id'],
						'name': tweet.retweeted_status.user.screen_name
					}
				})

			if not 'is_retweeted_player' in self.tweet_vars:
				self.tweet_vars.update({'is_retweeted_player': False})

		self.tweet_vars.update({'is_retweet': is_retweet, 'user_tweet': not is_retweet})

	def isSpell(self, tweet):

		def canSelfCast(spell = False):
			result = True
			if spell:
				if 'spell_actions' in spell:
					for action in spell['spell_actions']:
						if action['type'] != 1:
							result = False
							break

			return result

		found = False

		for spell in self.spellbook:

			if spell['keyword'] in self.RE_SPELLS:
				regexp = self.RE_SPELLS[spell['keyword']]
			else:
				regexp = re.compile(spell['keyword']+'(\t|\s|$)' , re.IGNORECASE+ re.UNICODE)
				self.RE_SPELLS.update({spell['keyword']: regexp})

			results = re.search(regexp, tweet.text)
			if results:

				if not self.isParam('is_mention') and canSelfCast(spell):
					self.tweet_vars.update({'is_self_target': True})

				if not found:
					self.tweet_vars.update({'spell': spell})
					found = True
				else:
					self.setActivity('spell')

				break

		self.tweet_vars.update({'is_spell': found})

	def isGroupEvent(self, tweet):

		def getTweetInfo():
			keys = ['is_spell']
			record = {'player_id': self.player['_id'], 'player_name': self.player['name'], 'player_lvl': self.player['lvl']}
			for key in keys:
				record[key] = self.tweet_vars[key]

			return record

		result = {'is_group_event': False}

		if self.player_events:
			for event in self.player_events:
				if event['start_date'] <= time.mktime(tweet.created_at.timetuple()) < event['finish_date']:

					in_area = True

					if in_area:
						try:
							event_str_id = str(event['_id'])
							activity = getTweetInfo()
							self.all_events[event_str_id]['activity'].append(activity)
							self.updated_events.add(event_str_id)
							result.update({'is_group_event': True, 'group_event': event_str_id})
						except Exception:
							pass

		self.tweet_vars.update(result)

	# --------------------------------------------------------------------------------------

	def checkDrop(self, is_dungeon = False, is_raid = False):

		def getItem(is_dungeon):

			def _getFixedItemDrop(uid):
				return self.model.items.getFixedItem(uid)

			if self.core.debug['always_drop']:
				is_drop = True
			elif is_dungeon:
				is_drop = self.balance.checkDungeonDrop()
			else:
				is_drop = self.balance.checkNormalDrop()

			item = False

			#if False:
			#	item = _getFixedItemDrop(34)
			#	is_drop = True

			if is_drop and not item:
				item_type = 0
				if is_raid:
					if self.balance.checkEpicDrop():
						item_type = 3
					elif self.balance.checkRareDrop():
						item_type = 2

				is_pool = self.balance.checkPoolDrop()

				if is_pool:
					item = False
					available = self.getRecordsByLvl(self.pool_items, self.player['lvl'])

					if available:
						item = self.getRandomRecordPop(available)
						if item:
							self.mongo.remove('items_pool', {'_id': item['_id']})

				if not is_pool or is_pool and not item:
					available = self.getRecordsByLvl(self.items[item_type], self.player['lvl'])
					if available:
						item = self.getRandomRecord(available)

			self.tweet_vars.update({'is_drop': is_drop, 'drop_item': item})
			return item

		def getPlayersItemByType(item_type):
			items = []

			for record in self.player_items:
				if record['type'] == item_type:
					items.append(record)

			if len(items)>0:
				if item_type == 6 and len(items) == 1:
					items.append([])
				return items
			else:
				return [False]

		def getCurrentItemForComparsion(item_type):
			player_items = getPlayersItemByType(item_type)

			if item_type != 6:
				player_item = player_items[0]
			else:
				if not player_items[0] or not player_items[1]:
					player_item = False
				else:
					if self.balance.isNewItemBetter(player_items[0]['bonus'],player_items[1]['bonus'],self.player['class']):
						player_item = player_items[0]
					else:
						player_item = player_items[1]

			return player_item

		def sellItem(item, which_item):
			if which_item == 'old':
				self.tweet_vars.update({'sell_item': item})
				self.model.items.autoSell(item['_id'])
			else:
				self.tweet_vars.update({'sell_item': item.data})

			self.getGold(self.tweet_vars['sell_item']['cost'], silence=True)

		def dropOutItem(item):
			if isinstance(item, dict):
				self.tweet_vars.update({'dropout_item': item})
			else:
				self.tweet_vars.update({'dropout_item': item.data})

		def equipItem(item):
			item.data.update({'player_id': self.player['_id'], 'equipped': True})
			self.model.items.lootItem(item.data)
			self._getPlayerEquippedItems()

		def pickupItem(item):
			item.data.update({'player_id': self.player['_id'], 'equipped': False})
			self.model.items.lootItem(item.data)

		blank_item = None
		blank_item = getItem(is_dungeon)

		if blank_item:
			new_item = self.model.game_item({})
			for field in blank_item:
				new_item.data.update({field: blank_item[field]})

			equipped = False

			current_item = getCurrentItemForComparsion(new_item.data['type'])

			if not current_item:
				item_usable = (new_item.data['type'] == 1) and (self.balance.isItemForClass(new_item.data, self.player['class'])) or new_item.data['type'] != 1
				if item_usable:
					equipItem(new_item)
					equipped = True

			if not equipped:
				if len(self.inventory_items) < self.balance.INVENTORY_SIZE:
					pickupItem(new_item)
				else:

					old_item = None
					min_cost = -1

					for item in self.inventory_items:
						if min_cost < 0 or item['cost'] < min_cost:
							old_item = item
							min_cost = item['cost']

					if min_cost > new_item.data['cost']:
						dropOutItem(new_item)
					else:
						self.model.items.autoSell(old_item['_id'])
						dropOutItem(old_item)
						pickupItem(new_item)

			del blank_item

			self._getPlayerItems()

	def getGold(self, gold, silence = False, name = ''):

		if 'gold_protobuff' in self.player and self.player['gold_protobuff']:
			gold *= 2

		self.player['resources']['gold'] += gold
		if not silence:
			self.tweet_vars[name+'gold'] = gold
		self.updated_fields.add('resources')

	def getPVPScore(self, score, silence = False, not_guild = False):
		self.player['pvp_score'] += score
		if not silence:
			self.tweet_vars['pvp_score'] = score

		self.updated_fields.add('pvp_score')

		if not not_guild:
			if self.player['_guild_name'] in self.guilds_updates:
				self.guilds_updates[self.player['_guild_name']]['pvp_score'] += score
			else:
				self.guilds_updates.update({self.player['_guild_name']:{'pvp_score': score}})

	def getExp(self, exp, buff = False, name = ''):

		def levelUp():
			for stat in self.balance.classes_stats[str(self.player['class'])]:
				value = self.balance.classes_stats[str(self.player['class'])][stat]
				self.player['stat'][stat].update({
				'current': self.player['stat'][stat]['current'] + value,
				'max': self.player['stat'][stat]['max'] + value,
				'max_dirty': self.player['stat'][stat]['max_dirty'] + value })

			self.updated_fields.add('stat')

			self.player['lvl'] += 1
			self.updated_fields.add('lvl')

		if '2x_rate' in self.core.debug and self.core.debug['2x_rate']:
			exp *= 2

		if 'exp_protobuff' in self.player and self.player['exp_protobuff']:
			exp *= 2

		new_lvl = False

		if self.player['lvl'] >= self.balance.max_lvl:
			return False

		self.player['exp'] += exp

		if self.lvls[str(self.player['lvl']+1)] <= self.player['exp']:
			self.player['exp'] -= self.lvls[str(self.player['lvl']+1)]
			new_lvl = True

		if new_lvl:
			levelUp()
			self.tweet_vars['new_lvl'] = self.player['lvl']

		self.tweet_vars[name+'exp'] = exp
		self.updated_fields.add('exp')

	def getResources(self):

		situation = 'none'

		if self.isParam('is_event') and self.isParam('is_complete'):
			situation = 'raid'

		elif self.isParam('is_monster_kill'):
			if self.isParam('is_boss'):
				situation = 'boss'
			else:
				situation = 'monster'

		elif self.isParam('is_pvp_kill'):
			situation = 'pvp'

		result = self.balance.getResDropChances(situation)

		got_any = False
		for res_name in result:
			if result[res_name]:
				self.tweet_vars['res_'+res_name+'_got'] = True
				self.player['resources'][res_name] += 1
				got_any = True

		if got_any:
			self.updated_fields.add('resources')

	def getRandomDungeon(self):
		dungeons = self.getRecordsByLvl(self.dungeons, self.player['lvl'])
		if dungeons:
			current_dungeon = self.getRandomRecord(dungeons)
			self.tweet_vars['dungeon'] = current_dungeon
			return current_dungeon
		else:
			return False

	def getDungeon(self):
		if self.isParam('is_hashtag'):
			hashtags = self.tweet_vars['hashtags']

			if hashtags:
				for hashtag in hashtags:
					hashtag = hashtag.upper()
					if hashtag in self._hash_dungeons:
						current_dungeon = self._hash_dungeons[hashtag]
						self.tweet_vars['dungeon'] = current_dungeon
						return current_dungeon

			return self.getRandomDungeon()

		else:
			return False

	def getRaidByUID(self, UID):
		for dungeon in self.raids:
			if dungeon['UID'] == UID:
				return dungeon

	def getRandomMonster(self, dungeon_UID = False, must_be_boss = False):

		if dungeon_UID:
			current_dungeon = self.getRaidByUID(dungeon_UID)

		if dungeon_UID and current_dungeon:
			self.tweet_vars['is_boss'] = must_be_boss

			if must_be_boss:
				available_records = current_dungeon['bosses']
			else:
				available_records = current_dungeon['monsters']

		else:
			x = self.player['position']['x']
			y = self.player['position']['y']

			geo_monsters = {'lvl_min': 1, 'lvl_max': 60}
			for coords in self.balance.GEO_MONSTERS:
				if x >= coords['x1'] and y >= coords['y1'] and x <= coords['x2'] and y <= coords['y2']:
					geo_monsters = coords

			available_records = self.getRecordsBetweenLvls(self.monsters, geo_monsters['lvl_min'], geo_monsters['lvl_max'])

		if not available_records:
			is_monster = False
		else:
			is_monster = True
			monster = self.getRandomRecord(available_records)
			self.tweet_vars['monster'] = monster

		self.tweet_vars['is_monster'] = is_monster

		return monster

	# --------------------------------------------------------------------------------------

	def getTargetInfo(self):

		def getEnemyInfo(field):
			return self.model.players.getPlayerRaw(self.tweet_vars[field], {
				'_guild_name': 1,
				'faction':1,
				'pvp':1
			})

		# return [is_non_player, is_pvp_enemy, is_friend]

		if self.isParam('is_self_target'):
			return [False, False, False]

		if self.isParam('mention_player_user_id'):

			if not self.isParam('is_mention_player'):
				return [True, False, False]

			enemy_info = getEnemyInfo('mention_player_user_id')

			if enemy_info:

				is_friend = enemy_info['_guild_name'] == self.player['_guild_name']

				if self.isParam('hashtags') and self.balance.PVP_FORCE in self.tweet_vars['hashtags']:
					if is_friend:
						self.tweet_vars['pvp_forced'] = True

					is_friend = False

				self.tweet_vars['is_friend_target'] = is_friend

				if is_friend:
					is_pvp = False
				else:
					is_pvp = enemy_info['pvp'] == 1

				return [False, is_pvp, is_friend]

			else:
				return [True, False, False]

		if self.isParam('is_retweet'):

			if self.isParam('is_retweeted_player'):
				enemy_info = getEnemyInfo('retweeted_user_id')

				if enemy_info:
					is_pvp = enemy_info['pvp'] == 1 and self.player['pvp'] == 1
					is_friend = not is_pvp

					return [False, is_pvp, is_friend]

				else:
					return [True, False, False]

			return [True, False, False]

		return [False, False, False]

	def setResult(self, result):
		if result:
			res = 'OK'
		else:
			res = 'FAIL'

		self.tweet_vars['action_result'] = res

	def processGameMechanic2(self):

		def getTweetHashKey(v, target):
			key = str(v['is_mention'])+str(v['is_retweet'])+str(v['is_hashtag'])+'#'
			key += str(self.player['pvp'] == 1)+'#'
			key += str(target[0])+str(target[1])+str(target[2])

			return key

		def getActionFromChances(actions):

			if len(actions) == 1:
				return actions[0]

			p = []
			i = 0

			for action in actions:
				p += [i]*action['p']
				i += 1

			return actions[p[random.randint(0, len(p)-1)]]

		def getMagic(target_info):
			target_spell_effects = {}

			if 'spell' in self.tweet_vars:
				mana_cost = self.tweet_vars['spell']['mana_cost']
				player_mana = self.player['stat']['MP']['current']

				target_spell_effects = {}

				if mana_cost > player_mana:
					del self.tweet_vars['is_spell']
					del self.tweet_vars['spell']
					self.tweet_vars['not_enough_mana'] = True

				if self.isParam('is_spell'):
					spell_effects = self.modules['spell_casting'].spellCasting(
						tweet_vars=self.tweet_vars
					)
					target_spell_effects = spell_effects['target_fields']
					self.tweet_vars['is_buff'] = spell_effects['is_buff']

					self.player['stat']['MP']['current'] -= mana_cost
					self.updated_fields.add('stat')

					if self.isParam('is_self_target'):
						self.actionBuffSomebody(spell_effects['target_fields'])
						self.tweet_vars.update({'is_self_buff': True})

					if target_info[2]:
						self.actionBuffSomebody(target_spell_effects, self.tweet_vars['mention_player'])

			return target_spell_effects

		self.getDirectionToLocation()

		target_info = self.getTargetInfo()
		key = getTweetHashKey(self.tweet_vars, target_info)

		if key in self.actions:
			action = getActionFromChances(self.actions[key])
			action_name = action['name']
			self.tweet_vars.update({'action': action})
		else:
			action_name = False

		target_spell_effects = getMagic(target_info)

		# ACTIONS
		if action_name in [
			'go_to_dungeon',
		    'peasant_help_dungeon',
		    'go_to_dungeon_assisted',
		    'peasant_kill_go_to_dungeon',
		    'player_fight_go_to_dungeon'
		]:
			dungeon = self.getDungeon()

		if action_name == 'monster_fight':
			self.actionMonsterFight(spell_effects=target_spell_effects)
			self.setResult(self.tweet_vars['is_monster_kill'])

		elif action_name == 'player_fight':
			target = self.tweet_vars['mention_player'] if self.isParam('is_mention') else False
			self.actionPlayerFight(target=target, spell_effects=target_spell_effects)

			if self.isParam('is_pvp_kill'):
				self.setResult(self.tweet_vars['is_pvp_kill'])
			else:
				self.actionMonsterFight(spell_effects=target_spell_effects)
				self.setResult(self.tweet_vars['is_monster_kill'])

		elif action_name == 'monster_assisted':
			self.actionMonsterFight(party=True, spell_effects=target_spell_effects)
			self.setResult(self.tweet_vars['is_monster_kill'])

		elif action_name == 'go_to_dungeon':
			self.actionMonsterFight(dungeon_UID=dungeon['UID'], spell_effects=target_spell_effects)
			self.setResult(self.tweet_vars['is_monster_kill'])

		elif action_name == 'peasant_kill':
			self.actionPeasantFight()
			self.setResult(True)

		elif action_name == 'peasant_assist':
			self.actionMonsterFight(spell_effects=target_spell_effects)
			self.setResult(self.tweet_vars['is_monster_kill'])

		elif action_name == 'peasant_help_dungeon':
			self.actionMonsterFight(dungeon_UID=dungeon['UID'], spell_effects=target_spell_effects)
			self.setResult(self.tweet_vars['is_monster_kill'])

		elif action_name == 'go_to_dungeon_assisted':
			self.actionMonsterFight(party=True, dungeon_UID=dungeon['UID'], spell_effects=target_spell_effects)
			self.setResult(self.tweet_vars['is_monster_kill'])

		elif action_name == 'peasant_kill_go_to_dungeon':
			self.actionMonsterFight(dungeon_UID=dungeon['UID'], spell_effects=target_spell_effects)
			self.setResult(self.tweet_vars['is_monster_kill'])

		elif action_name == 'peasant_meet':
			self.actionMeet(0)
			self.setResult(self.tweet_vars['is_meet_success'])

		elif action_name == 'players_meet':
			self.actionMeet(1)
			self.setResult(self.tweet_vars['is_meet_success'])

		elif action_name == 'pvp_players_meet':
			self.actionMeet(2)
			self.setResult(self.tweet_vars['is_meet_success'])

		if action_name and action['trigger'] == 'interaction':

			rewards = {}
			if action_name in ['monster_assisted', 'go_to_dungeon_assisted', 'players_meet']:
				if self.isParam('gold'):
					rewards['gold'] = self.tweet_vars['gold'] / 2

				if self.isParam('exp'):
					rewards['exp'] = self.tweet_vars['exp'] / 2

			data = {
				'mention_player': self.player['name'],
				'mention_player_user_id': self.player['user_id'],
				'is_mention_player': True,
			    'is_mention': True,
			    'rewards': rewards
			}

			if self.isParam('monster'):
				data.update({
					'monster': self.tweet_vars['monster'],
				    'is_monster': True
				})
			try:
				self.addInteraction(
				    self.player['user_id'],
				    self.player['name'],
				    self.tweet_vars['_to']['user_id'],
				    self.tweet_vars['_to']['name'],
				    action,
				    bool(self.tweet_vars['action_result'] == 'OK'),
				    data
			    )
			except Exception:
				pass

		self.postCheck()
		self.getResources()

	def processInteractionMechanic(self):
		self.setResult(self.tweet_vars['result'])

		if 'gold' in self.tweet_vars['rewards']:
			self.getGold(self.tweet_vars['rewards']['gold'])

		if 'exp' in self.tweet_vars['rewards']:
			self.getExp(self.tweet_vars['rewards']['exp'] / 2)

		if self.tweet_vars['action']['name'] == 'player_fight' and not self.tweet_vars['result']:
			self._getPVPRewards()

	def processGeoMechanic(self):
		if not self.isParam('is_poi'):
			return False

		is_dungeon = self.tweet_vars['poi']['type'] == 0
		is_raid = self.tweet_vars['poi']['type'] == 1
		is_location = self.tweet_vars['poi']['type'] == 2

		if is_dungeon:
			target_dungeon = False
			for dungeon in self.dungeons:
				if dungeon['UID'] == self.tweet_vars['poi']['UID']:
					target_dungeon_id = dungeon['UID']
					break

			if target_dungeon:
				monster = self.getRandomMonster(
					dungeon_UID = target_dungeon_id,
					must_be_boss = True
				)

				if monster:
					is_monster = True
					self.tweet_vars['monster'] = monster

					self.actionRandomMonsterKill(
						dungeon=True,
						monster=monster
					)

				else:
					is_monster = False

				self.tweet_vars['is_monster'] = is_monster

	def processGroupEventMechanic(self):

		if self.tweet_vars['event_type'] == 'raid':
			self.actionGetRaidRewards()

		elif self.tweet_vars['event_type'] == 'war':
			self.actionGetGvGRewards()

		elif self.tweet_vars['event_type'] == 'fvf':
			self.actionGetFvFRewards()

		self.player['direction'] = self.getAutoNewForceDirection()
		self.updated_fields.add('direction')

	def postCheck(self):
		if self.isParam('mention_player') and self.tweet_vars['mention_player'] == self.player['name']:
			self.tweet_vars['is_mention'] = False
			del self.tweet_vars['mention_player']

		if self.player['pvp'] and not self.isParam('pvp_ignored') and not self.isParam('is_mention'):
			self.tweet_vars['pvp_ignored'] = True

	# --------------------------------------------------------------------------------------
	# Action Level

	def _setStatsAfterFight(self, fight_result):
		if fight_result['side_1']:
			for stat in fight_result['side_1'][0]:
				if int(fight_result['side_1'][0][stat]) != -1:
					self.player['stat'][stat]['current'] -= int(fight_result['side_1'][0][stat])
					if self.player['stat'][stat]['current'] <= 0:
						self.player['stat'][stat]['current'] = 1
				else:
					self.player['stat'][stat]['current'] = -int(fight_result['side_1'][0][stat])

			self.updated_fields.add('stat')

	def actionMonsterFight(self, dungeon_UID = False, party = False, spell_effects = False, monster = False):

		def getMonsterStat(monster, spell_effects):

			if spell_effects:
				for effect_name in spell_effects:
					if effect_name in monster['stat']:
						monster['stat'][effect_name] -= spell_effects[effect_name]
					else:
						if effect_name == 'DMG_DONE':
							monster['stat']['HP'] -= spell_effects[effect_name]

			return monster['stat']

		monster = self.getRandomMonster(dungeon_UID)

		if monster:
			self.tweet_vars['monster'] = monster

			sides = {
				'side_1': [{ 'type': 'player', 'obj': self.model.players.getCurrentStats(self.player['stat'])}],
				'side_2': [{ 'type': 'monster', 'obj': getMonsterStat(monster, spell_effects) }]
			}

			if party and self.player['stat']['HP']['current'] > 2:
				if self.isParam('is_mention_player'):
					party_info = self.model.players.getStatsByUserID(self.tweet_vars['mention_player_user_id'])
					sides['side_1'].append({ 'type': 'player', 'obj': self.model.players.getCurrentStats(party_info['stat'])})
					reward_koeff = float(self.player['lvl'])/(party_info['lvl']+self.player['lvl'])
				else:
					reward_koeff = 0.7
			else:
				reward_koeff = 1

			diff_level = monster['lvl_min'] - self.player['lvl']
			is_penalty = False
			afraid_chance = 0
			if diff_level > 0:
				if diff_level >= self.balance.DIFF_MONSTER_LVL:
					is_penalty = True
					if diff_level >= self.balance.DIFF_MONSTER_LVL_100:
						afraid_chance = 100
					else:
						afraid_chance = self.balance.CHANCE_TO_AFRAID

			self.player['is_penalty'] = is_penalty

			fight_result = self.modules['fight'].fightBetweenPlayerAndMonster(
				sides,
				penalty = is_penalty,
				afraid_chance = afraid_chance
			)

			monster_kill = fight_result['winner'] == 'side_1'
			self.tweet_vars['is_monster_kill'] = monster_kill
			if monster_kill:
				self._getRewards(monster, bool(dungeon_UID), reward_koeff)

			self._setStatsAfterFight(fight_result)

	def actionPlayerFight(self, target = False, spell_effects = False):

		def getPlayerInfoForBattle(player):
			player_items = self._getPlayerEquippedItems(player['_id'], fields='bonus')

			stats = self.model.players.getCurrentStats(player['stat'])

			if player_items:
				for item in player_items:
					for stat_name in item['bonus']:
						if item['bonus'][stat_name]:
							stats[stat_name] += item['bonus'][stat_name]

			return stats

		def getSpellEffects(stats, spell_effects):
			for effect_name in spell_effects:
				try:
					if effect_name in stats:
						stats -= spell_effects[effect_name]
					else:
						if effect_name == 'DMG_DONE':
							stats['HP'] -= spell_effects[effect_name]
				except Exception:
					pass

			return stats

		def getNearTarget():
			near_players = self.model.players.getNearPlayers(
				self.player['position']['x'],
				self.player['position']['y'],
				pvp = 1,
				lvl = self.player['lvl'],
				name = self.player['name']
			)

			if near_players:
				target_info = random.sample(near_players, 1)[0]
				target = target_info['name']
				if target != self.player['name']:
					self.tweet_vars.update({
						'is_mention': True,
						'is_mention_player': True,
						'mention_player': target_info['name'],
						'mention_player_user_id': target_info['user_id'],
						'mention_lvl': target_info['lvl'],
						'_to': {
							'user_id': target_info['user_id'],
							'name': target_info['name']
						}
					})
				else:
					target = False
			else:
				target = False

			return target

		if not target:
			target = getNearTarget()

		if target:

			enemy = self.model.players.getEnemyPlayerData(target)

			if enemy and 'pvp' in enemy and enemy['pvp']:

				enemy_stats = getPlayerInfoForBattle(enemy)

				sides = {
				'side_1': [{ 'type': 'player', 'obj': self.model.players.getCurrentStats(self.player['stat'])}],
				'side_2': [{ 'type': 'player', 'obj': getSpellEffects(enemy_stats, spell_effects) }]
				}

				fight_result = self.modules['fight'].fightBetweenPlayerAndMonster(sides)

				player_kill = fight_result['winner'] == 'side_1'
				if player_kill:
					self._getPVPRewards()

				self.tweet_vars['is_pvp_kill'] = player_kill

				self._setStatsAfterFight(fight_result)

	def actionPeasantFight(self):
		self.tweet_vars.update({
			'is_pvp_kill': True,
			'is_np': True
		})

		str_lvl = str(self.player['lvl'])
		if str_lvl in self.pvp_rewards:
			self.getExp(int(float(self.pvp_rewards[str_lvl]) / 10))

	def actionMeet(self, type_of_meeting = 0):
		# 0 - with peasant
		# 1 - with player
		# 2 - with enemy

		if type_of_meeting == 0:
			is_success = self.balance.meetPeasantSuccess()
			self.tweet_vars['is_meet_success'] = is_success
			if is_success:
				self.getExp(random.randint(10,25))

		elif type_of_meeting == 1:
			is_success = self.balance.meetPlayerSuccess()
			self.tweet_vars['is_meet_success'] = is_success
			if is_success:
				self.getExp(self.player['lvl']*5 + random.randint(1,10))

		elif type_of_meeting == 2:
			is_success = self.balance.meetPVPSuccess()
			self.tweet_vars['is_meet_success'] = is_success
			if is_success:
				self.getExp(self.player['lvl']*3 + random.randint(1,10))
				self.getGold(random.randint(10,25))

	def actionBuffSomebody(self, buff_effects, target_name = False):

		def getTargetInfo(target_name):
			player = self.model.players.getEnemyPlayerData(target_name)
			return player

		def processBuff(buffs, buff_effects):

			buff = {
			'buff_name': self.tweet_vars['spell']['name'],
			'actions': buff_effects,
			'buff_img': self.tweet_vars['spell']['img'],
			'start_time': time.time(),
			'length': 3600
			}

			if 'UID' in self.tweet_vars['spell']:
				buff.update({
				'buff_uid': self.tweet_vars['spell']['UID']
				})
			else:
				buff.update({
				'buff_id': self.tweet_vars['spell']['_id']
				})

			already_has_this_buff = False
			for i in range(0, len(buffs)):
				if buffs[i]['buff_name'] == buff['buff_name']:
					already_has_this_buff = True
					buffs[i] = buff
					break

			if not already_has_this_buff:
				buffs.append(buff)

			return buffs

		if self.isParam('is_self_target'):

			self.player['buffs'] = processBuff(self.player['buffs'], buff_effects)

			if 'DMG_DONE' in buff_effects:
				new_HP = self.player['stat']['HP']['current'] - buff_effects['DMG_DONE']
				if new_HP <= 0:
					new_HP = 1

				self.player['stat']['HP']['current'] = new_HP
				self.updated_fields.add('stat')

			self.updated_fields.add('buffs')

		else:
			friend = getTargetInfo(target_name)
			if friend:
				friend['buffs'] = processBuff(friend['buffs'], buff_effects)
				self.model.players.updatePlayerBuffs(friend['_id'], friend['buffs'])

	# --------------------------------------------------------------------------------------
	# Rewards

	def _getRewards(self, monster, is_dungeon = False, reward_koeff = 1):
		self.getExp(int(float(monster['exp'])*reward_koeff))
		self.getGold(int(float(monster['gold'])*reward_koeff))
		self.checkDrop(is_dungeon = is_dungeon)

	def _getQuestRewards(self, quest):
		self.getExp(quest['reward_exp'], name='quest_')
		self.getGold(quest['reward_gold'], name='quest_')

	def _getPVPRewards(self, reward_koeff = 1):

		reward = 0
		if not (self.isParam('is_friend_target') and self.isParam('pvp_forced')):
			reward = random.randint(4,6)

		if reward != 0:
			str_lvl = str(self.player['lvl'])
			if str_lvl in self.pvp_rewards:
				self.getExp(self.pvp_rewards[str_lvl])

		self.getPVPScore(reward)

	def actionGetRaidRewards(self):
		if not self.tweet_vars['is_ignored'] and self.isParam('complete_raid'):
			self.getExp(int(float(self.tweet_vars['boss']['exp'])/self.tweet_vars['people']))
			self.getGold(int(float(self.tweet_vars['boss']['gold'])/self.tweet_vars['people']))
			self.checkDrop(is_dungeon = True, is_raid = True )

	def actionGetFvFRewards(self):
		if not self.tweet_vars['is_ignored']:
			if self.player['faction'] == self.tweet_vars['winner_faction']:
				self.getPVPScore(self.balance.PVP_FVF_REWARD, not_guild = True)
			else:
				self.getPVPScore(self.balance.PVP_FVF_LOOSE_REWARD, not_guild = True)

	def actionGetGvGRewards(self):
		if not self.tweet_vars['is_ignored']:
			if self.player['_guild_name'] == self.tweet_vars['winner_guild_name']:
				self.getPVPScore(self.balance.PVP_GVG_REWARD, not_guild = True)

	# --------------------------------------------------------------------------------------
	# Questing

	def setQuest(self):
		for quest in self.quests:
			if quest['dungeon']['UID'] == self.player['direction']['UID']:
				try:
					already = self.player['quest']['UID'] == quest['UID']
				except Exception:
					already = False

				if not already:
					self.tweet_vars.update({
					'is_quest': True,
					'quest': quest
					})

					self.player['quest'] = {'UID': quest['UID'], 'time': time.time()}
					self.updated_fields.add('quest')

	def checkQuest(self):
		if not ('quest' in self.player and self.player['quest']):
			return False

		for quest in self.quests:
			if quest['UID'] == self.player['quest']['UID']:
				our_quest = quest
				break
		else:
			our_quest = False

		if our_quest:
			if our_quest['type'] == 1 and self.isParam('is_monster') and self.tweet_vars['monster']['UID'] == our_quest['kill_boss_UID']:
				quest_complete = self.isParam('is_monster_kill')

				self.tweet_vars.update({
					'quest_finished': quest_complete,
					'quest': our_quest
				})

				self.player.update({
					'quest': False,
					'last_quest_time': time.time()
				})

				self.updated_fields.update(['quest', 'last_quest_time'])
				self._getQuestRewards(our_quest)

	# --------------------------------------------------------------------------------------
	# Moving

	def getDirectionToLocation(self):
		if self.isParam('is_move_order'):

			is_new_direction = False

			if 'direction' in self.player and self.player['direction']:
				if 'force_time' in self.player['direction'] and self.player['direction']['force_time'] > time.time():
					is_new_direction = False
				else:
					if not (self.player['direction']['type'] == self.tweet_vars['move_order']['type'] and self.player['direction']['UID'] == self.tweet_vars['move_order']['UID'] ):
						is_new_direction = True
			else:
				is_new_direction = True

			if is_new_direction:
				self.player['direction'] = self.tweet_vars['move_order'].copy()
				self.updated_fields.add('direction')

				if not ('quest' in self.player and self.player['quest']):
					if not ('last_quest_time' in self.player and time.time() - self.player['last_quest_time'] <= self.balance.QUEST_LEN):
						self.setQuest()

	def getAutoNewForceDirection(self):
		events = self.mongo.getu('events', {'people':{'$all':[self.player['_id']]}, 'start_date': {'$gte': time.time()}}, sort={'start_date': 1}, limit=1)
		if events:
			if events[0]['type'] == 'raid':
				for raid in self.raids:
					if raid['UID'] == events[0]['target']:
						return {
						'position': raid['position'],
						'UID': raid['UID'],
						'type': raid['type'],
						'force_time': events[0]['start_date'],
						'name': raid['name'],
						}

		return False

	def movingPlayer(self):

		MOVEMENT_DEBUG = False

		def getDirectionPath(coords, direction_coords):

			# is player x coord is greater than direction x coord?
			xgt = coords['x'] > direction_coords['x']
			xeq = coords['x'] == direction_coords['x']

			# for y
			ygt = coords['y'] > direction_coords['y']

			if xeq:
				if ygt:
					path = 2
				else:
					path = 5

			elif xgt:
				if ygt:
					path = 1
				else:
					path = 6
			else:
				if ygt:
					path = 3
				else:
					path = 4

			return path

		def getClearPath(last):

			available_paths = Set([1,2,3,4,5,6])

			decline_path = last + 3
			if decline_path > 6:
				decline_path -= 6

			minor_path1 = decline_path - 1
			if minor_path1 < 1:
				minor_path1 += 6

			minor_path2 = decline_path + 1
			if minor_path2 > 6:
				minor_path2 -= 6

			minor_paths = Set([minor_path1, minor_path2])
			major_paths = available_paths.difference(Set([decline_path, minor_path1, minor_path2, last]))
			super_path = last

			chances = []
			for path in available_paths:
				k = 0
				if path in minor_paths:
					k = self.core.PATH_MINOR_P
				elif path in major_paths:
					k = self.core.PATH_MAJOR_P
				elif path == super_path:
					k = self.core.PATH_SUPER_P

				for i in range(0, k):
					chances.append(path)

			return chances[random.randint(0,99)]

		def getPVPPath(coords):
			x_available = Set()
			if coords['x'] <= self.core.AREA_PVP['x'][0]:
				x_available = Set([3,4])
			if coords['x'] >= self.core.AREA_PVP['x'][1]:
				x_available = Set([1,6])

			y_available = Set()
			if coords['y'] <= self.core.AREA_PVP['y'][0]:
				y_available = Set([6,5,4])
			if coords['y'] >= self.core.AREA_PVP['y'][1]:
				y_available = Set([1,2,3])

			if not x_available:
				return random.sample(y_available, 1)[0]
			if not y_available:
				return random.sample(x_available, 1)[0]

			return random.sample(x_available and y_available, 1)[0]

		def setCoords(path, coords):
			if path == 1:
				coords['x'] -= 1
				coords['y'] -= 1
			elif path == 2:
				coords['y'] -= 1
			elif path == 3:
				coords['x'] += 1
				coords['y'] -= 1
			elif path == 4:
				coords['x'] += 1
				coords['y'] += 1
			elif path == 5:
				coords['y'] += 1
			elif path == 6:
				coords['x'] -= 1
				coords['y'] += 1

		def getBorderPath(coords):
			if coords['x'] == self.core.MAP_WIDTH:
				path = random.sample([1, 6], 1)[0]
			elif coords['x'] == 0:
				path = random.sample([3, 4], 1)[0]
			elif coords['y'] == self.core.MAP_HEIGHT:
				path = 2
			elif coords['y'] == 0:
				path = 5

			return path

		def checkCoordsCorrect(coords):
			if coords['x'] > self.core.MAP_WIDTH:
				coords['x'] = self.core.MAP_WIDTH
			elif coords['x'] < 0:
				coords['x'] = 0

			if coords['y'] > self.core.MAP_HEIGHT:
				coords['y'] = self.core.MAP_HEIGHT
			elif coords['y'] < 0:
				coords['y'] = 0

		def checkGeoPoints(coords):

			str_x = str(coords['x'])
			str_y = str(coords['y'])

			is_point = str_x in self.location_matrix and str_y in self.location_matrix[str_x]

			if is_point:

				fields = {}
				fields['already_visited'] = 'last_poi_name' in self.player and self.player['last_poi_name'] == self.location_matrix[str_x][str_y][0]['name']

				fields.update({
				'is_poi': True,
				'poi': self.location_matrix[str_x][str_y][0]
				})

				self.player['last_poi_name'] = self.location_matrix[str_x][str_y][0]['name']
				self.updated_fields.add('last_poi_name')

				if 'direction' in self.player and self.player['direction'] and coords['x'] == self.player['direction']['position']['x'] and self.player and coords['y'] == self.player['direction']['position']['y']:
					# direction reached
					fields.update({
					'is_direction': True
					})

					if not ('force_time' in self.player['direction'] and self.player['direction']['force_time'] > time.time()):
						self.player['direction'] = self.getAutoNewForceDirection()
						self.updated_fields.add('direction')

				fields.update({'is_geo_event': True})
				self.parse(fields)

		if not 'last' in self.player['position']:
			last = 1
		else:
			last = lasts = self.player['position']['last'][0]

		coords = self.player['position']
		checkCoordsCorrect(coords)

		# path to
		# 1 — left top (x: -1, y:-1)
		# 2 — top (y: -1)
		# 3 — right top (x: +1, y: -1)
		# 4 — right bottom (x: +1, y:+1)
		# 5 — bottom (y: +1)
		# 6 — left bottom (x: -1, y: +1)

		func_name = 'none'
		if coords['x'] in [0, self.core.MAP_WIDTH] or coords['y'] in [0, self.core.MAP_HEIGHT]:
			path = getBorderPath(coords)
			func_name = 'getBorderPath'
		else:

			direction_path = False
			if 'is_penalty' in self.player and self.player['is_penalty']:
				func_name = 'FearRun'
				direction_path = True
				path = getDirectionPath(coords, {'x':29, 'y':24})

			else:
				if 'direction' in self.player and self.player['direction']:
					direction_path = self.balance.chance(self.balance.CHANCE_DIRECTION)
					if direction_path:
						func_name = 'getDirectionPath'
						path = getDirectionPath(coords, self.player['direction']['position'])

			if not direction_path:
				if self.player['pvp']:
					if self.core.AREA_PVP['x'][0] <= coords['x'] <= self.core.AREA_PVP['x'][1] and self.core.AREA_PVP['y'][0] <= coords['y'] <= self.core.AREA_PVP['y'][1]:
						path = getClearPath(last)
						func_name = 'getBorderPath + pvp'
					else:
						path = getPVPPath(coords)
						func_name = 'getPVPPath'
				else:
					path = getClearPath(last)
					func_name = 'getClearPath'

		setCoords(path, coords)

		if MOVEMENT_DEBUG:
			print
			print ' ----- Movement ----- '
			print '----->>>>> ', func_name
			print '----->>>>> ', path, coords
			print

		coords['last'] = [path]

		self.player['position'] = coords
		self.updated_fields.add('position')

		checkGeoPoints(coords)

	# --------------------------------------------------------------------------------------
	# Updating stats and achvs

	def updateStatistics(self):

		def getChangeStatArray(data):

			def changeStat(key, value):
				if key in fields:
					fields[key] += value
				else:
					fields.update({key: value})

			fields = {}
			if 'new_lvl' in data:
				changeStat('lvl', data['new_lvl'])

			if 'is_monster_kill' in data and data['is_monster_kill']:
				changeStat('kills_monster', 1)

				if 'is_mention' in data and data['is_mention']:
					changeStat('kills_monster_party', 1)

				if 'dungeon' in data and data['dungeon'] or 'poi' in data and data['poi']:
					dungeon_id = 0

					if 'dungeon' in data and data['dungeon']:
						dungeon_id = data['dungeon']['UID']

					if 'poi' in data and data['poi']:
						dungeon_id = data['poi']['UID']

					changeStat('dungeons_runs', 1)

					if not 'is_mention' in data or not data['is_mention']:
						changeStat('dungeons_runs_alone',1)

					if 'is_boss' in data and data['is_boss']:
						changeStat('kills_boss',1)
						changeStat('dungeons_classic_complete_count',1)
						changeStat('dungeons_classic_complete_dungeon_'+str(dungeon_id),1)

			if 'is_drop' in data and data['is_drop']:
				changeStat('items_looted', 1)

			if 'is_spell' in data and data['is_spell'] and not 'not_enough_mana' in data:
				changeStat('spells_used', 1)
				if 'is_monster_kill' in data and data['is_monster_kill']:
					changeStat('kills_monster_magic', 1)

			if 'is_raid' in data and data['is_raid']:
				changeStat('raids_runs',1)
				if 'complete_raid' in data and data['complete_raid']:
					changeStat('raids_completed',1)
					changeStat('raid_complete_'+str(data['dungeon']['UID']),1)

			if 'is_pvp_kill' in data and data['is_pvp_kill'] and 'is_pvp_kill' in data and data['is_pvp_kill']:
				if 'is_np' in data and data['is_np']:
					changeStat('pvp_np_kills_player',1)
				else:
					changeStat('pvp_kills_player',1)


			return fields

		updated = getChangeStatArray(self.tweet_vars)

		is_changed = self.stats.update(self.player_stats, updated)
		if is_changed:
			self.updated_fields.add('statistics')

		self.tweet_vars.update({'statistics_updated': is_changed})

	def updateAchievements(self):

		def getAchvName(uid):
			return self.static_achvs[str(uid)]

		if self.isParam('statistics_updated'):
			new_achvs = self.achvs.update(self.player_achvs, self.player_stats)
			if len(new_achvs) > 0:

				self.tweet_vars['achvs'] = []
				for achv_id in new_achvs:
					self.tweet_vars['achvs'].append({'achv_name': getAchvName(achv_id), 'achv_UID': achv_id})
					self.player['achv_points'] = int(self.player['achv_points']) + 1

				self.updated_fields.add('achv_points')
				self.updated_fields.add('achvs')


	# --------------------------------------------------------------------------------------
	# Parsing

	def parse(self, tweet):

		def isMetric(metric_name):
			return self.isParam(metric_name)

		def getMetrics():

			current_metric = False

			if isMetric('is_mention'):
				self.setActivity('mention')
				current_metric = True

			if isMetric('is_hashtag'):
				self.setActivity('hash')
				current_metric = True

			if isMetric('is_retweet'):
				self.setActivity('rt')
				current_metric = True

			if not current_metric:
				self.setActivity('clear')

		def getInfoAboutTweet(tweet):

			self.tweet_vars.update({
				'tweet_id': tweet.id,
				'tweet_text': tweet.text
			})

			debuff = self.modules['censore_filter'].censoreFilter(tweet)
			if debuff:
				self.setActivity('bad_words')

			if self.player['lvl']:
				if self.modules['ignore_game_tweets'].isGameTweet(tweet):
					self.setActivity('ignore_game')
					return False

			if self.modules['ignore_services'].isBlackListTweet(tweet):
				self.setActivity('ignore_service')
				return False

			self.isRetweet(tweet)
			self.isMention(tweet)
			self.isHashtag(tweet)
			self.isSpell(tweet)
			self.isGroupEvent(tweet)

			return True

		def getInfoAboutInteraction(tweet):
			self.tweet_vars.update(tweet)
			self.tweet_vars.update({'interaction': True})

		def getInfoAboutEvent(event):

			if event['event_type'] == 'raid':
				self.tweet_vars.update({
				'is_raid': True,
				'event_type': 'raid',
				'is_event': True,
				'complete_raid': event['is_complete'],
				'dungeon': event['dungeon'],
				'boss': event['boss'],
				'people': event['people'],
				'is_ignored': event['is_ignored'],
				})

			elif event['event_type'] == 'war':

				if event['event']['target'] == event['event']['winner_id']:
					winner = event['event']['target']
					winner_name = event['event']['target_name']
					looser = event['event']['guild_side']
					looser_name = event['event']['guild_side_name']
				else:
					looser = event['event']['target']
					looser_name = event['event']['target_name']
					winner = event['event']['guild_side']
					winner_name = event['event']['guild_side_name']

				self.tweet_vars.update({
				'event': event['event'],
				'is_event': True,
				'event_type': 'war',
				'is_ignored': event['is_ignored'],
				'winner_guild': winner,
				'winner_guild_name': winner_name,
				'looser_guild': looser,
				'looser_guild_name': looser_name,
				})

			elif event['event_type'] == 'fvf':

				if event['event']['sides'][0] == event['event']['winner_id']:
					win_uid = 0
					loose_uid = 1
				else:
					win_uid = 1
					loose_uid = 0

				winner = event['event']['sides'][win_uid]
				winner_name = event['event']['sides_names'][win_uid]
				looser = event['event']['sides'][loose_uid]
				looser_name = event['event']['sides_names'][loose_uid]

				self.tweet_vars.update({
				'event': event['event'],
				'is_event': True,
				'event_type': 'fvf',
				'is_ignored': event['is_ignored'],
				'winner_faction': winner,
				'winner_faction_name': winner_name,
				'looser_faction': looser,
				'looser_faction_name': looser_name,
				})

		def getInfoAboutGeo(geo):
			self.tweet_vars.update(geo)

		try:
			self.tweet_vars = {'player': self.player['name']}
		except Exception:
			self.getExceptionText('Player not exist')
			return False

		parse_it = True

		if not isinstance(tweet, dict):
			parse_it = getInfoAboutTweet(tweet)
		else:
			if 'is_event' in tweet:
				getInfoAboutEvent(tweet)
			elif 'is_geo_event' in tweet:
				getInfoAboutGeo(tweet)
			else:
				getInfoAboutInteraction(tweet)

		getMetrics()

		if not parse_it:
			return False

		if self.isParam('is_group_event'):
			pass
		elif self.isParam('is_geo_event'):
			self.processGeoMechanic()
		elif self.isParam('interaction'):
			self.processInteractionMechanic()
		elif self.isParam('is_event') and self.tweet_vars['event_type'] in ['raid', 'war', 'fvf'] :
			self.processGroupEventMechanic()
		else:
			self.processGameMechanic2()

		self.checkQuest()

		self.updateStatistics()
		self.updateAchievements()
		self.countMetrics()

		self.composeMessage()

		self._debug_tweetVars()

	# --------------------------------------------------------------------------------------
	# DEBUG

	def _debug_tweetVars(self, local_debug=False):
		if self.DEBUG or local_debug:
			print
			print '----- tweet vars -----'
			for item in self.tweet_vars:
				try:
					print '>',item,'=', self.tweet_vars[item]
				except Exception:
					print '> UNICODE ERROR'
			print '----- ---------- -----'

	def _debug_interactions(self):
		if self.DEBUG:
			print
			print '----- interactions -----'
			print self.interactions
			print '----- ------------ -----'
			print
			print '----- reverse interactions -----'
			print self.reverse_interactions
			print '----- -------------------- -----'
