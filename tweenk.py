# -*- coding: UTF-8 -*-

# This is Tweeria server application
# You can find routing settings here, adapters for db
# and caching

import __init__
import inspect
import settings

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import cherrypy
import site_builder
import informer
import db
import time
from sets import Set
import memcache_controller
from controllers_loader import controllersLoader
from bson import ObjectId

class TweenkApp():

	exposed = True

	cache = memcache_controller.cacheController()
	cache.cleanCache()

	controller = controllersLoader()
	mongo = db.mongoAdapter()

	caching = True
	debug = False

	pages = Set()

	def __init__(self):
		self.page_runners = {}
		pages = []
		for item in self.controller.alias:
			for type_of_method in item['type']:
				if not type_of_method in self.page_runners:
					self.page_runners.update({type_of_method:[item]})
				else:
					self.page_runners[type_of_method].append(item)

		for runner in self.page_runners:
			if 'default' in self.page_runners[runner][0]['type']:
				pages += self.page_runners[runner][0]['urls']
			else:
				pages += self.page_runners[runner][0]['type']

		for item in pages:
			self.pages.add(item)

	def _getCachedContent(self, page):
		from_cache = False
		save_cache = False
		if not self.cache.isPlayer():
			loaded = self.cache.cacheLoad(page, cherrypy.request.query_string)

			if not loaded:
				save_cache = True
			else:
				from_cache = True

		if from_cache:
			page_content = loaded['content']
		else:
			page_content = False

		if self.debug:
			print ''
			print page, cherrypy.request.query_string
			print ' — from cache', from_cache
			print ' — save cache', save_cache

		return {'content': page_content, 'need_save': save_cache}

	def _setCachedContent(self, page, page_content):
		self.cache.cacheSave(page, cherrypy.request.query_string, page_content)

	def _load(self, func_name, page, params):
		for variant in self.page_runners[func_name]:
			if page in variant['urls']:

				if self.caching:
					page_content = self._getCachedContent(page)
					if not page_content['content']:
						page_content['content'] = self.controller.controllers[variant['name']].printPage(page, params)

					if page_content['need_save']:
						self._setCachedContent(page, page_content['content'])

				else:
					page_content = {'content': self.controller.controllers[variant['name']].printPage(page, params)}

				return page_content['content']

		return builder.throwWebError(params=params)

	def _force(self, controller_name, page, params):
		if self.caching:
			page_content = self._getCachedContent(page)
			if not page_content['content']:
				page_content['content'] = self.controller.controllers[controller_name].printPage(page, params)

			if page_content['need_save']:
				self._setCachedContent(page, page_content['content'])

		else:
			page_content = {'content': self.controller.controllers[controller_name].printPage(page, params) }

		return page_content['content']

	def index(self, **params):
		return self._load(inspect.stack()[0][3],'index', params)

	def default(self, page, **params):
		if page in self.pages:
			return self._load(inspect.stack()[0][3], page, params)

		return self._force('player', page, params)

	def a(self, page, **params):
		return self._load(inspect.stack()[0][3], page, params)

	def u(self, page, **params):
		return self._load(inspect.stack()[0][3], page, params)

	def guilds(self, guild_name = '', **params):

		guild_name = guild_name.replace("_", " ")
		guild_exists = self.mongo.find('guilds', {'name': guild_name}, {'_id': 1})

		if guild_exists:
			return self._force('guild', guild_name, params)
		else:
			return self._load(inspect.stack()[0][3], guild_name, params)

	def events(self, event_id = '', **params):
		try:
			_id = ObjectId(event_id)
			event = self.mongo.find('events', {'_id': _id}, {'_id': 1})

		except Exception:
			event = False

		if event:
			return self._force('events', event_id, params)
		else:
			return self._load(inspect.stack()[0][3], event_id, params)

	def obj(self,obj_type, guid = 0,prefix = 0,suffix = 0):
		#page = str(obj_type)+'/'+str(guid)+'/'+str(prefix)+'/'+str(suffix)
		text = informer.getInfo(obj_type,guid,prefix,suffix)
		return text

	obj.exposed = True
	index.exposed = True
	default.exposed = True
	u.exposed = True
	a.exposed = True
	guilds.exposed = True
	events.exposed = True

root = TweenkApp()

if __name__ == '__main__':

	print '# ----------------------------------------- #'
	print '#  Tweeria version:', tweenk_core.__version__, 'build:', tweenk_core.__build__
	print '# ----------------------------------------- #'

	builder = site_builder.builder(tweenk_core, tweenk_balance)
	informer = informer.Informer()
	cherrypy.quickstart(TweenkApp(), config=tweenk_core.conf_name)
else:
	cherrypy.tree.mount(TweenkApp(), config=tweenk_core.conf_name)