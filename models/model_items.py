#!/usr/bin/python
# -*- coding: utf-8 -*-

import __init__
from random import randint
import settings
from time import time
from bson import ObjectId


class Item(settings.BaseObj):
    data = {
        'player_id': None,
        'item_UID': 0,
        'name': '',
        'type': 0,
        'view': 0,
        'color': 0,
        'bonus': {},
        'text': "",
        'cost': 0,
        'img': '',
        'equipped': False,
        'sell': False,
    }


class CraftedItemInstance():
    data = {
        'img': '',
        'color': 0,
        'lvl_min': 0,
        'lvl_max': 0,
        'bonus': {},
        'cost': 0,
        'desc': '',
        'view': '',
        'type': 0,
        'name': '',
        'author': 0,
        'sale_info': {
            'sell_times': 0,
            'total_earn': 0,
            'active': False
        },
        'equipped': False,
        'create_time': 0,
        'approve': {
            'approved': False,
            'time': 0,
            'approver_id': ''
        },
        'img_info': {
            'author': '',
            'link': '',
            'email': '',
            'twitter': ''
        },
        'first_approve': True
    }

    def __init__(self):
        pass


class ModelItems():
    col = settings.database.cols

    like_types = {
        'item': 'col_crafted',
        'artwork': 'col_artworks',
        'spell': 'col_spells_crafted_patterns'
    }

    def __init__(self, connection):
        self.mongo = connection
        self.balance = settings.balance()

    # ADD

    def addCraftedItem(self, player_id, data, eore_added):
        if '_id' in data:
            del data['_id']

        player_update = {'resources.ore': -self.balance.ORE_COST_PER_ITEM}
        if eore_added:
            player_update.update({'resources.eore': -eore_added})

        data.update({'create_time': time()})
        self.mongo.insert(self.col['col_crafted'], data)
        self.mongo.updateInc(self.col['players'], {'_id': player_id}, player_update)

    # GET

    def getCraftedItems(self, _id, fields={}):
        return self.mongo.getu(self.col['col_crafted'], {'author': _id}, sort={'create_time': -1}, fields=fields)

    def getActiveItemsByPlayer(self, _id, fields={}):
        return self.mongo.getu(self.col['col_crafted'], {'author': _id, 'sale_info.active': True},
                               sort={'create_time': -1}, fields=fields)

    def getAllSellingCraftedItems(self, skip=0, limit=0, query={}, sort_query={}):
        if not sort_query:
            sort_query.update({'approve.time': -1})

        query.update({'sale_info.active': True})
        return self.mongo.getu(
            self.col['col_crafted'],
            search=query,
            skip=skip,
            limit=limit,
            sort=sort_query
        )


    def getAllSellingCraftedItemsCount(self, search):
        search.update({'sale_info.active': True})

        return self.mongo.count(
            self.col['col_crafted'],
            search=search,
        )


    def getCountByQuery(self, search):
        return self.mongo.count(
            self.col['col_crafted'],
            search=search,
        )


    def getWaitingItems(self, user_id=False, approved=False, rejected=False, skip=0, limit=0, sorting={'create_time': 1}):
        if rejected:
            record = {'reject': {'$exists': rejected}}
        else:
            record = {
            'approve.approved': approved,
            'reject': {'$exists': rejected}
            }

        if user_id:
            record.update({'author': user_id})

        return self.mongo.getu(self.col['col_crafted'], record, sort=sorting, limit=limit, skip=skip)


    def getApprovedItemsCount(self):
        return self.mongo.count(self.col['col_crafted'], {
        'approve.approved': False,
        'reject': {'$exists': False}
        })


    def getApprovedItems(self, user_id=False):
        return self.getWaitingItems(user_id, True)


    def getLastApprovedItems(self, count=6):
        return self.mongo.getu(self.col['col_crafted'], search={'approve.approved': True}, sort={'approve.time': -1},
                               limit=count)


    def getCraftedItem(self, _id):
        return self.mongo.find(self.col['col_crafted'], {'_id': ObjectId(_id)})


    def getItem(self, _id):
        return self.mongo.find(self.col['col_created'], {'_id': ObjectId(_id)})


    def getItems(self, _ids, fields={}):
        query = {'_id': {'$in': list(_ids)}}
        return self.mongo.getu(self.col['col_crafted'], query, fields)


    def getDeletedThings(self, fields={}):
        return self.mongo.getu(self.col['col_items_deleted'], {}, fields, sort={'deleted_time': -1})


    def getNPItemFromBase(self, item_UID):
        return self.mongo.find(self.col['col_shop_items'], {'item_UID': int(item_UID)})


    def getAllNPItems(self):
        return self.mongo.getu(self.col['col_shop_items'])


    def getPlayerBuyedItems(self, player_id, fields={}):
        return self.mongo.getu(self.col['col_created'], {'player_id': player_id}, fields=fields)


    def getSellingItems(self):
        created_items = self.mongo.getu(self.col['col_crafted'], {'approve.approved': True, 'sale_info.active': True})
        reselling_items = self.mongo.getu(self.col['col_created'], {'sell': True})
        return created_items + reselling_items


    def getEquippedItems(self, player_id, fields_filter=None):
        if fields_filter == 'bonus':
            fields = {'bonus': 1}
        elif fields_filter == 'parser':
            fields = {'bonus': 1, 'type': 1, 'cost': 1, 'name': 1, 'UID': 1}
        else:
            fields = {}

        return self.mongo.getu(self.col['col_created'], {'player_id': player_id, 'equipped': True}, fields)


    def getInventoryCount(self, player_id):
        return self.mongo.count(self.col['col_created'], {'player_id': player_id, 'equipped': False})


    def getFixedItem(self, uid):
        return self.mongo.find(self.col['col_items'], {'UID': uid})


    def getItemLikes(self, item_id):
        if not isinstance(item_id, ObjectId):
            try:
                item_id = ObjectId(item_id)
            except Exception:
                pass

        likes = self.mongo.find(self.col['col_items_likes'], {'item_id': item_id})
        if not likes:
            return {'people': []}
        else:
            return likes


    def getItemsLikes(self, _ids):
        query = []
        for id in _ids:
            query.append({'item_id': id})

        if len(query) > 0:
            mongoQuery = {'$or': query}
        else:
            mongoQuery = {}

        return self.mongo.getu(self.col['col_items_likes'], mongoQuery, {'_id': 0})


    def isReportItem(self, item_id, player_id):
        if not isinstance(item_id, ObjectId):
            try:
                item_id = ObjectId(item_id)
            except Exception:
                pass

        reports = self.mongo.find(self.col['col_items_reports'], {'item_id': item_id}, {'people': 1})
        if not reports:
            return False
        else:
            return player_id in reports['people']


    # IS

    def isCraftedItemExists(self, _id):
        return self.mongo.find(self.col['col_crafted'], {'_id': ObjectId(_id)}, fields={'_id': 1})

    # MISC

    def updateItemData(self, _id, data, no_need_approve):
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

        self.mongo.raw_update(self.col['col_crafted'], {'_id': _id}, record)


    def approveCraftedItem(self, _id, approver_id, beta=False, tag=''):
        object_id = ObjectId(_id)

        self.mongo.raw_update(self.col['col_crafted'], {'_id': object_id}, {
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

        item = self.mongo.find(self.col['col_crafted'], {'_id': object_id}, {'_id': 0, 'sale_info': 0, 'approve': 0})

        if beta:
            item['cost'] = 0
        else:
            item['cost'] = randint(1, 5)

        delete_data = {}

        if 'old_data' in item:
            delete_data.update({'old_data': 1})

        if 'first_approve' in item:
            delete_data.update({'first_approve': 1})

        if delete_data:
            self.mongo.raw_update(self.col['col_crafted'], {'_id': object_id}, {'$unset': delete_data})

        if 'first_approve' in item:
            item.update({'player_id': item['author'], 'sell': False, 'copy': True})
            self.mongo.insert(self.col['col_created'], item)


    def rejectCraftedItem(self, _id, rejecter_id, reason=''):
        object_id = ObjectId(_id)
        self.mongo.raw_update(self.col['col_crafted'], {'_id': object_id}, {
        '$unset': {'approve': 1},
        '$set': {
        'reject': {
        'rejected': True,
        'time': time(),
        'rejecter_id': rejecter_id,
        'reason': reason
        },
        'sale_info.active': False
        }
        })


    def toMarket(self, item_id, cost):
        object_id = ObjectId(item_id)
        item = self.mongo.find(self.col['col_crafted'], {'_id': object_id}, {'lvl_min': 1})
        if item:
            min_cost = self.balance.getItemMinCost({'lvl': item['lvl_min']})
            if cost < min_cost:
                cost = min_cost

            self.mongo.update(self.col['col_crafted'], {'_id': object_id}, {'cost': cost, 'sale_info.active': True})


    def deleteItem(self, item, deleted_person='-'):
        if item:
            self.mongo.remove(self.col['col_crafted'], {'_id': item['_id']})
            if '_id' in item:
                del item['_id']
            item.update({
            'deleted_type': 'item',
            'deleted_time': time(),
            'deleted_person': deleted_person
            })
            self.mongo.insert(self.col['col_items_deleted'], item)


    def buyNPItem(self, player_id, item):
        def buyTitle(item):

            if item['type'] != 105:
                return False

            item = {
            "name": item['name'],
            "item_UID": item['item_UID'],
            "type": item['type'],
            'current': True,
            "desc": item['desc']
            }

            new_array = []

            player = self.mongo.find(self.col['players'], {'_id': player_id, 'titles': {'$exists': 1}},
                                     {'titles': 1, 'user_id': 1, 'name': 1})
            if player:
                for thing in player['titles']:
                    thing.update({'current': False})
                    new_array.append(thing)

            new_array.append(item)

            self.mongo.update(self.col['players'], {'_id': player_id}, {'titles': new_array})

        self.mongo.updateInc(self.col['players'], {'_id': player_id}, {'resources.gold': -item['cost']})

        del item['_id']

        # если покупаем титул или артворк, то это другая история
        # надо записать в базу с игроками
        buyTitle(item)

        # создаем копию предмета и сохраняем в отдельную таблицу
        item.update({'player_id': player_id})
        self.mongo.insert(self.col['col_created'], item)


    def buyCraftedItem(self, player_id, item):
        inventory_count = self.getInventoryCount(player_id)
        if inventory_count < self.balance.INVENTORY_SIZE:

            self.mongo.updateInc(self.col['players'], {'_id': player_id}, {'resources.gold': -item['cost']})

            if player_id != item['author']:
                self.mongo.updateInc(self.col['players'], {'_id': item['author']}, {'resources.gold': item['cost']})

            self.mongo.updateInc(self.col['col_crafted'], {'_id': item['_id']},
                                 {'sale_info.sell_times': 1, 'sale_info.total_earn': item['cost']})

            item.update({
            'player_id': player_id,
            'sell': False,
            'copy': True,
            'parent_id': item['_id']
            })

            del item['_id'], item['sale_info'], item['approve']

            self.mongo.insert(self.col['col_created'], item)


    def sellItem(self, player_id, uid, to_pool=False):
        item = self.mongo.find(self.col['col_created'], {'player_id': player_id, '_id': ObjectId(uid)})
        if item:
            self.mongo.remove(self.col['col_created'], {'_id': item['_id']})
            self.mongo.updateInc(self.col['players'], {'_id': player_id}, {'resources.gold': item['cost']})

            if to_pool and self.balance.chance(self.balance.CHANCE_TO_POOL):
                del item['_id']
                item.update({'pooled_date': time()})
                self.mongo.insert(self.col['col_items_pool'], item)

            return item['cost']

        return 0


    def cancelSelling(self, player_id, item):
        if 'sell' in item and item['sell']:
            self.mongo.update(self.col['col_created'], {'_id': item['_id']}, {'player_id': player_id, 'sell': False})
        else:
            self.mongo.update(self.col['col_crafted'], {'_id': item['_id']}, {'sale_info.active': False})


    def equipItem(self, uid, player_id, player_class, old_id=0, player_lvl=1):
        try:
            correct_uid = int(uid)
            field = 'UID'
        except Exception:
            correct_uid = ObjectId(uid)
            field = '_id'

        item_new = self.mongo.find(self.col['col_created'], {'player_id': player_id, field: correct_uid},
                                   {'_id': 1, 'type': 1, 'item_UID': 1, 'equipped': 1, 'view': 1, 'lvl_min': 1})

        if item_new:
            item_usable = int(item_new['lvl_min']) <= player_lvl and (
            (item_new['type'] == 1) and (self.balance.isItemForClass(item_new, player_class)) or item_new['type'] != 1)

            if item_usable:
                new_item_type = int(item_new['type'])

                if item_new['equipped']:
                    if new_item_type != 6 or new_item_type == 6 and old_id == '0':
                        self.mongo.update(self.col['col_created'], {'_id': item_new['_id']}, {'equipped': False})
                    else:
                        return False
                else:

                    # с кольцами нужно специально работать
                    if new_item_type == 6:
                        if old_id == '0' or old_id == 0:
                            item_old = False
                        else:
                            try:
                                int_uid = int(old_id)
                                item_old = self.mongo.find(self.col['col_created'],
                                                           {'player_id': player_id, 'equipped': True, 'type': new_item_type,
                                                            'UID': int_uid})
                            except Exception:
                                item_old = self.mongo.find(self.col['col_created'],
                                                           {'player_id': player_id, 'equipped': True, 'type': new_item_type,
                                                            '_id': ObjectId(old_id)})
                    else:
                        item_old = self.mongo.find(self.col['col_created'],
                                                   {'player_id': player_id, 'equipped': True, 'type': new_item_type})

                    if item_old:
                        self.mongo.update(self.col['col_created'], {'_id': item_old['_id']}, {'equipped': False})

                    self.mongo.update(self.col['col_created'], {'_id': item_new['_id']}, {'equipped': True})

                return True

            else:
                return False

        return False


    def autoSell(self, item_id):
        self.mongo.remove(self.col['col_created'], {'_id': item_id})


    def lootItem(self, item):
        if '_id' in item:
            del item['_id']

        self.mongo.insert(self.col['col_created'], item)


    def unpackBetaItems(self, player):
        if player:
            beta_items = self.mongo.getu(self.col['col_beta_items'], {'author_beta': player['user_id']}, {'_id': 0})
            if beta_items:
                for item in beta_items:
                    item.update({
                    'author': player['_id'],
                    'from_beta': True
                    })
                    self.mongo.insert(self.col['col_crafted'], item)

                items_to_approve = self.mongo.getu(self.col['col_crafted'], {'author': player['_id'], 'from_beta': True})
                for item in items_to_approve:
                    self.approveCraftedItem(item['_id'], 'game')


    def likeItem(self, item_id, player_id, thing_type='item'):
        if not isinstance(item_id, ObjectId):
            try:
                item_id = ObjectId(item_id)
            except Exception:
                pass

        is_exist = self.mongo.find(self.col['col_items_likes'], {'item_id': item_id}, {'_id': 1})
        if is_exist:
            self.mongo.raw_update(self.col['col_items_likes'], {'item_id': item_id}, {'$addToSet': {'people': player_id}})
        else:

            if not thing_type in self.like_types:
                thing_type = 'item'

            collection_name = self.like_types[thing_type]

            thing_info = self.mongo.find(self.col[collection_name], {'_id': item_id}, {'author': 1})

            if thing_info:
                self.mongo.insert(self.col['col_items_likes'], {
                'item_id': item_id,
                'people': [player_id],
                'thing_type': thing_type,
                'author_id': thing_info['author']
                })


    def reportItem(self, item_id, player_id, type_of='item'):
        if not isinstance(item_id, ObjectId):
            try:
                item_id = ObjectId(item_id)
            except Exception:
                pass

        is_exist = self.mongo.find(self.col['col_items_reports'], {'item_id': item_id}, {'_id': 1})
        if is_exist:
            self.mongo.raw_update(self.col['col_items_reports'], {'item_id': item_id}, {'$addToSet': {'people': player_id}})
        else:
            self.mongo.insert(self.col['col_items_reports'], {
            'item_id': item_id,
            'people': [player_id],
            'type': type_of
            })


    def updateItem(self, item_id, data):
        if not isinstance(item_id, ObjectId):
            item_id = ObjectId(item_id)

        self.mongo.update(self.col['col_crafted'], {'_id': item_id}, data)
