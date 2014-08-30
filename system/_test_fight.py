# -*- coding: utf-8 -*-

import __init__
import settings

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import os, inspect
import db

modules ={}

def _loadModules():
	modules_folder = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])+'/parser_modules'

	for item in os.listdir(modules_folder):
		if item[-2:] == 'py':
			modules.update({item[:-3:]:__import__(item[:-3:])})

def testFight(type_of_fight, sides):

	mongo = db.mongoAdapter()

	if 'player1' in sides:
		sides['player1'] = mongo.find('players', {'name': sides['player1']})
		sides['player1'].update({'items': mongo.getu('items_created', {'player_id': sides['player1']['_id']})})

	if 'player2' in sides:
		sides['player2'] = mongo.find('players', {'name': sides['player2']})

	if 'monster' in sides:
		sides['monster'] = mongo.find('monsters', {'name': sides['monster']})

	if type_of_fight == 1:
		return modules['fight'].fightBetweenPlayerAndMonster(
			{
				'side_1': [
					{ 'type': 'player', 'obj': sides['player1'] }
				],
				'side_2': [
					{ 'type': 'monster', 'obj': sides['monster'] }
			    ]
			}
		)

if __name__ == '__main__':

	_loadModules()
	print testFight(1, {
		'player1': 'ido_q',
	    'monster': 'Larva'
	})

