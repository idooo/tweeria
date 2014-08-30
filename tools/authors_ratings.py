#!/usr/bin/python
# -*- coding: utf-8 -*-

# This is artists rating counter
# author: Alex Shteinikov

import __init__
import settings

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import db
import time
from bson import ObjectId

class artistsRatingsCounter:

	mongo = db.mongoAdapter()
	balance = settings.balance()
	core = settings.core()

	def countRatings(self):

		starttime = time.time()

		authors = {}

		likes = self.mongo.getu('items_likes', {'author_id': {'$exists': True}})

		for like in likes:
			author_str_id = str(like['author_id'])
			if not author_str_id in authors:
				authors.update({author_str_id: 0})

			authors[author_str_id] += len(like['people'])

		self.mongo.cleanUp('authors_likes')

		for author_str_id in authors:
			author_info = self.mongo.find('players', {'_id': ObjectId(author_str_id)}, {'_id': 1, 'name': 1, 'avatar': 1})

			if author_info:
				self.mongo.insert('authors_likes', {
					'author_id': author_info['_id'],
				    'author_name': author_info['name'],
				    'author_avatar': author_info['avatar'],
				    'likes': authors[author_str_id]
				})

		message = 'Artist ratings was counted by '+str(time.time()-starttime)+' seconds'
		print message

if __name__ == "__main__":
	arc = artistsRatingsCounter()
	arc.countRatings()
