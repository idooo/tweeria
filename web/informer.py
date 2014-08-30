# -*- coding: utf-8 -*-

import db
import __main__
from bson import ObjectId

class Informer():

	spell_types = ['','+','','-']

	core = __main__.tweenk_core
	data = __main__.tweenk_balance
	mongo = db.mongoAdapter()

	def __init__(self):
		pass

	def getItemInfo(self, item_uid, can_use = 0, suffix_uid = 0):

		try:
			item = self.mongo.find('items',{'UID':int(item_uid)})
			player_item = False
		except Exception:
			item = self.mongo.find('items_created',{'_id':ObjectId(item_uid)})
			player_item = True

		if not item:
			return 'In Soviet Russia items pickup you!'

		if not player_item:
			img = './data/items/'+str(item['img'])+'.jpg'
			custom_class = ''
		else:
			img = item['img']+'_fit.png'
			custom_class = 'class="player_item"'

		response = "<img src='"+img+"'><c "+custom_class+"><n"+str(int(item['color']))+">"+item['name']+"</n"+str(item['color'])+">"

		try:
			if can_use == '0':
				response += "<t class='item-cant-use'>"
			else:
				response += "<t>"

			if int(item['type']) != 1:
				response += self.data.item_types[int(item['type'])]
			else:
				response += item['view'].title()

			response += ', Level '+str(item['lvl_min'])+"</t>"
		except :
			pass

		if 'DMG' in item['bonus'] and item['bonus']['DMG'] > 0:
			response += "<dmg>"+self.data.stats_name['DMG']+" "+str(int(item['bonus']['DMG'])-1)+"-"+str(int(item['bonus']['DMG'])+1)+"</dmg>"

		if 'DEF' in item['bonus'] and item['bonus']['DEF'] > 0:
			response += "<def>"+self.data.stats_name['DEF']+" "+str(int(item['bonus']['DEF']))+"</def>"

		for stat in ['int','str','dex','luck','HP','MP']:
			if stat in item['bonus'] and item['bonus'][stat] != 0:
				response += "<s>""+"+str(int(item['bonus'][stat]))+" "+self.data.stats_name[stat]+"</s>"

		response += "</c><div class='clear'></div>"

		return response

	def getTriviaItemsInfo(self, item_uid):

		item = self.mongo.find('shop_items', {'item_UID': int(item_uid)})
		if not item:
			return 'In Soviet Russia items pickup you!'

		result = "<img src='/data/items/non_combat/"+item['img']+".jpg?"+__main__.tweenk_core.__version__+"'>"
		result += "<c class='player_item'><n0>"+item['name']+"</n0>"

		if item['desc'] == '0':
			result += '<t>Description is empty. Write to us about this item!</t>'
		else:
			result += "<span class='trivia-desc'>"+item['desc']+"</span>"

		if item['author'] != '0':
			result += "<span class='trivia-author'> Description by "+item['author']+"</span>"

		result += "</c><br class='clear'/>"

		return result

	def getMonsterInfo(self, uid):
		monster = self.mongo.find('monsters',{'UID':int(uid)}, {
			'name':1, 'lvl_min':1, 'boss':1, 'area':1, 'class':1, 'dungeon':1
		})

		if not monster:
			return 'In Soviet Russia monster kills you!'

		response = '<c class="noimg"><n>'+monster['name']+'</n>'

		response += '<def>Level '+str(monster['lvl_min'])+'</def>'

		if len(monster['class'])>3:
			response += '<s>'+monster['class']+'</s>'

		if monster['boss']:
			dungeon = self.mongo.find('dungeons',{'UID':monster['dungeon']})
			response += '<s>Boss in '+dungeon['name']+'</s>'

		elif monster['area']['area_dungeon']:
			dungeon = self.mongo.find('dungeons',{'UID':monster['dungeon']})
			response += '<s>Monster in '+dungeon['name']+'</s>'

		response += "</c>"
		return response

	def getDungeonInfo(self, uid):
		dungeon = self.mongo.find('dungeons',{'UID': int(uid)}, {'name':1, 'lvl_min':1, 'lvl_max':1})

		if not dungeon:
			return 'In Soviet Russia dungeon runs you!'

		response = '<c class="noimg"><n>'+dungeon['name']+'</n>'
		response += '<def>Level '+str(dungeon['lvl_min'])+' &#8212; '+str(dungeon['lvl_max'])+'</def>'

		#response += '<s>'+dungeon['desc']+'</s>'

		response += "</c>"

		return response

	def getShopItemInfo(self, type_id, uid):
		item = self.mongo.findOne('shop_items',{'UID': int(uid)})

		if not item:
			return 'In Soviet Russia shop buys you!'

		response = "<img src='./data/items/non_combat/"+str(item['img'])+".jpg'><c><n>"+item['name']+'</n>'
		response += '<def>'+str(item['desc'])+'</def>'

		if 'bonus' in item:
			for stat in ['int','str','dex','luck','HP','MP']:
				if item['bonus'][stat] != 0:
					response += "<s>""+"+str(int(item['bonus'][stat]))+" "+self.data.stats[stat]+"</s>"

		response += "</c>"

		return response

	def getBGInfo(self, uid):
		battleground = self.mongo.find('battlegrounds','UID', int(uid))

		if not battleground:
			return 'In Soviet Russia battleground runs you!'

		response = '<c class="noimg"><n>'+battleground['name']+'</n>'
		response += '<def>Level '+str(battleground['lvl_min'])+' &#8212; '+str(battleground['lvl_max'])+'</def>'

		#response += '<s>'+dungeon['desc']+'</s>'

		response += "</c>"

		return response

	def getSpellInfo(self, uid):

		spell = self.mongo.find('spells', {'_id': ObjectId(uid)})

		if not spell:
			spell = self.mongo.find('spells_created', {'_id': ObjectId(uid)})
		else:
			spell['img'] = './data/spells/'+spell['img']+'.jpg'

		if not spell:
			return 'In Soviet Russia spells cast you!'

		result = "<img src='"+spell['img']+"' width='54'>"
		result += "<c class='player_item'><n0>"+spell['name']+"</n0>"
		result += "<t>"+spell['keyword']+"</t><br><s>"

		for action in spell['spell_actions']:
			result += self.spell_types[action['type']] + str(action['value']) + self.data.stats_name[action['effect']]+ '<br>'

		result += "</s></c><div class='clear'></div>"

		return result

	# Deprecated
	def getUserInfo(self, nickname):
		pass

	def getAchvInfo(self, uid):

		achv = self.mongo.find('achievements_static', {'UID':int(uid)})
		if not achv:
			return 'In Soviet Russia achievement earns you!'

		return "<img src='"+self.core.IMAGE_ACHV_FOLDER+achv['img']+".jpg'><c><n0>"+achv['name']+"</n0><s>"+achv['text']+"</s></c>"

	def getInfo(self, obj, main_uid, prefix_uid = 0, suffix_uid = 0):
		obj_type = int(obj)

		result = ''
		
		if obj_type == 1:
			result = self.getItemInfo(main_uid, prefix_uid, suffix_uid)
		elif obj_type == 2:
			result = self.getMonsterInfo(main_uid)
		elif obj_type == 3:
			result = self.getDungeonInfo(main_uid)
		elif obj_type == 4:
			result = self.getUserInfo(main_uid)
		elif obj_type == 5:
			result = self.getAchvInfo(main_uid)
		elif obj_type == 6:
			result = self.getBGInfo(main_uid)
		elif obj_type == 7:
			result = self.getShopItemInfo(main_uid, prefix_uid)
		elif obj_type == 8:
			result = self.getTriviaItemsInfo(main_uid)
		elif obj_type == 9:
			result = self.getDungeonInfo(main_uid)
		elif obj_type == 10:
			result = self.getSpellInfo(main_uid)

		return result

		

if __name__ == '__main__':		
	i = Informer()
	print i.getInfo(1,102,15,22)
