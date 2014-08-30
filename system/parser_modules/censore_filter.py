# -*- coding: utf-8 -*-

import re

__author__ = 'ido'


RE_MAT = re.compile(u'(fuck|asshole|putin)',re.I)

def censoreFilter(tweet):

	if re.search(RE_MAT, tweet.text.encode('utf8')):
		return True

	return False
