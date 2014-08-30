# -*- coding: utf-8 -*-

import re

__author__ = 'ido'

RE_IGNORE = re.compile('◇')

def isGameTweet(tweet):

	try:
		tweet.source.index(u'tweeria')
		return True
	except Exception:
		pass

	try:
		is_button = tweet.source.index(u'tweetbutton')
		is_tweeria_hash = False
		for hashtag in tweet.entities['hashtags']:
			if hashtag['text'] == u'tweeria':
				is_tweeria_hash = True
				break

		if is_button and is_tweeria_hash:
			return True

	except Exception:
		pass

	if re.search(RE_IGNORE, tweet.text.encode('utf8')):
		return True

	return False