#!/usr/bin/python
# -*- coding: utf-8 -*-

import __init__
import os, sys, inspect
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/python_memcached-1.48-py2.7.egg')

import Image
import ImageFont, ImageDraw
import re
import basic
from urllib import urlretrieve
import socket

socket.setdefaulttimeout(20)

class imageCreator(basic.defaultClass):

	DIR = ''

	# на сервере рисует текст на 4 пикселя выше чем на тестовом локальном

	def __init__(self):
		self.mongoConnect()
		self.loadSettings()
		self.loadBalance()
		self.DIR = os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])+'/../'
		basic.defaultClass.__init__(self)

	def getPlayerAvatarLocalURL(self, username, url):

		extention = re.search('\.(png|gif|jpg|jpeg)$',url,re.I)
		if not extention:
			extention = '.jpg'
		else:
			extention = extention.group()

		filepath = self.DIR + self.core.TEMPLATES_FOLDER+self.core.IMAGE_BUFFER_FOLDER+username+'__'+extention
		print filepath
		urlretrieve(url.encode('utf-8'),filepath)

		return filepath

	def getPreview(self, player):

		# загружаем аватар
		local_url = self.getPlayerAvatarLocalURL(player['name'], player['avatar'])

		try:
			im_ava_clear = Image.open(local_url)
			im_ava_clear.convert('RGBA')
		except :
			print local_url, player['name'], player['avatar']

		# убираем прозрачность
		im_ava = Image.new("RGB", im_ava_clear.size, (223, 220, 215))
		if len(im_ava_clear.split())>3:
			im_ava.paste(im_ava_clear, mask=im_ava_clear.split()[3])
		else:
			im_ava.paste(im_ava_clear)


		# загружаем бэкграунд
		im_bg = Image.open(self.DIR + self.core.TEMPLATES_FOLDER+self.core.IMAGE_GEN_SOURCE_FOLDER+'bg.png')
		im_bg.convert('RGBA')


		PTserif_12 = ImageFont.truetype(self.DIR + self.core.TEMPLATES_FOLDER+"data/fonts/serif.ttf", 12)
		PTserif_18 = ImageFont.truetype(self.DIR + self.core.TEMPLATES_FOLDER+"data/fonts/serif_bold.ttf", 18)

		PTserif_14_bold = ImageFont.truetype(self.DIR + self.core.TEMPLATES_FOLDER+"data/fonts/serif_bold.ttf", 14)


		im_preview = Image.new("RGB", (350, 60), (255,255,255))
		im_preview.paste(im_bg, (0,0))
		im_preview.paste(im_ava, (33,4))



		draw = ImageDraw.Draw(im_preview)

		lvl = int(player['lvl'])
		if lvl < 10:
			draw.text((13, 8), str(lvl), font=PTserif_14_bold, fill=(255,255,255))
		else:
			if lvl < 20:
				draw.text((9, 8), str(lvl), font=PTserif_14_bold, fill=(255,255,255))
			else:
				draw.text((10, 8), str(lvl), font=PTserif_14_bold, fill=(255,255,255))


		p_class = self.balance.classes[int(player['class'])]
		try:
			p_class = self.balance.races[int(player['race'])] + ' ' + p_class
		except:
			pass


		guilds = self.mongo.getAll_perfect('guilds',{'people':{'$all':[player['_id']]}},{'name':1})
		if guilds:
			draw.text((85, 4), player['name'], font=PTserif_18, fill=(0,0,0))
			draw.text((85, 25), guilds[0]['name'], font=PTserif_14_bold, fill=(137,71,0))
			draw.text((85, 43), p_class, font=PTserif_12, fill=(77,77,77))
		else:
			draw.text((85, 4), player['name'], font=PTserif_18, fill=(0,0,0))
			draw.text((85, 27), p_class, font=PTserif_12, fill=(77,77,77))


		draw.text((265, 40), str(player['pvp_score']), font=PTserif_14_bold, fill=(119,0,0))
		draw.text((321, 40), str(player['achv_points']), font=PTserif_14_bold, fill=(0,93,132))

		im_preview.save(self.DIR + self.core.TEMPLATES_FOLDER+self.core.IMAGE_GEN_FOLDER+player['name']+'.png', "PNG")

	def genarateOne(self, name):
		player = self.mongo.findOne('players',{'name': name})
		if player:
			self.getPreview(player)
			print 'Preview generated ', name
		else:
			print 'No player with'

	def generateAll(self):
		players = self.mongo.getAll('players')
		for player in players:
			print 'Started ', player['name']
			try:
				self.getPreview(player)
				print 'Preview generated ', player['name']
			except:
				print 'fail', player['name']



if __name__ == '__main__':
	ic = imageCreator()

	#ic.genarateOne('suxxes')
	ic.generateAll()
