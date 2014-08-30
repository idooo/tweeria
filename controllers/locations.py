# -*- coding: UTF-8 -*-

import basic

class locationController(basic.defaultController):

	DIR = './locations/'

	@basic.methods
	def methods(self, params = {}):
		return {
			'type_of_form': {
				# ...
			}
		}

	@basic.printpage
	def printPage(self, page, params):
		return {
			'world': self.printWorldMap,
		}

	def printWorldMap(self, fields, params):

		def getPlayersPoints(player):

			is_admin = 'login_admin' in self.cur_player

			players = self.model.players.getNearPlayers(
				player['position']['x'],
				player['position']['y'],
				additional=True,
				name=self.cur_player['login_name'],
				all_map=False
			)

			points = {}

			for player in players:
				point_hash = str(player['position']['x'])+'_'+str(player['position']['y'])

				record = {
					"name": player['name'],
					'class': self.balance.classes[str(player['class'])],
					'race':  self.balance.races[player['faction']][player['race']],
					"lvl": player['lvl'],
					"img": player['avatar']
				}

				if point_hash in points:
					points[point_hash]['count'] += 1
					points[point_hash]['players'].append(record)
				else:
					coords = self.sbuilder.core_settings.relativePosition(player['position'])
					points.update({
						point_hash: {
							'count': 1,
							'pos': {
								'y': coords['x'],
								'x': coords['y']
							},
							'players': [record]
						}
					})

			return points

		def getPlacesPoints():
			points = {}

			dungeons = self.model.misc.getDungeons()

			if self.cur_player:
				geo_raids = self.model.events.getGvGEvents(self.cur_player['login_id'])
			else:
				geo_raids = []

			locations = self.model.misc.getLocations() + dungeons + geo_raids

			for location in locations:

				point_hash = str(location['position']['x'])+'_'+str(location['position']['y'])
				coords = self.sbuilder.core_settings.relativePosition(location['position'])

				if location['type'] == 'war':
					location.update({
						'name': 'Guild war '+location['guild_side_name']+' vs. '+location['target_name'],
					    'hashtag': location['promoted_hashtag']
					})

				record = {
					'name': location['name'],
				    'desc': location['desc'],
				    'type': location['type'],
				    'hashtag': location['hashtag']
				}

				if location['type'] < 2:
					record.update({
						'lvl_min': location['lvl_min'],
						'lvl_max': location['lvl_max'],
						'type': location['type'],
					    'max_players': location['max_players']
					})

				points.update({
					point_hash: {
						'count': 1,
						'pos': {
							'y': coords['x'],
							'x': coords['y']
						},
						'places': [record]
					}
				})

			return points

		fields.update({self.title: 'World map'})





		if self.cur_player:

			player = self.model.players.getPlayer(self.cur_player['login_user_id'], 'map')
			fields.update({
				'login_class': self.balance.classes[str(player['class'])],
				'login_race':  self.balance.races[player['faction']][player['race']],
				})

			fields.update({
				'player_coords': self.core.relativePosition(player['position']),
				'places': getPlacesPoints()
			})


			if 'name' in params:
				otherPlayer = self.model.players.getPlayer(params['name'], 'other_map_player')

				if otherPlayer:
					fields.update({
						'other_player':{
							'class': self.balance.classes[str(otherPlayer['class'])],
							'race':  self.balance.races[otherPlayer['faction']][otherPlayer['race']],
							'coords': self.core.relativePosition(otherPlayer['position']),
							'lvl': otherPlayer['lvl'],
							'img': otherPlayer['avatar']
						}
					})


			return basic.defaultController._printTemplate(self, 'world', fields)

		else:
			return self.sbuilder.throwWebError(1002)


data = {
	'class': locationController,
	'type': ['u'],
	'urls': ['world']
}