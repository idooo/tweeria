#!/usr/bin/python
# -*- coding: utf-8 -*-

# This is rating counter
# author: Alex Shteinikov

import __init__
import settings
import time
import random

tweenk_core = settings.core()
tweenk_balance = settings.balance()

import db
import logger
import time

class ratingsCounter:

	K1 = 0.02
	K2 = 1.5
	K_kill = 100
	RD = 25

	mongo = db.mongoAdapter()
	balance = settings.balance()
	core = settings.core()
	log = logger.logger('logs/system_events.log')

	def __init__(self):
		pass

	def countUserRatings(self):

		def countTheUserRating(sort_field, result_field):
			self.players.sort(key=lambda x: x[sort_field])
			self.players.reverse()
			place = 1

			for player in self.players:
				if 'banned' in player and player['banned']:
					player.update({result_field: 100500})
				else:
					player.update({result_field: place})
					place += 1

		starttime = time.time()

		for player in self.players:

			# Умножаем уровень на 100 млн и прибавляем опыт
			# чтобы два раза не сравнивать (по уровню и по опыту)
			# а учитывать общее значение

			player.update({'rating':player['lvl']*100000000+player['exp']})

			# Если нет информации о том сколько твитов игрока за день получено
			# то считаем 0

			if not 'today_parsed_tweets' in player:
				player.update({'today_parsed_tweets': 0})


			# Если нет информации о том сколько pvp points игрок за день набрал
			# то считаем что все (что вчера у него было 0 очков)

			if not 'prev_day_pvp' in player:
				player.update({'pvp_per_day': player['pvp_score']})
			else:
				player.update({'pvp_per_day': player['pvp_score'] - player['prev_day_pvp']})

			# Считаем рейтинг игрока по метрикам


			global_metric = 0
			if player['lvl'] == 1:
				global_metric = 0

			else:
				if 'metrics' in player:
					if 'monster_kill' in player['metrics']:
						for hour in player['metrics']['monster_kill']:
							global_metric += (self.balance.max_lvl-player['metrics']['monster_kill'][hour]['lvl']*self.K2)*self.K1*self.K_kill*player['metrics']['monster_kill'][hour]['value']
					else:
						global_metric = 0

				try:
					if player['ratings']['trending_position'] <= 10:
						if player['ratings']['trending_position'] <= 3:
							global_metric = global_metric * 0.7
						elif player['ratings']['trending_position'] <= 7:
							global_metric = global_metric * 0.8
						else:
							global_metric = global_metric * 0.9
				except Exception:
					pass

				global_metric = global_metric + global_metric/100 * random.randint(0,self.RD)

			player.update({'trending_score': global_metric})


		# Считаем место игрока в глобальном рейтинге игроков по опыту,
		# Если уровень одинаковый, то выше в рейтинге тот, у кого больше опыта
		countTheUserRating('rating', 'rating_by_exp')

		# ... в общем рейтинге игроков по pvp points
		countTheUserRating('pvp_score', 'rating_by_pvp')

		# ... в общем рейтинге игроков по achv_points
		countTheUserRating('achv_points', 'rating_by_achv_points')

		# ... trending players
		countTheUserRating('trending_score', 'trending_position')


		for player in self.players:
			record = {
				'rating_by_exp': player['rating_by_exp'],
				'rating_by_pvp': player['rating_by_pvp'],
				'rating_by_achv_points': player['rating_by_achv_points'],
			    'trending_position': player['trending_position'],
			    'trending_score': player['trending_score']
			}

			self.mongo.update('players', {'_id':player['_id']}, {'ratings':record})


		message = 'Player ratings was counted by '+str(time.time()-starttime)+' seconds'
		self.log.write(message)
		print message

	def countGuildRatings(self):

		def countGuildRating(field):
			self.guilds.sort(key=lambda x: x[field])
			self.guilds.reverse()

			place = 1
			for guild in self.guilds:
				guild.update({field: place})
				place += 1
		
		starttime = time.time()

		for guild in self.guilds:

			guild.update({
				'buff_global_metric': 0,
				'buff_rating': 0,
				'buff_pvp': 0,
				'pvp_score': 0,
				})

			query = []
			for id in guild['people']:
				query.append({'_id':id})

			members = self.mongo.getu('players', search = {'$or':query}, fields = {'lvl':1, 'pvp_score':1, 'ratings':1})

			for player in members:
				try:
					guild['buff_global_metric'] += player['ratings']['trending_score']
					guild['buff_rating'] += player['lvl']
					guild['buff_pvp'] += player['pvp_score']
				except Exception:
					pass

			if len(members)<5:
				guild['buff_global_metric'] = 0

			guild['pvp_score'] = int(guild['buff_pvp'])

		# Считает место гильдии в глобальном рейтинге гильдии
		# по сумме уровня членов гильдии

		countGuildRating('buff_rating')

		# ... sum trending members
		countGuildRating('buff_global_metric')

		# .. по общему pvp_score участников
		countGuildRating('buff_pvp')


		for guild in self.guilds:
			record = {
				'rating_place_members_lvl': guild['buff_rating'],
			    'rating_place_members_pvp': guild['buff_pvp'],
			    'trending_position': guild['buff_global_metric'],
			    'pvp_score': guild['pvp_score']
			}
			self.mongo.update('guilds',{'_id':guild['_id']}, {'ratings':record})
			

		message = 'Guilds ratings was counted by '+str(time.time()-starttime)+' seconds'
		self.log.write(message)
		print message

	def countAll(self):
		self.players = self.mongo.getu('players', {'banned':{'$exists':False}}, {'_id':1, 'lvl':1, 'exp':1, 'achv_points': 1, 'pvp_score':1, 'metrics':1, 'ratings':1})
		self.banned_players = self.mongo.getu('players', {'banned':{'$exists':True}}, {'_id':1, 'lvl':1, 'exp':1, 'achv_points': 1, 'pvp_score':1, 'metrics':1})
		self.guilds = self.mongo.getu('guilds',{},{'id':1, 'name':1, 'people':1})

		self.countUserRatings()
		self.countGuildRatings()

		for player in self.banned_players:
			record = {
				'rating_by_exp': 100500,
				'rating_by_pvp': 100500,
				'rating_by_achv_points': 100500,
			    'trending_position': 100500,
			    'trending_score': 0
			}

			self.mongo.update('players', {'_id':player['_id']}, record)

		self.exit()

	def countGameStatistics(self):
		count_players = []
		for index in range(0, len(self.balance.faction)):
			query = {'faction': index, '$or': [{'race': 0}, {'race':1}]}
			count_players.append(self.mongo.count('players', query))

		count_avg_level = [0,0,0]
		players = self.mongo.getu('players', {}, {'lvl':1, 'faction':1})
		for player in players:
			count_avg_level[player['faction']] += player['lvl']

		for index in range(0, len(self.balance.faction)):
			try:
				count_avg_level[index] = float(int(float(count_avg_level[index]) / count_players[index] * 10))/10
			except Exception:
				count_avg_level[index] = 0.0

		current_time = time.localtime()
		hashkey = str(current_time.tm_year) + str(current_time.tm_yday)

		lastday_stat = self.mongo.find('game_statistics', {'type': 'lastday_avg_level'})

		if not lastday_stat or time.localtime().tm_hour > 20 and not lastday_stat['hashkey'] == hashkey:
			self.mongo.update('game_statistics', {'type': 'lastday_avg_level'}, {'type': 'lastday_avg_level', 'data': count_avg_level, 'hashkey': hashkey}, True)
			self.mongo.update('game_statistics', {'type': 'lastday_count'}, {'type': 'lastday_count', 'data': count_players, 'hashkey': hashkey}, True)

		self.mongo.update('game_statistics', {'type': 'players_count'}, {'type': 'players_count', 'data': count_players}, True)
		self.mongo.update('game_statistics', {'type': 'players_avg_level'}, {'type': 'players_avg_level', 'data': count_avg_level}, True)

	def exit(self):
		self.log.closeFile()

if __name__ == "__main__":

	urc = ratingsCounter()
	urc.countGameStatistics()
	urc.countAll()
