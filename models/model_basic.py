#!/usr/bin/python
# -*- coding: utf-8 -*-

import __init__
import db
from model_player import ModelPlayers, PlayerInstance
from model_guilds import ModelGuilds
from model_items import ModelItems, CraftedItemInstance, Item
from model_spells import ModelSpells, CraftedSpellPattern, SpellBook
from model_events import ModelEvents, Event
from model_guilds import ModelGuilds, Guild
from model_achv_stats import ModelSA
from model_misc import ModelMisc, Artwork


class BasicObject():

	data = {}

	def __init__(self, record):
		data.update(record)

class DataModel():

	def __init__(self):
		self.mongo = db.mongoAdapter()

		self.players = ModelPlayers(self.mongo)
		self.playerInstance = PlayerInstance

		self.items = ModelItems(self.mongo)
		self.crafted_item = CraftedItemInstance
		self.game_item = Item

		self.spells = ModelSpells(self.mongo)
		self.craftedSpellPattern = CraftedSpellPattern
		self.spellbook = SpellBook

		self.event = Event
		self.events = ModelEvents(self.mongo)

		self.guild = Guild
		self.guilds = ModelGuilds(self.mongo)

		self.sa = ModelSA(self.mongo)

		self.misc = ModelMisc(self.mongo)
		self.artwork = Artwork

	def getLvls(self):
		return self.mongo.find('lvls')




