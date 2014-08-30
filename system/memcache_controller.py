# -*- coding: utf-8 -*-

import db
import time
import re
import cherrypy
import memcache
import __main__


class cacheController():
    collection = 'cache'
    mongo = db.mongoAdapter()
    mc = memcache.Client(['127.0.0.1:11211'], debug=1)
    core = __main__.tweenk_core

    exclude = [
        'new', 'login', 'registration', 'logout', 'admin'
    ]

    def __init__(self):
        pass

    def cleanCache(self):
        self.mc.flush_all()

    def isPlayer(self):
        cookie = cherrypy.request.cookie
        is_player = 'user_id' in cookie.keys() and 'hash' in cookie.keys()
        return is_player

    def cacheLoad(self, page_name, params=[]):
        if page_name in self.exclude:
            return False

        try:
            key = '|'.join([page_name, '#'.join(params)])
            cache = self.mc.get(key.encode('utf-8'))
            if cache:
                if time.time() - int(cache['time']) < self.core.CACHE_TIME:
                    return cache

        except Exception:
            print 'Can not load cache', page_name

        return False

    def deleteCache(self, page_name, player, params={}):
        try:
            mobile = self.isMobile()
            key = '|'.join([page_name, player, '#'.join(params), mobile])
            self.mc.delete(key.encode('utf-8'))
        except:
            print 'Can not delete cache', page_name

    def cacheSave(self, page_name, params={}, content=''):

        if page_name in self.exclude:
            return False

        print 'saving...'
        try:
            key = '|'.join([page_name, '#'.join(params)])
            obj = {'content': content, 'time': time.time()}
            self.mc.set(key.encode('utf-8'), obj)
            return True
        except Exception:
            print 'Can not save cache', page_name
            return False

    def permanentSave(self, page_name, params={}, content=''):
        self.cacheSave(page_name, params, content)

    def permanentLoad(self, page_name, params=[]):
        try:
            key = '|'.join([page_name, '_', '#'.join(params), '_'])
            cache = self.mc.get(key.encode('utf-8'))

            if cache:
                return cache
        except Exception:
            print 'Can not load cache', page_name

        return False

    def tmpLoad(self, tmp_name):
        try:
            cache = self.mc.get(tmp_name.encode('utf-8'))

            if cache:
                if time.time() - int(cache['time']) < self.core.TMP_CACHE_TIME:
                    return cache
        except:
            print 'Can load template cache', tmp_name

        return False

    def tmpSave(self, tmp_name, content):
        try:
            self.mc.set(tmp_name.encode('utf-8'), {'content': content, 'time': time.time()})
        except:
            print 'Can not save template cache', tmp_name