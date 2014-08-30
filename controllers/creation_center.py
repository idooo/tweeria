# -*- coding: UTF-8 -*-

import basic
from functions import prettyItemBonus, formatTextareaInput
import re
from sets import Set
from misc import miscController
import time

class creationCenterController(basic.defaultController):

	DIR = './ugc/'
	RE_CHECK_NAME = re.compile('^[a-zA-Z0-9\s\-\+\']+$', re.U+re.I)

	@basic.printpage
	def printPage(self, page, params):

		return {
			'create_artwork': self.printCreatingArtwork,
		    'creation_center': self.printCreationCenter,
		    'create': self.printSelectCreationForm,
		    'artwork': self.printArtworkPage,
		    'edit_artwork': self.printArtworkEditPage,
		    'request': self.printRequestForm
		}

	@basic.methods
	def methods(self, params = {}):
		return {
			'type_of_form': {
				'cancel_sell': self.cancelSellingCraftedItem,
				'cancel_spell_sell': self.cancelSellingSpellPattern,
				'cancel_artwork_sell': self.cancelSellingArtwork,
			    'create_artwork': self.createArtwork,
			    'put_crafted_item_to_market': self.putCraftedItemToMarket,
			    'put_crafted_pattern_to_market': self.putSpellPatternToMarket,
			    'put_artwork_to_market': self.putArtworkToMarket,
			    'edit_artwork': self.editArtwork,
			    'delete_artwork': self.deleteArtwork,
			    'request_auth': self.requestAuth
			}
		}

	# --------------------------------------------------------------------------------------------------
	# Misc

	def getArtwork(self, params, logged_check = False, self_item_check = False, ever_default=False):

		if logged_check and not self.cur_player:
			return {'error': 1002}

		artwork = False
		if 'id' in params and params['id']:
			artwork = self.model.misc.getArtworkById(params['id'])
			if not artwork:
				artwork = self.model.misc.getBuiltInArtworkByUID(params['id'])

		if not artwork:
			return {'error': 5001}
		else:
			if not (self.cur_player and
			        ('login_admin' in self.cur_player and self.cur_player['login_admin'] or
			         'login_moderator' in self.cur_player and self.cur_player['login_moderator'] or
			         self.cur_player['login_id'] == artwork['author'])
			):
				if 'reject' in artwork and artwork['reject']:
					if not (self.cur_player and self.cur_player['login_id'] == artwork['author']):
						return {'error': 5002}

				elif not 'approve' in artwork or not artwork['approve']['approved']:
					return {'error': 5003}


		if self_item_check:
			can_edit = (artwork['author'] == self.cur_player['login_id'] and not artwork['sale_info']['active']) or 'login_admin' in self.cur_player or 'login_moderator' in self.cur_player

			if not can_edit:
				self.sbuilder.httpRedirect('../')

		return artwork

	# --------------------------------------------------------------------------------------------------
	# Page methods

	def putCraftedItemToMarket(self, params):
		try:
			if '_id' in params and int(params['cost'])> 0:
				self.model.items.toMarket(params['_id'], int(params['cost']))
		except Exception:
			pass

		self.sbuilder.httpRedirect(params['__page__'])

	def putSpellPatternToMarket(self, params):
		try:
			if '_id' in params and int(params['cost'])> 0:
				self.model.spells.toMarket(params['_id'], int(params['cost'])  )
		except Exception:
			pass

		self.sbuilder.httpRedirect(params['__page__'])

	def putArtworkToMarket(self, params):
		try:
			if '_id' in params and int(params['cost'])> 0:
				self.model.misc.artworkToMarket(params['_id'], int(params['cost']))
		except Exception:
			pass

		self.sbuilder.httpRedirect(params['__page__'])

	def cancelSellingSpellPattern(self, params):
		is_spell = params['copy'] == 'True'
		id = params['spell_id']

		if is_spell:
			spell = self.model.spells.getUserSpellByID(id)
		else:
			# pattern
			spell = self.model.spells.getSpellPatternByID(id)

		if spell:
			self.model.spells.cancelSelling(self.cur_player['login_id'], spell)
		else:
			return self.error('Item not found')

		self.sbuilder.httpRedirect(params['__page__'])

	def cancelSellingCraftedItem(self, params):
		copy_of_item = params['copy'] == 'True'
		id = params['item_id']

		if copy_of_item:
			item = self.model.items.getItem(id)
		else:
			item = self.model.items.getCraftedItem(id)

		if item:
			self.model.items.cancelSelling(self.cur_player['login_id'], item)
		else:
			return self.error('Item not found')

		self.sbuilder.httpRedirect(params['__page__'])

	def cancelSellingArtwork(self, params):
		id = params['artwork_id']

		artwork = self.model.misc.getArtworkById(id)

		if artwork:
			self.model.misc.cancelSelling(self.cur_player['login_id'], artwork)
		else:
			return self.error('Artwork not found')

		self.sbuilder.httpRedirect(params['__page__'])

	def createArtwork(self, params):

		if self.balance.MIN_LEVEL_TO_CREATE > self.cur_player['login_lvl']:
			return self.sbuilder.throwWebError(6001)

		rules = {
			'name': {'min_length':3, 'max_length': 40, 'match': self.RE_CHECK_NAME, 'not_dublicate': {'col_artworks': 'name'}},
			'desc': {'min_length':4, 'max_length': 1000},
			'img': {'not_null': 1},
			'race': {'not_null':1},
			'class': {'gte':1, 'lte': 3, 'not_null':1},
			'cost': {'int': 1, 'gt': 0, 'lt': 1000000, 'not_null': 1}
		}

		status = self.checkParams(params, rules)

		if status['status']:

			buff = params['race'].split(':')
			if len(buff) == 2:
				faction_id = int(buff[0])
				race_id = int(buff[1])
			else:
				return False

			cost = int(params['cost'])
			if cost < 0:
				cost = 1

			artwork = self.model.artwork({
				"cost": cost,
				"img": params["img"],
				"faction": faction_id,
				"author": self.cur_player['login_id'],
				"race": race_id,
				"desc": formatTextareaInput(params['desc']),
				"class": int(params['class']),
				"name": params['name'].strip().title()
			})

			artwork.data.update(self.model.misc.getImageInfo(params))

			self.model.misc.addArtwork(artwork.data)
			self.sbuilder.httpRedirect(self.core.loaded_data['site_address']+'/u/creation_center?creation=ok&type=artwork')

		else:
			params.update({'errors': status['errors']})

	def editArtwork(self, params):

		artwork = self.getArtwork(params, logged_check=True, self_item_check=True)

		rules = {
			'desc': {'min_length':4, 'max_length': 1000},
			'race': {'not_null': 1},
			'class': {'gte':1, 'lte': 3, 'not_null':1},
			'cost': {'int': 1, 'gt': 0, 'lt': 1000000, 'not_null': 1}
		}

		if artwork['name'] != params['name']:
			rules.update({'name': {'min_length':3, 'max_length': 40, 'match': self.RE_CHECK_NAME, 'not_dublicate': {'col_artworks': 'name'}}})

		status = self.checkParams(params, rules)

		if status['status']:

			buff = params['race'].split(':')
			if len(buff) == 2:
				faction_id = int(buff[0])
				race_id = int(buff[1])
			else:
				return False

			cost = int(params['cost'])
			if cost < 0:
				cost = 1

			new_artwork_data = {
				"cost": cost,
				"faction": faction_id,
				"race": race_id,
				"desc": formatTextareaInput(params['desc']),
				"class": int(params['class']),
				"name": params['name'].strip()
			}

			if params['img'].strip():
				new_artwork_data.update({"img": params["img"]})

			new_artwork_data.update(self.model.misc.getImageInfo(params))

			old_data = {}
			for key in ['name', 'desc', 'cost', 'race', 'class', 'faction', 'img']:
				if key in new_artwork_data and new_artwork_data[key] != artwork[key]:
					old_data.update({key: artwork[key]})

			for key in ['link', 'name', 'email', 'twitter']:
				if key in new_artwork_data['img_info'] and new_artwork_data['img_info'][key] and key in artwork['img_info']:
					old_data.update({'Artwork: '+key: artwork['img_info'][key]})

			no_need_approve = 'login_admin' in self.cur_player and self.cur_player['login_admin'] or 'login_moderator' in self.cur_player and self.cur_player['login_moderator']
			if not no_need_approve:
				no_need_approve = 'cost' in old_data and len(old_data) == 1 or not old_data
			else:
				self.model.misc.writeToLog(self.cur_player['login_id'], {
					'action': 'artwork edit',
					'artwork_id': artwork['_id']
				})

			new_artwork_data.update({'old_data': old_data})

			self.model.misc.updateArtworkData(artwork['_id'], new_artwork_data, no_need_approve)

			self.sbuilder.httpRedirect('/u/artwork?id='+params['id']+'&edit=ok')

		self.sbuilder.httpRedirect('/u/edit_artwork?id='+params['id']+'&edit=fail')

	def deleteArtwork(self, params):
		artwork = self.getArtwork(params, logged_check=True, self_item_check=True)
		self.model.misc.deleteArtwork(artwork, self.cur_player['login_name'])

		self.sbuilder.httpRedirect('/u/creation_center?delete=artwork')

	def requestAuth(self, params):

		rules = {
			'link': {'not_null': 1, 'min_length': 3},
			'fullname': {'not_null': 1, 'min_length': 3},
			'email': {'not_null': 1},
		    'rules': {'not_null': 1}
		}

		status = self.checkParams(params, rules)

		if status['status']:

			data = {
				'twitter_name': self.cur_player['login_name'],
			    'game_id': self.cur_player['login_id'],
				'link': params['link'].strip(),
			    'fullname': params['fullname'].strip(),
			    'email': params['email'].strip(),
			    'time': time.time(),
				'additional': formatTextareaInput(params['additional'])
			}

			self.model.misc.addAuthRequest(data)

			self.sbuilder.httpRedirect('/thx?n=ugc_request')

		else:
			params.update({'errors': status['errors']})

	# --------------------------------------------------------------------------------------------------
	# Print pages

	def printCreatingArtwork(self, fields, params):
		fields.update({self.title: 'Add new artwork'})

		if not self.cur_player:
			return self.sbuilder.throwWebError(1002)

		response = self._printUGCDisablePage(fields)
		if response: return response

		if self.balance.MIN_LEVEL_TO_CREATE > self.cur_player['login_lvl']:
			return self.sbuilder.throwWebError(6001)

		if self.cur_player and self.cur_player['login_ugc_disabled']:
			return self.sbuilder.httpRedirect('/u/create')

		fields.update(self.balance.classes_and_races)

		player = self.model.players.getPlayerBy_ID(self.cur_player['login_id'], {'agree_with_rules': 1})

		if not ('agree_with_rules' in player and player['agree_with_rules']):
			return basic.defaultController._printTemplate(self, 'rules_agree_form', fields)

		return basic.defaultController._printTemplate(self, 'create_artwork', fields)

	def printCreationCenter(self, fields, params):

		fields.update({self.title: 'Creation center'})

		if not self.cur_player:
			return self.sbuilder.throwWebError(1002)

		items = self.model.items.getCraftedItems(self.cur_player['login_id'])
		spells = self.model.spells.getSpellsPattern(self.cur_player['login_id'])
		artworks = self.model.misc.getAllArtworksByPlayer(self.cur_player['login_id'])

		fields.update({
			'stat_names': self.balance.stats_name,
			'can_create': self.balance.MIN_LEVEL_TO_CREATE <= self.cur_player['login_lvl']
		})

		if self.core.debug['create_by_invite']:
			fields['can_create'] = self.cur_player and self.cur_player['login_ugc_enabled']

		items += spells + artworks

		sell_statuses = {
			'sell': 'Selling',
		    'not_sell': 'Not Selling',
		    'waiting': 'Waiting',
		    'rejected': 'Rejected'
		}

		for item in items:
			if 'reject' in item:
				status = 'rejected'

			elif item['approve'] and item['approve']['approved']:
				if item['sale_info']['active']:
					status = 'sell'
				else:
					status = 'not_sell'
			else:
				status = 'waiting'

			# Если заклинание, то ставим соответствующий тип
			if 'spell_actions' in item:
				item['view'] = 'Spell'
				item['img'] += '_fit.png'

			# если артворк
			elif 'faction' in item:
				item['img'] += '_fit.png'
				item['view'] = 'Artwork'
			# если предмет, то сделаем красивый вывод стат
			else:
				item['view'] = item['view'].title()
				item.update(prettyItemBonus(item, self.balance.stats_name))
				item['img'] = '/' + item['img'] + '_fit.png'

			item.update({'status': sell_statuses[status], 'raw_status': status})

		fields.update({'items': items})

		return basic.defaultController._printTemplate(self, 'creation_center', fields)

	def printSelectCreationForm(self, fields, params):

		fields.update({self.title: 'Create new'})

		if not self.cur_player:
			return self.sbuilder.throwWebError(1002)

		response = self._printUGCDisablePage(fields)
		if response: return response

		fields.update({'can_create': self.balance.MIN_LEVEL_TO_CREATE <= self.cur_player['login_lvl']})

		return basic.defaultController._printTemplate(self, 'select_create_form', fields)

	def printArtworkPage(self, fields, params):

		artwork = self.getArtwork(params)
		if 'error' in artwork:
			return self.sbuilder.throwWebError(artwork['error'], 'Artwork')

		if 'author' in artwork:
			author = self.model.players.getPlayerBy_ID(artwork['author'], {'name':1})
			if author:
				artwork.update({'author_name': author['name']})

		if 'UID' in artwork:
			artwork['img'] = self.core.ARTWORK_SHOP_PATH+artwork['img']+'.jpg'
		else:
			artwork['img'] += '_fit.png'

		artwork['img_info'] = miscController.formatArtworkInfo(artwork['img_info'])

		if 'reject' in artwork:
			try:
				rejecter = self.model.players.getPlayerBy_ID(artwork['reject']['rejecter_id'], {'name':1})
				fields.update({'reject_name': rejecter['name']})
			except Exception:
				fields.update({'reject_name': 'game'})

		artwork.update({
		    'race_name': self.balance.races[artwork['faction']][artwork['race']],
		    'class_name': self.balance.classes[str(artwork['class'])]
		})

		fields.update(artwork)

		if self.cur_player:

			artworks = self.model.misc.getPlayersBuyedArtworks(self.cur_player['login_id'])

			for art in artworks:
				if art['name'] == artwork['name']:
					already_have = True
					break
			else:
				already_have = False

			fields.update({
				'already_have': already_have,
				'player_race_name': self.balance.races[self.cur_player['login_faction']][self.cur_player['login_race']],
				'player_class_name': self.balance.classes[str(self.cur_player['login_class'])]
			})

		likes = self.model.items.getItemLikes(artwork['_id'])

		fields.update({
			self.title: artwork['name']+' artwork page',
			'likes': len(likes['people']),
			'is_like': self.cur_player and self.cur_player['login_id'] in likes['people'],
			'is_reported': self.cur_player and self.model.items.isReportItem(artwork['_id'], self.cur_player['login_id']),
			'reasons': self.balance.getRejectReasons(self.balance.artwork_reject_reasons),
			'categories': self.balance.categories
		})

		return basic.defaultController._printTemplate(self, 'artwork_page', fields)

	def printArtworkEditPage(self, fields, params):

		artwork = self.getArtwork(params, logged_check=True, self_item_check=True)

		artwork['faction_race'] = str(artwork['faction'])+':'+str(artwork['race'])

		fields.update({self.title: 'Edit '+artwork['name']+' page'})
		fields.update(artwork)

		return basic.defaultController._printTemplate(self, 'artwork_edit_page', fields)

	def printRequestForm(self, fields, params):
		fields.update({self.title: 'Request authorisation'})

		if 'errors' in params:
			for error in params['errors']:
				fields.update({'_E_'+error['name']: True})

		return basic.defaultController._printTemplate(self, 'request_auth', fields)


data = {
	'class': creationCenterController,
	'type': ['u'],
	'urls': ['create_artwork', 'request', 'creation_center', 'create', 'artwork', 'edit_artwork']
}