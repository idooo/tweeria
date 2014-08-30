#!/usr/bin/python
# -*- coding: utf-8 -*-

# author: Alex Shteinikov

import __init__
import settings
tweenk_core = settings.core()
tweenk_balance = settings.balance()

import optparse
import db

class adminControl():


	mongo = db.mongoAdapter()

	def __init__(self):
		pass

	def setAdmin(self, player_name):
		self.mongo.update('players', {'name': player_name}, {'admin': True})

	def unsetAdmin(self, player_name):
		self.mongo.raw_update('players', {'name': player_name}, {'$unset': { 'admin': 1}})

if __name__ == '__main__':

	ac = adminControl()

	p = optparse.OptionParser()
	p.add_option('--set_admin', '-s', action="store_true")
	p.add_option('--unset_admin', '-u', action="store_true")

	(options, arguments) = p.parse_args()

	if options.set_admin:
		ac.setAdmin(arguments[1])

	if options.unset_admin:
		ac.unsetAdmin(arguments[1])
