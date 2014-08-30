# -*- coding: UTF-8 -*-

import re
import basic
import cherrypy
from time import time
from PIL import Image, ImageOps
import memcache_controller
from functions import getReadbleTime, getMessages, formatTextareaInput
from events import eventsController
import json

class guildsController(basic.defaultController):

	cache = memcache_controller.cacheController()
	DIR = './guilds/'

	RE_CHECK_NAME = re.compile('^[a-zA-Z0-9\s\-\+]+$', re.U+re.I)

	@basic.methods
	def methods(self, params = {}):
		return {
			'type_of_form': {
				'create_guild': self.createGuild,
			    'change_settings': self.changeSettings,
			    'leave_guild': self.leaveGuild,
			    'kick_player': self.kickPlayer,
			    'promote_leadership': self.promoteLeader,
			    'join_guild': self.joinGuild,
			    'delete_guild': self.deleteGuild,
			    'ask_join_guild': self.requestInvite,
			    'withdraw_request': self.withdrawRequest,
			    'reject_invite': self.rejectInvite,
			    'approve_invite': self.acceptInvite,
			    'add_news': self.addNews,
			    'delete_news': self.deleteNews
			},
		    'find': self.findGuilds
		}

	@basic.printpage
	def printPage(self, page, params):
		return {
		    'add': self.printAddForm,
		    'settings': self.printGuildSettings,
		    'addnews': self.printAddNewsForm,
		    'news': self.printNewsList,
		    'story': self.printNewsPage,
		    '': self.printGuildsList,
			'__default__':      {
									'method': self.printGuildDetail,
									'params': {'guildname': page}
								}
		}

	# --------------------------------------------------------------------------------------------------
	# Misc

	@staticmethod
	def formatGuilds(self, guilds):
		for guild in guilds:
			guild['img'] = self.core.getAvatarLink(guild)
			guild['people.count'] = int(guild['people_count'])

		return guilds

	def _formatGuildMembers(self, guild, players, show_creator=False, people_field_name='people'):

		people = []

		for player in players:

			new_player = {
				'_id': player['_id'],
				'name': player['name'],
				'class_name': self.balance.classes[str(player['class'])],
				'lvl': int(player['lvl']),
				'avatar': player['avatar'],
				'achv_points': int(player['achv_points']),
				'pvp_score': int(player['pvp_score']),
			    'leadership': player['stat']['lead']['current'],
				'user_id': player['user_id'],
				'race_name': self.balance.races[player['faction']][player['race']]
			}

			if player['_id'] == guild['creator']:
				new_player.update({'creator': True})
				creator = new_player.copy()

			people.append(new_player)
			del new_player

		if show_creator:
			return {'creator': creator, people_field_name: people}
		else:
			return {people_field_name: people}

	def autoLeaveGvG(self, player_id):

		gvg_events = self.model.events.getGvGEvents(player_id, {'_id': 1})
		for event in gvg_events:
			self.model.events.leaveEvent(event['_id'], player_id)

		eventsController.updatePlayerDirection(self, player_id)

	def deleteGvG(self, guild_id):
		self.model.events.removeGvGEventsByGuild(guild_id)

	def uploadImage(self, guild, image, just_return_str = True):

		def resizeImage(buffer_filepath, local_filepath):
			image = Image.open(buffer_filepath)

			width, height = image.size
			need_resize = False

			if width > self.core.MAX_AVA_WIDTH:
				width = self.core.MAX_AVA_WIDTH
				need_resize = True

			if height > self.core.MAX_AVA_HEIGHT:
				height = self.core.MAX_AVA_HEIGHT
				need_resize = True

			if need_resize:
				thumb = ImageOps.fit(image, (width,height), Image.ANTIALIAS)
				thumb.save(local_filepath, "PNG")
			else:
				image.save(local_filepath, "PNG")

		if image.filename == '':
			return {'not_uploaded': True}
		else:
			result = re.search('\.(png|gif|jpg|jpeg)$',image.filename,re.I)
			if result:

				size = int(cherrypy.request.headers['content-length'])

				if size < self.sbuilder.core_settings.MAX_UPLOAD_FILE_SIZE:

					data = image.file.read()
					filename = guild['link_name']+result.group().lower()

					local_buffer_filepath = self.sbuilder.core_settings.TEMPLATES_FOLDER+self.sbuilder.core_settings.IMAGE_BUFFER_FOLDER+filename
					local_filepath =self.sbuilder.core_settings.TEMPLATES_FOLDER+ self.sbuilder.core_settings.GUILDS_AVATAR_FOLDER+guild['link_name']+'.png'
					fp = open(local_buffer_filepath,'w')
					fp.write(data)
					fp.close()

					resizeImage(local_buffer_filepath, local_filepath)

					return {'link':guild['link_name']+'.png'}

				else:
					error = 'img.big_size'
					code = 1
			else:
				error = 'img.incorrect_extention'
				code = 2
		try:
			return {'error': error, 'code':code}
		except:
			pass

	# --------------------------------------------------------------------------------------------------
	# Page methods

	# -- Misc

	def findGuilds(self, params):
		if 'find' in params:
			regx = re.compile(re.sub('<.*?>','',params['find']), re.IGNORECASE)
			search_query = {'name': {'$regex': regx}}

			result = self.model.guilds.getGuildsListSearch(search_query)

		else:
			result = []

		return json.dumps(result)


	# -- Guild Admin

	def promoteLeader(self, params):
		guild = self.model.guilds.getGuildByName(self.cur_player['login_guild'])
		if guild:
			self.model.guilds.promoteLeadership(guild['_id'], params['player_name'])
			return self.sbuilder.redirect('/guilds/'+guild['link_name'])

	def changeSettings(self, param):

		guild = self.model.guilds.getGuildByName(self.cur_player['login_guild'])

		rules = {
		    'description': {},
		    'site_link': {}
		}

		status = self.checkParams(param, rules)

		updated_fields = {}
		if 'image_file' in param:
			new_avatar = self.uploadImage(guild, param['image_file'])

			if 'error' in new_avatar:
				status = self.thrownCheckError('image', 'oops')

			if not 'error' in new_avatar and not 'not_uploaded' in new_avatar:
				updated_fields.update({'img':new_avatar['link']})

		if status['status']:

			param['site_link'] = re.sub('.*\:\/\/','',param['site_link'])
			param['description'] = formatTextareaInput(param['description'])

			type_of_membership = not 'closed' in param

			updated_fields.update({
				'open': type_of_membership,
				'description': param['description'],
				'site_link' : param['site_link']
			})

			self.model.guilds.changeSettings(guild['_id'], updated_fields)
			self.httpRedirect(param, '?success=ok')

	def rejectInvite(self, params):
		player = self.model.players.getPlayer(params['player_user_id'])
		guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])
		if player:
			self.model.guilds.rejectInvite(guild['_id'], player['_id'])

	def acceptInvite(self, params):
		player = self.model.players.getPlayer(params['player_user_id'])
		guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])

		if player and guild:
			self.model.guilds.removeAllRequests(player['_id'])
			self.model.guilds.joinGuild(guild['_id'], player['_id'], guild['name'])

	def kickPlayer(self, params):
		guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])
		if guild:
			player = self.model.players.getPlayer(params['user_id'])
			if player and player['_id'] in guild['people']:

				# если игрок есть и он не основатель гильдии то выпиливаем
				if player['_id'] != guild['creator']:
					self.model.guilds.leaveGuild(guild['_id'], player['_id'])
					self.autoLeaveGvG(player['_id'])

	def deleteGuild(self, params):
		guild = self.model.guilds.getGuildByName(params['guild_search_name'])
		if guild:
			if len(guild['people']) == 1:
				self.deleteGvG(guild['_id'])
				self.model.guilds.removeGuild(guild['_id'], self.cur_player['login_id'])
				return self.sbuilder.redirect('/top?success=delete')

	# -- Users

	def withdrawRequest(self, params):
		guild = self.model.guilds.getGuildByName(params['guild_search_name'])
		self.model.guilds.rejectInvite(guild['_id'], self.cur_player['login_id'])
		self.httpRedirect(params)

	def leaveGuild(self, params):
		params['user_id'] = self.cur_player['login_user_id']
		self.kickPlayer(params)
		self.httpRedirect(params)

	def requestInvite(self, params):
		guild = self.model.guilds.getGuildByName(params['guild_search_name'])

		if guild and not guild['open'] and self.cur_player:
			player_in_guild = self.model.guilds.getPlayersGuild(self.cur_player['login_user_id'])
			if not player_in_guild and not self.cur_player['login_id'] in guild['request']:
				self.model.guilds.askInvite(guild['_id'], self.cur_player['login_id'])

		self.httpRedirect(params)

	def joinGuild(self, params):

		if self.cur_player['login_guild'] == '':

			guild = self.model.guilds.getGuildByName(params['guild_search_name'])

			if guild and self.cur_player:
				player_in_guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])
				if not player_in_guild:
					if int(guild['open']) == 1:
						self.model.guilds.joinGuild(guild['_id'], self.cur_player['login_id'], guild['name'])
				else:
					pass

		self.httpRedirect(params)

	# -- Create

	def createGuild(self, params):

		rules = {
			'name': {'min_length':3, 'max_length': 21, 'match': self.RE_CHECK_NAME},
		    'image_file': {'exist':1}
		}

		status = self.checkParams(params, rules)

		if self.cur_player['login_guild'] != '':
			return self.sbuilder.redirect('/guilds/'+self.cur_player['login_guild'])

		if status['status']:

			is_open_guild = 'closed' in params

			params['name'] = params['name'].strip()

			new_guild = self.model.guild({
				'name': params['name'],
				'description': formatTextareaInput(params['desc']),
				'creator': self.cur_player['login_id'],
				'open': not is_open_guild,
				'site_link': params['site_link'],
				'people_count': 1,
			    'guild_points': 0,
				'people': [self.cur_player['login_id']],
				'search_name': params['name'].upper(),
				'link_name': re.sub(' ','_', params['name']),
			    'faction': self.cur_player['login_faction']
			})

			exist = self.model.guilds.isGuildExist(params['name'].upper())
			if exist:
				return self.sbuilder.redirect('/guilds/add?error=1&name='+params['name']+'&desc='+params['desc'])

			if 'image_file' in params:
				avatar = self.uploadImage(new_guild.data, params['image_file'])
			else:
				avatar = 'not_uploaded'

			if 'not_uploaded' in avatar:
				new_guild.data['img'] = ''
			elif not 'error' in avatar:
				new_guild.data['img'] = avatar['link']
			else:
				return {'error':avatar['error']}

			result = self.model.guilds.addGuild(new_guild.data.copy())

			del new_guild

			if result:
				return self.sbuilder.redirect('/guilds/'+params['name'])
			else:
				return self.sbuilder.redirect('/guilds/add?error=1&name='+params['name']+'&desc='+params['desc'])

		else:
			params.update({'operation_result': 'error', 'errors': status['errors']})

	# -- News

	def addNews(self, params):
		guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])
		if guild and guild['creator'] == self.cur_player['login_id']:
			rules = {
				'text': {'min_length':3}
			}

			status = self.checkParams(params, rules)

			if status['status']:
				news_body = {
					'header': params['header'].strip(),
					'text': formatTextareaInput(params['text']),
					'link': params['link'].strip(),
				    'create_date': time(),
				    'UID': int(time()),
				    'author': self.cur_player['login_id'],
				    'author_name': self.cur_player['login_name']
				}

				self.model.guilds.addNewsToBase(guild['_id'], news_body)

				return self.sbuilder.redirect('/guilds/story?id='+str(news_body['UID']))
			else:
				return self.sbuilder.redirect('/guilds/addnews?error=true')

	def deleteNews(self, params):
		guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])
		if guild and guild['creator'] == self.cur_player['login_id'] and 'UID' in params:
			try:
				UID = int(params['UID'])
			except Exception:
				return self.sbuilder.redirect('/guilds/'+guild['link_name'])

			self.model.guilds.removeNewsFromBase(guild['_id'], UID)
			return self.sbuilder.redirect('/guilds/'+guild['link_name'])

	# --------------------------------------------------------------------------------------------------
	# Print pages

	def printGuildSettings(self, fields, params):

		fields.update({self.title: 'Guild settings'})

		guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])

		if not guild:
			return self.sbuilder.throwWebError(404)

		if guild['creator'] == self.cur_player['login_id']:

			guild['img'] = self.core.getAvatarLink(guild)
			guild['closed'] = not guild['open']
			fields.update(guild)

			fields.update(self._formatGuildMembers(guild,self.model.guilds.getGuildMembers(guild), show_creator=True))
			fields.update(self._formatGuildMembers(guild,self.model.guilds.getGuildMembers(guild, 'request'), people_field_name='requesters'))

			return basic.defaultController._printTemplate(self, 'guild_settings', fields)
		else:
			return self.sbuilder.throwWebError(3001)

	def printGuildDetail(self, fields, params = {}):

		guildname = params['guildname']

		guild = self.model.guilds.getGuildByName(guildname)
		if guild:
			guild['img'] = self.core.getAvatarLink(guild)
			if guild['img'].find("./") == 0:
				guild['img'] = guild['img'][2:]

			if 'site_link' in guild:
				if guild['site_link'] == '':
					del guild['site_link']

				elif guild['site_link'][:7] != 'http://':
					guild['site_link'] = 'http://'+guild['site_link']

			fields.update(guild)

			sort_name = ''
			sort_order = -1

			if 's' in params:
				if params['s'] == 'lead':
					sort_name = 'stat.lead.current'
				elif params['s'] == 'name':
					sort_name = 'name'
				elif params['s'] == 'achv':
					sort_name = 'achv_points'
				elif params['s'] == 'lvl':
					sort_name = 'lvl'
				elif params['s'] == 'pvp':
					sort_name = 'pvp_score'

			if 'o' in params:
				if params['o'] == '1':
					sort_order = 1

			if sort_name:
				sort = {sort_name: sort_order}
			else:
				sort = {}

			guild_members = self.model.guilds.getGuildMembers(guild, sort_query=sort)

			fields.update(self._formatGuildMembers(guild, guild_members, show_creator=True))

			if self.cur_player:
				if self.cur_player['login_id'] == fields['creator']['_id']:
					fields.update({'login_creator': True})
				else:
					players_guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])
					if players_guild:
						if players_guild['name'] == guild['name']:
							fields.update({'in_guild':'this'})
						else:
							fields.update({'in_guild':'other'})
					else:
						if self.cur_player['login_id'] in guild['request']:
							fields.update({'requested': True})
						fields.update({'in_guild': False})

			messages = self.model.guilds.getGuildMessages(guild['name'])['history']

			fields.update({
				'messages': getMessages(messages),
			    self.title: '"'+guild['name']+'" guild'
			})

			news = self.model.guilds.getGuildNews(guild['_id'])['news'][::-1]
			last_news = news[:2]

			# cut text
			desc_cut = 128

			for story in last_news:
				if len(story['text']) > desc_cut:
					story['text'] = story['text'][:desc_cut:] + '...'

			fields.update({
				'news': last_news,
			    'events': self.model.events.getGuildEventsByID(guild['_id'])
			})

			if 'name' in params:
				inviter_info = self.model.players.getPlayerRawByName(params['name'], {'avatar': 1})
				if inviter_info and 'avatar' in inviter_info:
					fields.update({'inviter_avatar': inviter_info['avatar']})

			return basic.defaultController._printTemplate(self, 'guild_detail', fields)
		else:
			return self.sbuilder.throwWebError(404)

	def printGuildsList(self, fields, params):
		fields.update({self.title: 'Guild list'})

		return self.sbuilder.redirect('/top')

	def printAddForm(self, fields, params):
		if not self.cur_player:
			return self.sbuilder.redirect('http://tweeria.com')

		fields.update({self.title: 'Add new guild'})
		return basic.defaultController._printTemplate(self, 'guild_add', fields)

	def printAddNewsForm(self, fields, params):
		guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])

		if not guild:
			return self.sbuilder.throwWebError(404)

		if guild['creator'] != self.cur_player['login_id']:
			return self.sbuilder.throwWebError(3001)

		fields.update({self.title: 'Add news'})
		fields.update(guild)
		return basic.defaultController._printTemplate(self, 'add_news', fields)

	def printNewsList(self, fields, params):
		guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])

		if not guild:
			return self.sbuilder.throwWebError(404)

		fields.update({self.title: 'News list'})

		news = self.model.guilds.getGuildNews(guild['_id'])['news'][::-1]

		fields.update(guild)
		fields.update({'news': news})

		return basic.defaultController._printTemplate(self, 'news_list', fields)

	def printNewsPage(self, fields, params):

		guild = self.model.guilds.getPlayersGuild(self.cur_player['login_id'])

		if not guild:
			return self.sbuilder.throwWebError(404)

		fields.update({self.title: 'News page'})
		fields.update(guild)

		if not 'id' in params:
			return self.sbuilder.redirect('/guilds/'+guild['link_name'])

		news = self.model.guilds.getGuildNews(guild['_id'])['news']

		try:
			news_UID = int(params['id'])
		except Exception:
			news_UID = 0

		if news_UID != 0:
			for story in news:
				if story['UID'] == news_UID:
					fields.update({'story': story})
					break
			else:
				news_UID = 0

		if 'story' in fields:
			fields['story'].update({
				'create_date_f': getReadbleTime(fields['story']['create_date']),
			    'img': self.core.GUILDS_AVATAR_FOLDER+guild['img']
			})

		if not news_UID:
			return self.sbuilder.redirect('/guilds/'+guild['link_name'])

		return basic.defaultController._printTemplate(self, 'news_page', fields)

data = {
	'class': guildsController,
	'type': ['guilds'],
	'urls': ['', 'add', 'settings', 'addnews', 'news', 'story']
}