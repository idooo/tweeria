#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hi my name is Kayo 3.5
# I like to catch people's tweets
#
#
#
# author: Alex Shteinikov

import __init__
import settings

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import sys
import tweepy
import db
import tweet_parser
import post_notifications
import fvf_creator
import liveblog_integration
import post_process
import authors_ratings
import threading
import time
from sets import Set
import re
import inspect
import logger
import ratings
import random
import os

class ThreadWithExc(threading.Thread):

	name = ''

	def __init__(self, parent, name):
		self.name = name
		self.parent = parent
		threading.Thread.__init__(self)

	def run(self):
		while True:
			if not self.parent.local_queue.ended:
				user = self.parent.local_queue.get()
				timeline = self.parent.getTimelineFromTwitter(user)

				if timeline:
					self.parent.timelines[user['user_id']] = timeline
				else:
					self.parent.missing_players.append(user)
			else:
				break

class ThreadPostNotification(threading.Thread):

	name = ''

	def __init__(self, parent, name):
		self.name = name
		self.parent = parent
		threading.Thread.__init__(self)

	def run(self):
		while True:
			if not self.parent.queue.ended:
				notification = self.parent.queue.get()
				self.parent.postNotification(notification)

			else:
				break

class myQueue(list):

	cursor = 0
	body = []

	ended = False

	def add(self, items):
		if isinstance(items, list):
			for item in items:
				self.body.append(item)
		else:
			self.body.append(items)

	def next(self):
		self.cursor += 1
		if self.cursor == len(self.body):
			self.ended = True

		try:
			result = self.body[self.cursor]
		except:
			self.ended = True

	def item(self):
		return self[i]

	def get(self):
		result = self.body[self.cursor]
		self.next()
		return result

	def count(self):
		return len(self.body)

	def slice(self, start, end):
		result = []
		for i in range(start, end):
			if not self.ended:
				try:
					result.append(self.get())
				except Exception:
					break
			else:
				break

		return result

	def reset(self):
		self.body = []
		self.ended = False
		self.cursor = 0

class serviceCatcher():

	core_settings = settings.core()
	data = settings.balance()

	log = logger.logger()
	LOG_NAME = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])+'/logs/newparser.log'
	LOCK_NAME = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])+'/__lock__'

	timelines = {}

	p_key = core_settings.p_parser_key
	p_secret = core_settings.p_parser_secret

	mongo = db.mongoAdapter()

	queue = myQueue()
	local_queue = myQueue()
	missing_players = []

	auths = {}
	apis = {}

	threads = {}
	threads_number = 0

	request_time = 0
	parse_time = 0
	group_number = 0

	graph_tweets = {}

	def __init__(self):
		self.parser = tweet_parser.tweetParser(debug = False)

	def _createLock(self):
		fp = open(self.LOCK_NAME,'w')
		fp.write('YEAH')
		fp.close()

	def loadDataToQueue(self, array = False):

		self.queue = myQueue()
		self.queue.body = []

		if not array:
			buff_players = self.mongo.getu(
				'players',
				search = {'banned':{'$exists':False}, 'last_login': {'$gte': time.time() - self.core_settings.MAX_TIME_TO_SLEEP }},
				fields = {'user_id':1, 'name':1, 'token1':1,'token2':1},
				sort={'last_login': -1}
			)
		else:
			buff_players = array

		self.queue.add(buff_players)

	def startThread(self, name):
		self.threads.update({name:ThreadWithExc(self, name)})
		self.threads[name].start()

	def startPostThread(self, name):
		self.threads.update({name:ThreadPostNotification(self, name)})
		self.threads[name].start()

	def getTimelineFromTwitter(self, user):
		try:
			self.auths[user['user_id']] = tweepy.OAuthHandler(self.p_key, self.p_secret)
			self.auths[user['user_id']].set_access_token(user['token1'], user['token2'])
			self.apis[user['user_id']] = tweepy.API(self.auths[user['user_id']])
			timeline = self.apis[user['user_id']].user_timeline(include_entities=1, include_rts=True)

		except Exception, e:
			timeline = False
			print 'Error',user['name'],e

		try:
			del self.auths[user['user_id']]
			del self.apis[user['user_id']]
		except Exception:
			pass

		return timeline

	def getParsedTimeline(self, user):

		if not user['user_id'] in self.timelines or  not self.timelines[user['user_id']]:
			self.counts['n_players'] += 1
			return False

		statuses = self.timelines[user['user_id']]

		is_player = self.parser.changePlayer(user['user_id'], restore_health=True)
		
		if not is_player:
			return False

		last_id = self.parser.player['last_id']

		# DEBUG VAR

		if tweenk_core.debug['load_deprecated_tweets']:
			last_id = 1

		if last_id == 0:
			statuses = [statuses[0]]

		parsed = 0
		for i in range(0,len(statuses)):
			if statuses[(len(statuses)-1-i)].id > last_id:
				self.parser.parse(statuses[(len(statuses)-1-i)])
				self.counts['parsed_tweets'] += 1
				parsed += 1

		if parsed > 0:
			self.parser.movingPlayer()
			self.parser.getNotifications()
		
		try:
			self.parser.savePlayerData(last_id = statuses[0].id)

			self.counts['y_players'] += 1
			self.counts['tweets'] += len(self.timelines[user['user_id']])
		except Exception:
			print '>>>>', user

		del self.timelines[user['user_id']]

	def postNotification(self, notification):

		try:
			self.auths[notification['name']] = tweepy.OAuthHandler(self.p_key, self.p_secret)
			self.auths[notification['name']].set_access_token(notification['token1'].decode('utf-8'), notification['token2'].decode('utf-8'))
			self.apis[notification['name']] = tweepy.API(self.auths[notification['name']])
			self.apis[notification['name']].update_status(self.nCenter.parseNotification(notification).decode('utf-8'))
			self.posted_tweets += 1

		except Exception, e:
			print 'Error post',notification['name'],e

	def saveFinalData(self):

		t = time.time()

		self.parser.processEvents()
		self.parser.saveCurrentEvents()
		self.parser.finalDataSave()

		self.log.write('Events parse time '+str(time.time()-t)+' seconds\n\n')

	def parseIt(self, user_count = 1000, start_user_no = 0, threads = 64):

		print 'Parse from',start_user_no,'to',start_user_no+user_count-1,'users (',len(self.queue.body),')'

		self.local_queue.reset()
		self.local_queue.add(self.queue.slice(start_user_no, start_user_no+user_count-1))

		for user in self.local_queue.body:
			self.timelines.update({user['user_id']:[]})
			self.auths.update({user['user_id']:[]})
			self.apis.update({user['user_id']:[]})

		local_request_time = time.time()

		for i in range(0,threads):
			self.threads_number += 1
			name = 'Thread_'+str(self.threads_number)
			self.startThread(name)

		count = 0
		running = True
		while running:
			time.sleep(1)
			count += 1

			if self.local_queue.ended:
				print '> Queue ended'

				self.request_time += time.time() - local_request_time
				local_parse_time = time.time()

				for user in self.local_queue.body:
					print 'try:',user['name']
					self.getParsedTimeline(user)
					print 'ok'
					time.sleep(0.1)

				self.parse_time += time.time() - local_parse_time
				self.group_number += 1

				print '> Parse group',self.group_number,'ended'

				running = False
				break

	def parseItNoThreads(self,  user_count = 1000, start_user_no = 0):

		print 'Parse from',start_user_no,'to',start_user_no+user_count-1,'users (',len(self.queue.body),')'

		self.local_queue.reset()
		self.local_queue.add(self.queue.slice(start_user_no, start_user_no+user_count-1))

		for user in self.local_queue.body:
			self.timelines.update({user['user_id']:[]})
			self.auths.update({user['user_id']:[]})
			self.apis.update({user['user_id']:[]})

		local_request_time = time.time()

		while True:
			if not self.local_queue.ended:
				user = self.local_queue.get()
				timeline = self.getTimelineFromTwitter(user)

				if timeline:
					self.timelines[user['user_id']] = timeline
			else:
				break

		if self.local_queue.ended:
			print '> Queue ended'

			self.request_time += time.time() - local_request_time
			local_parse_time = time.time()

			for user in self.local_queue.body:
				print 'try:',user['name']
				self.getParsedTimeline(user)
				print 'ok'
				time.sleep(0.1)

			self.parse_time += time.time() - local_parse_time
			self.group_number += 1

			print '> Parse group',self.group_number,'ended'

	def appendGraphTweets(self):
		if len(self.graph_tweets)>0:
			if not self.mongo.collectionExist("graph_tweets"):
				self.mongo.createCollection("graph_tweets")

			for user in self.graph_tweets:
				userTweets = self.graph_tweets[user]
				self.core_settings.mpr(user)
				self.mongo.updateWOSet("graph_tweets",{"player" : user}, {"player": user,"tweets":userTweets}, True)
				print self.mongo.getLastError()
				pass
		pass

	def parseInterations(self):

		self.parser.interactions.sort(key=lambda x: x['to']['id'])

		while self.parser.interactions:

			interaction = self.parser.interactions.pop()

			if self.parser.player['user_id'] != interaction['to']['id']:
				self.parser.changePlayer(interaction['to']['id'])

			print 'interaction', self.parser.player['name']
			self.parser.parse(interaction)
			self.parser.savePlayerData()

	def start(self, threads = 64, step = 250, missing_players = False):

		self.loadDataToQueue(missing_players)

		self.counts = {
			'tweets':0,
			'parsed_tweets':0,
			'players': self.queue.count(),
			'n_players':0,
			'y_players':0,
		    'all_players': self.mongo.count('players', {})
		}

		self.log.openFile(self.LOG_NAME)

		completed = 0
		while completed < self.queue.count():
			if threads == 1:
				self.parseItNoThreads(user_count = step, start_user_no = completed)
			else:
				self.parseIt(user_count = step, start_user_no = completed, threads = threads)
			completed += step
			pass

		print 'parse_time', self.parse_time

		self.log.write('Parsed '+str(self.counts['parsed_tweets'])+' / '+str(self.counts['tweets'])+' tweets by '+str(self.counts['y_players'])+' / '+str(self.counts['players'])+' / '+str(self.counts['all_players'])+' players')
		self.log.write('Total groups '+str(self.group_number)+' by '+str(step)+' players')
		self.log.write('Requests time '+str(self.request_time)+' seconds')
		self.log.write('Parse time '+str(self.parse_time)+' seconds\n\n')

		self._createLock()

	def postTwitterNotifications(self, threads = 64):

		posted_time = time.time()
		notifications = self.mongo.getu('notification_queue')

		if notifications:
			note_count = len(notifications)
		else:
			note_count = 0

		self.posted_tweets = 0

		print 'Posting '+str(note_count)+' notifications ...'

		if notifications:
			self.queue = myQueue()
			random.shuffle(notifications)
			self.queue.add(notifications)

			self.nCenter = post_notifications.TweetNotificationCenter()

			self.threads = {}
			self.auths = {}
			self.apis = {}

			for notification in self.queue.body:
				self.auths.update({notification['name']:[]})
				self.apis.update({notification['name']:[]})

			for i in range(0,threads):
				self.threads_number += 1
				name = 'Thread_'+str(self.threads_number)
				self.startPostThread(name)

			running = True
			while running:
				time.sleep(1)
				if self.queue.ended:
					running = False
					break

			time.sleep(5)

		self.log.openFile(self.LOG_NAME)
		self.log.write('Posted '+str(self.posted_tweets)+' / '+str(note_count)+' notifications')
		self.log.write('Posting time '+str(time.time()-posted_time)+' seconds\n\n')
		self.log.closeFile()

		self.mongo.remove('notification_queue')

if __name__ == '__main__':

	def isServiceRunning():
		process = os.popen("ps x -o pid,args | grep service_catcher").readlines()

		RE_PATTRN = re.compile('service_catcher.py')

		count = 0
		for line in process:
			result = re.search(RE_PATTRN, line.strip())
			if result: count += 1

		return True if count > 2 else False

	if isServiceRunning():
		print '..already working..'
		exit()

	#
	# parsing ------------------------
	#

	# amount of parallel threads that will be used to fetch tweets
	threads = 1

	service = serviceCatcher()
	service.start(threads = threads, step = 500)

	if service.missing_players:
		service.start(threads = threads, step = 500, missing_players = service.missing_players)

	service.parseInterations()

	service.saveFinalData()
	service.postTwitterNotifications(16)

	#
	# post processing ----------------
	#

	pp = post_process.postProcess()
	pp.process()

	# faction vs faction event auto creation
    # Feature was experimental and disabled
    #
	#fvf = fvf_creator.FVFCreator()
	#fvf.checkAndCreateFvF()

	#
	# ratings ------------------------
	#

	urc = ratings.ratingsCounter()
	urc.countGameStatistics()
	urc.countAll()

	#
	# authors ratings ----------------
	#

	arc = authors_ratings.artistsRatingsCounter()
	arc.countRatings()

	#
	# get last blog posts ------------
	# This addon will get rss field from the remote source,
    # parse it to display on the main page (news)
    #
	#wp = liveblog_integration.LBIntegration()
	#wp.getBlogLastPosts()

