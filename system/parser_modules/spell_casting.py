# -*- coding: utf-8 -*-

# TODO ограничение на количество одновременных баффов и дебаффов у игрока

from sets import Set
import time
import random

__author__ = 'ido'

def checkResistance(res, damage_type, damage_value):
	dmg = damage_value
	return int(float(dmg)/100*(100-res[damage_type]))

def spellCasting(tweet_vars):

	def addBuff(action, stat_name, type_of_buff ):

		# type_of_buff: 1 - buff, 0 - debuff
		return {
			'buff_align': type_of_buff,
			'buff_name': tweet_vars['spell']['name'],
		    'actions': [{
			    'stat_name': stat_name,
			    'action_align': type_of_buff,
			    'value': action['value'],
			}],
			'start_time': time.time(),
			'length': 3600
		}

	def addEffect(fields, effect_name, value):
		if effect_name in fields:
			fields[effect_name] += value
		else:
			fields.update({
				effect_name: value
			})

	# [{u'type': 2, u'name': u'Fire', u'value': 5, u'effect': u'DMG'}]

	player_fields = {}
	target_fields = {}

	is_buff = True

	for action in tweet_vars['spell']['spell_actions']:

		# buff
		if action['type'] in [1,3]:
			mn = 1
			if action['type'] == 3:
				is_buff = False
				mn = -1

			addEffect(target_fields, action['effect'], mn*action['value'])

		# спелл прямого действия
		elif action['type'] == 2:
			is_buff = False
			if action['effect'] == 'DMG':
				dmg = int(action['value'])
				addEffect(target_fields, 'DMG_DONE', dmg)


	return {
		'target_fields': target_fields,
	    'player_fields': player_fields,
	    'is_buff': is_buff
	}

