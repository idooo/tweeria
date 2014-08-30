# -*- coding: utf-8 -*-

import __init__
import tweepy
import db
import re
import os
import inspect
import datetime
import cherrypy
import time
import memcache_controller
import __main__

from functions import plural, pluralEnd, format_datetime, summAr
from jinja2 import Environment, ModuleLoader, Template, FunctionLoader, FileSystemLoader, ChoiceLoader

def _profile(method_to_decorate):
	def wrapper(*args, **kwargs):
		t_start = time.time()
		result = method_to_decorate(*args, **kwargs)
		t_all = time.time() - t_start
		print method_to_decorate.__name__,'\t', t_all
		return result

	return wrapper

class builder():

	cur_time = datetime.datetime.now()

	loads = 0
	mongo = db.mongoAdapter()
	cache = memcache_controller.cacheController()

	env = Environment(
		auto_reload=True,
		loader=FileSystemLoader(__main__.tweenk_core.APP_DIR+'templates/')
	)

	# print len(env.list_templates('.jinja2')),'templates loaded'

	env.filters['plural'] = plural
	env.filters['pluralEnd'] = pluralEnd
	env.filters['datetime'] = format_datetime
	env.filters['summAr'] = summAr

	def __init__(self, core = None, balance = None):

		if not core:
			core = __main__.tweenk_core
			balance = __main__.tweenk_balance

		self.balance = balance
		self.core_settings = core
		self.base_fields = self.core_settings.base_fields

		self.precompileRegexps()

	def precompileRegexps(self):
		self.RE_if = re.compile("((\{if\s([^\}]*)\})(((?!\{if\s([^\}]*)\}).)*?)(\{endif\}))", re.S+re.M)
		self.RE_vars = re.compile("(\{([^\}]*)\})")
		self.RE_for = re.compile("(\{for\s([^\}]*)\}(.*?)\{endfor\})",re.S+re.M)
		self.RE_load = re.compile("(\{load\:([^\}]*)\})")
		self.RE_comments = re.compile("(\{\*.*?\*\})",re.S+re.M)
		self.RE_mobile = re.compile("(android|iphone)", re.I)

	def isMobileDevice(self):
		if self.core_settings.debug['mobile_debug']:
			return True
		return re.search(self.RE_mobile, cherrypy.request.headers.get('user-agent', ''))

	def setCookie(self, params, age = 604800):
		cookie = cherrypy.response.cookie
		for item in params:
			cookie[item] = params[item]
			cookie[item]['path'] = '/'
			cookie[item]['max-age'] = age
			cookie[item]['version'] = 1

	def getOneCookie(self, cookie_name):
		cookie = cherrypy.request.cookie
		if cookie_name in cookie.keys():
			return cookie[cookie_name].value
		else:
			return False

	def deleteCookie(self, name):
		self.setCookie({name:''},0)

	def getCookie(self):
		cookie = cherrypy.request.cookie
		if 'hash' in cookie.keys() and 'user_id' in cookie.keys():
			return {
				'hash':cookie['hash'].value,
				'user_id': int(cookie['user_id'].value),
				'just_login': 'just_login' in cookie.keys()
			}

	def getLoginCookie(self):
		cookie = cherrypy.request.cookie
		if 'login' in cookie.keys():
			return cookie['login'].value

	def playerLogged(self):

		def updateUserInfo(player):
			p_key = self.core_settings.p_key
			p_secret = self.core_settings.p_secret

			auth = tweepy.OAuthHandler(p_key, p_secret)
			auth.set_access_token(player['token1'], player['token2'])
			api = tweepy.API(auth)
			user = api.me()

			if user.utc_offset:
				utc_offset = user.utc_offset
			else:
				utc_offset = 0

			data = {
				'avatar': user.profile_image_url,
				'utc_offset': utc_offset,
			    'name': user.screen_name,
			}

			updated = {}

			for key in data:
				if data[key] != player[key]:
					updated.update({key: data[key]})

			if updated:
				player.update(updated)
				self.mongo.raw_update('players', {'_id': player['_id']}, {'$set': updated})

			return data

		cookie = self.getCookie()
		if cookie or self.core_settings.always_login:

			if cookie:
				query = {'user_id':int(cookie['user_id'])}
			else:
				query = {'name': self.core_settings.login_name}

			query.update({'banned': {'$exists': 0}})

			player = self.mongo.find('players', query, {
				'name': 1,
				'avatar': 1,
				'lvl': 1,
				'_id': 1,
				'user_id': 1,
				'last_login': 1,
				'session_hash': 1,
				'admin': 1,
			    'resources':1,
			    'faction': 1,
			    'race':1,
			    'token1':1,
			    'token2':1,
			    'class':1,
			    '_guild_name': 1,
			    'moderator':1,
			    'utc_offset':1,
			    'ugc_disabled':1,
			    'ugc_enabled':1
			})

			if not cookie and player:
				cookie = {'hash': player['session_hash'],'user_id':player['user_id']}

			if player:
				if 'session_hash' in player:
					if player['session_hash'] == cookie['hash']:

						if 'just_login' in cookie and cookie['just_login']:
							try:
								updateUserInfo(player)
							except Exception:
								pass

						if 'utc_offset' in player and player['utc_offset']:
							utc_offset = player['utc_offset']
						else:
							utc_offset = 0

						result_hash = {
							'login_name' : player['name'],
							'login_avatar' : player['avatar'],
							'login_lvl' : player['lvl'],
							'login_id' : player['_id'],
							'login_user_id' : player['user_id'],
							'login_faction' : player['faction'],
						    'login_resources': player['resources'],
						    'login_race': player['race'],
						    'login_class': player['class'],
						    'login_race_str': self.balance.races[int(player['faction'])][int(player['race'])],
						    'login_class_str': self.balance.classes[str(player['class'])],
						    'login': True,
						    'login_utc_offset': utc_offset,
						    'login_ugc_disabled': 'ugc_disabled' in player and player['ugc_disabled'],
						    'login_ugc_enabled': 'ugc_enabled' in player and player['ugc_enabled']
							}

						if 'admin' in player and player['admin']:
							result_hash.update({'login_admin': True})
						elif 'moderator' in player and player['moderator']:
							result_hash.update({'login_moderator': True})

						if '_guild_name' in player and player['_guild_name']:
							guild_name = player['_guild_name']
						else:
							guild_name = ''

						result_hash.update({'login_guild': guild_name})

						if 'last_login' in player and player['last_login']>(time.time()-self.core_settings.LAST_LOGIN_TIMEOUT):
							pass
						else:
							self.mongo.update('players', {'user_id':int(cookie['user_id'])}, {'last_login': time.time()})
							if 'last_login' in player and player['last_login'] > time.time() - self.core_settings.MAX_TIME_TO_SLEEP:
								pass
							else:
								message = self.balance.wakeup_message
								message['time'] = time.time()
								self.mongo.raw_update('messages_created', {'user_id': player['user_id']}, {
									'$push': {'last': message}
								})

						return result_hash

		return False

	def createSession(self, user_id):
		auth_hash = self.core_settings.getAuthHash(user_id)
		self.setCookie({'user_id': user_id, 'hash': auth_hash})
		self.mongo.update('players',{'user_id':user_id},{'session_hash':auth_hash})

	def throwWebError(self, error_code = 404, params = {}):

		# Метод обработки ошибок

		error = 'Unknown error'
		if error_code == 404:
			error = 'Page Not Found'

		elif error_code == 1001:
			error = 'Admin auth required'

		elif error_code == 1002:
			error = 'You must <a href="/login">login</a> to see this page '

		elif error_code == 2001:
			if 'invites' in self.core_settings.debug and self.core_settings.debug['invites']:
				self.httpRedirect(self.core_settings.loaded_data['site_address'])

			error = 'Auth Failed'

		elif error_code == 3001:
			error = 'No rights to edit this'

		elif error_code == 4001:
			error = 'Can\'t join to this event. '
			if params:
				error += params

		# item errors
		elif error_code == 5001:
			if params:
				error = params+' not found'
			else:
				error = 'Thing not found'

		elif error_code == 5002:
			if params:
				error = 'This '+params+' was rejected'
			else:
				error = 'This thing was rejected'

		elif error_code == 5003:
			if params:
				error = 'This '+params+' is waiting for approve'
			else:
				error = 'This thing is waiting for approve'

		elif error_code == 5004:
			error = 'Message not found!'

		# lvl <
		elif error_code == 6001:
			error = 'Your level is too low to create new things'

		elif error_code == 7001:
			error = 'Player not found'

		fields = {'error': error, 'code':error_code }

		return self.loadTemplate('error.jinja2', fields)

	def redirect(self, url, text = "Redirecting ... "):
		fields = {'redirect_url':url,'redirect_text':text}
		return self.loadTemplate('redirect.jinja2',fields)

	def httpRedirect(self, url):
		raise cherrypy.HTTPRedirect(url)

	def parseLogin(self, fields = None, param = None):
		auth = tweepy.OAuthHandler(self.core_settings.p_key, self.core_settings.p_secret)
		url = auth.get_authorization_url(True)
		self.setCookie({'login':'yeah'}, 20)
		return self.redirect(url)

	def parseLogout(self, fields = None, param = None):
		self.deleteCookie('hash')
		return self.redirect('index')

	def getMobileTemplates(self):
		re_TMP = re.compile('tmp$')
		mobile_templates = []
		self.mobile_templates = []

		for dirname, dirnames, filenames in os.walk(self.core_settings.MOBILE_TEMPLATES_FOLDER):
			for filename in filenames:
				if re.search(re_TMP, filename):
					buff = os.path.join(dirname, filename)
					buff = buff.replace(self.core_settings.MOBILE_TEMPLATES_FOLDER,'')
					mobile_templates.append(buff)

		self.mobile_templates = mobile_templates

	def findMobileTemplate(self, tmp_name):
		for tmp in self.mobile_templates:
			if tmp == tmp_name:
				return True

		return False

	def prettifyTmpPath(self, tmp_path):
		return tmp_path.replace('./','')

	def loadTextFromFilename(self, filename):
		# для мобильной версии отдельные шаблоны
		fileExt = ""
		filename = self.prettifyTmpPath(filename)
		abspath = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])+'/../'

		fileAr = os.path.splitext(filename)

		if (fileAr[1] != ".jinja2"):
			filename+=".tmp"

		if self.isMobileDevice() and self.findMobileTemplate(filename):
			filename = abspath+self.core_settings.MOBILE_TEMPLATES_FOLDER+filename
		else:
			filename = abspath+self.core_settings.TEMPLATES_FOLDER+filename

		try:
			cache_tmp = self.cache.tmpLoad(filename)
		except Exception:
			cache_tmp = False

		if cache_tmp:
			text = cache_tmp['content']
		else:
			fp = open(filename,'r')

			text = fp.read()
			if not re.match('(\{|\<)',text[:3]):
				text = text[3:]

			try:
				self.cache.tmpSave(filename, text)
			except Exception:
				pass

		return text

	def loadTemplate(self, filename = '', fields = {}, incoming_text = False, useJ = False):

		if not 'current_page' in fields:
			fields.update({
				'current_page': filename,
				'version': self.core_settings.__version__,
				'address': cherrypy.request.path_info[1:],
				'build': self.core_settings.__build__,
				'conf_name': self.core_settings.loaded_data['conf_name']
			})

		if not 'login' in fields:
			fields.update({'login':False})

		fields.update(self.base_fields)

		template = self.env.get_template(filename)
		fields.update({"fields": fields})
		text = template.render(fields)

		return text

if __name__ == '__main__':
	builder = builder()