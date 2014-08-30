# -*- coding: UTF-8 -*-

import basic
import time
from sets import Set
from bson import ObjectId
from random import sample
from datetime import datetime
from functions import formatTextareaInput, getRelativeDate
import json

class eventsController(basic.defaultController):

	DIR = './events/'

	@basic.printpage
	def printPage(self, page, params):
		return {
			'events': self.printEvents,
		    'new': self.printNewEvent,
			'__default__':      {
				'method': self.printEventDetail,
				'params': {'event_UID': page}
			}
		}

	@basic.methods
	def methods(self, params = {}):
		return {
			'type_of_form': {
				'start_new_event': self.addNewEvent,
			    'join_event': self.joinEvent,
			    'leave_event': self.leaveEvent,
			    'get_event_players': self.getEventMembers
			}
		}

	# --------------------------------------------------------------------------------------------------
	# Misc

	def getFormattedEvents(self, player_id=None, player_guild = False, query = {}):

		if self.cur_player and self.cur_player['login_utc_offset']:
			utc_offset = self.cur_player['login_utc_offset']
		else:
			utc_offset = self.core.server_utc_offset

		raids = self.model.events.getRaidDungeons()


		if not player_id:
			events = self.model.events.getEvents(query=query, guild=player_guild)
		else:
			events = self.model.events.getEvents(player_id=player_id, query=query, guild=player_guild)

		people = []
		for event in events:
			if 'author' in event:
				people.append(event['author'])

		if people:
			players = self.model.players.getPlayersList(people, ['_id', 'name', 'stat.lead.current'])

		for event in events:
			display = True
			if event['guild_run']:
				display = player_guild and event['guild_side_name'] == player_guild

			event['guild_run_can_join'] = display

			if event['type'] == 'raid':
				for raid in raids:
					if raid['UID'] == event['target']:
						event.update({'where_name': raid['name'], 'people_count_max': raid['max_players']})
			elif event['type'] == 'war':
				del event['lvl_min']

			if 'author' in event:
				for player in players:
					if event['author'] == player['_id']:
						event.update({
							'author_name': player['name'],
						    'lead': player['stat']['lead']['current']
						})

			if not 'finished' in query:
				if event['start_date'] <= time.time():
					event['status'] = 'progress'
					operation = 'not_allowed'
				else:
					operation = 'not_joined'
					if self.cur_player and self.cur_player['login_id'] in event['people']:
						operation = 'joined'
			else:
				operation = 'not_joined'

			event.update({
				'people_count': len(event['people']),
				'start_date_f': getRelativeDate(int(event['start_date'])+utc_offset-self.core.server_utc_offset),
				'operation': operation
			})

		return events

	def isAvailableToJoinEvent(self, start_time):
		is_available = not self.model.events.getEventInThisTime(start_time, self.cur_player['login_id'])
		if not is_available:
			return {'result': False, 'error': 'same_time_error'}

		active_events = self.model.events.getPlayerActiveEventsCount(self.cur_player['login_id'])
		is_available = is_available and (active_events < self.balance.max_events)
		if not is_available:
			return {'result': False, 'error': 'max_events_error'}

		return {'result': True}

	@staticmethod
	def updatePlayerDirection(obj, player_id, event = False):

		player = obj.model.players.getPlayerBy_ID(player_id, {'direction': 1})

		if event:
			try:
				need_replace = event['start_date'] < player['direction']['force_time']
			except Exception:
				need_replace = True

		else:
			need_replace = True
			events = obj.model.events.getPlayersRawEvents(obj.cur_player['login_id'])
			if events:
				if events[0]['type'] == 'raid':
					event = events[0]

		if need_replace:
			if not event:
				direction = False

			elif event['type'] == 'raid':
				raid = obj.model.events.getRaidDungeonById(event['target'])

				direction = {
						'position': raid['position'],
						'type': raid['type'],
						'name': raid['name'],
						'UID': raid['UID'],
				        'force_time': event['start_date']
				}

			elif event['type'] == 'war':

				direction = {
					'position': event['position'],
					'type': 3,
					'name': 'War '+event['guild_side_name']+' vs. '+event['target_name'],
					'force_time': event['start_date']
				}

			obj.model.players.updatePlayerData(player_id, {'direction': direction})

	def canCreateGvGEvent(self, guild, player_id):
		top_pvp_players = self.model.guilds.getTopPvPGuildPlayers(guild['_id'])
		can_create = guild['creator'] == player_id
		if not can_create:
			for record in top_pvp_players:
				if record['_id'] == player_id:
					can_create = True
					break

		return can_create

	# --------------------------------------------------------------------------------------------------
	# Page methods

	def addNewEvent(self, params):

		def getHashtag(value):
			hashtag = value.strip()
			if hashtag:
				if hashtag[0] == '#':
					hashtag = hashtag[1:]

				return hashtag
			else:
				return False

		rules = {
			'desc': {},
			'start_date': {},
		    'event_type': {'in': ['war', 'raid', 'attack']}
		}

		status = self.checkParams(params, rules)

		if status['status']:

			try:
				start_time_wutc = time.mktime(datetime.strptime(params['start_date'], "%d.%m.%Y %H:%M").timetuple())
			except Exception:
				start_time_wutc = 0

			start_time = start_time_wutc + self.core.server_utc_offset - self.cur_player['login_utc_offset']

			if start_time < time.time():
				start_time = time.time() + 3600

			event = self.model.event({
				'type': params['event_type'],
				'author': self.cur_player['login_id'],
				'guild_run': 'guild_run' in params,
			    'desc': formatTextareaInput(params['desc']),
			    'start_date': start_time,
			    'create_date': time.time(),
			    'status': 'active',
			    'faction': self.cur_player['login_faction'],
			    'people': [self.cur_player['login_id']]
			})

			if 'hashtag' in params:
				event.data.update({'promoted_hashtag': getHashtag(params['hashtag'])})

			add_guild_data = False

			if params['event_type'] == 'raid':
				target = self.model.events.getRaidDungeonById(int(params['where']))
				event.data.update({
					'target': int(params['where']),
				    'target_name': target['name'],
				    'lvl_min': target['lvl_min'],
				    'lvl_max': target['lvl_max'],
				    'position': target['position']
				})
				finish_time = self.balance.LENGTH_OF_RAID

				if 'guild_run' in params:
					add_guild_data = True

			elif params['event_type'] == 'war':
				target = self.model.guilds.getGuildByName(params['vs_guild'], type_of_name='search_name')
				if target:

					raw_coords = sample(self.sbuilder.balance.GVG_POINTS, 1)[0]
					event.data.update({
						'target': target['_id'],
					    'target_name': target['name'],
					    'position': {'x': raw_coords[0], 'y': raw_coords[1]}
					})
				else:
					self.httpRedirect(params, '?fail=1&n=no_guild')

				add_guild_data = True

				finish_time = self.balance.LENGTH_OF_WAR

			else:
				finish_time = 0

			if add_guild_data:
				self_guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])
				if self_guild:

					if event.data['type'] == 'war' and not self.canCreateGvGEvent(self_guild, self.cur_player['login_id']):
						self.httpRedirect(params, '?fail=1&n=cant_create')

					event.data.update({
						'guild_side': self_guild['_id'],
						'guild_side_name': self_guild['name']
					})

					if event.data['type'] == 'war' and event.data['target'] == self_guild['_id']:
						self.httpRedirect(params, '?fail=1&n=your_guild')

				else:
					self.httpRedirect(params, '?fail=1&n=no_guild')

			event.data['finish_date'] = start_time + finish_time

			is_available = self.isAvailableToJoinEvent(start_time)

			if params['event_type'] == 'war' and is_available['result']:
				reach_max = self.model.events.getPlayerCreatedGuildEventsCount(self.cur_player['login_id']) >= self.sbuilder.balance.MAX_GVG_CREATED
				if reach_max:
					is_available = {
						'result': False,
					    'error': 'cant_create_more_gvg'
					}

			if is_available['result']:
				self.model.events.addNewEvent(event.data)
				self.updatePlayerDirection(self, self.cur_player['login_id'], event.data)

				event_id = self.model.events.getEventID(self.cur_player['login_id'], event.data['create_date'])
				params['__page__'] = '/events/'+str(event_id)
				self.httpRedirect(params, '?success=0')
			else:
				self.httpRedirect(params, '?fail=1&n='+is_available['error'])

	def joinEvent(self, params):

		rules = {
			'_id': {}
		}

		status = self.checkParams(params, rules)

		if status['status']:

			event = self.model.events.getEventData(params['_id'])

			if not event:
				return self.sbuilder.throwWebError(4001, 'Event not found')

			if self.cur_player['login_id'] in event['people']:
				return self.sbuilder.throwWebError(4001, 'You\'re already there' )

			if event['type'] == 'raid':
				raid = self.model.events.getRaidDungeonById(event['target'], only_max_people=True)
				if self.cur_player['login_lvl'] < event['lvl_min']:
					return self.sbuilder.throwWebError(4001, 'Your level is too low')

				if raid['max_players'] <= len(event['people']):
					return self.sbuilder.throwWebError(4001, 'Event is full of players')

			if event['type'] == 'fvf':
				if not self.cur_player['login_faction'] in event['sides']:
					return self.sbuilder.throwWebError(4001, 'This event is not for your faction')

			is_available = self.isAvailableToJoinEvent(event['start_date'])

			if is_available['result']:
				self.model.events.joinEvent(params['_id'], self.cur_player['login_id'])
				self.updatePlayerDirection(self, self.cur_player['login_id'], event)
				self.httpRedirect(params, '?success=1')
			else:
				self.httpRedirect(params, '?fail=1&n='+is_available['error'])

	def leaveEvent(self, params):
		self.model.events.leaveEvent(params['_id'], self.cur_player['login_id'])
		self.updatePlayerDirection(self, self.cur_player['login_id'])

		params['__page__'] = '/u/events'
		self.httpRedirect(params, '?success=3')

	def getEventMembers(self, params):
		# передать параметр _id евента
		event_id = params['event_id']

		returnHash = {
			"request_complete": True,
			"players" : self.model.events._getEventMembers(event_id)
		}
		
		return json.dumps(returnHash)

	# --------------------------------------------------------------------------------------------------
	# Print pages

	def printEvents(self, fields, params):

		def prettyDate(input):
			date = datetime.fromtimestamp(input)
			datef = '%d %b'
			strf = ' %H:%M'
			return date.strftime(datef+strf)

		fields.update({self.title: 'Upcoming events'})

		if self.cur_player:
			player_guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])
			if player_guild:
				player_guild = player_guild['name']

		else:
			player_guild = False

		query = {'only_active': 1}

		select = 'all'

		for filter_name in ['raids', 'wars', 'gruns', 'finished']:
			if filter_name in params:
				query.update({filter_name: 1})
				select = filter_name

		if 'finished' in params and self.cur_player:
			player_id = self.cur_player['login_id']
		else:
			player_id = None

		if self.cur_player:
			user_time = time.mktime(time.gmtime())+self.cur_player['login_utc_offset']
		else:
			user_time = time.time()

		fields.update({
			'events': self.getFormattedEvents(player_guild=player_guild, query=query, player_id=player_id),
		    'select': select,
		    'user_time': prettyDate(user_time)
		})

		return basic.defaultController._printTemplate(self, 'events_list', fields)

	def printEventDetail(self, fields, params):

		def getPlayersData(players, event):
			for player in players:
				if event['author'] == player['_id']:
					event.update({
						'author_name': player['name'],
					    'author_lead': player['stat']['lead']['current']
					})

				player.update({
					'class_name': self.balance.classes[str(player['class'])],
					'race_name':  self.balance.races[player['faction']][player['race']],
					})

				if event['status'] in ['fail', 'complete']:
					try:
						player.update({
							'performance': int(float(event['combat_log'][str(player['_id'])]['count'])/10*100)
						})
					except Exception:
						pass

			return players

		def getSidesPlayersData(players, target_guild, self_guild, event):
			target_players = []
			self_players = []

			for player in players:
				if event['author'] == player['_id']:
					event.update({
						'author_name': player['name'],
						'author_lead': player['stat']['lead']['current']
					})

				player.update({
					'class_name': self.balance.classes[str(player['class'])],
					'race_name':  self.balance.races[player['faction']][player['race']],
					})

				try:
					if 'combat_log' in event:
						str_id = str(player['_id'])
						if str_id in event['combat_log'][event['target_name']]:
							player['performance'] = int(event['combat_log'][event['target_name']][str_id]['performance'])
						elif str_id in event['combat_log'][event['guild_side_name']]:
							player['performance'] = int(event['combat_log'][event['guild_side_name']][str_id]['performance'])

				except Exception:
					player['performance'] = 0

				if player['_id'] in target_guild['people']:
					target_players.append(player)

				elif player['_id'] in self_guild['people']:
					self_players.append(player)

			return {
				'self': self_players,
			    'target': target_players
			}

		def getFactionsPlayersData(players, event):

			sides_players = [[],[],[]]

			if players:
				for player in players:
					player.update({
						'class_name': self.balance.classes[str(player['class'])],
						'race_name':  self.balance.races[player['faction']][player['race']],
						})

					sides_players[player['faction']].append(player)

			return {
				'side_1': sides_players[event['sides'][0]],
				'side_2': sides_players[event['sides'][1]]
			}

		def checkOperations(event):
			if event['start_date'] <= time.time() and not event['status'] in ['complete', 'fail']:
				event['status'] = 'progress'
				operation = 'not_allowed'
			else:
				operation = 'not_joined'

			if self.cur_player and self.cur_player['login_id'] in event['people']:
				operation = 'joined'

			if event['type'] == 'raid':
				if self.cur_player and event['lvl_min'] > self.cur_player['login_lvl']:
					operation = 'lvl'

				if len(event['people']) >= event['people_count_max']:
					operation = 'full'

			if self.cur_player and self.model.events.getPlayerActiveEventsCount(self.cur_player['login_id']) >= self.sbuilder.balance.max_events:
				if operation != 'joined':
					operation = 'not_allowed'

			if not operation in ['not_allowed', 'lvl', 'full']:
				event['can_join'] = True

			return operation

		fields.update({self.title: 'Event'})

		event = self.model.events.getEventData(params['event_UID'], full=True)
		players = self.model.events._getEventMembers(event['_id'])

		if self.cur_player and self.cur_player['login_utc_offset']:
			utc_offset = self.cur_player['login_utc_offset']
		else:
			utc_offset = self.core.server_utc_offset

		if self.cur_player:
			display = True
			if event['guild_run']:
				display = event['guild_side_name'] == self.cur_player['login_guild']

			event['guild_run_can_join'] = display

		if event['type'] == 'raid':
			raid = self.model.events.getRaidDungeonById(event['target'])
			event.update({
				'where_name': raid['name'],
				'people_count_max': raid['max_players'],
				'players': getPlayersData(players, event)
			})

			if event['status'] in ['fail', 'complete']:
				event['total_performance'] = int(float(event['result_points'])/raid['power']*100)

		elif event['type'] == 'war':
			target_guild = self.model.guilds.getGuildByID(event['target'])
			self_guild = self.model.guilds.getGuildByID(event['guild_side'])

			if self.cur_player:
				event['guild_run_can_join'] = self.cur_player['login_id'] in self_guild['people'] or self.cur_player['login_id'] in target_guild['people']

			sides = getSidesPlayersData(players, target_guild, self_guild, event)
			event.update({
				'where_img': self.core.GUILDS_AVATAR_FOLDER+target_guild['img'],
				'where_name': target_guild['name'],
			    'self_players': sides['self'],
			    'target_players': sides['target']
			})

		elif event['type'] == 'fvf':

			sides = getFactionsPlayersData(players, event)

			event.update({
				'where_name': '',
				'side_1_players': sides['side_1'],
				'side_2_players': sides['side_2']
			})

		operation = checkOperations(event)

		event.update({
			'people_count': len(event['people']),
			'start_date_f': getRelativeDate(int(event['start_date']), utc_offset - self.core.server_utc_offset),
			'finish_date_f': getRelativeDate(int(event['finish_date']), utc_offset - self.core.server_utc_offset),
			'operation': operation
		})

		fields.update({'event': event})

		tmp_name = 'event_page'
		if event['type'] == 'war':
			tmp_name = 'event_page_gvg'

		return basic.defaultController._printTemplate(self, tmp_name, fields)

	def printNewEvent(self, fields, params):

		if not self.cur_player:
			return self.sbuilder.redirect('http://tweeria.com')

		fields.update({self.title: 'Create new event'})

		raids = self.model.events.getRaidDungeons()
		available_raids = []

		for raid in raids:
			if raid['lvl_min'] <= self.cur_player['login_lvl'] <= raid['lvl_max']:
				available_raids.append(raid)

		if self.cur_player['login_utc_offset']:
			utc_offset = self.cur_player['login_utc_offset']
		else:
			utc_offset = 0

		utc_offset = utc_offset - self.core.server_utc_offset

		self_guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])
		can_create_gvg = self_guild and self.canCreateGvGEvent(self_guild, self.cur_player['login_id'])

		fields.update({
			'available_raids': available_raids,
		    'can_create_gvg': can_create_gvg,
		    'in_guild': bool(self_guild),
			'current_time': time.time(),
			'upcoming_time_f': datetime.fromtimestamp(time.time()+3600+utc_offset).strftime('%d.%m.%Y %H:%M')
		})

		return basic.defaultController._printTemplate(self, 'new_event', fields)

data = {
	'class': eventsController,
	'type': ['u', 'events'],
	'urls': ['events', 'new']
}