#!/usr/bin/python
# -*- coding: utf-8 -*-

# author: Alex Shteinikov

import __init__
import settings
import tweepy

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import db
import logger

class MentionsNotifications:

	mongo = db.mongoAdapter()
	balance = settings.balance()
	core = settings.core()

	p_key = core.p_parser_key
	p_secret = core.p_parser_secret

	def __init__(self):
		print 'Loaded '+str(len(self.core.loaded_data['bots']))+' bots:'
		for bot in self.core.loaded_data['bots']:
			print '> @'+bot['name']
		print

		self.setBot(0)

	def setBot(self, bot_id):
		self.bot_id = bot_id
		self.bot = self.core.loaded_data['bots'][bot_id]

	def postNotification(self, notification):
		try:
			auth = tweepy.OAuthHandler(self.p_key, self.p_secret)
			auth.set_access_token(self.bot['token1'].decode('utf-8'), self.bot['token2'].decode('utf-8'))
			api = tweepy.API(auth)
			api.update_status(notification)

		except Exception, e:
			print 'Error post', notification['name'],e



if __name__ == "__main__":

	mn = MentionsNotofications()
	mn.postNotification('@ido_q heya')