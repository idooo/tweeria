#!/usr/bin/python
# -*- coding: utf-8 -*-

import __init__
import settings
from time import time
from bson import ObjectId
from sets import Set

class CraftedSpellPattern(settings.BaseObj):

	data = {
		'img': '',
		'pvp': 0,
		'lvl_min': 0,
		'lvl_max': 0,
		'cost': 0,
	    'mana_cost': 0,
		'desc': '',
		'name': '',
		'author': 0,
		'sale_info': {
			'sell_times': 0,
			'total_earn': 0,
			'active': False
		},
		'active': False,
	    'keyword':'',
	    'spell_actions': [],
	    'create_time' : 0,
	    'approve': {
		    'approved': False,
		    'time': 0,
		    'approver_id': ''
	    }
	}

class SpellBook():

	data = {
		'player_id': 0,
	    'spells': []
	}

class ModelSpells():

	col_spells = settings.database.cols['col_spells']
	col_spellbooks = settings.database.cols['col_spellbooks']
	col_players = settings.database.cols['players']
	col_actions = settings.database.cols['col_spells_actions']
	col_spells_created = settings.database.cols['col_spells_created']
	col_spells_pattern = settings.database.cols['col_spells_crafted_patterns']
	col_beta_spells = settings.database.cols['col_beta_spells']
	col_items_deleted = settings.database.cols['col_items_deleted']

	def __init__(self, connection):
		self.mongo = connection
		self.balance = settings.balance

	# GET

	def getAvailableStandartSpells(self, player_lvl):
		return self.mongo.getu(self.col_spells, {'lvl_min':{'$lte': int(player_lvl)}, 'lvl_max': {'$gte': int(player_lvl)}})

	def getSpellBook(self, player_id, _fields = {}):
		return self.mongo.find(self.col_spellbooks, {'player_id': player_id}, _fields)

	def getSpellActions(self, lvl = 100):
		return self.mongo.getu(self.col_actions, {'lvl_min':{'$lte': lvl}})

	def getSpellPatternByID(self, _id):
		if not isinstance(_id, ObjectId):
			_id = ObjectId(_id)

		return self.mongo.find(self.col_spells_pattern, {'_id': _id})

	def getSpellPatternsByIDs(self, _ids, fields = {}):
		query = {'_id': {'$in': list(_ids)}}
		return self.mongo.getu(self.col_spells_pattern, query, fields)

	def getUserSpellByID(self, _id):
		return self.mongo.find(self.col_spells_created, {'_id':ObjectId(_id)})

	def getSpellActionsByID(self, uids):
		actions = Set()
		for uid in uids:
			actions.add(int(uid))

		return self.mongo.getu(self.col_actions, {'UID': {'$in': list(actions)}})

	def getSpellsPattern(self, _id, fields = {}):
		return self.mongo.getu(self.col_spells_pattern, {'author': _id}, fields=fields)

	def getActiveSpellsPattern(self, _id, fields = {}):
		return self.mongo.getu(self.col_spells_pattern, {'author': _id, 'sale_info.active': True}, fields=fields)

	def getWaitingSpells(self, user_id = False, approved = False, rejected = False, skip = 0, limit = 0, sorting={'create_time': 1}):
		if rejected:
			record = {'reject': {'$exists': rejected}}
		else:
			record = {
				'approve.approved': approved,
				'reject': {'$exists': rejected}
			}

		if user_id:
			record.update({'author': user_id})

		return self.mongo.getu(self.col_spells_pattern, record, skip=skip, limit=limit, sort=sorting)

	def getApprovedSpells(self, user_id = False):
		return self.getWaitingSpells(user_id, True)

	def getSellingSpells(self):
		created_spells = self.mongo.getu(self.col_spells_pattern, {'approve.approved': True, 'sale_info.active': True})
		reselling_spells = self.mongo.getu(self.col_spells_created, {'sell': True})
		return created_spells + reselling_spells

	def getBuyedSpells(self, player_id):
		return self.mongo.getu(self.col_spells_created, {'player_id': player_id})

	def getSpellsByIds(self, _ids):
		query_default = []
		query_created = []

		spells_default = []
		spells_created = []

		for _id in _ids:
			if isinstance(_id, ObjectId):
				query_created.append({'_id': _id})
			else:
				query_default.append({'UID': _id})

		if query_default:
			spells_default = self.mongo.getu(self.col_spells, search={ "$or" : query_default})

		if query_created:
			spells_created = self.mongo.getu(self.col_spells_created, search={ "$or" : query_created})

		return spells_created+spells_default

	def getAllSellingCraftedPatterns(self, skip = 0, limit = 0, query = {}, sort_query={}):
		if not sort_query:
			sort_query.update({'approve.time': -1})

		query.update({'sale_info.active': True})
		return self.mongo.getu(
			self.col_spells_pattern,
			search = query,
			skip = skip,
			limit = limit,
			sort = sort_query
		)

	def getCountActiveSpells(self, player_id):
		spellbook = self.getSpellBook(player_id, {'spells': 1})

		if spellbook:
			spells = Set()
			for spell in spellbook['spells']:
				spells.add(spell['spell_id'])

			return len(spells)
		else:
			return 10000

	def getAllSellingSpellsCount(self, search):

		search.update({'sale_info.active': True})

		return self.mongo.count(
			self.col_spells_pattern,
			search=search,
		)

	def getApprovedSpellsCount(self):
		return self.mongo.count(self.col_spells_pattern, {
			'approve.approved': False,
			'reject': {'$exists': False}
		})

	# GET ALL

	def getALLSpellsCreated(self, limit = 0):
		return self.mongo.getu(self.col_spells_created, limit=limit)

	def getALLSpells(self, limit = 0):
		return self.mongo.getu(self.col_spells, limit=limit)

	def getALLSpellbooks(self, limit = 0):
		return self.mongo.getu(self.col_spellbooks, limit=limit)

	def getPlayerSpells(self, player_id):
		return self.mongo.getu(self.col_spells_created, {'player_id': player_id}, {'name':1})

	def haveThisSpell(self, player_id, name):
		if self.mongo.find(self.col_spells_created, {'player_id': player_id, 'name': name}, {'_id':1}):
			return True
		else:
			return False


	# MISC

	def deleteSpell(self, spell, deleted_person = '-'):
		if spell:
			self.mongo.remove(self.col_spells_pattern, {'_id': spell['_id']})
			if '_id' in spell:
				del spell['_id']
			spell.update({
				'deleted_type': 'spell',
				'deleted_time': time(),
				'deleted_person': deleted_person
			})
			self.mongo.insert(self.col_items_deleted, spell)

	def updateSpellData(self, _id, data, no_need_approve):
		if isinstance(_id, str):
			_id = ObjectId(_id)

		if no_need_approve:
			record = {'$set': data}
		else:
			data.update({
				'sale_info.active': False,
				'approve': {
					'approved': False,
					'time': 0,
					'approver_id': ''
				},
			})

			record = {'$set': data, '$unset': {'reject': True}}

		self.mongo.raw_update(self.col_spells_pattern, {'_id': _id}, record)

	def moveToBook(self, player_id, spell_id, player_lvl = 1, builtin = False):
		spellbook = self.getSpellBook(player_id)
		result = False

		if spellbook:

			spells = Set()
			for active_spell in spellbook['spells']:
				if 'spell_UID' in active_spell:
					spells.add(active_spell['spell_UID'])
				else:
					spells.add(active_spell['spell_id'])

			need_change = len(spells) != len(spellbook['spells'])

			if builtin:
				spell = self.mongo.find(self.col_spells, {'UID': int(spell_id)})
			else:
				spell = self.mongo.find(self.col_spells_created, {'_id': ObjectId(spell_id), 'player_id': player_id })

			if spell and spell['lvl_min'] <= player_lvl:
				if 'UID' in spell:
					new_spell_id = spell['UID']
				else:
					new_spell_id = spell['_id']

				if not new_spell_id in spells:
					spells.add(new_spell_id)
					only_append = True
				else:
					only_append = False

				if need_change:
					new_spells = []
					for spell_id in spells:
						new_spells.append({'spell_id': spell_id})

					self.mongo.update(self.col_spellbooks, {'_id': spellbook['_id']}, {'spells': new_spells})
				else:
					if only_append:
						self.mongo.raw_update(self.col_spellbooks, {'_id': spellbook['_id']}, {'$push': {'spells': {'spell_id': new_spell_id}}})

				return only_append

		return result

	def moveFromBook(self, player_id, spell_id, builtin = False):
		spellbook = self.getSpellBook(player_id)

		if not builtin:
			spell_id = ObjectId(spell_id)
		else:
			spell_id = int(spell_id)

		if spellbook:
			spells = Set()
			for active_spell in spellbook['spells']:
				if 'spell_UID' in active_spell:
					spells.add(active_spell['spell_UID'])
				else:
					spells.add(active_spell['spell_id'])

			need_change = len(spells) != len(spellbook['spells'])

			if spell_id in spells:
				spells.remove(spell_id)
				need_change = True

			if need_change:
				new_spells = []
				for spell_id in spells:
					new_spells.append({'spell_id': spell_id})

				self.mongo.raw_update(self.col_spellbooks, {'_id': spellbook['_id']}, {'$set':{'spells': new_spells}})

	def createSpellPattern(self, player_id, spell, cost):
		if '_id' in spell:
			del spell['_id']

		spell.update({'create_time': time()})

		player_update = {'resources.prg': -cost}

		self.mongo.insert(self.col_spells_pattern, spell)
		self.mongo.updateInc(self.col_players, {'_id': player_id}, player_update )

	def approveSpellPattern(self, _id, approver_id = '', beta = False, tag = ''):

		object_id = ObjectId(_id)
		self.mongo.raw_update(self.col_spells_pattern, {'_id': object_id}, {
			'$unset': {'reject': 1, 'from_beta': 1},
			'$set': {
				'sale_info.active': True,
				'approve': {
					'approved': True,
					'time': time(),
					'approver_id': approver_id
				},
				'img_info.verified': True,
				'tag': tag
			}
		})

		spell = self.mongo.find(self.col_spells_pattern, {'_id': object_id}, {'_id':0, 'sale_info':0, 'approve':0})
		spell.update({'player_id': spell['author'], 'sell': False, 'copy': True})
		self.mongo.insert(self.col_spells_created, spell)

	def toMarket(self, spell_id, cost):
		object_id = ObjectId(spell_id)
		self.mongo.update(self.col_spells_pattern, {'_id': object_id}, {'cost': cost, 'sale_info.active': True})

	def rejectSpellPattern(self, _id, rejecter_id, reason = ''):

		object_id = ObjectId(_id)
		self.mongo.raw_update(self.col_spells_pattern, {'_id': object_id}, {
			'$unset': {'approve': 1},
			'$set': {
				'sale_info.active': False,
				'reject': {
					'rejected': True,
					'time': time(),
					'rejecter_id': rejecter_id,
					'reason': reason
				},
			}
		})

	def takeSpellCopyToPlayer(self, pattern_id, player_id = 'author'):
		pattern = self.mongo.find(self.col_spells_pattern, {'_id': ObjectId(pattern_id)}, {'_id':0, 'sale_info': 0, 'approve':0, 'cost': 0})
		if pattern:
			if player_id == 'author':
				pattern.update({'player_id': pattern['author']})
			else:
				pattern.update({'player_id': player_id})

			self.mongo.insert(self.col_spells_created, pattern)

	def cancelSelling(self, player_id, spell):
		if 'sell' in spell and spell['sell']:
			self.mongo.update(self.col_spells_created, {'_id': spell['_id']}, {'player_id': player_id, 'sell': False})
		else:
			self.mongo.update(self.col_spells_pattern, {'_id': spell['_id']}, {'sale_info.active': False})

	def buySpellPattern(self, player_id, spell):
		self.mongo.updateInc(self.col_players, {'_id': player_id}, {'resources.gold': -spell['cost']})
		self.mongo.updateInc(self.col_players, {'_id': spell['author']}, {'resources.gold': spell['cost']})

		self.mongo.updateInc(self.col_spells_pattern, {'_id': spell['_id']}, {'sale_info.sell_times': 1, 'sale_info.total_earn': spell['cost'] })

		del spell['_id'], spell['sale_info'], spell['approve']
		spell.update({'player_id': player_id, 'sell': False, 'copy': True})

		self.mongo.insert(self.col_spells_created, spell)

	def buyCopySpell(self, player_id, spell):
		self.mongo.updateInc(self.col_players, {'_id': player_id}, {'resources.gold': -spell['cost']})
		self.mongo.updateInc(self.col_players, {'_id': spell['player_id']}, {'resources.gold': spell['cost']})

		self.mongo.update(self.col_spells_created, {'_id': spell['_id']}, {'player_id': player_id, 'sell': False})

	def unpackBetaSpells(self, player):

		if player:
			beta_spells = self.mongo.getu(self.col_beta_spells, {'author_beta': player['user_id']}, {'_id': 0})
			if beta_spells:
				for spell in beta_spells:
					spell.update({
						'author': player['_id'],
						'from_beta': True
					})
					self.mongo.insert(self.col_spells_pattern, spell)

				items_to_approve = self.mongo.getu(self.col_spells_pattern, {'author': player['_id'], 'from_beta': True})
				for item in items_to_approve:
					self.approveSpellPattern(item['_id'], 'game')


	def updateSpell(self, spell_id, data):
		if not isinstance(spell_id, ObjectId):
			spell_id = ObjectId(spell_id)

		self.mongo.update(self.col_spells_pattern, {'_id': spell_id}, data)