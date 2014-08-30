# -*- coding: utf-8 -*-

import __init__
import settings

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import time
import datetime

class userinfo():

	def __init__(self, name, id):
		self.screen_name = name
		self.id = id

class retweetedStatus():

	def __init__(self, user):
		self.user = userinfo(user['screen_name'], user['id'])

class sampleTweet():
	text = "Прямо у ворот офиса прорвало трубы с горячей водой. Ведутся вялые раскопки"
	id = 119643098451161088
	retweeted = False
	in_reply_to_user_id = None
	created_at = datetime.datetime.fromtimestamp(time.time()-3000)

	def __init__(self, text=0, entities=None, retweet=None, source = None):
		if not entities: entities = {}
		if text != 0:
			self.text = text

		if entities:
			self.entities = entities

		if source:
			self.source = source
		else:
			self.source = u'asdasd'

		if retweet:
			self.retweeted_status = retweetedStatus(retweet['user'])


class tmer():

	def __init__(self):
		pass

	def start(self):
		self.t = time.time()

	def stop(self):
		n = time.time() - self.t
		return n

if __name__ == '__main__':

	_INTERACTIONS = True

	import tweet_parser

	timer = tmer()
	t = time.time()
	tweet = sampleTweet()

	tweet_samples = {
		'tweet_hash': sampleTweet(u"тестовое сообщение с тегом #pinnacle",{u'user_mentions': [], u'hashtags': [{u'indices': [30, 37], u'text': u'pinnacle'}], u'urls': []}),
		'tweet_normal': sampleTweet(u"тратата но у нас же авторизация не через гет",{u'user_mentions': [], u'hashtags': [], u'urls': []}),

		'tweet_hashtag_mention_non_player': sampleTweet(u"@non_player но у нас же авторизация не через гет #pinnacle",{u'user_mentions': [{u'id': 111, u'indices': [0, 10], u'id_str': u'111', u'screen_name': u'non_player'}], u'hashtags': [{u'indices': [30, 37], u'text': u'pinnacle'}], u'urls': []}),
		'tweet_hashtag_mention_player': sampleTweet(u"@Lord_MorTis но у нас же авторизация не через гет #pinnacle",{u'user_mentions': [{u'id': 46834560, u'indices': [0, 10], u'id_str': u'46834560', u'screen_name': u'Lord_MorTis'}], u'hashtags': [{u'indices': [30, 37], u'text': u'pinnacle'}], u'urls': []}),

		'tweet_mention_player': sampleTweet(u"@nosynq но у нас же авторизация не через гет",{u'user_mentions': [{u'id': 154952044, u'indices': [0, 10], u'id_str': u'154952044', u'screen_name': u'nosynq'}], u'hashtags': [], u'urls': []}),
		'tweet_mention': sampleTweet(u"@non_player но у нас же авторизация не через гет",{u'user_mentions': [{u'id': 25709577, u'indices': [0, 10], u'id_str': u'25709577', u'screen_name': u'non_player'}], u'hashtags': [], u'urls': []}),

		'tweet_rt_non_player': sampleTweet(u"о у нас же авторизация не через гет",{u'user_mentions': [], u'hashtags': [], u'urls': []}, retweet={'user': {'screen_name':'tweehex', 'id':802711830}}),
		'tweet_rt_player': sampleTweet(u"о у нас же авторизация не через гет",{u'user_mentions': [], u'hashtags': [], u'urls': []}, retweet={'user': {'screen_name':'Lord_MorTis', 'id':46834560}}),

		'tweet_spell_self': sampleTweet(u"bless :D",{u'user_mentions': [], u'hashtags': [], u'urls': []}),
		'tweet_spell': sampleTweet(u" но у нас же авторизация не через гет water",{u'user_mentions': [], u'hashtags': [], u'urls': []}),

		#

		'tweet_keyword': sampleTweet(u"майка но у нас же авторизация не через гет",{u'user_mentions': [], u'hashtags': [], u'urls': []}),
		'tweet_keyword2': sampleTweet(u"Между мы любим! но у нас же авторизация не через гет",{u'user_mentions': [], u'hashtags': [], u'urls': []}),
		'tweet_normal_MAT': sampleTweet(u"хуй         ",{u'user_mentions': [], u'hashtags': [], u'urls': []}),
		'tweet_normal_game': sampleTweet(u"◇ game tweet",{u'user_mentions': [], u'hashtags': [], u'urls': []}),
		'tweet_mention_ignored': sampleTweet(u"Владимир, если красота уйдёт, значит, это не та красота. http://vk.cc/14SAFu ",{u'user_mentions': [{u'id': 12164662, u'indices': [0, 10], u'id_str': u'12164662', u'screen_name': u'ido_q'}], u'hashtags': [], u'urls': []}),

		'tweet_mention_player_attack_spell': sampleTweet(u"@tweehex но у нас же авторизация не !arrow через гет",{u'user_mentions': [{u'id': 802711830, u'indices': [0, 10], u'id_str': u'802711830', u'screen_name': u'tweehex'}], u'hashtags': [], u'urls': []}),
		'tweet_mention_player_forced': sampleTweet(u"@tweehex но у нас же авторизация не через гет #die",{u'user_mentions': [{u'id': 802711830, u'indices': [0, 10], u'id_str': u'802711830', u'screen_name': u'tweehex'}], u'hashtags': [{u'indices': [30, 37], u'text': u'die'}], u'urls': []}),

		'tweet_mention_player_buff_spell': sampleTweet(u"@tweehex но у нас же авторизация не !!bless через гет",{u'user_mentions': [{u'id': 802711830, u'indices': [0, 10], u'id_str': u'802711830', u'screen_name': u'tweehex'}], u'hashtags': [], u'urls': []}),
		'tweet_mention_player_debuff_spell': sampleTweet(u"@tweehex но у нас же авторизация не !curse через гет",{u'user_mentions': [{u'id': 802711830, u'indices': [0, 10], u'id_str': u'802711830', u'screen_name': u'tweehex'}], u'hashtags': [], u'urls': []}),

		'smpl': sampleTweet(u"@BrotherKombarov Это вам спасибо, Дмитрий, вы сегодня выдали супер игру.",{u'user_mentions': [{u'id': 214124, u'indices': [0, 10], u'id_str': u'124124', u'screen_name': u'adsasd'}], u'hashtags': [{u'indices': [30, 37], u'text': u'дзюбадзюбазабивай'}], u'urls': []}),

		'game_tweet': sampleTweet(u"I've earned new achievement [Good Luck] - http://t.co/mszLq8uz #tweeria",{u'user_mentions': [], u'hashtags': [{u'indices': [30, 37], u'text': u'tweeria'}], u'urls': []}, source=u"<a href=\"http://tweeria.com\" rel=\"nofollow\">Tweeria</a>"),
		'game_tweet2': sampleTweet(u"I've earned new achievement [Good Luck] - http://t.co/mszLq8uz #tweeria",{u'user_mentions': [], u'hashtags': [{u'indices': [30, 37], u'text': u'tweeria'}], u'urls': []}, source=u"<a href=\"http://twitter.com/tweetbutton\" rel=\"nofollow\">Tweet Button</a>"),

		'tweet_hash2': sampleTweet(u"тестовое сообщение с тегом #pirates",{u'user_mentions': [], u'hashtags': [{u'indices': [30, 37], u'text': u'pirates'}], u'urls': []}),

		}

	timer.start()
	parser = tweet_parser.tweetParser(debug = True)
	print '# INIT COMPLETE', timer.stop()

	timer.start()

	parser.changePlayer(12164662, restore_health=True)

	print '# CHANGE PLAYER COMPLETE', timer.stop()
	timer.start()

	#parser.changePlayer(802711830, restore_health=True)
	parser.player['pvp'] = 0
	parser.parse(tweet_samples['tweet_normal'])
	if False:
		for sample in tweet_samples:
			print '# ', sample
			print '# ', sample
			print '# ', sample

			parser.parse(tweet_samples[sample])

			print '# ############################', sample


	print '# PARSE 1 COMPLETE', timer.stop()
	timer.start()

	parser.movingPlayer()

	print '# MOVING COMPLETE', timer.stop()
	timer.start()

	parser.getNotifications()

	print '# GET NOTIFICATIONS COMPLETE', timer.stop()
	timer.start()

	parser.savePlayerData()

	print '# SAVE PLAYER DATA COMPLETE', timer.stop()
	timer.start()

	if _INTERACTIONS:
		parser.interactions.sort(key=lambda x: x['to']['id'])

		while parser.interactions:
			interaction = parser.interactions.pop()

			if parser.player['user_id'] != interaction['to']['id']:
				parser.changePlayer(interaction['to']['id'])

			parser.parse(interaction)
			parser.savePlayerData()

	parser.processEvents()

	print '# EVENTS COMPLETE', timer.stop()
	timer.start()

	parser.saveCurrentEvents()
	parser.finalDataSave()


	print '# FINAL DATA SAVE COMPLETE', timer.stop()
	timer.start()

	print
	print 'time > ', str(time.time()-t)
