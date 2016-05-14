# -*- coding: UTF-8 -*-

import pymongo
import re
import __main__
from bson import ObjectId
import time

def _profile(method_to_decorate):
	def wrapper(*args, **kwargs):
		t_start = time.time()
		result = method_to_decorate(*args, **kwargs)
		t_all = time.time() - t_start
		print t_all
		return result

	return wrapper

def cleanhtml(raw_html):
	cleanr = re.compile('<.*?>')
	cleantext = re.sub(cleanr, '', raw_html)
	return cleantext

def sanitize(d):
	new_dict = {}
	for key, value in d.iteritems():
		if isinstance(value, dict):
			new_dict[key] = sanitize(value)
		elif type(value) == str or type(value) == unicode:
			new_dict[key] = cleanhtml(value)
		else:
			new_dict[key] = value

	return new_dict

class mongoAdapter():

	con = {}
	db = {}
	tweenk_conf = __main__.tweenk_core

	db_name = tweenk_conf.loaded_data['db_name']

	col = {}

	PROFILE = False

	def	__init__(self):
		self.con = pymongo.Connection(
			self.tweenk_conf.loaded_data['db_host'],
			self.tweenk_conf.loaded_data['db_port']
		)
		self.db = self.con[self.db_name]
		if self.tweenk_conf.loaded_data['db_user']:
			self.db.authenticate(
					self.tweenk_conf.loaded_data['db_user'],
					self.tweenk_conf.loaded_data['db_passw']
			)

	def profile(self, name, params):
		if self.PROFILE:
			print name,'\t',params

	def _getSorted(self, sort):
		sort_buff = []

		if isinstance(sort, dict):
			for item in sort:
				sort_buff.append([item, sort[item]])

		return sort_buff

	def setCollection(self,collection_name):
		self.collection = self.db[collection_name]

	def collectionExist(self, collection_name):
		return collection_name in self.db.collection_names()

	def createCollection(self, collection_name):
		try:
			self.db.create_collection(collection_name)
			return True
		except Exception:
			return False

	def cleanUp(self, collection_name):
		if self.collectionExist(collection_name):
			items = self.db[collection_name]
			items.remove()
		else:
			self.createCollection(collection_name)

	def addIndex(self, collection_name, field):
		collection = self.db[collection_name]
		collection.ensure_index(field,unique=True)
		print 'INDEXES FOR '+collection_name+' IS: ', collection.index_information()

	def insert(self,collection_name,item):
		items = self.db[collection_name]
		return items.insert(sanitize(item))

	def remove(self, collection_name, search = {}):
		self.profile('remove',collection_name)
		items = self.db[collection_name]
		items.remove(search)

	def updateWOSet(self,collection_name, search, update, insert = False, multi = False):
		self.profile('update',collection_name)
		items = self.db[collection_name]
		return items.update(search, sanitize(update), insert, multi)

	def update(self,collection_name, search, update, insert = False, multi = False):
		self.profile('update',collection_name)
		items = self.db[collection_name]
		return items.update(search, {"$set": sanitize(update)}, insert, multi)

	def deleteKeys(self,collection_name, search, keys):
		self.profile('delete key',collection_name)
		items = self.db[collection_name]

		records = {}
		for key in keys:
			records.update({key:1})

		return items.update(search, {"$unset": record})

	def raw_update(self,collection_name, search, update, insert = False, multi = False):
		self.profile('raw update',collection_name)
		items = self.db[collection_name]
		return items.update(search, sanitize(update), insert, multi)

	def raw_many_update(self,collection_name, search, update):
		self.profile('raw update',collection_name)
		items = self.db[collection_name]
		return items.update(search, sanitize(update), multi=True)

	def updateInc(self,collection_name, search, update, insert = False, multi = False):
		self.profile('update',collection_name)
		items = self.db[collection_name]
		return items.update(search, {"$inc": sanitize(update)}, insert, multi)

	def findSomeIDs(self,collection_name, ids, fields={}, sort = {}):
		query = []
		for id in ids:
			if not isinstance(id, ObjectId):
				id = ObjectId(id)

			query.append({'_id':id})

		if query:
			return self.getu(collection_name, search={ "$or" : query}, fields=fields, sort=sort)
		else:
			return False

	def getLastError(self):
		return self.db.error()

	def count(self, collection_name, search = {}):
		items = self.db[collection_name]
		return items.find(search).count()

	def find(self, collection_name, search = {}, fields = {}):
		#self.profile('find',collection_name)
		output = self.getu(collection_name, search = search, fields = fields, limit=1)
		if output:
			return output[0]
		else:
			return False

	def distinct(self,collection_name,field):
		items = {}

		if field != '':
			items = self.db[collection_name].distinct(field)

		return items

	def getu(self, collection_name, search = {}, fields = {}, limit = 0, sort = {}, skip = 0):

		if limit == 1:
			self.profile('find',collection_name)
		else:
			self.profile('getu',collection_name)

		items = self.db[collection_name]
		output = []

		if limit:
			if sort:
				if fields:
					result = items.find(search, fields).sort(self._getSorted(sort)).skip(skip).limit(limit)
				else:
					result = items.find(search).sort(self._getSorted(sort)).skip(skip).limit(limit)
			else:
				if fields:
					result = items.find(search, fields).skip(skip).limit(limit)
				else:
					result = items.find(search).skip(skip).limit(limit)
		else:
			if sort:
				if fields:
					result = items.find(search, fields).sort(self._getSorted(sort))
				else:
					result = items.find(search).sort(self._getSorted(sort))
			else:
				if fields:
					result = items.find(search, fields)
				else:
					result = items.find(search)

		if result:
			for i in result:
				output.append(i)

		return output