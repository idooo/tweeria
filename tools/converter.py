#!/usr/bin/python
# -*- coding: utf-8 -*-

# author: Alex Shteinikov

import __init__
import settings
tweenk_core = settings.core()
tweenk_balance = settings.balance()

import optparse
import db
import random
import achv
import time
import statistics
import os, sys, inspect
import re

class converter():

	mongo = db.mongoAdapter()

	buff = ''

	BASE_DIR = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])+'/../import_base/'

	def __init__(self):
		self.RE_SPLIT = re.compile('("(.*?)".*?(,|$))|((.*?),)')

	def test(self):
		print('This is test converter string')

	def splitLine(self, line):
		result = []
		res = re.findall(self.RE_SPLIT, line)
		if res:
			for r in res:
				if r[4] != '':
					result.append(r[4])
				else:
					result.append(r[1])

		return result

	def loadfile(self,filename):
		fp = open(self.BASE_DIR+filename,'r')
		self.buff = fp.readlines()

	def savefile(self,filename,text):
		fp = open(filename,'w')
		fp.write(text)

	# проверяет корректна ли строка и стоит ли ее обрабатывать

	def isCorrectString(self,string):
		return (string[0]>='1') and (string[0][0]<='9')

	def isCorrectMetricString(self, string):
		try:
			int(string[0][1])
		except Exception:
			return False

		return True

	# Нормализует строку stroke (ставит значения по умолчанию), 
	# создает хэш буфферных данных из данных из строки и заданных ключей

	def readToBuff(self,stroke,keys,data_buff):

		for i in range(0,len(keys)):
			if stroke[i] == '':
				stroke[i] = '0'

			data_buff[keys[i]] = stroke[i]

	# Сохраняет строковые атрибуты из буфферного хэша
	# в окончательный 	

	def getStrValues(self,data,data_buff,attrs):
		for attr_name in attrs:
			data[attr_name] = data_buff[attr_name].rstrip()

	# Сохраняет целочисленные атрибуты 
	# из буфферного хэша в окончательный

	def getNumValues(self,data,data_buff,attrs):
		for attr_name in attrs:
			if str.find(data_buff[attr_name],'.') > 0:
				data_buff[attr_name] = round(float(data_buff[attr_name]),1)

			data[attr_name] = int(data_buff[attr_name])

	def getBoolValues(self,data,data_buff,attrs):
		for attr_name in attrs:
			data[attr_name] = data_buff[attr_name].rstrip() == '1'

	# Сохраняет значения бонусов к характеристикам
	# из буфферного хэша в окончательный	

	def getBonusValues(self,data,data_buff,attrs):
		data['bonus'] = {}
		for attr_name in attrs:

			if data_buff[attr_name] == '':
				data_buff[attr_name] = '0'

			if str.find(data_buff[attr_name],'.') > 0:
				data_buff[attr_name] = round(float(data_buff[attr_name]),1)

			data['bonus'][attr_name]  = int(data_buff[attr_name])

	def printInfo(self, name, count):
		print 'Import '+name+' success'
		print 'Loaded '+str(count)+' '+name

	# ----------------------

	def settings(self):

		def settingsClasses(filename):
			self.loadfile(filename)

			keys = ['UID','name','priority_stat','available_weapons','starter_equip','damage_type']
			items_count = 0
			record = {}
			for line in self.buff:
				stroke = line.split(',')
				data_buff = {}
				data = {}
				if self.isCorrectString(stroke):
					self.readToBuff(stroke,keys,data_buff)
					self.getStrValues(data,data_buff,['name','priority_stat','available_weapons','starter_equip','damage_type'])
					self.getNumValues(data,data_buff,['UID'])
					b = {}
					for key in data:
						if not key in ['UID']:
							b.update({key: data[key]})

					record.update({str(data['UID']): b})
					items_count += 1

			self.printInfo('classes', items_count)
			return record

		def settingsStats(filename):
			self.loadfile(filename)

			keys = ['UID','class', 'str', 'dex', 'int', 'luck', 'DEF', 'DMG', 'HP', 'MP', 'lead', 'karma', 'fame', 'SPD', 'mastery']

			items_count = 0
			record = {}
			for line in self.buff:
				stroke = line.split(',')
				data_buff = {}
				data = {}
				if self.isCorrectString(stroke):
					self.readToBuff(stroke,keys,data_buff)
					self.getNumValues(data,data_buff,['UID', 'class', 'str', 'dex', 'int', 'luck', 'DEF', 'DMG', 'HP', 'MP', 'lead', 'karma', 'fame', 'SPD', 'mastery'])
					stat = {}
					for key in data:
						if not key in ['UID', 'class']:
							stat.update({key: data[key]})

					record.update({str(data['class']): stat})
					items_count += 1

			self.printInfo('classes stats', items_count)
			return record

		self.mongo.cleanUp('settings')

		record = {}
		record.update({'classes':settingsClasses('settings_classes_names.csv')})
		record.update({'classes_stats':settingsStats('settings_classes_stats.csv')})

		self.mongo.insert('settings',record)

	def spells(self):

		def spellsActions(filename):

			self.loadfile(filename)
			keys = ['UID', 'name', 'type', 'power', 'desc', 'monster', 'enemy', 'friend', 'self', 'lvl_min', 'lvl_max', 'effect', 'cost_by_effect', 'restriction_by_lvl', 'img', 'effect_desc', 'effect_value_text']


			self.mongo.cleanUp('spells_actions')
			items_count = 0
			actions = {}
			for line in self.buff:
				stroke = line.split(',')
				data_buff = {}
				data = {}

				if self.isCorrectString(stroke):
					self.readToBuff(stroke,keys,data_buff)
					self.getStrValues(data,data_buff,['name', 'desc', 'effect', 'power', 'img', 'effect_desc', 'effect_value_text'])
					self.getNumValues(data,data_buff,['UID','type','monster', 'enemy', 'friend', 'self', 'lvl_min', 'lvl_max', 'cost_by_effect', 'restriction_by_lvl'])
					actions.update({str(data['UID']): data})

					self.mongo.insert('spells_actions',data)
					items_count += 1

			self.printInfo('spell actions', items_count)

			return actions

		def spells(filename, actions):

			def getActions(line):
				list_of_actions = line.split(';')
				result = []
				for item in list_of_actions:
					number, value = item.split(':')

					buff = {
						'name': actions[number]['name'],
					    'effect': actions[number]['effect'],
					    'value': int(value),
					    'type': actions[number]['type'],
					    'power': actions[number]['power']
					}

					result.append(buff)

				return result

			self.loadfile(filename)
			keys = ['UID', 'name', 'desc', 'lvl_min', 'lvl_max', 'mana_cost', 'actions', 'keyword', 'img']

			self.mongo.cleanUp('spells')
			items_count = 0
			for line in self.buff:
				stroke = line.split(',')
				data_buff = {}
				data = {}

				if self.isCorrectString(stroke):
					self.readToBuff(stroke,keys,data_buff)
					self.getStrValues(data,data_buff,['name', 'desc', 'actions', 'keyword', 'img'])
					self.getNumValues(data,data_buff,['UID', 'lvl_min', 'lvl_max', 'mana_cost'])
					data['spell_actions'] = getActions(data['actions'])
					self.mongo.insert('spells',data)
					items_count += 1

			self.printInfo('spells', items_count)

		def updateSpellBooks():
			static_spells = self.mongo.getu('spells')
			spellbooks = self.mongo.getu('spellbooks')

			for spellbook in spellbooks:

				new_spells = []
				for spell in spellbook['spells']:

					for static_spell in static_spells:
						if 'spell_UID' in spell:
							if static_spell['UID'] == spell['spell_UID']:
								new_spells.append({'spell_id': static_spell['_id'], 'spell_UID': static_spell['UID']})
						else:
							new_spells.append({'spell_id': spell['spell_id']})

				self.mongo.update('spellbooks', {'_id': spellbook['_id']}, {'spells': new_spells})

		actions = spellsActions('spells_actions.csv')
		spells('spells.csv', actions)
		updateSpellBooks()

	def dungeons(self,filename):
		self.loadfile(filename)

		keys = ['UID','name', 'type', 'lvl_min','lvl_max','max_players','desc','holidays', 'power', 'x', 'y', 'hashtag']

		self.mongo.cleanUp('dungeons')

		items_count = 0

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if self.isCorrectString(stroke):

				self.readToBuff(stroke,keys,data_buff)

				self.getStrValues(data,data_buff,['desc','name', 'hashtag'])

				self.getNumValues(data,data_buff,['UID','type','lvl_min','lvl_max','max_players','holidays', 'power', 'x', 'y'])

				data.update({'position': {'x': data['x'], 'y': data['y']}})
				del data['x'], data['y']
				self.mongo.insert('dungeons',data)
				items_count += 1


		self.printInfo('dungeons', items_count)

	def quests(self,filename):
		self.loadfile(filename)

		keys = ['UID','name', 'type', 'lvl_min', 'kill_boss_UID','dungeon_UID','reward_gold','reward_exp', 'hashtag', 'desc']

		self.mongo.cleanUp('quests')

		items_count = 0

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if self.isCorrectString(stroke):

				self.readToBuff(stroke,keys,data_buff)
				self.getStrValues(data,data_buff,['desc','name','hashtag'])
				self.getNumValues(data,data_buff,['UID','type','kill_boss_UID','dungeon_UID','lvl_min', 'reward_gold', 'reward_exp'])

				self.mongo.insert('quests',data)
				items_count += 1


		self.printInfo('quests', items_count)

	def locations(self,filename):
		self.loadfile(filename)

		keys = ['UID','name', 'type', 'desc', 'holidays', 'x', 'y', 'hashtag']

		self.mongo.cleanUp('locations')

		items_count = 0

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if self.isCorrectString(stroke):

				self.readToBuff(stroke,keys,data_buff)

				self.getStrValues(data,data_buff,['desc','name', 'hashtag'])

				self.getNumValues(data,data_buff,['UID','type','holidays', 'x', 'y'])

				data.update({'position': {'x': data['x'], 'y': data['y']}})
				del data['x'], data['y']

				self.mongo.insert('locations',data)
				items_count += 1


		self.printInfo('locations', items_count)

	def pvp_rewards(self,filename):
		self.loadfile(filename)

		keys = ['lvl', 'exp']

		self.mongo.cleanUp('pvp_rewards')

		items_count = 0

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if self.isCorrectString(stroke):

				self.readToBuff(stroke,keys,data_buff)

				self.getNumValues(data,data_buff,['lvl', 'exp'])

				self.mongo.insert('pvp_rewards',data)
				items_count += 1

		self.printInfo('pvp rewards', items_count)

	def achvs(self, update_existing = False):

		def achvsNew(filename, collection_name):
			self.loadfile(filename)

			keys = ['UID','name','text','type','points','condition','order','visibility', 'img']

			self.mongo.cleanUp(collection_name)

			items_count = 0

			for line in self.buff:
				stroke = line.split(',')
				data_buff = {}
				data = {}

				if self.isCorrectString(stroke):
					self.readToBuff(stroke,keys,data_buff)

					self.getStrValues(data,data_buff,['condition','text','name', 'img'])

					self.getNumValues(data,data_buff,['UID','type','points','order','visibility'])

					if data['type'] != 0:
						conditions = data['condition'].split(';')

						record = {}
						for condition in conditions:
							_tmp_ = condition.split(':')
							try:
								_tmp_[1] = int(_tmp_[1])
							except Exception:
								pass
							record.update({_tmp_[0]: _tmp_[1]})

						data['condition'] = record

					self.mongo.insert(collection_name,data)
					items_count += 1

			self.printInfo('achievements', items_count)

		def updateExistingAchvs():
			ac_static = self.mongo.getu('achievements_static', fields={'UID':1})

			for achv in ac_static:
				achv['UID'] = str(achv['UID'])

			ac_created = self.mongo.getu('achievements')

			for player in ac_created:

				record = {}
				for static in ac_static:
					found = False
					for achv_number in player['achvs']:
						if achv_number == static['UID']:
							record.update({achv_number: player['achvs'][achv_number]})
							found = True

					if not found:
						record.update({static['UID']: False})

				_id = player['_id']
				player['achvs'] = record
				del player['_id']

				self.mongo.update('achievements', {'_id': _id}, player)

		achvsNew('achvs.csv', 'achievements_static')

		if update_existing:
			updateExistingAchvs()

	def messages(self, filename, collection_name, update_existing = False):

		def updatingExistingMessages():

			def getMessageByUID(records,uid):
				for record in records:
					if record['UID'] == uid:
						return record['message']

			messages = self.mongo.getu('messages')
			created_messages = self.mongo.getu('messages_created')

			for created_message_array in created_messages:
				player_updated = 0
				for created_message in created_message_array['last']:
					text = getMessageByUID(messages, created_message['data']['message_UID'])
					created_message['message'] = text
					player_updated += 1

				if player_updated > 0:
					self.mongo.update('messages_created', {'user_id': created_message_array['user_id']}, {'last': created_message_array['last']})

		self.loadfile(filename)
		keys = ['UID', 'type', 'message']

		self.mongo.cleanUp(collection_name)

		items_count = 0

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if self.isCorrectString(stroke):
				self.readToBuff(stroke,keys,data_buff)

				self.getStrValues(data,data_buff,['message'])

				self.getNumValues(data,data_buff,['UID','type'])

				data.update({'p': 1})

				self.mongo.insert(collection_name, data)
				items_count += 1

		self.printInfo('messages', items_count)

		if update_existing:
			updatingExistingMessages()

	def monsters(self,filename, collection_name):

		self.loadfile(filename)
		keys = ['UID','name','class','lvl_min','lvl_max','exp','gold',
		        'area_normal', 'area_dungeon', 'area_coords',
		        'boss','dungeon',
		        'text','holidays','art',
		        'str','dex','int','luck','DEF','DMG','HP','MP','SPD',
		        ]

		self.mongo.cleanUp(collection_name)
		items_count = 0

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if self.isCorrectString(stroke):
				self.readToBuff(stroke,keys,data_buff)

				self.getStrValues(data,data_buff,['name','class','text', 'art'])

				self.getNumValues(data,data_buff,[
					'UID','lvl_min','lvl_max','exp','gold','dungeon','holidays', 'str','dex','int','luck','DEF','DMG','HP','MP','SPD',
				])

				self.getBoolValues(data, data_buff, ['area_normal', 'area_dungeon', 'area_coords','boss'])

				stats = {}
				for stat in ['str','dex','int','luck','DEF','DMG','HP','MP','SPD']:
					stats.update({stat: data[stat]})
					del data[stat]

				areas_info = {}
				for area in ['area_normal', 'area_dungeon', 'area_coords']:
					areas_info.update({area: data[area]})
					del data[area]

				data.update({'stat': stats, 'area': areas_info})

				self.mongo.insert(collection_name, data)
				items_count += 1

		self.printInfo('monsters', items_count)

	def statistics(self, filename, collection_name):

		self.loadfile(filename)

		keys = ['UID','name','type','amount','visibility','text', 'order', 'group']

		self.mongo.cleanUp(collection_name)

		items_count = 0

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if self.isCorrectString(stroke):
				self.readToBuff(stroke,keys,data_buff)

				self.getStrValues(data,data_buff,['type','name', 'text'])

				self.getNumValues(data,data_buff,['UID','amount', 'visibility', 'order', 'group'])

				self.mongo.insert(collection_name,data)
				items_count += 1


		self.printInfo('statistics', items_count)

	def updateExistingStats(self):

		buff_static_stats = self.mongo.getu('statistics_static')

		static_stats = []
		for static in buff_static_stats:
			static_stats.append(static['name'])

		players_stats = self.mongo.getu('statistics')
		for player_stats in players_stats:
			new_player_stats = {}
			for stat_name in static_stats:
				if stat_name in player_stats['stats']:
					value = player_stats['stats'][stat_name]
				else:
					value = 0

				new_player_stats.update({stat_name: value})

			self.mongo.update('statistics', {'user_id': player_stats['user_id']}, {'stats': new_player_stats})

	def shopItems(self, filename, collection_name):
		self.loadfile(filename)
		keys = ['item_UID', 'id', 'name', 'type',  'desc', 'author', 'lvl_min', 'cost', 'img']

		self.mongo.cleanUp(collection_name)

		items_count = 0

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if self.isCorrectString(stroke):
				self.readToBuff(stroke,keys,data_buff)

				self.getStrValues(data,data_buff,['name','desc','img', 'author'])

				self.getNumValues(data,data_buff,['item_UID','type', 'lvl_min','cost'])

				self.mongo.insert(collection_name,data)
				items_count += 1

		self.printInfo('shop items', items_count)

	def artworks(self, filename, collection_name):
		self.loadfile(filename)
		keys = ['UID', 'name', 'faction', 'race',  'class',  'default', 'desc', 'cost', 'img', 'author', 'link', 'twitter', 'email']
		#self.mongo.cleanUp(collection_name)
		self.mongo.remove(collection_name, {'UID':{'$exists': True}})

		authors = {}

		items_count = 0

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if self.isCorrectString(stroke):
				self.readToBuff(stroke,keys,data_buff)

				self.getStrValues(data,data_buff,['name','desc','img', 'author', 'link', 'twitter', 'email'])

				self.getNumValues(data,data_buff,['UID', 'faction', 'race', 'class', 'cost', 'default'])

				if data['twitter'] in authors:
					author_id = authors[data['twitter']]
				else:
					_buff = self.mongo.find('players', {'name': data['twitter']}, {'_id': 1})
					if _buff:
						authors.update({data['name']: _buff['_id']})
						author_id = _buff['_id']
					else:
						authors.update({data['name']: ''})
						author_id = ''

				data.update({
					'builtin': True,
				    'img_info': {
					    'name': data['author'],
					    'link': data['link'],
				        'twitter': data['twitter'],
				        'email': data['email'],
				        'verified': True
				    },
				    'create_time': time.time(),
				    'sale_info': {
					    'active': True
				    },
				    'approve': {
					    'approved': True,
					    'time': 0,
					    'approver_id': ''
				    },
				    'author': author_id,
				    'random': random.random()
				})

				del data['link'], data['twitter'], data['email']

				self.mongo.insert(collection_name,data)
				items_count += 1

		self.printInfo('artworks', items_count)

	def clearall(self):
		for collection_name in [
			'players', 'spellbooks', 'achievements', 'messages_created', 'guild_messages', 'statistics', 'guilds',
		    'items_created', 'items_crafted', 'spells_crafted_patterns', 'spells_created', 'events', 'game_statistics',
		    'graph_tweets'
			]:

			self.mongo.cleanUp(collection_name)

	def actions(self, actions_file, events_file):

		col_actions = 'actions'
		col_meta_actions = 'meta_actions'

		self.loadfile(actions_file)
		keys = ['UID', 'name', 'desc', 'trigger', 'messages_OK', 'messages_FAIL', 'callback_OK', 'callback_FAIL']

		self.mongo.cleanUp(col_actions)
		self.mongo.cleanUp(col_meta_actions)

		items_count = 0
		actions = {}

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if len(stroke[0]) and stroke[0][0]=='A':
				self.readToBuff(stroke,keys,data_buff)
				self.getStrValues(data,data_buff,['UID', 'name', 'desc','trigger'])
				self.getNumValues(data,data_buff,['messages_OK', 'messages_FAIL','callback_OK', 'callback_FAIL'])

				uid = data['UID']

				self.mongo.insert(col_meta_actions, data)

				del data['UID'], data['desc']
				if data['trigger'] == '0':
					data['trigger'] = False

				actions.update({uid: data})
				items_count += 1

		self.printInfo('actions', items_count)

		# =========================

		self.loadfile(events_file)
		keys = ['UID', 'mention', 'rt', 'hashtag',  'pvp', 'non_player', 'player_pvp', 'friendly', 'code', 'p', 'trigger']

		items_count = 0
		is_metric = False

		_raw_actions = []
		events = {}

		for line in self.buff:
			stroke = line.split(',')
			data_buff = {}
			data = {}

			if self.isCorrectString(stroke) or is_metric:
				self.readToBuff(stroke,keys,data_buff)

				self.getStrValues(data,data_buff,['trigger', 'code'])
				self.getNumValues(data,data_buff,['UID','mention', 'rt', 'hashtag',  'pvp', 'non_player', 'player_pvp', 'friendly',  'p'])

				if data['code'] != '0':

					if not data['UID']:
						data['UID'] = is_metric
					else:
						is_metric = data['UID']

						event = {
							'tweet_data': {
								'mention': bool(data['mention']),
							    'rt': bool(data['rt']),
							    'hashtag': bool(data['hashtag'])
							},
						    'player': {
						        'pvp': bool(data['pvp'])
						    },
						    'target': {
							    'np': bool(data['non_player']),
						        'enemy': bool(data['player_pvp']),
						        'friend': bool(data['friendly'])
						    },
						    'actions': []
						}

						events.update({
							str(data['UID']): event
						})

					_action = {
						'code': data['code'],
						'p': data['p'],
						'trigger': data['trigger'],
						'event_id': data['UID']
					}
					_raw_actions.append(_action)

					items_count += 1

		for action in _raw_actions:
			event_id = str(action['event_id'])
			del action['event_id'], action['trigger']

			action.update(actions[action['code']])

			events[event_id]['actions'].append(action)


		self.mongo.insert(col_actions,events)

		self.printInfo('events', items_count)



if __name__ == '__main__':
	conv = converter()
	p = optparse.OptionParser()
	p.add_option('--settings', '-s', action="store_true")
	p.add_option('--shop', '-p', action="store_true")
	p.add_option('--spells', '-e', action="store_true")
	p.add_option('--dungeons', '-d', action="store_true")
	p.add_option('--locations', '-l', action="store_true")
	p.add_option('--achvs', '-a', action="store_true", help="Load achievements list")
	p.add_option('--monsters', '-m', action="store_true")
	p.add_option('--artworks', '-w', action="store_true")
	p.add_option('--quests', '-q', action="store_true")
	p.add_option('--stats', '-t', action="store_true")
	p.add_option('--mechanics', '-c', action="store_true")
	p.add_option('--pvp_rewards', '-v', action="store_true")
	p.add_option('--CLEAR', action="store_true")
	p.add_option('--USTATS', action="store_true")
	p.add_option('--UACHVS', action="store_true")
	p.add_option('--UMESSAGES', action="store_true")
	p.add_option('--NMESSAGES', action="store_true")

	(options, arguments) = p.parse_args()

	if options.settings:
		conv.settings()

	if options.spells:
		conv.spells()

	if options.dungeons:
		conv.dungeons('dungeons.csv')

	if options.achvs:
		conv.achvs()

	if options.monsters:
		conv.monsters('monsters.csv', 'monsters')

	if options.NMESSAGES:
		conv.messages('messages.csv', 'messages')

	if options.UMESSAGES:
		conv.messages('messages.csv', 'messages', update_existing=True)

	if options.shop:
		conv.shopItems('shop_items.csv', 'shop_items')

	if options.artworks:
		conv.artworks('artworks.csv', 'artworks')

	if options.stats:
		conv.statistics('stats.csv', 'statistics_static')

	if options.locations:
		conv.locations('locations.csv')

	if options.quests:
		conv.quests('quests.csv')

	if options.pvp_rewards:
		conv.pvp_rewards('pvp_rewards.csv')

	if options.CLEAR:
		conv.clearall()

	if options.USTATS:
		conv.updateExistingStats()

	if options.mechanics:
		conv.actions('Actions.csv', 'Events.csv')

	if options.UACHVS:
		conv.achvs(update_existing=True)