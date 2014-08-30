# -*- coding: utf-8 -*-

class TweetNotificationCenter():

	URL = 'http://tweeria.com'
	TAGS = '#tweeria'

	def __init__(self):
		pass

	def parseNotification(self, notification):
		count = len(notification['notifications'])

		text = ''
		if count == 1:
			n_type = notification['notifications'][0]['type']

			if n_type == 'achv':
				text = 'I\'ve earned new achievement ['+notification['notifications'][0]['data']+']'

			if n_type == 'lvl':
				text = 'I\'ve reached level '+str(notification['notifications'][0]['data'])

		else:
			achvs = 0
			achv = ''
			lvls = 0
			max_lvl = 0

			for note in notification['notifications']:
				if note['type'] == 'achv':
					achvs += 1
					achv = note['data']

				elif note['type'] == 'lvl':
					lvls += 1
					if note['data'] > max_lvl:
						max_lvl = note['data']

			if achvs > 1:
				text = 'I\'ve earned new achievement ['+notification['notifications'][0]['data']+'] and '+str(achvs-1)+' more'

			else:
				text = 'I\'ve reached level '+str(max_lvl)

		text += ' - '+self.URL+'/'+notification['name']
		text += ' '+self.TAGS

		return text

