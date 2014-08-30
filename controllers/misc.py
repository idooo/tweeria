# -*- coding: utf-8 -*-

import basic
import site_builder
import re
from sets import Set
from functions import getReadbleTime, prettyItemBonus, getDisplayPages
import math
from guild import guildsController
import json
import random
import cherrypy

class miscController(basic.defaultController):

	@basic.printpage
	def printPage(self, page, params):

		self.sbuilder = site_builder.builder()

		return {
			'index':            self.printIndex,
		    '':                 self.printIndex,
		    'login':            self.sbuilder.parseLogin,
		    'logout':           self.sbuilder.parseLogout,
		    'help':             self.printHelp,
		    'help_ugc':         self.printHelpApprove,
		    'help_auth':        self.printHelpAuth,
		    'search':           self.printSearchResults,
		    'all-players':      self.printAllPlayers,
		    'all-guilds':       self.printAllGuilds,
		    'ne':               self.printFactionPage,
		    'ha':               self.printFactionPage,
		    'ft':               self.printFactionPage,
		    #'test':             self.printTest
			'licenses':         self.printLicensesHelp,
		    'thx':              self.printThanks,
		    'invite':           self.printInvitePage,
		    'credits':          self.printCredits
		}

	@basic.methods
	def methods(self, params = {}):
		return {
			'type_of_form': {
				'agree_with_rules': self.agreeWithRules
			},
			'like': self.likeProxy,
		    'report': self.reportThing,
		}

	@staticmethod
	def formatArtworks(self, artworks):
		authors_ids = Set()
		for item in artworks:
			authors_ids.add(item['author'])

		players_names = self.model.players.getPlayersList(authors_ids, ['_id', 'name'])

		for artwork in artworks:

			artwork['race_name'] = self.balance.races[artwork['faction']][artwork['race']]
			artwork['class_name'] = self.balance.classes[str(artwork['class'])]

			if 'builtin' in artwork:
				artwork['img'] = self.core.ARTWORK_SHOP_PATH+artwork['img']+'.jpg'
				artwork['share_img'] = artwork['img']
			else:
				artwork.update({
					"share_img": artwork["img"][3:],
					'img': artwork['img']+'_fit.png'
				})

			for player in players_names:
				if player['_id'] == artwork['author']:
					artwork['author_name'] = player['name']
					break

		return artworks

	@staticmethod
	def formatArtworkInfo(info):
		if 'link' in info and info['link']:
			if len(info['link']) > 32:
				info['link_name'] = info['link'][:32]+'...'
			else:
				info['link_name'] = info['link']

		return info

	def formatPlayers(self, players):
		for player in players:
			player['lvl'] = int(player['lvl'])
			self.sbuilder.raceFormat(player)

		return players

	# --------------------------------------------------------------------------------------------------
	# Misc

	@staticmethod
	def likeIt(obj, params):
		ajax = False
		if "ajax" in params and int(params['ajax'])==1:
			ajax = True

		if not obj.cur_player:
			if ajax:
				return json.dumps({"error": 1,"message" : "1002"})
			else:
				return obj.sbuilder.throwWebError(1002)

		if '_id' in params:
			if 'type' in params:
				tp = params['type']
			else:
				tp = 'item'

			obj.model.items.likeItem(params['_id'], obj.cur_player['login_id'], tp)

		if ajax:
			return json.dumps({"success": 1,"liked" : "1"})
		else:
			obj.httpRedirect(params)

	def likeProxy(self, params):
		return self.likeIt(self, params)

	def reportThing(self, params):
		if not self.cur_player:
			return self.sbuilder.throwWebError(1002)

		if '_id' in params:
			if 'report_type' in params and params['report_type'] in ['item', 'spell', 'artwork']:
				type_of = params['report_type']
			else:
				type_of = 'item'

			self.model.items.reportItem(params['_id'], self.cur_player['login_id'], type_of)

		self.httpRedirect(params)

	def getBlogLastPosts(self, count = 2):
		posts = self.model.misc.getBlogPosts()
		return posts[:count]

	def agreeWithRules(self, params):
		if self.cur_player:
			self.model.players.updatePlayerData(self.cur_player['login_id'], {'agree_with_rules': True})

		self.httpRedirect(params)

	# --------------------------------------------------------------------------------------------------
	# Print pages

	def printIndex(self, fields, param):

		def getLastItems(last_count = 8):
			last_items = self.model.items.getLastApprovedItems(last_count)

			if self.cur_player:
				str_class = str(self.cur_player['login_class'])
			else:
				str_class = False

			authors_ids = Set()
			items_ids = Set()
			for item in last_items:
				authors_ids.add(item['author'])
				items_ids.add(item['_id'])
				item.update(prettyItemBonus(item, self.balance.stats_name))

				if item['type'] == 1 and str_class:
					if not item['view'] in self.sbuilder.balance.available_weapons[str_class]:
						item['cant_use'] = True

				item['img'] += '_fit.png'

			players_names = self.model.players.getPlayersList(authors_ids, ['_id', 'name'])
			item_likes = self.model.items.getItemsLikes(items_ids)

			for item in last_items:
				for player in players_names:
					if player['_id'] == item['author']:
						item['author_name'] = player['name']
						break

				for likes in item_likes:
					if likes['item_id'] == item['_id']:
						item['likes'] = len(likes['people'])
						is_like = False
						if self.cur_player:
							is_like = self.cur_player['login_id'] in likes['people']

						item['is_like'] = is_like
						break
				else:
					item['likes'] = 0

			return last_items

		def getTrendingPlayers(count = 8):
			players = self.model.players.getTrendingPlayers(count)
			for player in players:
				player.update({
					'class_name': self.balance.classes[str(player['class'])],
					'race_name':  self.balance.races[player['faction']][player['race']],
				})

			return players

		def getTrendingGuild(count = 8):
			guilds = self.model.guilds.getTrendingGuilds(count)
			return guilds

		def getFeaturedArtwork():
			artwork = self.model.misc.getRandomArtwork()
			if artwork:
				artwork['race_name'] = self.balance.races[artwork['faction']][artwork['race']]
				artwork['class_name'] = self.balance.classes[str(artwork['class'])]

				player = self.model.players.getPlayerBy_ID(artwork['author'], {'name': 1})

				if 'UID' in artwork:
					artwork['img'] = self.core.ARTWORK_PATH + artwork['img'] + '.jpg'
				else:
					artwork['img'] += '_fit.png'

				if player:
					artwork['author_name'] = player['name']

				likes = self.model.items.getItemLikes(artwork['_id'])
				if likes:
					artwork.update({
						'likes': len(likes['people']),
						'is_like': self.cur_player and self.cur_player['login_id'] in likes['people'],
					})

			return artwork

		def getRandomTitle():
			titles = [
				'Good news everyone!',
			    'Oh my, yes!',
			    'Ya filthy crab!',
			    'Bad news, nobody!',
			    'Pew pew pew',
			    'Me fail English? That`s unpossible',
			    'Uulwi ifis halahs gag erh\'ongg w\'ssh',
			    'You are not prepared!',
			    'BOOOONEEEESTOOORRMMM',
			    'Oppan orcish style',
			    'New toys? For me?',
			    'Thank you, @MeowMio',
			    '15.9% uptime',
			    '4 9 14 0 14 2',
			    'What does Marsellus Wallace look like?',
			    'May the Force be with you',
			    'Do not refresh this page',
			    'Refresh this page',
			    'No errors here',
			    'Fine!',
			    'Not bugs but features',
			    'QRATOR HTTP 502',
			    'Waka-Waka-Waka',
			    'Pinocchio was an android',
			    'You are cut out for Tweeria',
			    'Life sucks, get a helmet',
			    'Wrong username and password, %username%, try again',
			    'Wweerai owns teh Intarnet',
			    'Solutions are not the answer, %username%',
			    'Three Nations Army',
			    'Human Quan\'Zul Style!',
			    'ALGEBRAIC!',
			    'Are you an orcaholic, %username%?',
			    'Live long and prosper',
			    'Live fast - die young - undead forever',
			    'Tweeria Time!',
			    'The reckoning has come!',
			    'Shelter your weak, your young and your old!',
			]

			return random.sample(titles, 1)[0]

		def getArtistsLikes(count = 10):
			return self.model.misc.getAuthorsLikes(count)

		if self.cur_player:
			inventory_count = self.model.items.getInventoryCount(self.cur_player['login_id'])
		else:
			inventory_count = 0

		fields.update(self.model.misc.getGameStatistics())

		fields.update({
			self.title: getRandomTitle(),
			'inventory_count': inventory_count,
			'featured_artwork': getFeaturedArtwork(),
			'last_items': getLastItems(),
		    'authors_likes': getArtistsLikes(10),
			'trending_players': getTrendingPlayers(5),
		    'trending_guilds': getTrendingGuild(5),
		    'blog_posts': self.getBlogLastPosts(2),
		    'tip': self.model.misc.getRandomTip()
		})

		return basic.defaultController._printTemplate(self, 'index', fields)

	def printSearchResults(self, fields, param):

		fields.update({self.title: 'Search'})

		if 'q' in param:
			regx = re.compile(re.sub('<.*?>','',param['q']), re.IGNORECASE)
			search_query = {'name': {'$regex': regx}}
		else:
			search_query = {}

		if 'q' in param and len(param['q']) > 1:

			players = self.model.players.getPlayersListFiltered(
				search_query = search_query,
				count = 20,
				page = 1
			)

			for player in players:
				player.update({
					'class_name': self.balance.classes[str(player['class'])],
					'race_name':  self.balance.races[player['faction']][player['race']],
					})

			guilds = self.model.guilds.getGuildsListFiltered(
				search_query = search_query,
				count = 20,
				page = 1
			)

			fields.update({'players': players, 'guilds': guilds})

		else:
			fields.update({'error': 'empty_search'})

		return basic.defaultController._printTemplate(self, 'search', fields)

	def printTest(self, fields, param):
		return basic.defaultController._printTemplate(self, 'players/registration', fields)

	def printThanks(self, fields, param):
		return basic.defaultController._printTemplate(self, 'misc/thx', fields)

	def printHelp(self, fields, param):
		fields.update({self.title: 'Help'})
		return basic.defaultController._printTemplate(self, 'misc/help', fields)

	def printLicensesHelp(self, fields, param):
		fields.update({self.title: 'Licenses'})
		return basic.defaultController._printTemplate(self, 'misc/licenses', fields)

	def printHelpApprove(self, fields, param):

		fields.update({self.title: 'Help UGC'})
		return basic.defaultController._printTemplate(self, 'misc/help_ugc', fields)

	def printHelpAuth(self, fields, param):

		fields.update({self.title: 'Help auth'})
		return basic.defaultController._printTemplate(self, 'misc/help_auth', fields)

	def printAllPlayers(self, fields, param):

		fields.update({self.title: 'All players'})

		def getPaginatorData(players_on_page):
			players_count = self.model.players.getPlayersCount()

			pages = int(math.ceil(float(players_count) / players_on_page))

			fields.update({
				'total_pages': pages
			})

		def getSortParams():
			if not 'pi' in param:
				fields.update({'param_pi': 1})

			try:
				page_number = int(param['pi'])
			except Exception:
				page_number = 1

			if 'field' in param:
				sort_field = param['field']
			else:
				sort_field = 'lvl'

			sort_order = -1
			if 'order' in param:
				try:
					sort_order = int(param['order'])
				except Exception:
					pass

			return {
				'page_number': page_number,
			    'sort_field': sort_field,
			    'sort_order': sort_order
			}

		players_on_page = 20

		sort_params = getSortParams()

		players = self.model.players.getPlayersListFiltered(
			count = players_on_page,
			page = sort_params['page_number'],
			field = sort_params['sort_field'],
			sort = sort_params['sort_order']
		)

		getPaginatorData(players_on_page)

		for player in players:
			player.update({
				'class_name': self.balance.classes[str(player['class'])],
				'race_name':  self.balance.races[player['faction']][player['race']],
				})

		fields.update({'players': players})

		fields.update({'display_pages': getDisplayPages(int(fields['param_pi']), fields['total_pages'], 10)})

		return basic.defaultController._printTemplate(self, 'players/all_players', fields)

	def printAllGuilds(self, fields, param):

		fields.update({self.title: 'All guilds'})

		def getPaginatorData(guilds_on_page):
			guilds_count = self.model.guilds.getGuildsCount()

			pages = int(math.ceil(float(guilds_count) / guilds_on_page))

			fields.update({
				'total_pages': pages
			})

		def getSortParams():
			if not 'pi' in param:
				fields.update({'param_pi': 1})

			try:
				page_number = int(param['pi'])
			except Exception:
				page_number = 1

			if 'field' in param:
				sort_field = param['field']
			else:
				sort_field = 'people_count'

			sort_order = -1
			if 'order' in param:
				try:
					sort_order = int(param['order'])
				except Exception:
					pass

			return {
				'page_number': page_number,
				'sort_field': sort_field,
				'sort_order': sort_order
			}

		guilds_on_page = 20

		sort_params = getSortParams()
		getPaginatorData(guilds_on_page)

		guilds = self.model.guilds.getGuildsListFiltered(
			count = guilds_on_page,
			page = sort_params['page_number'],
			field = sort_params['sort_field'],
			sort = sort_params['sort_order']
		)

		if self.cur_player:
			guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])
			if guild:
				guild =  guildsController.formatGuilds(self,[guild])[0]

				fields.update({
					'login_guild': guild
				})

		fields.update({'guilds': guilds})
		fields.update({'display_pages': getDisplayPages(int(fields['param_pi']), fields['total_pages'], 10)})

		return basic.defaultController._printTemplate(self, 'guilds/all_guilds', fields)

	def printFactionPage(self, fields, param):

		sides = {
			'ne': 0,
			'ha': 1,
			'ft': 2
		}

		side_id = sides[fields['__page__']]

		fields.update({
			'side_name': self.sbuilder.balance.faction[side_id]
		})

		return basic.defaultController._printTemplate(self, 'misc/faction', fields)

	def printInvitePage(self, fields, param):

		player = False
		player_name = False

		for key in param:
			if key[:2] != '__' and key != 'guild':
				player_name = key
				break

		if player_name:
			player = self.model.players.getPlayerRawByName(player_name, {
				'name': 1,
				'class':1,
			    '_guild_name': 1,
			    'race': 1,
			    'faction': 1,
			    'lvl': 1,
			    'avatar': 1
			})

		if not player:
			return self.sbuilder.throwWebError(404)

		player.update({
			'class_name': self.balance.classes[str(player['class'])],
			'race_name': self.balance.races[player['faction']][player['race']]
		})

		fields.update({'player': player})

		return basic.defaultController._printTemplate(self, 'misc/landing_page', fields)

	def printCredits(self, fields, param):
		fields.update({self.title: 'Credits'})
		return basic.defaultController._printTemplate(self, 'misc/credits', fields)

data = {
	'class': miscController,
    'type': ['index', 'default'],
	'urls': [
		'', 'index', 'thx', 'logout', 'licenses',
		'login', 'search', 'help', 'all-players',
		'all-guilds', 'ne', 'ft', 'ha', 'test', 'help_ugc', 'help_auth',
	    'invite', 'credits'
	]
}
