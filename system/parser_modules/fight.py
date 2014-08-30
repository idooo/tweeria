# -*- coding: utf-8 -*-

import random
from math import ceil
from sets import Set

def fightBetweenPlayerAndMonster(sides, penalty = False, afraid_chance = 0):

	def getAvgParam(side, param):
		sum = 0
		tp = param.values()[0]
		max = -1
		for member in side:
			if tp == 'max':
				if member['obj'][param.keys()[0]] > max:
					max = member['obj'][param.keys()[0]]
			else:
				sum += member['obj'][param.keys()[0]]

		if tp == 'max':
			return max
		elif tp == 'avg':
			return float(sum)/len(side)
		elif tp == 'sum':
			return sum

	def getEnemySide(side_name):
		if side_name == 'side_1':
			return 'side_2'
		else:
			return 'side_1'

	fight = {
		'side_1': {},
	    'side_2': {}
	}

	DMG_DIFF_CONST = 0.1

	for side_name in sides:
		# считаем средние параметры для каждой стороны
		for param in [{'luck': 'avg'}, {'DEF': 'max'}, {'HP':'sum'}]:
			fight[side_name].update({
				param.values()[0]+'_'+param.keys()[0]: getAvgParam(sides[side_name], param)
			})

	for side_name in sides:
		sum_dmg = 0
		for member in sides[side_name]:

			member_luck = float(member['obj']['luck'])
			luck_p = member_luck/(fight[getEnemySide(side_name)]['avg_luck']+member_luck)

			cur_dmg = member['obj']['DMG']
			dirty_damage = {
				'min': cur_dmg*(1-DMG_DIFF_CONST)-fight[getEnemySide(side_name)]['max_DEF']/2,
				'max': cur_dmg*(1+DMG_DIFF_CONST)-fight[getEnemySide(side_name)]['max_DEF']/2,
				'abs': cur_dmg*DMG_DIFF_CONST,
			}

			# если не смогли пробить броню то наносим лишь небольшой урон
			if dirty_damage['min'] < 0:
				dirty_damage['min'] = dirty_damage['abs']

				if dirty_damage['max'] < 0:
					dirty_damage['max'] = dirty_damage['abs']

			clear_damage = dirty_damage['min']+(dirty_damage['max']-dirty_damage['min'])*luck_p
			member['obj'].update({'clear_damage': {u'current': clear_damage}})
			sum_dmg += clear_damage

		if sum_dmg <= 0:
			sum_dmg = 1

		fight[side_name]['sum_dmg'] = sum_dmg
		fight[side_name]['clear_strikes'] = ceil(float(fight[getEnemySide(side_name)]['sum_HP'])/sum_dmg)

	if fight['side_1']['clear_strikes'] == fight['side_2']['clear_strikes']:
		fight['side_1']['clear_strikes'] += ((random.randint(0,1)-0.5)*2)

	if not penalty:
		win = fight['side_1']['clear_strikes'] < fight['side_2']['clear_strikes']
	else:
		if random.randint(1,100) > afraid_chance:
			win = fight['side_1']['clear_strikes'] < fight['side_2']['clear_strikes']
		else:
			win = False

	if win:
		winner = 'side_1'
	else:
		winner = 'side_2'

	for side_name in ['side_1', 'side_2']:
		fight[side_name]['DMG_done'] = ceil(fight[winner]['clear_strikes']*fight[side_name]['sum_dmg'])

	result = {'winner': winner, 'side_1': [], 'side_2': []}
	for side_name in sides:
		for member in sides[side_name]:
			record = {}
			if member['type'] == 'player':
				if side_name == winner:
					record = {'HP': fight[getEnemySide(side_name)]['DMG_done'] }
				else:
					record = {'HP': -1 }

			result[side_name].append(record)

	return result

def fightBetweenGroups(sides, players_info, balance, event):

	MAGIC_BONUS = 0.15
	HASH_BONUS = 0.15
	LEAD_BONUS = 0.05
	DEF_REDUCE = 0.05

	for side in sides:
		sides[side].update({
			'people': {},
			'max_lead': 0
		})

	for player in players_info:

		main_stat = balance.priority_stats[str(player['class'])]

		# m_attack = dmg + dmg/100 * main_stat
		# m_defense = hp + hp/100 * def

		m_attack = player['stat']['DMG']['current'] + float(player['stat']['DMG']['current'])/100 * player['stat'][main_stat]['current']
		m_defense = player['stat']['HP']['current'] + float(player['stat']['HP']['current'])/100 * player['stat']['DEF']['current']

		side = False
		if event['type'] == 'war':
			if player['_guild_name'] == sides['side_1']['name']:
				side = 'side_1'
			elif player['_guild_name'] == sides['side_2']['name']:
				side = 'side_2'

		elif event['type'] == 'fvf':
			if player['faction'] == sides['side_1']['id']:
				side = 'side_1'
			elif player['faction'] == sides['side_2']['id']:
				side = 'side_2'

		if side:
			if player['stat']['lead']['current'] > sides[side]['max_lead']:
				sides[side]['max_lead'] = player['stat']['lead']['current']

			sides[side]['people'].update({
				str(player['_id']): {
					'id': player['_id'],
					'm_attack': m_attack,
					'm_defense': m_defense,
					'attack_sum': 0,
					'defense_sum': 0,
					'performance': 0
				}
			})

	if not sides['side_1']['people'] or not sides['side_2']['people']:
		return False

	for activity in event['activity']:
		str_player_id = str(activity['player_id'])
		if str_player_id in sides['side_1']['people']:
			side = 'side_1'
		elif str_player_id in sides['side_2']['people']:
			side = 'side_2'
		else:
			side = False

		if side:
			m_a = sides[side]['people'][str_player_id]['m_attack']
			m_d = sides[side]['people'][str_player_id]['m_defense']

			sides[side]['people'][str_player_id]['attack_sum'] += m_a  + float(m_a * sides[side]['max_lead'] * LEAD_BONUS)
			sides[side]['people'][str_player_id]['defense_sum'] += m_d

	ignored = Set()

	for side in sides:
		sum_a = 0
		sum_d = 0
		for player in sides[side]['people']:
			sum_a += sides[side]['people'][player]['attack_sum']
			sum_d += sides[side]['people'][player]['defense_sum']

		for player in sides[side]['people']:
			if sum_a == 0:
				performance = 0
			else:
				performance = round(sides[side]['people'][player]['attack_sum']/sum_a*100)

			sides[side]['people'][player] = {
				'performance': performance,
				'id': sides[side]['people'][player]['id']
			}

			if performance <= 1:
				ignored.add(sides[side]['people'][player]['id'])

		sides[side].update({
			'sum_a': sum_a,
			'sum_d': sum_d * DEF_REDUCE
		})

	sides['side_1']['ratio'] = sides['side_1']['sum_a'] - sides['side_2']['sum_d']
	sides['side_2']['ratio'] = sides['side_2']['sum_a'] - sides['side_1']['sum_d']

	if sides['side_1']['ratio'] > sides['side_2']['ratio']:
		winner = 'side_1'
	else:
		winner = 'side_2'

	return {
		'winner_id': sides[winner]['id'],
		'winner_name': sides[winner]['name'],
		'combat': {
			sides['side_1']['name'] : sides['side_1']['people'],
			sides['side_2']['name'] : sides['side_2']['people'],
			'ignored': ignored
		}
	}