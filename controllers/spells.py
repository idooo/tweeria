# -*- coding: UTF-8 -*-

import basic
from functions import formatTextareaInput
import re
from misc import miscController

class spellsController(basic.defaultController):

	DIR = './ugc/'
	RE_CHECK_NAME = re.compile('^[a-zA-Z\s\-\+\']+$', re.U+re.I)

	@basic.methods
	def methods(self, params = {}):
		return {
			'type_of_form': {
				'create_spell': self.createSpellPattern,
			    'edit_spell': self.editSpell,
			    'delete_spell': self.deleteSpell
			}
		}

	@basic.printpage
	def printPage(self, page, params):
		return {
			'create_spell':     self.printSpellCreate,
		    'spell':            self.printSpellPage,
		    'edit_spell':       self.printSpellEditPage
		}

	# --------------------------------------------------------------------------------------------------
	# Misc

	def getSpell(self, params, logged_check = False, self_item_check = False):

		if logged_check and not self.cur_player:
			return {'error': 1002}

		spell = False
		if 'id' in params and params['id']:
			try:
				spell = self.model.spells.getSpellPatternByID(params['id'])
			except Exception:
				pass

		if not spell:
			return {'error': 5001}
		else:
			if not (self.cur_player and
			        ('login_admin' in self.cur_player and self.cur_player['login_admin'] or
			         'login_moderator' in self.cur_player and self.cur_player['login_moderator'] or
			         self.cur_player['login_id'] == spell['author'])
			):
				if 'reject' in spell and spell['reject']:
					if not (self.cur_player and self.cur_player['login_id'] == spell['author']):
						return {'error': 5002}

				elif not 'approve' in spell or not spell['approve']['approved']:
					return {'error': 5003}

		if self_item_check:
			can_edit = (spell['author'] == self.cur_player['login_id'] and not spell['sale_info']['active']) or 'login_admin' in self.cur_player or 'login_moderator' in self.cur_player

			if not can_edit:
				self.sbuilder.httpRedirect('../')

		return spell

	# --------------------------------------------------------------------------------------------------
	# Page methods

	def createSpellPattern(self, params):

		def getSpellActionsFormatted(params):
			spell_actions = []

			for param_number in [1,2,3]:
				param = 'action'+str(param_number)
				if param in params and params[param] != '':
					try:
						param_id = int(params[param])
						value = int(params['action1_value'][param_number-1])
					except Exception:
						param_id = False

					if param_id:
						spell_actions.append({
							'UID': param_id,
						    'value': value
						})

			_ids = []
			for action in spell_actions:
				_ids.append(action['UID'])

			active_actions = self.model.spells.getSpellActionsByID(_ids)

			result = []

			for action in spell_actions:
				for active in active_actions:
					if int(action['UID']) == active['UID']:
						result.append({
							'UID': int(action['UID']),
							'value': action['value'],
							'effect': active['effect'],
						    'power': active['power'],
						    'type': active['type'],
						    'name': active['name'],
						    'img': active['img'],
						    'effect_desc': active['effect_desc'],
						    '_misc': {
							    'restriction': active['restriction_by_lvl'],
						        'cost': active['cost_by_effect']
						    }
						})

			return result

		def isEnoughResources(params, cost):
			return self.cur_player['login_resources']['prg'] >= cost

		if self.balance.MIN_LEVEL_TO_CREATE > self.cur_player['login_lvl']:
			return self.sbuilder.throwWebError(6001)

		rules = {
			'name': {'min_length':3, 'max_length': 40, 'match': self.RE_CHECK_NAME, 'not_dublicate': {'col_spells_crafted_patterns': 'name'}},
			'desc': {'min_length':5, 'max_length': 140},
			'img': {},
			'cost': {'gt': 0, 'lt': 1000000, 'not_null': 1},
			'lvl': {'gt': 0, 'lte': int(self.cur_player['login_lvl'])},
			'action1': {},
			'keyword': {'gte': 3, 'lte': 20, 'match': self.RE_CHECK_NAME, 'not_dublicate': {'col_spells_crafted_patterns': 'keyword'}},
			'action1_value': {'not_null': 1}
		}

		status = self.checkParams(params, rules)

		if status['status']:

			cost = int(params['cost'])
			if cost < 0:
				cost = 1

			spell_pattern = self.model.craftedSpellPattern({
				'img': params['img'],
				'lvl_min': int(params['lvl']),
				'lvl_max':  self.balance.max_lvl,
				'desc': formatTextareaInput(params['desc']),
				'name': params['name'].strip().title(),
				'author': self.cur_player['login_id'],
				'keyword': params['keyword'],
			    'cost': cost
			})

			spell_pattern.data.update(self.model.misc.getImageInfo(params))

			# Проверяем эффекты
			spell_actions = getSpellActionsFormatted(params)

			cost_parch = len(spell_actions)

			if not isEnoughResources(params, cost_parch):
				self.thrownCheckError('Not enough parchment', 'There are no parchment to craft spell')

			if spell_actions:
				total_cost = 0
				for spell_action in spell_actions:
					if spell_action['_misc']['restriction']*self.cur_player['login_lvl'] < spell_action['value']:
						self.thrownCheckError('Spell effect error', 'Restriction error')
					total_cost += (spell_action['_misc']['cost']*spell_action['value'])
					del spell_action['_misc']

				spell_pattern.data.update({
					'mana_cost': total_cost,
				    'spell_actions': spell_actions
				})

			if not spell_actions or total_cost == 0:
				self.thrownCheckError('No effects', 'There are no effects')

			self.model.spells.createSpellPattern(self.cur_player['login_id'], spell_pattern.data, cost_parch)

			params.update({'operation': 'add_spell', 'operation_result': 'ok'})
			self.sbuilder.httpRedirect(self.core.loaded_data['site_address']+'/u/creation_center?creation=ok&type=spell')

		else:
			params.update({'operation': 'add_spell', 'operation_result': 'error', 'errors': status['errors']})

	def editSpell(self, params):
		spell = self.getSpell(params, logged_check=True, self_item_check=True)

		rules = {
			'desc': {'min_length':5, 'max_length': 140},
			'cost': {'gt': 0, 'lt': 1000000, 'not_null': 1}
		}

		if spell['keyword'] != params['keyword']:
			rules.update({'keyword': {'gte': 3, 'lte': 20, 'match': self.RE_CHECK_NAME, 'not_dublicate': {'col_spells_crafted_patterns': 'keyword'}}})

		if spell['name'] != params['name']:
			rules.update({'name': {'min_length':3, 'max_length': 40, 'match': self.RE_CHECK_NAME, 'not_dublicate': {'col_spells_crafted_patterns': 'name'}}})

		status = self.checkParams(params, rules)
		
		if status['status']:

			cost = int(params['cost'])
			if cost < 0:
				cost = 1

			new_spell = {
				'desc': formatTextareaInput(params['desc']),
				'name': params['name'],
				'keyword': params['keyword'],
				'cost': cost
			}

			if params['img'].strip():
				new_spell.update({"img": params["img"]})

			new_spell.update(self.model.misc.getImageInfo(params))

			old_data = {}
			for key in ['name', 'desc', 'cost', 'keyword', 'img']:
				if key in new_spell and spell[key] != new_spell[key]:
					old_data.update({key: spell[key]})

			for key in ['link', 'name', 'email', 'twitter']:
				if key in new_spell['img_info'] and new_spell['img_info'][key] and key in spell['img_info']:
					old_data.update({'Artwork: '+key: spell['img_info'][key]})

			no_need_approve = 'login_admin' in self.cur_player and self.cur_player['login_admin'] or 'login_moderator' in self.cur_player and self.cur_player['login_moderator']
			if not no_need_approve:
				no_need_approve = 'cost' in old_data and len(old_data) == 1 or not old_data
			else:
				self.model.misc.writeToLog(self.cur_player['login_id'], {
					'action': 'spell edit',
					'spell_id': spell['_id']
				})

			new_spell.update({'old_data': old_data})

			self.model.spells.updateSpellData(spell['_id'], new_spell, no_need_approve)

			self.sbuilder.httpRedirect('/u/spell?id='+params['id']+'&edit=ok')

		self.sbuilder.httpRedirect('/u/edit_spell?id='+params['id']+'&edit=fail')

	def deleteSpell(self, params):
		spell = self.getSpell(params, logged_check=True, self_item_check=True)
		self.model.spells.deleteSpell(spell, self.cur_player['login_name'])

		self.sbuilder.httpRedirect('/u/creation_center?delete=spell')

	# --------------------------------------------------------------------------------------------------
	# Print pages

	def printSpellCreate(self, fields, params):

		fields.update({self.title: 'Create new spell'})

		if not self.cur_player:
			return self.sbuilder.throwWebError(1002)

		response = self._printUGCDisablePage(fields)
		if response: return response

		if self.balance.MIN_LEVEL_TO_CREATE > self.cur_player['login_lvl']:
			return self.sbuilder.throwWebError(6001)

		if self.cur_player and self.cur_player['login_ugc_disabled']:
			return self.sbuilder.httpRedirect('/u/create')

		actions = self.model.spells.getSpellActions(self.cur_player['login_lvl'])
		fields.update({'actions': actions})

		player = self.model.players.getPlayer(self.cur_player['login_name'],'game', flags = ['no_messages'])

		if not ('agree_with_rules' in player and player['agree_with_rules']):
			return basic.defaultController._printTemplate(self, 'rules_agree_form', fields)

		fields.update({'player': player})

		if player['resources']['prg'] >= 1:
			return basic.defaultController._printTemplate(self, 'create_spell', fields)
		else:
			return basic.defaultController._printTemplate(self, 'not_enough/ne_spell', fields)

	def printSpellPage(self, fields, params):

		spell = self.getSpell(params)
		if 'error' in spell:
			return self.sbuilder.throwWebError(spell['error'], 'spell')

		author = self.model.players.getPlayerBy_ID(spell['author'], {'name':1})
		if author:
			spell.update({'author_name': author['name']})

		spell['img'] += '_fit.png'
		spell['img_info'] = miscController.formatArtworkInfo(spell['img_info'])

		fields.update(spell)

		likes = self.model.items.getItemLikes(spell['_id'])

		if 'reject' in spell:
			try:
				rejecter = self.model.players.getPlayerBy_ID(spell['reject']['rejecter_id'], {'name':1})
				fields.update({'reject_name': rejecter['name']})
			except Exception:
				fields.update({'reject_name': 'game'})

		if self.cur_player:
			fields.update({'already_have': self.model.spells.haveThisSpell(self.cur_player['login_id'], spell['name'])})

		fields.update({
			self.title: author['name']+' spell page',
			'likes': len(likes['people']),
			'is_like': self.cur_player and self.cur_player['login_id'] in likes['people'],
			'is_reported': self.cur_player and self.model.items.isReportItem(spell['_id'], self.cur_player['login_id']),
			'reasons': self.balance.getRejectReasons(self.balance.spell_reject_reasons),
			'categories': self.balance.categories
		})

		return basic.defaultController._printTemplate(self, 'spell_page', fields)

	def printSpellEditPage(self, fields, params):

		spell = self.getSpell(params, logged_check=True, self_item_check=True)

		fields.update({self.title: 'Edit '+spell['name']+' page'})
		fields.update(spell)

		return basic.defaultController._printTemplate(self, 'spell_edit_page', fields)

data = {
	'class': spellsController,
	'type': ['u'],
	'urls': ['create_spell', 'spell', 'edit_spell']
}