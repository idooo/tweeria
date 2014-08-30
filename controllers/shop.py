# -*- coding: UTF-8 -*-

import basic
from sets import Set
import math
import json
from functions import prettyItemBonus, getDisplayPages, getReadbleTime
from misc import miscController
import re
import cherrypy
from bson import BSON
from bson import json_util

import pprint


class shopController(basic.defaultController):
    DIR = './shop/'
    pp = pprint.PrettyPrinter(indent=4)

    @basic.methods
    def methods(self, params={}):
        return {
            'type_of_form': {
            'buy_NP_item': self.buyItem,
            'buy_crafted_item': self.buyItem,
            'buy_spell': self.buySpell,
            'buy_artwork': self.buyArtwork
        },
            'page_type': self.printAjaxShopRecords,
            'like': self.likeProxy
        }

    @basic.printpage
    def printPage(self, page, params):
        return {
            #'shop': self.printShopDisabled,
            'shop': self.printShopPage,
            'promo': self.printPromoPage
        }

    # --------------------------------------------------------------------------------------------------
    # Misc


    def likeProxy(self, params):
        return miscController.likeIt(self, params)


    def getPlayerBuyedItems(self, _id):
        return self.model.items.getPlayerBuyedItems(_id)


    def getLikesDict(self, items_ids):
        buff_item_likes = self.model.items.getItemsLikes(items_ids)

        item_likes = {}
        for item_like in buff_item_likes:
            item_likes.update({
            str(item_like['item_id']):
                {
                    'count': len(item_like['people']),
                    'people': item_like['people']
                }
            })

        return item_likes


    def getLike(self, item_likes, _id):
        str_id = str(_id)
        record = {
            'likes': 0,
            'is_like': False
        }

        if str_id in item_likes:
            record['likes'] = item_likes[str_id]['count']
            if self.cur_player:
                record['is_like'] = self.cur_player['login_id'] in item_likes[str_id]['people']

        return record

    # --------------------------------------------------------------------------------------------------
    # Page methods


    def buyArtwork(self, params):
        ajax = False
        if "ajax" in params and int(params['ajax']) == 1:
            ajax = True

        id = params['artwork_id']
        artwork_crafted_by_player = False

        try:
            id = int(id)
        except Exception:
            artwork_crafted_by_player = True

        try:
            if artwork_crafted_by_player:
                artwork = self.model.misc.getArtworkById(id)
            else:
                artwork = self.model.misc.getArtworkByUID(id)

            buff = self.model.players.getPlayer(self.cur_player['login_user_id'], {'resources': 1, 'artworks': 1},
                                                flags=['no_messages'])
            already_artworks = buff['artworks']
            user_resources = buff['resources']

        except Exception:
            if ajax:
                return json.dumps({"error": 1, "message": "Unknown Error"})
            else:
                return self.error('Unknown Error')

        if not artwork:
            if ajax:
                return json.dumps({"error": 1, "message": "Artwork not found"})
            else:
                return self.error('Artwork not found')

        if user_resources['gold'] < artwork['cost']:
            if ajax:
                return json.dumps({"error": 1, "message": "Not enough gold"})
            else:
                return self.error('Not enough gold')

        player_data = {
            '_id': self.cur_player['login_id'],
            'class': self.cur_player['login_class'],
            'faction': self.cur_player['login_faction'],
            'race': self.cur_player['login_race']
        }

        if artwork_crafted_by_player:
            error = self.model.misc.buyCraftedArtwork(player_data, artwork)
        else:
            error = self.model.misc.buyStandardArtwork(player_data, artwork)

        if error:
            if ajax:
                return json.dumps({"error": 1, "message": "Unknown Error"})
            else:
                return self.error('Unknown Error')

        if ajax:
            authors_ids = Set()
            authors_ids.add(artwork['author'])

            players_names = self.model.players.getPlayersList(authors_ids, ['_id', 'name'])

            user_resources.update({
                "item_name": artwork["name"],
                "item_id": id,
                "gold": int(user_resources["gold"]) - int(artwork["cost"]),
                "success": 1
            })

            if len(players_names) > 0:
                user_resources.update({
                    "item_author": players_names[0]["name"]
                })
            return json.dumps(user_resources)
        else:
            self.httpRedirect(params, '?success=ok&n=' + artwork['name'])


    def buyItem(self, params):
        ajax = False
        if "ajax" in params and int(params['ajax']) == 1:
            ajax = True

        id = params['item_id']
        item_crafted_by_player = False
        try:
            id = int(id)
        except Exception:
            item_crafted_by_player = True

        try:
            if item_crafted_by_player:
                item = self.model.items.getCraftedItem(id)
                if 'reject' in item and item['reject']:
                    raise Exception
            else:
                item = self.model.items.getNPItemFromBase(id)
                already_items = self.getPlayerBuyedItems(self.cur_player['login_id'])

            user_resources =self.model.players.getPlayer(
                self.cur_player['login_user_id'],
                {'resources': 1},
                ['no_messages']
            )['resources']

        except Exception:
            if ajax:
                return json.dumps({"error": 1, "message": "Unknown Error"})
            else:
                return self.error('Unknown Error')

        if not item:
            if ajax:
                return json.dumps({"error": 1, "message": "Item not found"})
            else:
                return self.error('Item not found')

        if user_resources['gold'] < item['cost']:
            if ajax:
                return json.dumps({"error": 1, "message": "Not enough gold"})
            else:
                return self.error('Not enough gold')

        if item_crafted_by_player:
            self.model.items.buyCraftedItem(self.cur_player['login_id'], item)

            try:
                params['__query__'] = params['__query__'][:params['__query__'].index('&success')]
            except Exception:
                pass

        else:
            for already_item in already_items:
                if 'item_UID' in already_item and already_item['item_UID'] == item['item_UID'] and already_item['type'] == item['type']:
                    self.sbuilder.httpRedirect(params['__page__'])

            self.model.items.buyNPItem(self.cur_player['login_id'], item)

        if ajax:
            user_resources.update({
                "item_name": item["name"],
                "item_id": id,
                "gold": int(user_resources["gold"]) - int(item["cost"]),
                "success": 1
            })
            return json.dumps(user_resources)

        else:
            if 'backlink' in params:
                self.httpRedirect(params)
            else:
                self.sbuilder.httpRedirect(params['__page__'] + '?success=ok&n=' + item['name'])


    def buySpell(self, params):
        ajax = False
        if "ajax" in params and int(params['ajax']) == 1:
            ajax = True

        id = params['spell_id']
        try:
            spell = self.model.spells.getSpellPatternByID(id)
            user_resources = self.model.players.getPlayer(self.cur_player['login_user_id'], {'resources': 1})['resources']

        except Exception:
            if ajax:
                return json.dumps({"error": 1, "message": "Unknown Error"})
            else:
                return self.error('Unknown Error')

        if not spell:

            if ajax:
                return json.dumps({"error": 1, "message": "Spell not found"})
            else:
                return self.error('Spell not found')

        if user_resources['gold'] < spell['cost']:
            if ajax:
                return json.dumps({"error": 1, "message": "Not enough gold"})
            else:
                return self.error('Not enough gold')

        self.model.spells.buySpellPattern(self.cur_player['login_id'], spell)

        try:
            params['__query__'] = params['__query__'][:params['__query__'].index('&success')]
        except Exception:
            pass

        if ajax:
            user_resources.update({
                "item_name": spell["name"],
                "item_id": id,
                "gold": int(user_resources["gold"]) - int(spell["cost"])
            })

            user_resources.update({"success": 1})
            return json.dumps(user_resources)

        else:
            if 'backlink' in params:
                self.httpRedirect(params)
            else:
                self.sbuilder.httpRedirect(
                    params['__page__'] + '?' + params['__query__'] + '&success=ok&n=' + spell['name'] + '&sb=' + params[
                        'spell_id'])

    # --------------------------------------------------------------------------------------------------
    # Ajax print pages


    def getPaginatorData(self, items_on_page, spells_on_page, artworks_on_page, search):
        verified = True
        if self.cur_player and 'login_admin' in self.cur_player and self.cur_player['login_admin']:
            verified = 'nm'

        players_items_count = self.model.items.getAllSellingCraftedItemsCount(search['items'])
        spells_count = self.model.spells.getAllSellingSpellsCount(search['spells'])
        artworks_count = self.model.misc.getAllArtworksCount(search['artworks'], verified)

        items_pages = int(math.ceil(float(players_items_count) / items_on_page))
        spells_pages = int(math.ceil(float(spells_count) / spells_on_page))
        artworks_pages = int(math.ceil(float(artworks_count) / artworks_on_page))

        return {
            'item_pages': items_pages,
            'spell_pages': spells_pages,
            'artwork_pages': artworks_pages
        }


    def printAjaxShopRecords(self, params):
        def getSearchParams(params):

            keys = ['search', 'type', 'cost_min', 'cost_max', 'author', 'level_min', 'level_max', 'only_can_use', 'race',
                    'class', 'keyword', 'tag']

            search = {}
            if 'search' in params:
                for key in keys:

                    if key in params:
                        stripped = params[key].strip()
                        if stripped:
                            search.update({key: stripped})

                if 'search' in search:
                    search['name'] = {'$regex': re.compile('.*' + search['search'] + '.*', re.IGNORECASE)}
                    del search['search']

                if 'keyword' in search:
                    search['keyword'] = {'$regex': re.compile('.*' + search['keyword'] + '.*', re.IGNORECASE)}

                if 'tag' in search:
                    search['tag'] = {'$regex': re.compile('.*' + search['tag'] + '.*', re.IGNORECASE)}

                if 'type' in search:
                    item_type = search['type'].split(':')
                    if len(item_type) != 1:
                        search['view'] = item_type[1]

                    search['type'] = int(item_type[0])

                if 'author' in search:
                    player_id = self.model.players.getPlayer_ID(
                        {'$regex': re.compile('.*' + search['author'] + '.*', re.IGNORECASE)})
                    if player_id:
                        search['author'] = player_id
                    else:
                        search['author'] = 0

                if 'cost_min' in search:
                    try:
                        search['cost'] = {'$gte': int(search['cost_min'])}
                    except Exception:
                        pass

                    del search['cost_min']

                if 'cost_max' in search:
                    try:
                        if "cost" in search:
                            search['cost'].update({'$lte': int(search['cost_max'])})
                        else:
                            search['cost'] = {'$lte': int(search['cost_max'])}
                    except Exception:
                        pass

                    del search['cost_max']

                if 'level_min' in search:
                    try:
                        search['lvl_min'] = {'$gte': int(search['level_min'])}

                    except Exception:
                        pass

                    del search['level_min']

                if 'level_max' in search:
                    try:
                        if "lvl_min" in search:
                            search['lvl_min'].update({'$lte': int(search['level_max'])})
                        else:
                            search['lvl_min'] = {'$lte': int(search['level_max'])}
                    except Exception:
                        pass

                    del search['level_max']

                if 'race' in search:
                    try:
                        info = search['race'].split(':')
                        info[0], info[1] = int(info[0]), int(info[1])

                        if not -1 in info:
                            search.update({
                            'race': info[1],
                            'faction': info[0]
                            })
                        else:
                            raise Exception

                    except Exception:
                        del search['race']

                if 'class' in search:
                    try:
                        class_id = int(search['class'])
                        if not class_id:
                            raise Exception
                        search['class'] = class_id

                    except Exception:
                        del search['class']

            if 't' in params:
                prefix = params['t']
                for key in keys:
                    if key in params:
                        fields.update({'param_' + prefix + '_' + key: params[key]})

            return search

        def getSortParams(params):
            if 's' in params:
                if 'o' in params and params['o'] in ['-1', '1']:
                    order = int(params['o'])
                else:
                    order = 1

                if params['s'] in ['type', 'name', 'lvl_min', 'author', 'cost', 'date']:
                    if params['s'] == 'date':
                        prm = 'create_time'
                    else:
                        prm = params['s']

                    return {prm: order}

            return {}

        if not self.isAjax():
            page_sharp = ''

            if 'page_type' in params and params['page_type'] in ['items', 'spells', 'artworks']:
                page_sharp = '#!tab-' + params['page_type']

            params['__page__'] = '/u/shop/' + page_sharp
            return self.httpRedirect(params)

        fields = {'stat_names': self.balance.stats_name}

        if self.cur_player:
            already_items = self.getPlayerBuyedItems(self.cur_player['login_id'])
            inventory_count = self.model.items.getInventoryCount(self.cur_player['login_id'])
        else:
            already_items = []
            inventory_count = 0

        _search = getSearchParams(params)

        search = {
            'items': {},
            'spells': {},
            'artworks': {}
        }

        sort = getSortParams(params)

        if 't' in params:
            if params['t'] == 'item':
                search['items'] = _search
            elif params['t'] == 'artwork':
                search['artworks'] = _search
            elif params['t'] == 'spell':
                search['spells'] = _search

            fields.update({'is_' + params['t'] + '_filter': True})

        #print ">>>>> PARAMS <<<<<<"
        #print params

        default_params = {
            's': 'name',
            'o': 1,
            'pi': 1,
            'ps': 1,
            'pa': 1
        }

        for param_name in default_params:
            if param_name in params:
                new_param = params[param_name]
                if param_name != 's':
                    new_param = int(new_param)
                    if param_name == 'o':
                        new_param *= -1
            else:
                new_param = default_params[param_name]

            fields.update({'param_' + param_name: new_param})

        items_on_page = 20
        spells_on_page = 20
        artworks_on_page = 15

        fields.update(self.getPaginatorData(items_on_page, spells_on_page, artworks_on_page, search))

        view = 0
        if 'view' in params:
            if params['view'] == 'tiled':
                view = 1

        fields.update({'view': view})

        if "view" in params and int(params["view"]) == 1:
            templatePart = "list"
        else:
            templatePart = "table"
        template = "shop_items_" + templatePart

        if 'page_type' in params:

            if params['page_type'] == 'new':
                template = "shop_news_list"
                fields.update({
                    'new_things': self.getNewThings()
                })

            elif params['page_type'] == 'items':
                template = "shop_items_" + templatePart
                fields.update({
                    'inventory_count': inventory_count,
                    'players_items': self.getPlayersItems(
                        params,
                        items_on_page,
                        search['items'],
                        sort,
                        total_pages=fields['item_pages']
                    ),
                    'display_items_pages': getDisplayPages(int(fields['param_pi']), fields['item_pages'], 10)
                })

            elif params['page_type'] == 'spells':
                template = "shop_spells_" + templatePart
                fields.update({
                    'spells': self.getSpells(
                        params,
                        spells_on_page,
                        search['spells'],
                        sort,
                        total_pages=fields['spell_pages']
                    ),
                    'display_spells_pages': getDisplayPages(int(fields['param_ps']), fields['spell_pages'], 10)
                })

            elif params['page_type'] == 'artworks':
                template = "shop_artworks_list"
                fields.update({
                    'artworks': self.getArtworks(
                        params,
                        artworks_on_page,
                        search['artworks'],
                        total_pages=fields['artwork_pages']
                    ),
                    'display_artworks_pages': getDisplayPages(int(fields['param_pa']), fields['artwork_pages'], 10)
                })

            elif params['page_type'] == 'trivia':
                template = "shop_trivias_list"
                fields.update({
                    'shop_items': self.getTriviaItems(already_items)
                })

            logged = self.sbuilder.playerLogged()

            if logged:
                fields.update({'login': True})

            htmlField = ({"html": basic.defaultController._printTemplate(self, template, fields.copy())})

            fields.update({"html": htmlField})

            fields = json.dumps(fields, sort_keys=True, indent=4, default=json_util.default)

        else:
            fields = False

        return fields


    def getNewThings(self, params=False):
        items_on_page = 16
        artworks_on_page = 3

        last_items = self.getPlayersItems({}, items_on_page, sort={'create_time': -1})
        last_artworks = self.getArtworks({}, artworks_on_page)

        return {
            'ni': last_items,
            'na': last_artworks
        }


    def getPlayersItems(self, params, items_on_page=20, search={}, sort={}, total_pages=0):
        if self.cur_player:
            str_class = str(self.cur_player['login_class'])
        else:
            str_class = False

        page = 1

        if 'pi' in params:
            try:
                page = int(params['pi'])
            except Exception:
                pass

        if page > total_pages:
            page = 1

        players_items = self.model.items.getAllSellingCraftedItems(limit=items_on_page, skip=(page - 1) * items_on_page,
                                                                   query=search, sort_query=sort)

        authors_ids = Set()
        items_ids = Set()

        for item in players_items:
            authors_ids.add(item['author'])
            items_ids.add(item['_id'])

        players_names = self.model.players.getPlayersList(authors_ids, ['_id', 'name'])
        item_likes = self.getLikesDict(items_ids)

        for item in players_items:

            if item['type'] == 1 and str_class:
                if not item['view'] in self.sbuilder.balance.available_weapons[str_class]:
                    item['cant_use'] = True

            for player in players_names:
                if player['_id'] == item['author']:
                    item['author_name'] = player['name']
                    break

            item['img'] = '/' + item['img'] + '_fit.png'

            item.update(prettyItemBonus(item, self.balance.stats_name))
            if "stat_parsed" in item:
                item.update({"bonus_parsed": json.dumps(item['stat_parsed'])})

            if "img" in item:
                item.update({"share_img": item["img"][3:]})

            item.update(self.getLike(item_likes, item['_id']))
            item.update({
            'create_date_f': getReadbleTime(item['create_time'])
            })

        return players_items


    def getSpells(self, params, spells_on_page=20, search={}, sort={}, total_pages=0):
        page = 1
        if 'ps' in params:
            try:
                page = int(params['ps'])
            except Exception:
                pass

        if page > total_pages:
            page = 1

        spells = self.model.spells.getAllSellingCraftedPatterns(limit=spells_on_page, skip=(page - 1) * spells_on_page,
                                                                query=search, sort_query=sort)

        if self.cur_player:
            _spells = self.model.spells.getPlayerSpells(self.cur_player['login_id'])
            player_spells = Set()
            for _spell in _spells:
                player_spells.add(_spell['name'])

        authors_ids = Set()
        spells_ids = Set()

        for spell in spells:
            authors_ids.add(spell['author'])
            spells_ids.add(spell['_id'])

        players_names = self.model.players.getPlayersList(authors_ids, ['_id', 'name'])
        spell_likes = self.getLikesDict(spells_ids)

        for spell in spells:
            spell['already_have'] = self.cur_player and spell['name'] in player_spells

            for player in players_names:
                if player['_id'] == spell['author']:
                    spell['author_name'] = player['name']

            spell['img'] += '_fit.png'
            if "spell_actions" in spell:
                for action in spell["spell_actions"]:

                    if action["effect"].upper() in self.sbuilder.balance.stats_name:
                        stat = action["effect"].upper()
                    else:
                        stat = action["effect"].lower()

                    action.update({
                    "stat_name": self.sbuilder.balance.stats_name[stat]
                    })

            spell.update({
            "share_img": spell["img"][3:],
            })

            spell.update(self.getLike(spell_likes, spell['_id']))
            spell.update({
            'create_date_f': getReadbleTime(spell['create_time'])
            })

        return spells


    def getArtworks(self, params, artworks_on_page=20, search={}, total_pages=0):
        page = 1
        if 'pa' in params:
            try:
                page = int(params['pa'])
            except Exception:
                pass

        if page > total_pages:
            page = 1

        verified = True
        if self.cur_player and 'login_admin' in self.cur_player and self.cur_player['login_admin']:
            verified = 'nm'

        artworks = self.model.misc.getAllArtworks(
            limit=artworks_on_page,
            skip=(page - 1) * artworks_on_page,
            approved=True,
            search=search,
            sort_query={'approve.time': -1},
            verified=verified
        )

        items_ids = Set()
        for artwork in artworks:
            items_ids.add(artwork['_id'])

        item_likes = self.getLikesDict(items_ids)

        for artwork in artworks:
            artwork.update(self.getLike(item_likes, artwork['_id']))
            artwork.update({
            'create_date_f': getReadbleTime(artwork['create_time'])
            })

        return miscController.formatArtworks(self, artworks)


    def getTriviaItems(self, already_items):
        buff_shop_items = self.model.items.getAllNPItems()
        shop_items = []

        item_types = [
            {'name': "mounts", "title": "Mounts", "code": 101, 'shop_items': []},
            {'name': "estate", "title": "Estate", "code": 102, 'shop_items': []},
            {'name': "pets", "title": "Pets", "code": 103, 'shop_items': []},
            {'name': "titles", "title": "Titles", "code": 105, 'shop_items': []}
        ]

        for shop_item in buff_shop_items:
            if self.cur_player:
                if not 'not_allowed' in shop_item:
                    for already_item in already_items:
                        if 'item_UID' in already_item and shop_item['item_UID'] == already_item['item_UID'] and shop_item[
                            'type'] == already_item['type']:
                            shop_item.update({'have_it': True})
                            break

                    if not 'have_it' in shop_item:
                        shop_item['can_buy'] = shop_item['cost'] <= self.cur_player['login_resources']['gold']
                        shop_items.append(shop_item)
            else:
                shop_items.append(shop_item)

            for item_type in item_types:
                if item_type['code'] == shop_item['type']:
                    item_type['shop_items'].append(shop_item)

        return item_types

    # --------------------------------------------------------------------------------------------------
    # Print pages


    def printShopPage(self, fields, params):
        fields.update({self.title: 'Shop'})

        fields.update({'stat_names': self.balance.stats_name})

        if self.cur_player:
            inventory_count = self.model.items.getInventoryCount(self.cur_player['login_id'])
            can_create = self.balance.MIN_LEVEL_TO_CREATE <= self.cur_player['login_lvl']
        else:
            inventory_count = 0
            can_create = False

        search = {
            'items': {},
            'spells': {},
            'artworks': {}
        }

        if not 'pi' in params:
            fields.update({'param_pi': 1})

        if not 'ps' in params:
            fields.update({'param_ps': 1})

        if not 'pa' in params:
            fields.update({'param_pa': 1})

        items_on_page = 20
        spells_on_page = 20
        artworks_on_page = 15

        fields.update(self.getPaginatorData(items_on_page, spells_on_page, artworks_on_page, search))

        fields.update({
            'inventory_count': inventory_count,
            'can_create': can_create,
            'categories': self.balance.categories,
            'min_lvl_to_create': self.balance.MIN_LEVEL_TO_CREATE
        })

        return basic.defaultController._printTemplate(self, 'shop', fields)


    def printPromoPage(self, fields, params):
        return basic.defaultController._printTemplate(self, 'promo', fields)


    def printShopDisabled(self, fields, params):
        return basic.defaultController._printTemplate(self, 'disabled', fields)


data = {
    'class': shopController,
    'type': ['u'],
    'urls': ['shop', 'promo']
}