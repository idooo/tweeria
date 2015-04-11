# -*- coding: utf-8 -*-

# Core and balance settings
#
# author: Alex Shteinikov

import random
import logger
import md5
from time import time
import __main__
import sys, os, inspect
import ConfigParser
import pprint
from bson import ObjectId

def _profile(method_to_decorate):
	def wrapper(*args, **kwargs):
		t_start = time()
		result = method_to_decorate(*args, **kwargs)
		t_all = time() - t_start
		print method_to_decorate.__name__,'\t', t_all
		return result

	return wrapper

class CoreConfigParser():

	debug_var_names =  [
		'mobile_debug',
		'always_monster',
	    'always_boss',
	    'always_drop',
	    'load_deprecated_tweets',
	    'invites',
	    'pickup_all_items',
	    '2x_rate',
	    'ignore_radius',
	    'always_create_fvf',
	    'create_by_invite'
	]

	def __init__(self):

		try:
			print '> Loading', sys.argv[1], 'config for Twitter'
		except Exception:
			print '> Loading default config for Twitter'
			try:
				sys.argv[1] = 'default'
			except Exception:
				sys.argv.append('default')

		self.conf_str_name = sys.argv[1]

		self.conf_name = os.path.join(os.path.dirname(__file__)+'/../conf/', sys.argv[1]+'.conf')
		self.config = ConfigParser.ConfigParser()
		self.config.read(self.conf_name)

	def prettyStr(self, datastr):
		return datastr[1:len(datastr)-1]

	def readData(self):
		try:
			p_key = self.prettyStr(self.config.get('parser','auth.key'))
			p_secret = self.prettyStr(self.config.get('parser','auth.secret'))
			p_parser_key = self.prettyStr(self.config.get('parser','parser.key'))
			site_address = self.prettyStr(self.config.get('global','tweenk.host'))
			p_parser_secret = self.prettyStr(self.config.get('parser','parser.secret'))
			db_host = self.prettyStr(self.config.get('database','db.host'))
			db_port = int(self.config.get('database','db.port'))
			db_user = self.prettyStr(self.config.get('database','db.user'))
			db_passw = self.prettyStr(self.config.get('database','db.pass'))
			db_name = self.prettyStr(self.config.get('database','db.name'))

			fields = {
				'p_key':p_key,
				'p_secret':p_secret,
				'p_parser_key':p_parser_key,
				'p_parser_secret':p_parser_secret,
				'db_host':db_host,
				'site_address': 'http://' + site_address + '/',
				'db_port':db_port,
				'db_user':db_user,
				'db_passw':db_passw,
				'db_name':db_name,
			    'conf_name': self.conf_str_name
				}

		except Exception, e:
			print '>>> Error! Unable to load config data'
			print str(e)
			exit()

		try:
			always_login = self.config.get('debug','user.login')
			login_name = self.prettyStr(self.config.get('debug','user.name'))

			fields.update({
				'always_login': always_login,
			    'login_name': login_name
			})

		except Exception:
			pass

		bots = []

		try:
			utc_global_offset = int(self.config.get('global','utc.offset'))
			fields.update({
				'utc_global_offset': utc_global_offset
			})
		except Exception:
			fields.update({
				'utc_global_offset': 0
			})

		try:
			for i in [1]:
				str_i = str(i)
				bot = {
					'name': self.prettyStr(self.config.get('bots', str_i+'.name')),
					'token1': self.prettyStr(self.config.get('bots', str_i+'.token1')),
					'token2': self.prettyStr(self.config.get('bots', str_i+'.token2'))
				}
				bots.append(bot)

		except Exception:
			pass

		fields.update({'bots': bots})

		debug_vars = {}
		for param in self.debug_var_names:
			try:
				buff = self.config.get('debug', param)
			except Exception:
				buff = False

			debug_vars.update({param: buff})

		fields.update({'debug': debug_vars})

		return fields

class core():

	BLOG_FEED_URL = 'http://tweeria.wordpress.com/feed/'

	MAX_TIME_TO_SLEEP = 7776000

	FINISHED_EVENTS_LIFETIME = 1209600

	loaded_data = {}

	log = logger.logger('/logs/parser.log')

	__version__ = u"2.3.2b"

	APP_DIR = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])+'/../'

	TEMPLATES_FOLDER = './templates/'
	MOBILE_TEMPLATES_FOLDER = './templates/mobile/'

	DELETED_ARTWORK_IMG = './data/artwork_delete.jpg'

	TMP_IMG_PATH = './templates/data/buffer/'
	PATH_FOR_UPLOADED_IMAGES = APP_DIR+'templates'
	RESIZED_IMG_PATH = './data/resized_image/'
	GUILDS_AVATAR_FOLDER = './data/resized_image/guilds_avatars/'
	GUILD_DEF_AVATAR = './data/guild_default.jpg'

	MAX_UPLOAD_FILE_SIZE = 256000 # 250kb
	MAX_AVA_WIDTH = 200
	MAX_AVA_HEIGHT = 200

	MAX_ARTWORK_UPLOAD_FILE_SIZE = 1598464 #1.5Mb
	MAX_ARTWORK_WIDTH = 600
	MAX_ARTWORK_HEIGHT = 1000

	THUMB_ARTWORK_WIDTH = 240
	THUMB_ARTWORK_HEIGHT = 400

	MAX_ITEM_SPELL_WIDTH = 100
	MAX_ITEM_SPELL_HEIGHT = 100

	THUMB_ITEM_SPELL_WIDTH = 56
	THUMB_ITEM_SPELL_HEIGHT = 56

	IMAGE_BUFFER_FOLDER = '/data/buffer/'
	IMAGE_GEN_FOLDER = './data/generated/'

	ARTWORK_PATH = '/data/characters/'
	ARTWORK_SHOP_PATH = ARTWORK_PATH

	IMAGE_ACHV_FOLDER = './data/achvs/'
	IMAGE_SPELL_FOLDER = './data/spells/'

	LAST_LOGIN_TIMEOUT = 3600

	IMAGE_GEN_SOURCE_FOLDER = './data/to_generator/'
	IMAGE_RACE = {'Human':'human', 'Orc':'orc', 'Troll':'troll', 'Elf':'elf','Undead':'undead','Dwarf':'dwarf'}

	CACHE_TIME = 30
	TMP_CACHE_TIME = 1

	md5_pass_phrase = 'none'
	md5_invite_phrase = 'none'


	# MAP settings
	# hex sizes
	HEX_WIDTH = 36
	HEX_HEIGHT = 40

	HEX_LEFT = 3
	HEX_TOP = 0

	HEX_TOP_MINUS = 32

	# map size
	MAP_WIDTH = 59
	MAP_HEIGHT = 49

	# -------------

	# pathfinding and moving

	PATH_MINOR_P = 5
	PATH_MAJOR_P = 25
	PATH_SUPER_P = 40

	AREA_PVP = {'x':[21,37], 'y': [17, 30]}

	# -------------

	max_stored_messages = 20
	max_guild_stored_messages = 20
	max_notable_messages = 5

	# DEBUG VARS
	always_login = False

	# for elfrey mpr
	pp = pprint.PrettyPrinter(indent=4)

	def __init__(self):
		config_loader = CoreConfigParser()
		self.loaded_data = config_loader.readData()

		self.HOST = self.loaded_data['site_address']

		# Twitter API keys
		self.p_key = self.loaded_data['p_key']
		self.p_secret = self.loaded_data['p_secret']

		# Twitter parser API keys
		self.p_parser_key = self.loaded_data['p_parser_key']
		self.p_parser_secret = self.loaded_data['p_parser_secret']

		self.server_utc_offset = self.loaded_data['utc_global_offset']

		# DEBUG
		if 'always_login' in self.loaded_data:
			self.always_login = self.loaded_data['always_login']
			if self.always_login:
				self.login_name = self.loaded_data['login_name']

		self.debug = self.loaded_data['debug']

		self.conf_name = config_loader.conf_name

		self.base_fields = {'host': self.HOST}

		self.getBuildInfo()

	def getAuthHash(self, user_id):
		return md5.new(str(user_id)+self.md5_pass_phrase).hexdigest()

	def getBuildInfo(self):
		result = os.popen('git log | grep "^commit" | wc -l')
		lines = result.readlines()

		self.__build__ = int(lines[0])

	def getInviteHash(self):
		return md5.new(self.md5_invite_phrase).hexdigest()

	def getAvatarLink(self, guild):
		if not 'img' in guild or guild['img'] == 'none' or not guild['img']:
			return self.GUILD_DEF_AVATAR
		else:
			return self.GUILDS_AVATAR_FOLDER+guild['img']

	def mpr(self,what):
		self.pp.pprint(what)
		return what

	def relativePosition(self, coords):
		TOP_SHIFT = self.HEX_TOP
		if coords['x'] % 2 == 1:
			TOP_SHIFT = self.HEX_TOP_MINUS

		x = coords['x'] * self.HEX_WIDTH + self.HEX_LEFT
		y = coords['y'] * self.HEX_HEIGHT + TOP_SHIFT

		return {'x': x, 'y': y}

	def getMap(self):
		import db
		mongo = db.mongoAdapter()
		coords_array = mongo.getu('map', sort={'y': 1, 'x': 1})
		map = [[]]

		x = 0
		y = 0

		for item in coords_array:
			if x < self.MAP_WIDTH:
				pass
			else:
				map.append([])
				x = 0
				y += 1

			map[y].append([item['tile'],item['elevation']])
			x += 1

class balance():

	rejected_reasons = [
		'Low quality artwork', #0
		'Not a fantasy artwork', #1
		'Not a fantasy item', #2
		'Not a fantasy spell', #3
		'Not a good name', #4
		'Not a good description', #5
		'Duplicating artwork', #6
	    'Forbidden content', #7
	    'Copyright problem' #8
	]

	item_reject_reasons = [0,1,2,4,5,6,7,8]
	spell_reject_reasons = [0,1,3,4,5,6,7,8]
	artwork_reject_reasons = [0,1,4,5,6,7,8]

	categories = [
		{'name': 'Classic fantasy' , 'value': 'Classic'},
		{'name': 'Anime content' , 'value': 'Anime' },
		{'name': 'Comics related', 'value': 'Comics'},
		{'name': 'Steampunk', 'value': 'Steampunk'},
		{'name': 'Holidays related', 'value': 'Holidays'},
		{'name': 'Pixel', 'value': 'Pixel'},
		{'name': 'Fun items', 'value': 'Fun'}
	]

	decline_reasons = [
		{
			'name': "No portfolio",
			'value': "Portfolio link doesn't exist or not working. Please send us a working link to your art."
		},
	    {
	        'name': 'Not proven portfolio',
	        'value': "There is not enough proves to authorise you and your portfolio. PLease provide additional information."
	    },
	    {
		    'name': 'Low quality',
	        'value': "Your works is not good enough to place in Tweeria."
	    },
	    {
		    'name': 'Wrong theme',
	        'value': "Themes of your works do not fit typical medieval fantasy setting."
	    },
	    {
		    'name': '...',
		    'value': ""
	    }
	]

	# minimal level to create content
	MIN_LEVEL_TO_CREATE = 1

	# MONSTERS_GEO
	GEO_MONSTERS = [
		{'x1': 0, 'y1':0, 'x2': 59, 'y2': 49, 'lvl_min': 40, 'lvl_max': 60},
		{'x1': 4, 'y1':3, 'x2': 54, 'y2': 44, 'lvl_min': 25, 'lvl_max': 45},
		{'x1': 8, 'y1':6, 'x2': 50, 'y2': 41, 'lvl_min': 17, 'lvl_max': 30},
		{'x1': 12, 'y1':10, 'x2': 46, 'y2': 37, 'lvl_min': 7, 'lvl_max': 20},
		{'x1': 16, 'y1':13, 'x2': 42, 'y2': 34, 'lvl_min': 0, 'lvl_max': 10}
	]

	# chance to add item into the items pool
	CHANCE_TO_POOL = 20
	CHANCE_FROM_POOL = 20
	POOLED_MAX_TIME = 604800

	#
	max_lvl = 60

	# in pvp ..
	CHANCE_TO_ATTACK_MONSTER = 50

	# monster level penalty
	DIFF_MONSTER_LVL = 4
	CHANCE_TO_AFRAID = 90
	DIFF_MONSTER_LVL_100 = 7

	# quest length
	QUEST_LEN = 86400

	# craft items
	ORE_COST_PER_ITEM = 0

	MAX_STATS_ITEM_CREATE = {
		'25': 75,
	    '30': 100,
	    '40': 150,
	    '45': 200,
	    '50': 250,
	    '55': 300,
	    '60': 350
	}

	# chance to select direction way
	CHANCE_DIRECTION = 80

	# -------------
	# inventory

	INVENTORY_SIZE = 16

	# --------------------------------------------------------------------------------------------------
	# Events
	#
	max_events = 5

	LENGTH_OF_RAID = 3600
	LENGTH_OF_WAR = 3600
	LENGTH_OF_FVF = 10800

	# Leadership
	LEAD = [
			{"min": -1, "max": 0, "min_fol": 25, "lead": 1},
			{"min": 1, "max": 2, "min_fol": 100, "lead": 2},
			{"min": 3, "max": 6, "min_fol": 200, "lead": 3},
			{"min": 7, "max": 10, "min_fol": 400, "lead": 4},
			{"min": 11, "max": 15, "min_fol": 800, "lead": 5},
			{"min": 16, "max": 24, "min_fol": 1500, "lead": 6},
			{"min": 25, "max": 36, "min_fol": 3000, "lead": 7},
			{"min": 37, "max": 59, "min_fol": 6000, "lead": 8},
			{"min": 60, "max": 99, "min_fol": 12000, "lead": 9},
			{"min": 100, "max": 10000000, "min_fol": 24000, "lead": 10}
	]

	AUTHOR_EVENT_BONUS = 2

	# Max active spells
	MAX_ACTIVE_SPELLS = 5
	MAX_ACTIVE_BUFFS = 3

	stats_name = {
		"str":     "Strength",
		"dex":     "Dexterity",
		"int":     "Intellect",
		"luck":    "Luck",
		"DEF":     "Defense",
		"DMG":     "Damage",
		"HP":      "Hit points",
		"MP":      "Mana points",
		"lead":    "Leaderhip",
		"karma":   "Karma",
		"fame":    "Fame",
		"SPD":     "Speed",
	    'mastery': "Mastery"
	}

	resources = {
		"prg": "Magic pergament",
		"ore": "Iron Ore",
		"eore": "Enchanted Ore",
		"gold": "Gold"
	}

	item_types = ['0','Weapon','2','3','Helm','Necklace','Ring','Boots','Waist','Wrist','Gloves','Legs','Chest','Shoulders']

	faction = ['Northern Expansion', 'Human Alliance', 'Free Tribes']

	races = [['Undead', 'Faceless'],['Human', 'Elf'],['Orc', 'Troll']]

	welcome_message = {
		"message": "Welcome to Tweeria. Just keep writing tweets and look at your hero",
		"data": {
			"player": "_",
			"time": 0,
		    'message_UID': 1000
		}
	}

	wakeup_message = {
		"message": "Hooray! Player woke up and continued his legendary journey",
		"data": {
			"player": "_",
			"time": 0,
			'message_UID': 1000
		}
	}

	guild_message = {
		"message": "Guild was created",
		"data": {
			"time": 0,
			'message_UID': 1001
		}
	}

	# Tweets

	# posting after registration

	REGISTRATION_TWEET = "I've joined Tweeria: Lazy Twitter #RPG! Join me and get some luck for free!"

	# ---------

	started_locations = [
		{'x': 29, 'y': 15},
		{'x': 19, 'y': 32},
		{'x': 39, 'y': 31}
	]

	# ----------
	PVP_RADIUS = 6
	PVP_LVL_DIFF = 10
	PVP_FORCE = u'pewpew'

	PVP_GVG_REWARD = 10
	GVG_GUILD_WIN_REWARD = 3
	GVG_GUILD_LOOSE_REWARD = 1

	MAX_GVG_CREATED = 2 # per one author

	GVG_POINTS = [
		[27,23],[28,23],[29,22],[30,23],[31,23],[28,24],[29,23],
		[30,24],[31,24],[30,25],[31,25],[27,26],[28,26],[29,26],
		[30,27],[28,27],[29,27]
	]

	GVG_RADIUS = 3
	RAID_RADIUS = 3
	FVF_RADIUS = 5

	# FVF options

	FVF_POINT = {'x': 29, 'y': 24}

	PVP_FVF_REWARD = 15
	PVP_FVF_LOOSE_REWARD = 3

	# fvf creates ones per this time
	FVF_CREATE_TIME = 86400

	# fvf start time random edges
	FVF_START_TIME_MIN = 21600
	FVF_START_TIME_MAX = 64800

	# fvf hashtags
	FVF_HASHES = ['north','alliance','tribes']

	# ----------
	# resources drop rates

	DROP_ORE_P = {
		'monster':  2,
	    'boss':     5,
	    'pvp':      2,
	    'craft':    [5, 100],
	    'sell':     [5, 100]
	}

	DROP_ENCHORE_P = {
		'monster':  0,
		'boss':     2,
		'pvp':      1,
		'raid':     4,
		'craft':    [5, 100],
		'sell':     [10, 50]
	}

	DROP_PARCH_P = {
		'monster':  2,
		'boss':     4,
		'pvp':      2,
		'raid':     5,
		'craft':    [5, 100],
		'sell':     [10, 100]
	}

	DROP_RES_P = {
		'ore': DROP_ORE_P,
	    'eore': DROP_ENCHORE_P,
	    'prg': DROP_PARCH_P
	}

	def getResDropChances(self, situation = 'none'):
		drop_result = {}
		for drop_name in self.DROP_RES_P:
			if situation in self.DROP_RES_P[drop_name]:
				drop_result[drop_name] = self.chance(self.DROP_RES_P[drop_name][situation])
			else:
				drop_result[drop_name] = 0

		return drop_result

	# ----------

	def __init__(self):
		self.getSettings()

	def getItemMinCost(self, params):
		return int(float(params['lvl'])*(10+float(params['lvl'])/10))

	def getSettings(self):
		import db
		mongo = db.mongoAdapter()
		settings_raw = mongo.find('settings')

		self.classes = {}
		self.priority_stats = {}
		self.available_weapons = {}
		self.starter_equip = {}
		self.damage_type = {}
		self.classes_stats = {}
		self.classes_and_races = {}

		artworks = mongo.getu('artworks', {'default': 1}, {'_id': 1, 'img':1, 'faction':1, 'race':1, 'class':1})

		self.default_artworks = {}
		for artwork in artworks:
			self.default_artworks.update({
				str(artwork['faction'])+str(artwork['race'])+str(artwork['class']): {
					'src': artwork['img'],
				    '_id': artwork['_id']
				}
			})

		if settings_raw:
			for class_id in settings_raw['classes']:
				item = settings_raw['classes'][class_id]
				self.classes.update({class_id: item['name']})
				self.priority_stats.update({class_id: item['priority_stat']})
				self.available_weapons.update({class_id: item['available_weapons'].split(';')})
				self.starter_equip.update({class_id: map(int, item['starter_equip'].split(';'))})
				self.damage_type.update({class_id: item['damage_type']})
				self.classes_stats.update({class_id: settings_raw['classes_stats'][class_id]})

			self.classes_and_races = self.getClassesAndRaces()

	def getClassesAndRaces(self):
		races = []
		for i in range(0, len(self.races)):
			for j in range(0, len(self.races[i])):
				races.append({
					'name': self.races[i][j],
					'faction': i,
					'race': j,
					'value': str(i)+':'+str(j)
				})

		classes = []
		for i in self.classes:
			classes.append({
			'name': self.classes[i],
			'value': str(i)
			})

		return {
			'races': races,
			'classes': classes
		}

	def chance(self, percent):
		return random.randint(1,100) > (100-percent)

	def monsterMeetChance(self, tweet_length = 83):
		return self.chance(int(float(tweet_length * 0.9)))

	def bossMeetChance(self):
		return self.chance(33)

	def checkNormalDrop(self):
		return self.chance(50)

	def checkPoolDrop(self):
		return self.chance(self.CHANCE_FROM_POOL)

	def checkDungeonDrop(self):
		return self.chance(80)

	def checkRareDrop(self):
		return self.chance(75)

	def checkEpicDrop(self):
		return self.chance(25)

	def meetPeasantSuccess(self):
		return self.chance(90)

	def meetPlayerSuccess(self):
		return self.chance(80)

	def meetPVPSuccess(self):
		return self.chance(50)

	def isNewItemBetter(self, current_item, new_item, player_class_id):

		cur = 0
		new = 0

		for stat in ['dex','int','str','luck']:
			if not stat in current_item:
				current_item[stat] = 0

			if not stat in new_item:
				new_item[stat] = 0

			if stat == self.priority_stats[str(player_class_id)]:
				cur += current_item[stat] * 35
				new += new_item[stat]*35
			else:
				cur += current_item[stat]*10
				new += new_item[stat]*10

		for stat in ['DMG','DEF','HP','MP']:
			if stat in current_item:
				cur = cur + current_item[stat]

			if stat in new_item:
				new = new + new_item[stat]

		return new>cur

	def isItemForClass(self, item, player_class_id):
		return item['view'] in self.available_weapons[str(player_class_id)]

	def getRejectReasons(self, numbers):
		reasons = []
		for number in numbers:
			try:
				reasons.append({
				'id': number,
				'name': self.rejected_reasons[number]
				})
			except Exception:
				pass

		return reasons

	def getMaxStatsForItemCreate(self, lvl):
		str_lvl = str(lvl)
		result = 50

		for condition in self.MAX_STATS_ITEM_CREATE:
			if condition <= str_lvl:
				result = self.MAX_STATS_ITEM_CREATE[condition]
			else:
				break

		return result


class databaseSettings():

	# aliases for DB collections

	def __init__(self):
		pass

	cols = {
		'players': 'players',
		'guilds': 'guilds',

		'col_items': 'items',
		'col_created': 'items_created',
		'col_crafted': 'items_crafted',
		'col_shop_items': 'shop_items',
	    'col_items_deleted': 'items_deleted',
	    'col_items_likes': 'items_likes',
	    'col_items_reports': 'items_reports',
	    'col_items_pool': 'items_pool',
		'col_artworks': 'artworks',

		'col_spellbooks': 'spellbooks',
		'col_spells': 'spells',
		'col_spells_created': 'spells_created',
		'col_spells_crafted_patterns': 'spells_crafted_patterns',
		'col_spells_actions': 'spells_actions',

		'col_events': 'events',

		'col_dungeons': 'dungeons',
		'col_locations': 'locations',

	    'col_monsters': 'monsters',

	    'col_achv_static': 'achievements_static',
		'col_achvs': 'achievements',
	    'col_stats_static': 'statistics_static',
	    'col_stats': 'statistics',

	    'authors_likes': 'authors_likes',

		'meta_actions': 'meta_actions',
	    'actions': 'actions',

		'authors_requests': 'authors_requests',

	    'col_messages': 'messages',
	    'col_messages_created': 'messages_created',
	    'col_guild_messages': 'guild_messages',
	    'col_guilds_news': 'guilds_news',

	    'col_invites': 'invites',
		'col_tweeria_log': 'tweeria_log',

	    'col_beta_players': 'beta_players',
	    'col_beta_items': 'beta_items',
	    'col_beta_spells': 'beta_spells',
	    'col_beta_artworks': 'beta_artworks',

	    'col_gamestats': 'game_statistics',

		'col_admin_bad_people': 'admin_bad_people'
	}

class BaseObj():

	data = {}

	def __init__(self, record):
		self.data.update(record)

	def __setitem__(self, key, value):
		self.data[key]= value

class _obj():

	id = 0

	def __init__(self, _id):

		if not isinstance(_id, ObjectId):
			_id = ObjectId(_id)

		self.id = _id

	def __setitem__(self, value):
		self.id = value

	def __getitem__(self):
		return self.id

if __name__ == '__main__':
	bal = balance()
else:
	database = databaseSettings()