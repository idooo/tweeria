# -*- coding: utf-8 -*-

__author__ = 'ido'

ignored = [u'YouTube']

def isBlackListTweet(tweet):

	if 'user_mentions' in tweet.entities and tweet.entities['user_mentions']:

		name = tweet.entities['user_mentions'][0]['screen_name']

		if name in ignored:
			return True


	return False