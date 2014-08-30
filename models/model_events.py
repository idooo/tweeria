#!/usr/bin/python
# -*- coding: utf-8 -*-

import __init__
import settings
from time import time
from settings import _obj
from bson import ObjectId

class Event(settings.BaseObj):

	data = {
		'type': 0,
	    'author': '',
	    'guild_run': False,
	    'target': 0,
	    'start_date': 0,
	    'finish_date': 0,
	    'create_date': 0,
	    'desc': '',
	    'faction': -1,
	    'lvl_min': 1,
	    'lvl_max': 60,
	    'active': False,
	    'people': [],
	    'promoted_hashtag': False,
	    'activity': [],
	    'status': ''  # active — скоро случится; progress — идет сейчас; complete — завершено удачно; fail — провалено
	}

class ModelEvents():

	col_events = settings.database.cols['col_events']
	col_dungeons = settings.database.cols['col_dungeons']
	col_players = settings.database.cols['players']

	def __init__(self, connection):
		self.mongo = connection
		self.balance = settings.balance

	# GET

	def getRaidDungeons(self, lvl = False):
		record = {'type': 1}
		if lvl:
			record.update({'lvl_min': {'$lte': lvl}, 'lvl_max': {'$gte': lvl}})

		return self.mongo.getu(self.col_dungeons, record, sort={'lvl_min':-1})

	def getRaidDungeonById(self, uid, only_max_people = False):
		fields = {}
		if only_max_people:
			fields = {'max_players': 1}

		return self.mongo.find(self.col_dungeons, {'UID': uid}, fields)

	def getEvents(self, query={}, player_id=None, guild='', fields = {}):

		datedelta = 86400
		sort = {'start_date': 1}

		if 'finished' in query:
			search = {'$or': [{'status':'complete'}, {'status': 'fail'}], 'finish_date': {'$gte': time()-datedelta }}
			sort = {'finish_date': -1}
		elif 'only_active' in query:
			search = {'status': 'active'}
		elif 'upcoming' in query:
			search = {'$or': [{'status':'active'}, {'status': 'progress'}]}
		else:
			search = {}

		if 'raids' in query:
			search.update({'type': 'raid'})

		if 'wars' in query:
			search.update({'type': 'war'})

		if 'gruns' in query:
			if guild:
				search.update({'guild_run': True, 'guild_side_name': guild})

		if player_id:
			search.update({'people':{'$all':[player_id]}})

		return self.mongo.getu(self.col_events, search=search, sort=sort, fields=fields)

	def getEventData(self, event_id, full = False):
		if not isinstance(event_id, ObjectId):
			event_id = ObjectId(event_id)

		if full:
			fields = {}
		else:
			fields = {
				'target':1,
			    'type': 1,
				'people': 1,
				'start_date':1,
				'finish_date':1,
				'lvl_min':1,
			    'sides':1,
			    'position':1,
			    'guild_side_name':1,
			    'target_name':1
			}

		return self.mongo.find(self.col_events, {'_id': event_id}, fields)

	def _getEventMembers(self, event_id):
		try:
			event = self.mongo.find(self.col_events, {'_id': ObjectId(event_id)}, {'people': 1, 'author': 1})
		except Exception:
			event = None

		if event:
			event_members = event['people']
			players = self.mongo.findSomeIDs(self.col_players, event_members, sort={'lvl':1}, fields={
				'name': 1,
				'class': 1,
				'lvl':1,
				'avatar': 1,
				'race': 1,
				'faction': 1,
			    '_id': 1,
			    '_guild_name':1,
			    'stat.lead.current':1
			})

			return players

		else:
			return False

	def getJustFinishedEvents(self):
		return self.mongo.getu(self.col_events, {
			'$and': [
				{'status': {'$ne': 'complete'}},
				{'status': {'$ne': 'fail'}},
			    {'finish_date': {'$lte': time()}}
			]
		})

	def getEventID(self, author_id, create_date):
		event = self.mongo.find(self.col_events, {'author': author_id, 'create_date':create_date}, {'_id':1})
		if event:
			return event['_id']
		else:
			return False

	def getPlayersRawEvents(self, player_id):
		return self.mongo.getu(self.col_events, {'people':{'$all':[player_id]}, 'start_date': {'$gte': time()}}, sort={'start_date': 1}, limit=1)

	def getGvGEvents(self, player_id = False, fields = {}):
		if player_id:
			return self.mongo.getu(self.col_events, {'people':{'$all':[player_id]}, 'type': 'war'}, fields = fields)
		else:
			return self.mongo.getu(self.col_events, {'type': 'war'}, fields = fields)

	# ADD

	def addNewEvent(self, event):
		if '_id' in event:
			del event['_id']

		self.mongo.insert(self.col_events, event)

	def updateEvent(self, event_id, event_info):
		self.mongo.update(self.col_events, {'_id': event_id}, event_info)

	# MISC

	def removeGvGEventsByGuild(self, guild_id):
		self.mongo.remove(self.col_events, {
			'$or': [ {'guild_side': guild_id}, {'target': guild_id} ]
		})

	def joinEvent(self, event_id, player_id):
		self.mongo.raw_update(self.col_events, {'_id': _obj(event_id).id}, {'$push':{'people': player_id}})

	def leaveEvent(self, event_id, creator_id):
		if not isinstance(event_id, ObjectId):
			event_id = ObjectId(event_id)

		event = self.mongo.find(self.col_events, {'_id': event_id}, {'people': 1, 'author': 1})

		if event:
			# если автор хочет покинуть событие...
			if 'author' in event and event['author'] == creator_id:

				# ... если он один, то просто удалим эвекнт
				if len(event['people']) == 1:
					self.mongo.remove(self.col_events, {'_id': event_id})

				# ... иначе, назначим первого попавшегося новым автором
				else:
					for player_id in event['people']:
						if player_id != creator_id:
							self.mongo.raw_update(self.col_events, {'_id': event_id}, {'$pull':{'people': creator_id}, '$set': {'author': player_id} })

			else:
				for player in event['people']:
					if player == creator_id:
						self.mongo.raw_update(self.col_events, {'_id': event_id}, {'$pull':{'people': creator_id}})

	def markJustFinishedAsFinished(self, events):
		for event in events:
			try:
				record = {
					'status': event['status'],
					'combat_log': event['combat']
				}

				if event['type'] == 'raid':
					record.update({'result_points': event['result_points']})
				elif event['type'] == 'war':
					record.update({
						'winner': event['winner'],
					    'winner_id': event['winner_id']
					})
			except Exception:

				if not 'status' in event:
					event['status'] = 'fail'

				if not 'combat' in event:
					event['combat'] = []

				record = {
					'status': event['status'],
					'combat_log': event['combat']
				}

			self.mongo.update(self.col_events, {'_id': event['_id']}, record)

	def getEventInThisTime(self, start_time, player_id):
		event = self.mongo.find(self.col_events, {'start_date':{'$lte':start_time}, 'finish_date':{'$gt':start_time}, 'people':{'$all':[player_id]}}, {'_id':1})
		if event:
			return True

		return False

	def getGuildEventsByID(self, guild_smth, limit = 0, fields = {}):
		if isinstance(guild_smth, ObjectId):
			query = [ { 'target': guild_smth } , { 'guild_side' : guild_smth } ]
		else:
			query = [ { 'target_name': guild_smth } , { 'guild_side_name' : guild_smth } ]

		return self.mongo.getu(
			self.col_events,
			{
				'$or' : query,
			    'status' : {'$in': ['active', 'progress']}
			},
			fields=fields,
			sort={'start_date': 1},
			limit=limit
		)

	def getFactionEventsByID(self, faction_id, limit = 0, fields = {}):
		return self.mongo.getu(
			self.col_events,
				{
				'sides' : {'$all': [faction_id]},
				'status' : {'$in': ['active', 'progress']}
			},
			fields=fields,
			sort={'start_date': 1},
			limit=limit
		)

	def getPlayerActiveEventsCount(self, player_id):
		return self.mongo.count(self.col_events, { '$or' : [ { 'status': 'active' } , { 'status' : 'progress' } ], 'people':{'$all':[player_id]}})

	def getPlayerCreatedGuildEventsCount(self, player_id):
		return self.mongo.count(self.col_events, { 'type': 'war', '$or' : [ { 'status': 'active' } , { 'status' : 'progress' } ], 'author': player_id})
