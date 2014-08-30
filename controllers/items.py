# -*- coding: UTF-8 -*-

import basic, os, shutil
import re
from functions import formatTextareaInput, prettyItemBonus
from misc import miscController

class itemsController(basic.defaultController):

	DIR = './ugc/'
	RE_CHECK_NAME = re.compile('^[a-zA-Z\s\-\+\']+$', re.U+re.I)

	@basic.methods
	def methods(self, params = {}):
		return {
			'type_of_form': {
				'add_item': self.addNewItem,
			    'edit_item': self.editItem,
			    'delete_item': self.deleteItem
			}
		}

	@basic.printpage
	def printPage(self, page, params):
		return {
		    'craft_item':       self.printCraftItemPage,
		    'item':             self.printItemPage,
		    'edit_item':        self.printItemEditPage
		}

	# --------------------------------------------------------------------------------------------------
	# Misc

	def getItem(self, params, logged_check = False, self_item_check = False):

		if logged_check and not self.cur_player:
			return {'error': 1002}

		item = False
		if 'id' in params and params['id']:
			try:
				item = self.model.items.getCraftedItem(params['id'])
			except Exception:
				pass

		if not item:
			return{'error': 5001}
		else:
			if not (self.cur_player and
			        ('login_admin' in self.cur_player and self.cur_player['login_admin'] or
			         'login_moderator' in self.cur_player and self.cur_player['login_moderator'] or
			         self.cur_player['login_id'] == item['author'])
			):

				if 'reject' in item and item['reject']:
					if not (self.cur_player and self.cur_player['login_id'] == item['author']):
						return {'error': 5002}

				elif not 'approve' in item or not item['approve']['approved']:
					return {'error': 5003}

		if self_item_check:
			can_edit = (item['author'] == self.cur_player['login_id'] and not item['sale_info']['active']) or 'login_admin' in self.cur_player or 'login_moderator' in self.cur_player

			if not can_edit:
				self.sbuilder.httpRedirect('../')

		return item

	def getPlayerBuyedItems(self, _id):
		return self.model.items.getPlayerBuyedItems(_id)

	# --------------------------------------------------------------------------------------------------
	# Page methods

	def addNewItem(self, params):

		def isEnoughResources(params):
			is_enough = self.cur_player['login_resources']['ore'] >= self.balance.ORE_COST_PER_ITEM
			if 'rune' in params:
				is_enough = is_enough and self.cur_player['login_resources']['eore'] >= int(params['rune'])

			return is_enough

		if self.balance.MIN_LEVEL_TO_CREATE > self.cur_player['login_lvl']:
			return self.sbuilder.throwWebError(6001)

		try:
			min_cost = self.balance.getItemMinCost({'lvl': int(params['level'])})
		except Exception:
			min_cost = self.balance.getItemMinCost({'lvl': self.cur_player['login_lvl']})

		rules = {
			'name': {'min_length':3, 'max_length': 40, 'match': self.RE_CHECK_NAME, 'not_dublicate': {'col_crafted': 'name'}},
			'desc': {'min_length':4, 'max_length': 1000},
			'img': {'not_null': 1},
		    'level': {'gt': 0, 'not_null':1, 'int': 1},
		    'item_type': {'not_null':1},
			'cost': {'int': 1, 'gt': min_cost-1, 'lt': 1000000 ,'not_null': 1}
		}

		status = self.checkParams(params, rules)

		if status['status']:

			if isEnoughResources(params):

				crafted_item = self.model.crafted_item()

				original_file = self.sbuilder.core_settings.APP_DIR+self.sbuilder.core_settings.TEMPLATES_FOLDER+params['img']
				if os.path.exists(original_file):
					dest_file_name = original_file.split("/")[-1]
					dest_file = self.sbuilder.core_settings.APP_DIR+self.sbuilder.core_settings.TEMPLATES_FOLDER+self.sbuilder.core_settings.IMAGE_BUFFER_FOLDER+dest_file_name
					shutil.copyfile(original_file,dest_file)
					os.unlink(original_file)
					params['img'] = self.sbuilder.core_settings.RESIZED_IMG_PATH+'items/'+dest_file_name
				else:
					params['img'] = ""

				cost = int(params['cost'])
				if cost < min_cost-1:
					cost = min_cost

				crafted_item.data.update({
					'name': params['name'].strip().title(),
					'desc': formatTextareaInput(params['desc']),
					'author': self.cur_player['login_id'],
					'img': params['img'],
					'cost': cost,
					'lvl_min': int(params['level']),
					'lvl_max': self.balance.max_lvl,
				})

				crafted_item.data.update(self.model.misc.getImageInfo(params))

				item_type_data = params['item_type'].split(':')
				if len(item_type_data) > 1:
					crafted_item.data['type'] = int(item_type_data[0])
					crafted_item.data['view'] = item_type_data[1]
				else:
					crafted_item.data['type'] = int(params['item_type'])
					crafted_item.data['view'] = self.balance.item_types[int(params['item_type'])]

				bonus = {}

				total_max_bonus = int(self.cur_player['login_lvl'])*2+10
				total_value = 0

				for key in ['str', 'dex', 'int', 'luck', 'DEF', 'DMG', 'HP', 'MP']:
					try:
						value = int(params[key])
					except Exception:
						value = 0

					if value != 0:
						total_value += value
						bonus.update({key: value})

				if total_value <= total_max_bonus:
					crafted_item.data.update({'bonus': bonus})

					if 'rune' in params:
						eore_added = int(params['rune'])
					else:
						eore_added = False

					self.model.items.addCraftedItem(self.cur_player['login_id'], crafted_item.data, eore_added)

					params.update({'operation': 'add_item', 'operation_result': 'ok'})

					self.sbuilder.httpRedirect(self.core.loaded_data['site_address']+'/u/creation_center?creation=ok&type=item')

				else:
					params.update({'operation': 'add_item', 'operation_result': 'error', 'errors': status['errors']})

			else:
				params.update({'operation': 'add_item', 'operation_result': 'error', 'errors': status['errors']})

		else:
			params.update({'operation': 'add_item', 'operation_result': 'error', 'errors': status['errors']})

	def editItem(self, params):
		item = self.getItem(params, logged_check=True, self_item_check=True)

		min_cost = self.balance.getItemMinCost({'lvl': item['lvl_min']})

		rules = {
			'desc': {'min_length':4, 'max_length': 1000},
			'item_type': {'not_null':1},
			'cost': {'int': 1, 'gt': min_cost-1, 'lt': 1000000 ,'not_null': 1}
		}

		if item['name'] != params['name']:
			rules.update({'name': {'min_length':3, 'max_length': 40, 'match': self.RE_CHECK_NAME, 'not_dublicate': {'col_crafted': 'name'}}})

		status = self.checkParams(params, rules)

		if status['status']:

			new_item_data = {}

			item_type_data = params['item_type'].split(':')
			if len(item_type_data) > 1:
				new_item_data['type'] = int(item_type_data[0])
				new_item_data['view'] = item_type_data[1]
			else:
				new_item_data['type'] = int(params['item_type'])
				new_item_data['view'] = self.balance.item_types[int(params['item_type'])]

			cost = int(params['cost'])
			if cost < min_cost-1:
				cost = min_cost

			try:
				original_file = self.sbuilder.core_settings.APP_DIR+self.sbuilder.core_settings.TEMPLATES_FOLDER+params['img']
				if os.path.exists(original_file):
					dest_file_name = original_file.split("/")[-1]
					dest_file = self.sbuilder.core_settings.APP_DIR+self.sbuilder.core_settings.TEMPLATES_FOLDER+self.sbuilder.core_settings.IMAGE_BUFFER_FOLDER+dest_file_name
					shutil.copyfile(original_file,dest_file)
					os.unlink(original_file)
					new_item_data.update({'img':self.sbuilder.core_settings.RESIZED_IMG_PATH+'items/'+dest_file_name})

			except Exception:
				pass

			new_item_data.update({
				'name': params['name'].strip(),
				'desc': formatTextareaInput(params['desc']),
				'cost': cost
			})

			new_item_data.update(self.model.misc.getImageInfo(params))

			old_data = {}
			for key in ['name', 'desc', 'cost', 'type', 'img']:
				if key in new_item_data and new_item_data[key] != item[key]:
					old_data.update({key: item[key]})

			for key in ['link', 'name', 'email', 'twitter']:
				if key in new_item_data['img_info'] and new_item_data['img_info'][key] and key in item['img_info']:
					old_data.update({'Artwork: '+key: item['img_info'][key]})

			no_need_approve = 'login_admin' in self.cur_player and self.cur_player['login_admin'] or 'login_moderator' in self.cur_player and self.cur_player['login_moderator']
			if not no_need_approve:
				no_need_approve = 'cost' in old_data and len(old_data) == 1 or not old_data
			else:
				self.model.misc.writeToLog(self.cur_player['login_id'], {
					'action': 'item edit',
				    'item_id': item['_id']
				})

			new_item_data.update({'old_data': old_data})

			self.model.items.updateItemData(item['_id'], new_item_data, no_need_approve)

			self.sbuilder.httpRedirect('/u/item?id='+params['id']+'&edit=ok')

		self.sbuilder.httpRedirect('/u/edit_item?id='+params['id']+'&edit=fail')

	def deleteItem(self, params):
		item = self.getItem(params, logged_check=True, self_item_check=True)
		self.model.items.deleteItem(item, self.cur_player['login_name'])

		self.sbuilder.httpRedirect('/u/creation_center?delete=item')

	# --------------------------------------------------------------------------------------------------
	# Print pages

	def printCraftItemPage(self, fields, params):

		fields.update({self.title: 'Craft new item'})

		if not self.cur_player:
			return self.sbuilder.throwWebError(1002)

		response = self._printUGCDisablePage(fields)
		if response: return response

		if self.balance.MIN_LEVEL_TO_CREATE > self.cur_player['login_lvl']:
			return self.sbuilder.throwWebError(6001)

		if self.cur_player and self.cur_player['login_ugc_disabled']:
			return self.sbuilder.httpRedirect('/u/create')

		player = self.model.players.getPlayer(self.cur_player['login_name'],'game', flags = ['no_messages'])

		if not ('agree_with_rules' in player and player['agree_with_rules']):
			return basic.defaultController._printTemplate(self, 'rules_agree_form', fields)

		fields.update({
			'player': player,
		    'max_stat_level': self.balance.getMaxStatsForItemCreate(player['lvl'])
		})

		if player['resources']['ore'] >= self.sbuilder.balance.ORE_COST_PER_ITEM:
			return basic.defaultController._printTemplate(self, 'create_item', fields)
		else:
			return basic.defaultController._printTemplate(self, 'not_enough/ne_item', fields)

	def printItemPage(self, fields, params):

		item = self.getItem(params)
		if 'error' in item:
			return self.sbuilder.throwWebError(item['error'], 'item')

		item.update(prettyItemBonus(item, self.balance.stats_name))

		author = self.model.players.getPlayerBy_ID(item['author'], {'name':1})
		if author:
			item.update({'author_name': author['name']})

		item['img'] = '/'+item['img']+'_fit.png'

		item['img_info'] = miscController.formatArtworkInfo(item['img_info'])

		fields.update(item)

		likes = self.model.items.getItemLikes(item['_id'])

		if 'reject' in item:
			try:
				rejecter = self.model.players.getPlayerBy_ID(item['reject']['rejecter_id'], {'name':1})
				fields.update({'reject_name': rejecter['name']})
			except Exception:
				fields.update({'reject_name': 'game'})

		if self.cur_player:
			fields.update({
				'inventory_count': self.model.items.getInventoryCount(self.cur_player['login_id']),
			    'inventory_max': self.sbuilder.balance.INVENTORY_SIZE
			})

		fields.update({
			self.title: item['name']+' page',
		    'likes': len(likes['people']),
		    'is_like': self.cur_player and self.cur_player['login_id'] in likes['people'],
		    'is_reported': self.cur_player and self.model.items.isReportItem(item['_id'], self.cur_player['login_id']),
		    'reasons': self.balance.getRejectReasons(self.balance.item_reject_reasons),
		    'categories': self.balance.categories
		})

		return basic.defaultController._printTemplate(self, 'item_page', fields)

	def printItemEditPage(self, fields, params):

		item = self.getItem(params, logged_check=True, self_item_check=True)

		item.update(prettyItemBonus(item, self.balance.stats_name))

		if item['type'] == 1:
			item['type'] = '1:'+item['view']
		else:
			item['type'] = str(item['type'])

		fields.update({self.title: 'Edit '+item['name']+' page'})
		fields.update(item)


		return basic.defaultController._printTemplate(self, 'item_edit_page', fields)

data = {
	'class': itemsController,
	'type': ['u'],
	'urls': ['market', 'craft_item', 'my_items', 'waiting_items', 'item', 'edit_item']
}