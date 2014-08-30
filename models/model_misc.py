#!/usr/bin/python
# -*- coding: utf-8 -*-

import __init__
import settings
import re
from bson import ObjectId
from time import time
from sets import Set
import random


class Artwork(settings.BaseObj):
    data = {
    "cost": 0,
    "img": "",
    "faction": -1,
    "author": None,
    "race": -1,
    "desc": "",
    "class": -1,
    "name": "",
    'sale_info': {
    'sell_times': 0,
    'total_earn': 0,
    'active': False
    },
    'create_time': 0,

    'approve': {
    'approved': False,
    'time': 0,
    'approver_id': ''
    },

    'img_info': {
    'name': '',
    'link': ''
    }
    }


class ModelMisc():
    col = settings.database.cols

    RE_HTTP_FILTER = re.compile('.*\:\/\/', re.I + re.U)

    def __init__(self, connection):
        self.mongo = connection
        self.balance = settings.balance

    def getDungeons(self):
        return self.mongo.getu(self.col['col_dungeons'])

    def getLocations(self):
        return self.mongo.getu(self.col['col_locations'])

    def getGameStatistics(self):
        stats = self.mongo.getu(self.col['col_gamestats'], {'data': {'$exists': True}}, {'type': 1, 'data': 1})
        result = {}
        for item in stats:
            result[item['type']] = item['data']

        return result

    def getMonsters(self):
        return self.mongo.getu(self.col['col_monsters'])

    def getReportThings(self, type_of):
        return self.mongo.getu(self.col['col_items_reports'], {'type': type_of}, {'_id': 0})

    def getRawArtworks(self, query={}, fields={}):
        return self.mongo.getu(self.col['col_artworks'], query, fields)

    def deleteRawArtworks(self, query):
        return self.mongo.remove(self.col['col_artworks'], query)

    def getMessages(self):
        return self.mongo.getu(self.col['col_messages'], fields={'_id': 0})

    def getNotableMessages(self):
        raw_data = self.mongo.find(self.col['col_gamestats'], {'type': 'notable_messages'})
        if raw_data:
            return raw_data['data']
        else:
            return []

    def getAllArtworks(self,
                       skip=0,
                       limit=0,
                       approved='all',
                       class_and_race=False,
                       rejected=False,
                       search={},
                       users_only=False,
                       sort_query={'create_time': -1},
                       verified='nm'
    ):

        if approved == 'all':
            query = {}
        elif approved:
            query = {'approve.approved': {'$ne': not approved}}
        elif not rejected:
            query = {'approve.approved': False}
        else:
            query = {}

        if verified != 'nm':
            if verified:
                query.update({'$and': [{'img_info.verified': {'$exists': True}}, {'img_info.verified': True}]})
            else:
                query.update({'or': [{'img_info.verified': {'$exists': False}}, {'img_info.verified': False}]})

        if users_only:
            query.update({'UID': {'$exists': False}})

        query.update({'reject': {'$exists': rejected}})
        query.update(search)

        if class_and_race:
            for key in class_and_race:
                query.update({key: class_and_race[key]})

        return self.mongo.getu(self.col['col_artworks'], search=query, skip=skip, limit=limit, sort=sort_query)

    def getRandomArtwork(self):
        x = random.random()
        artworks = self.mongo.getu(self.col['col_artworks'], {
        'random': {'$lte': x},
        'sale_info.active': True,
        'img_info.verified': True
        })
        if not artworks:
            artworks = self.mongo.getu(self.col['col_artworks'], {
            'random': {'$gte': x},
            'sale_info.active': True,
            'img_info.verified': True
            })

        if not artworks:
            return []

        return random.sample(artworks, 1)[0]

    def getAllArtworksByPlayer(self, _id, fields={}):
        return self.mongo.getu(self.col['col_artworks'], {'author': _id}, fields=fields)

    def getActiveArtworksByPlayer(self, _id, fields={}):
        return self.mongo.getu(self.col['col_artworks'], {'author': _id, 'sale_info.active': True}, fields=fields)


    def getArtworkById(self, _id):
        if not isinstance(_id, ObjectId):
            try:
                _id = ObjectId(_id)
            except Exception:
                return False

        return self.mongo.find(self.col['col_artworks'], {'_id': _id})

    def getBuiltInArtworkByUID(self, UID):
        if not isinstance(UID, int):
            try:
                UID = int(UID)
            except Exception:
                return False

        return self.mongo.find(self.col['col_artworks'], {'UID': UID})

    def getArtworksByIds(self, _ids, fields={}):
        query = {'_id': {'$in': list(_ids)}}
        return self.mongo.getu(self.col['col_artworks'], query, fields)

    def getAllArtworksCount(self, search, verified):

        search.update({'sale_info.active': True})

        if verified != 'nm':
            if verified:
                search.update({'$and': [{'img_info.verified': {'$exists': True}}, {'img_info.verified': True}]})
            else:
                search.update({'or': [{'img_info.verified': {'$exists': False}}, {'img_info.verified': False}]})

        return self.mongo.count(
            self.col['col_artworks'],
            search=search,
        )

    def getArtworkByUID(self, uid):
        return self.mongo.find(self.col['col_artworks'], {'UID': uid})

    def getPlayersBuyedArtworks(self, player_id):
        buff = self.mongo.find(self.col['players'], {'_id': player_id}, {'artworks': 1})
        if buff and 'artworks' in buff:
            return buff['artworks']
        else:
            return []

    def changePlayerArtworks(self, player_id, artwork_img):
        available_artworks = self.getPlayersBuyedArtworks(player_id)
        if available_artworks:

            artworks = []
            for artwork in available_artworks:
                if artwork['img'] == artwork_img:
                    artwork.update({'current': True})
                else:
                    artwork.update({'current': False})

                artworks.append(artwork)

            self.mongo.update(self.col['players'], {'_id': player_id}, {'artworks': artworks})

    def getPlayerInvite(self, player_name):
        return self.mongo.find(self.col['col_invites'], {'name': player_name})

    def getRareAchvs(self):
        return self.mongo.getu(self.col['col_achv_static'], {'type': 6})

    def getAchv(self, UID):
        return self.mongo.find(self.col['col_achv_static'], {'UID': UID})

    def getBlogPosts(self):
        raw = self.mongo.find(self.col['col_gamestats'], {'type': 'blog_posts'}, {'posts'})
        if raw:
            return raw['posts']
        else:
            return []

    def getApprovedArtworksCount(self):
        return self.mongo.count(self.col['col_artworks'], {
        'approve.approved': False,
        'reject': {'$exists': False}
        })

    def isTipsExists(self):
        return self.mongo.find(self.col['col_gamestats'], {'type': 'tips'}, {'_id': 1})

    def getTips(self):
        tips = self.mongo.find(self.col['col_gamestats'], {'type': 'tips'}, {'tips': 1})
        if tips:
            return tips['tips']
        else:
            return []

    def getChangeLevels(self):
        levels = self.mongo.find(self.col['col_gamestats'], {'type': 'levels'}, {'info': 1})
        if levels:
            return levels['info']
        else:
            return []

    def getRandomTip(self):
        _tips = self.mongo.find(self.col['col_gamestats'], {'type': 'tips'}, {'tips': 1})
        tips = []
        for tip in _tips['tips']:
            if tip['enable']:
                tips.append(tip)

        if tips:
            return tips[random.randint(0, len(tips) - 1)]
        else:
            return False

    # ADD

    def addTip(self, tip, author_id=False, author_name=False, not_new=False):

        tip_data = {
            'content': tip,
            'author': author_id,
            'author_name': author_name,
            'enable': True,
            'uid': int(time()),
            'random': random.random()
        }

        if not_new:
            self.mongo.raw_update(self.col['col_gamestats'], {'type': 'tips'}, {'$push': {'tips': tip_data}})
        else:
            self.mongo.insert(self.col['col_gamestats'], {
                'type': 'tips',
                'tips': [tip_data]
            })

    def updateTips(self, tips):
        self.mongo.update(self.col['col_gamestats'], {'type': 'tips'}, {'tips': tips})

    def addArtwork(self, artwork):
        artwork.update({'random': random.random()})
        if '_id' in artwork:
            del artwork['_id']

        self.mongo.insert(self.col['col_artworks'], artwork)

    # Tags ============================================================================================

    def getTags(self):
        tags = self.mongo.find(self.col['col_gamestats'], {'type': 'tags'}, {'tags': 1})
        if tags:
            return tags['tags']
        else:
            return []

    def addTag(self, name, variable, author_id=False, author_name=False):

        tag_data = {
            'name': name,
            'variable': variable,
            'author': author_id,
            'author_name': author_name,
            'uid': int(time())
        }

        is_tags_exist = self.mongo.find(self.col['col_gamestats'], {'type': 'tags'})

        if is_tags_exist:
            self.mongo.raw_update(self.col['col_gamestats'], {'type': 'tags'}, {'$push': {'tags': tag_data}})
        else:
            self.mongo.insert(self.col['col_gamestats'], {
                'type': 'tags',
                'tags': [tag_data]
            })

    def deleteTags(self, uid):
        tags = self.getTags()
        new_tags = []
        for tag in tags:
            if tag['uid'] != uid:
                new_tags.append(tag)

        self.mongo.update(self.col['col_gamestats'], {'type': 'tags'}, {'tags': new_tags})

    # MISC

    def writeToLog(self, player_id, action):
        self.mongo.insert(self.col['col_tweeria_log'], {
        'time': time(),
        'player_id': player_id,
        'action': action
        })

    def deleteArtwork(self, artwork, deleted_person='-'):
        if artwork:
            self.mongo.remove(self.col['col_artworks'], {'_id': artwork['_id']})
            if '_id' in artwork:
                del artwork['_id']

            artwork.update({
            'deleted_type': 'artwork',
            'deleted_time': time(),
            'deleted_person': deleted_person
            })

            self.mongo.insert(self.col['col_items_deleted'], artwork)

    def saveNotableMessages(self, messages):
        self.mongo.update(self.col['col_gamestats'], {'type': 'notable_messages'},
                          {'type': 'notable_messages', 'data': messages}, True)

    def approveArtwork(self, _id, approver_id, tag=''):
        object_id = ObjectId(_id)
        self.mongo.raw_update(self.col['col_artworks'], {'_id': object_id}, {
        '$unset': {'reject': 1, 'from_beta': 1},
        '$set': {
        'sale_info.active': True,
        'approve': {
        'approved': True,
        'time': time(),
        'approver_id': approver_id
        },
        'img_info.verified': True,
        'tag': tag
        }
        })

        artwork = self.mongo.find(self.col['col_artworks'], {'_id': object_id})
        self._artworkAddToPlayer(artwork['author'], artwork)

    def rejectArtwork(self, _id, rejecter_id, reason=''):
        object_id = ObjectId(_id)
        self.mongo.raw_update(self.col['col_artworks'], {'_id': object_id}, {
        '$unset': {'approve': 1},
        '$set': {
        'sale_info.active': False,
        'reject': {
        'rejected': True,
        'time': time(),
        'rejecter_id': rejecter_id,
        'reason': reason
        },
        }
        })

    def updateArtworkData(self, _id, data, no_need_approve):
        if isinstance(_id, str):
            _id = ObjectId(_id)

        if no_need_approve:
            record = {'$set': data}
        else:
            data.update({
            'sale_info.active': False,
            'approve': {
            'approved': False,
            'time': 0,
            'approver_id': ''
            },
            })

            record = {'$set': data, '$unset': {'reject': True}}

        self.mongo.raw_update(self.col['col_artworks'], {'_id': _id}, record)

    def cancelSelling(self, player_id, artwork):
        if 'sell' in artwork and artwork['sell']:
            self.mongo.update(self.col['col_artworks'], {'_id': artwork['_id']},
                              {'player_id': player_id, 'sell': False})
        else:
            self.mongo.update(self.col['col_artworks'], {'_id': artwork['_id']}, {'sale_info.active': False})

    def artworkToMarket(self, artwork_id, cost):
        object_id = ObjectId(artwork_id)
        self.mongo.update(self.col['col_artworks'], {'_id': object_id}, {'cost': cost, 'sale_info.active': True})

    def _artworkAddToPlayer(self, player_id, artwork):

        def cleanUpArtwork(artwork):
            del artwork['cost'], artwork['class'], artwork['race']
            if 'sale_info' in artwork and not 'UID' in artwork:
                del artwork['sale_info'], artwork['approve'], artwork['img_info']
            else:
                del artwork['builtin']

        artwork['current'] = True

        new_array = []
        player = self.mongo.find(self.col['players'], {
        '_id': player_id,
        'artworks': {'$exists': 1}},
                                 {'artworks': 1, 'user_id': 1, 'name': 1, 'class': 1, 'race': 1, 'faction': 1}
        )

        if player:

            is_match = True
            if not player['race'] == 1 and not player['faction'] == 0:
                for key in ['class', 'race', 'faction']:
                    is_match = is_match and artwork[key] == player[key]
            else:
                is_match = artwork['class'] == player['class']

            if is_match:

                cleanUpArtwork(artwork)

                for thing in player['artworks']:
                    thing.update({'current': False})
                    new_array.append(thing)

                new_array.append(artwork)

                self.mongo.update(self.col['players'], {'_id': player_id}, {'artworks': new_array})

    def buyCraftedArtwork(self, player, artwork):

        if player['race'] == artwork['race'] and player['faction'] == artwork['faction'] and player['class'] == artwork[
            'class']:

            self.mongo.updateInc(self.col['players'], {'_id': player['_id']}, {'resources.gold': -artwork['cost']})
            self.mongo.updateInc(self.col['players'], {'_id': artwork['author']}, {'resources.gold': artwork['cost']})
            self.mongo.updateInc(self.col['col_artworks'], {'_id': artwork['_id']},
                                 {'sale_info.sell_times': 1, 'sale_info.total_earn': artwork['cost']})

            self._artworkAddToPlayer(player['_id'], artwork)

            return False

        else:
            return 'error!'

    def buyStandardArtwork(self, player, artwork):

        if player['race'] == artwork['race'] and player['faction'] == artwork['faction'] and player['class'] == artwork[
            'class']:

            self.mongo.updateInc(self.col['players'], {'_id': player['_id']}, {'resources.gold': -artwork['cost']})
            self._artworkAddToPlayer(player['_id'], artwork)

            return False

        else:
            return 'error!'

    def getImageInfo(self, params):

        img_source, name, email, twitter = '', '', '', ''
        if 'img_source' in params:
            img_source = re.sub(self.RE_HTTP_FILTER, '', params['img_source'])

        if 'img_author' in params:
            name = params['img_author'].strip()

        if 'img_twitter' in params:
            twitter = params['img_twitter'].strip()
            if twitter and twitter[0] == '@':
                twitter = twitter[1:]

        if 'img_email' in params:
            email = params['img_email'].strip()

        if 'copyright_type' in params:
            copy = params['copyright_type']
        else:
            copy = 'unknown'

        return {
        'img_info': {
        'link': img_source,
        'name': name,
        'twitter': twitter,
        'email': email,
        'iamauthor': 'iamauthor' in params,
        'copyright': copy,
        'verified': 'verified' in params
        }
        }

    def isDuplicate(self, collection_name, search):
        return self.mongo.find(settings.database.cols[collection_name], search)

    def setFeaturedArtwork(self, artwork_id, n):
        try:
            obj_id = ObjectId(artwork_id)
        except Exception:
            return False

        artwork = self.mongo.find(self.col['col_artworks'], {'_id': obj_id})
        player_name = self.mongo.find(self.col['players'], {'_id': artwork['author']}, {'name': 1})

        featured_artworks = self.mongo.find(self.col['col_gamestats'], {'type': 'featured_artwork'}, {'_id': 0})

        if featured_artworks:
            record = {
            'img': artwork['img'],
            'class': artwork['class'],
            'race': artwork['race'],
            'faction': artwork['faction'],
            'author_name': player_name['name'],
            'artwork_name': artwork['name'],
            'artwork_id': artwork['_id']
            }

            featured_artworks['artworks'][n] = record

            self.mongo.update(self.col['col_gamestats'], {'type': 'featured_artwork'}, featured_artworks, True)

    def unpackBetaArtworks(self, player):

        if player:
            artworks = self.mongo.getu(self.col['col_beta_artworks'], {'author_beta': player['user_id']}, {'_id': 0})
            if artworks:
                for artwork in artworks:
                    artwork.update({
                    'author': player['_id'],
                    'from_beta': True
                    })
                    self.mongo.insert(self.col['col_artworks'], artwork)

                artworks_to_approve = self.mongo.getu(self.col['col_artworks'],
                                                      {'author': player['_id'], 'from_beta': True})
                for artwork in artworks_to_approve:
                    self.approveArtwork(artwork['_id'], 'game')

    def updateArtwork(self, artwork_id, data):
        if not isinstance(artwork_id, ObjectId):
            artwork_id = ObjectId(artwork_id)

        self.mongo.update(self.col['col_artworks'], {'_id': artwork_id}, data)

    def saveDeletedArtworksPaths(self, paths):
        is_paths = self.mongo.find(self.col['col_gamestats'], {'type': 'deleted_artworks'})
        if is_paths:
            self.mongo.raw_update(self.col['col_gamestats'], {'type': 'deleted_artworks'},
                                  {'$pushAll': {'paths': paths}})
        else:
            self.mongo.insert(self.col['col_gamestats'], {'type': 'deleted_artworks', 'paths': paths})

    # auth requests

    def addAuthRequest(self, request):
        request.update({'status': 'waiting'})
        self.mongo.insert(self.col['authors_requests'], request)

    def getAuthRequestsCount(self):
        return self.mongo.count(self.col['authors_requests'],
                                {'$or': [{'status': {'$exists': False}}, {'status': 'waiting'}]})

    def getAuthRequests(self):
        return self.mongo.getu(self.col['authors_requests'],
                               {'$or': [{'status': {'$exists': False}}, {'status': 'waiting'}]})

    def markAuthRequestById(self, id, status='no_info', additional=None):
        if not isinstance(id, ObjectId):
            id = ObjectId(id)

        record = {'status': status}

        if additional:
            record.update(additional)

        self.mongo.update(self.col['authors_requests'], {'_id': id}, record)

    def delAuthRequestsByPlayerId(self, player_id, except_id=None):
        if not isinstance(player_id, ObjectId):
            player_id = ObjectId(player_id)

        if except_id and not isinstance(except_id, ObjectId):
            except_id = ObjectId(except_id)

        self.mongo.remove(self.col['authors_requests'], {
        'game_id': player_id,
        '_id': {'$ne': except_id},
        '$or': [{'status': {'$exists': False}}, {'status': 'waiting'}]
        })

    # actions and messages

    def getActions(self, fields={}):
        return self.mongo.getu(self.col['meta_actions'], fields=fields)

    def getActionByName(self, name):
        return self.mongo.find(self.col['meta_actions'], {'name': name})

    def getMessagesByAction(self, action):

        message_type_uids = Set()
        message_result_types = ['messages_OK', 'messages_FAIL', 'callback_OK', 'callback_FAIL']

        for key in message_result_types:
            if key in action and action[key]:
                message_type_uids.add(action[key])

        if not message_type_uids:
            return []

        query = []
        for uid in message_type_uids:
            query.append({'type': uid})

        return self.mongo.getu(self.col['col_messages'], {'$or': query}, sort={'UID': 1})

    def getMessageById(self, _id):
        if not isinstance(_id, ObjectId):
            try:
                _id = ObjectId(_id)
            except Exception:
                return False

        return self.mongo.find(self.col['col_messages'], {'_id': _id})

    def saveMessageData(self, _id, data):
        if not isinstance(_id, ObjectId):
            try:
                _id = ObjectId(_id)
            except Exception:
                return False

        self.mongo.update(self.col['col_messages'], {'_id': _id}, data)

    def addNewMessage(self, data):

        uid_info = self.mongo.getu(self.col['col_messages'], {'type': {'$ne': 0}}, {'UID': 1}, sort={'UID': -1},
                                   limit=1)
        uid = uid_info[0]['UID'] + 1

        data.update({'UID': uid})
        self.mongo.insert(self.col['col_messages'], data)

    def deleteMessage(self, _id):
        if not isinstance(_id, ObjectId):
            try:
                _id = ObjectId(_id)
            except Exception:
                return False

        return self.mongo.remove(self.col['col_messages'], {'_id': _id})

    # authors likes

    def getAuthorsLikes(self, count=10, fields={}, skip=0):
        return self.mongo.getu(self.col['authors_likes'], fields, limit=count, sort={'likes': -1}, skip=skip)

    def getAuthorsCount(self):
        return self.mongo.count(self.col['authors_likes'])

    def getAuthorLikes(self, _id, fields={}):
        return self.mongo.find(self.col['authors_likes'], {'author_id': _id}, fields=fields)