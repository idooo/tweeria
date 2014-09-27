#!/usr/bin/python
# -*- coding: utf-8 -*-

# Wordpress integration
# author: Alex Shteinikov

import __init__
import settings
from time import strftime
from dateutil.parser import parse
import datetime

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import db
import logger
import re
import tweepy

class LBIntegration():

	mongo = db.mongoAdapter()
	log = logger.logger('logs/system_events.log')
	core = tweenk_core

	user_name = 'tweeria'
	_news_hashtag = 'news'

	RE_SUB = re.compile('#'+_news_hashtag, re.IGNORECASE+re.UNICODE+re.MULTILINE)

	def __init__(self):
		pass

	def getBlogLastPosts(self):

		def getRelativeDate(input):
			date = datetime.datetime.fromtimestamp(input)

			datef = '%d %b'
			strf = ' %H:%M'

			return date.strftime(datef+strf)

		player_info = self.mongo.find('players', {'name': self.user_name}, {'_id':1, 'token1':1, 'token2': 1})

		try:
			auth = tweepy.OAuthHandler(self.core.p_key, self.core.p_secret)
			auth.set_access_token(player_info['token1'], player_info['token2'])
			api = tweepy.API(auth)
			timeline = api.user_timeline(include_entities=1, include_rts=True)

		except Exception:
			print "Error..."
			return False

		new_posts = []
		for post in timeline:
			is_news = False
			if 'hashtags' in post.entities:
				for hashtag in post.entities['hashtags']:
					if hashtag['text'] == self._news_hashtag:
						is_news = True

						break

			if is_news:
				text = re.sub(self.RE_SUB, '', post.text)
				text = text.strip()

				t = post.created_at # %B

				date = int(t.strftime("%d"))
				if date == 1:
					date_str = 'st'
				elif date == 2:
					date_str = 'nd'
				elif date == 3:
					date_str = 'rd'
				else:
					date_str = 'th'

				date_str = t.strftime("%d")+date_str+' '+t.strftime("%B")

				text = re.sub(
					'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)',
					r'<a href="\1">\1</a>',
					text)

				new_posts.append({
					'text': text,
					'id': post.id,
				    'date': date_str
				})

		new_post_update = []
		old_posts = self.mongo.find('game_statistics', {'type': 'blog_posts'})

		for new_post in new_posts:
			for old_post in old_posts['posts']:
				if new_post['id'] == old_post['id']:
					break
			else:
				new_post_update.append(new_post)

		if new_post_update:
			for post in new_post_update:
				old_posts['posts'].append(post)

				newlist = sorted(old_posts['posts'], key=lambda k: k['id'],reverse=True)

				self.mongo.update('game_statistics', {'type': 'blog_posts'}, {'posts': newlist})

		message = 'Got '+str(len(new_post_update))+' posts from @'+self.user_name
		self.log.write(message)
		print message

if __name__ == '__main__':

	wp = LBIntegration()
	wp.getBlogLastPosts()
