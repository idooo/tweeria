# -*- coding: UTF-8 -*-


import basic
import tweepy
import re
import json
import math
from sets import Set
from time import time, localtime
from guild import guildsController
from random import randint, sample
import memcache_controller
from functions import getMessages, prettyItemBonus, getRelativeDate, getDisplayPages
from misc import miscController

import cherrypy


class playerController(basic.defaultController):
    DIR = './players/'
    RE_ITEMS_UIDS = re.compile('^(\d)\#(.*)')

    query_result = False

    def __init__(self):
        basic.defaultController.__init__(self)
        self._getStaticAchvs()
        self.cache = memcache_controller.cacheController()

    @basic.printpage
    def printPage(self, page, params):
        return {
            'top': self.printTopList,
            'registration': self.redirectToTwitter,
            'new': self.printCreatingPlayerPage,
            'spellbook': self.printSpellbook,
            'inv': self.printInviteCenter,
            'authors': self.printTopAuthors,
            'settings': self.printSettings,
            '__default__': {
                'method': self.printPlayerPage,
                'params': {'username': page}
            }
        }

    @basic.methods
    def methods(self, params={}):
        return {
            'type_of_form': {
                'add_user': self.finishCreatingNewPlayer,
                'equip_item': self.equipItem,
                'sell_item': self.sellItem,
                'change_title': self.changeSettings,
                'change_player_settings': self.changeSettings,
                'change_pvp': self.changeSettings,
                'change_artwork': self.changeSettings,
                'move_spell_to_book': self.setSpellActive,
                'move_spell_from_book': self.setSpellInactive,
                'change_post_setting': self.changePostToTwitter,
                'send_mention_invite': self.sendMentionInvite,
                'get_friends': self.getFriends,
                'reset_hero': self.resetHero
            }
        }

    # --------------------------------------------------------------------------------------------------
    # Misc

    def _getStaticAchvs(self):
        self.static = self.model.players.getAchvStaticForPrint()

    def isPlayerAlreadyRegistered(self, user_id):
        player = self.model.players.getPlayer(user_id)
        return player

    def authorizePlayer(self, player, to_invite_page=False):
        self.sbuilder.createSession(int(player['user_id']))

        if to_invite_page:
            return self.sbuilder.redirect(self.core.HOST + 'inv', 'Redirecting ... ')
        else:
            backlink = self.sbuilder.getOneCookie('login_back_url')
            if backlink:
                return self.sbuilder.redirect(self.core.HOST + backlink, 'Redirecting ... ')
            else:
                return self.sbuilder.redirect(self.core.HOST + player['name'], 'Redirecting to your profile')

    def redirectToTwitter(self, fields=None, params=None):

        if 'backlink' in params:
            self.sbuilder.setCookie({'login_back_url': params['backlink']}, 30)

        self.sbuilder.setCookie({'just_login': True}, 30)

        # реферальная кука
        username = False
        if len(params) > 1:
            for param in params:
                if not param in ['__page__', '__query__', 'backlink', 'guild']:
                    self.sbuilder.setCookie({'referal_name': param}, 300)
                    username = param
                    if 'guild' in params and username:
                        info = self.model.players.getPlayerRawByName(username, {'_guild_name': 1})
                        if info and info['_guild_name']:
                            self.sbuilder.setCookie({'guild_invite': info['_guild_name']}, 300)
                    break

        auth = tweepy.OAuthHandler(self.core.p_key, self.core.p_secret)
        url = auth.get_authorization_url(True)
        return self.sbuilder.redirect(url)

    def getPlayersGuild(self, user_id):
        return self.model.guilds.getPlayersGuild(user_id)

    # --------------------------------------------------------------------------------------------------
    # Page methods

    def sendMentionInvite(self, params):

        if self.cur_player and 'name' in params and params['name']:
            if params['name'][0] == '@':
                params['name'] = params['name'][1:]

            text = '@' + params['name'] + ' join my journey in Tweeria http://tweeria.com/invite?' + self.cur_player[
                'login_name'] + ' #rpg'
            result = self.model.players.postMentionInvite(self.cur_player['login_id'], text)
        else:
            result = False

        cherrypy.response.headers['Content-Type'] = "application/json"
        return json.dumps({"invited": result})

    # -------------

    def equipItem(self, params):
        if 'uid' in params:
            uid = params['uid']

            if 'old_id' in params:
                old_id = params['old_id']
            else:
                old_id = '0'

            returnHash = {
                "equipted": self.model.items.equipItem(
                    uid, self.cur_player['login_id'],
                    self.cur_player['login_class'],
                    old_id,
                    self.cur_player['login_lvl']
                ),
                "stats": self.model.players.recalculateStats(self.cur_player['login_id'])
            }
        else:
            returnHash = {'equipted': False, 'stats': {}}

        cherrypy.response.headers['Content-Type'] = "application/json"
        return json.dumps(returnHash)

    def sellItem(self, params):

        rules = {
        'uid': {'not_null': 1},
        }

        returnHash = {'sold': False}
        status = self.checkParams(params, rules)

        if status['status']:
            created_by_player = int(params['created_by_player']) == 1
            cost = self.model.items.sellItem(self.cur_player['login_id'], params['uid'], to_pool=created_by_player)

            if created_by_player:
                cost = int(float(cost) / 2)

            returnHash = {
                "sold": True,
                "goldgained": cost,
                "stats": self.model.players.recalculateStats(self.cur_player['login_id'])
            }

        cherrypy.response.headers['Content-Type'] = "application/json"
        return json.dumps(returnHash)

    def changePostToTwitter(self, param):
        checked = 'post_to_twitter' in param and param['post_to_twitter'] == '1'
        self.model.players.updatePlayerData(self.cur_player['login_id'], {'post_to_twitter': checked})
        self.httpRedirect(param)

    def changeSettings(self, param):

        # метод для смены артворка/титула
        def changeThings(type_name, param_name, param, field_name):
            availiable_things = self.mongo.getu('players',
                                                {'_id': self.cur_player['login_id'], type_name: {'$exists': 1}},
                                                {'_id': 1, type_name: 1})
            if availiable_things:
                things = []
                for thing in availiable_things[0][type_name]:

                    if thing[field_name] == int(param[param_name]):
                        thing.update({'current': True})
                    else:
                        thing.update({'current': False})

                    things.append(thing)

                self.mongo.update('players', {'_id': self.cur_player['login_id']}, {type_name: things})

        if 'pvp_mode' in param:
            pvp = int(param['pvp_mode'])
            if not pvp in [0, 1]:
                pvp = 0

            param.update({'success': True})
            self.mongo.update('players', {'user_id': self.cur_player['login_user_id']}, {'pvp': pvp}, True)

        if 'change_title' in param:
            changeThings('titles', 'change_title', param, 'item_UID')

        if 'change_artwork' in param:
            self.model.misc.changePlayerArtworks(self.cur_player['login_id'], param['change_artwork'])

        self.sbuilder.httpRedirect(param['__page__'])

    def printCreatingPlayerPage(self, fields, param):

        fields.update({self.title: 'Choose your path'})

        def checkInfoActuality(old_data, new_data, auth):
            record = {}

            if new_data.screen_name != old_data['name']:
                record.update({'name': new_data.screen_name})

            if new_data.profile_image_url != old_data['avatar']:
                record.update({'img': new_data.profile_image_url})

            if auth.access_token.key != old_data['token1'] or auth.access_token.secret != old_data['token2']:
                record.update({
                    'token1': auth.access_token.key,
                    'token2': auth.access_token.secret
                })

            if not 'utc_offset' in old_data or new_data.utc_offset != old_data['utc_offset']:
                record.update({'utc_offset': new_data.utc_offset})

            return record

        def getLeadership(following, followers):

            if following == 0:
                ratio = 0
            else:
                ratio = int(float(followers) / following)

            lead = 0
            for record in self.balance.LEAD:
                if record['min'] <= ratio and record['min_fol'] <= followers:
                    lead = record['lead']

            return lead

        if not 'oauth_token' in param and not 'oauth_verifier' in param:
            return self.sbuilder.redirect('../')

        consumer_key = self.core.p_key
        consumer_secret = self.core.p_secret

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

        auth.set_request_token(param['oauth_token'], param['oauth_verifier'])

        try:
            auth.get_access_token(param['oauth_verifier'])
        except tweepy.TweepError:
            return self.sbuilder.throwWebError(2001)

        api = tweepy.API(auth)
        user = api.me()

        if 'invites' in self.core.debug and self.core.debug['invites']:
            allowed = self.model.misc.getPlayerInvite(user.screen_name)
            if not allowed:
                return self.sbuilder.throwWebError(2001)

        #login = self.sbuilder.getLoginCookie()

        player = self.isPlayerAlreadyRegistered(user.id)
        if player:
            diff_data = checkInfoActuality(player, user, auth)
            if diff_data:
                self.model.players.updatePlayerData(player['_id'], diff_data)

            return self.authorizePlayer({'name': user.screen_name, 'user_id': int(user.id)})

        if user.utc_offset:
            utc_offset = user.utc_offset
        else:
            utc_offset = 0

        fields.update({
            'id': user.id,
            'login_name': user.screen_name,
            'avatar': user.profile_image_url,
            'access_key': auth.access_token.key,
            'access_secret': auth.access_token.secret,
            'step': 1,
            'utc': utc_offset,
            'rto': getLeadership(user.friends_count, user.followers_count)
        })

        buff = self.sbuilder.balance.classes
        classes = []
        for key in buff:
            record = {
            'id': key,
            'name': buff[key]
            }
            classes.append(record)

        fields.update({'classes': classes})

        # check referal

        referal_name = self.sbuilder.getOneCookie('referal_name')
        if referal_name:
            fields.update({'referal': referal_name})

        guild_invite = self.sbuilder.getOneCookie('guild_invite')
        if guild_invite:
            fields.update({'guild_invite': guild_invite})

        return self.sbuilder.loadTemplate(self.DIR + 'registration.jinja2', fields)

    def finishCreatingNewPlayer(self, param):

        def getReferalBonus(referal_name, user_id, user_name):
            self.model.players.giveBonusToReferal(referal_name, user_id, user_name)

        if self.isPlayerAlreadyRegistered(int(param['id'])):
            return self.authorizePlayer({'name': param['login_name'], 'user_id': int(param['id'])})

        rules = {
            'token1': {},
            'token2': {},
            'login_name': {'not_null': True},
            'avatar': {},
            'id': {'gt': 1},
            'sex': {'gte': 0, 'lte': 1},
            'class': {'gte': 1, 'lte': len(self.balance.classes)},
            'utc': {'int': 1}
        }

        status = self.checkParams(param, rules)

        if 'race' in param:
            buff = param['race'].split(':')

            try:
                faction = int(buff[0])
                race = int(buff[1])
            except Exception:
                status = False
        else:
            status = False

        if status:

            # чтобы в параметры фигню не передали и 500 не упала

            try:
                _class = int(param['class'])
                _user_id = int(param['id'])
                _sex = int(param['sex'])
                _utc = int(param['utc'])
                _rto = int(param['rto'])
            except Exception:
                return self.redirectToTwitter()

            new_player = self.model.playerInstance({
                'class': _class,
                'user_id': _user_id,
                'avatar': param['avatar'],
                'name': param['login_name'],
                'token1': param['token1'],
                'token2': param['token2'],
                'sex': _sex,
                'post_to_twitter': 'post_to_twitter' in param,
                'race': race,
                'utc_offset': _utc,
                'faction': faction,
                'last_login': time(),
                'position': self.balance.started_locations[faction]
            })

            stats = {}
            for stat in self.balance.classes_stats[param['class']]:
                value = self.balance.classes_stats[param['class']][stat]
                stats.update({stat: {'current': value, 'max': value, 'max_dirty': value}})

            # бонус по реферальной программе
            if 'referal' in param:
                for type_name in stats['HP']:
                    stats['HP'][type_name] += 5
                    stats['luck'][type_name] += 1

            # присоединятся к гильдии?
            join_guild = ''
            if 'guild_invite' in param and param['guild_invite'].strip():
                join_guild = param['guild_invite'].strip()

            if 'rto' in param:
                rto = _rto
                if rto > 10:
                    rto = 10

                stats.update({
                    "lead": {
                        "current": rto,
                        "max": rto,
                        "max_dirty": rto
                    }
                })

            new_player.data.update({'stat': stats})

            player_id = self.model.players.addNewPlayer(
                new_player.data.copy(),
                self.balance.starter_equip[param['class']], # стартовые вещи (UIDs)
                join_guild
            )

            if self.model.players.isBetaPlayer(_user_id):
                player_info = self.model.players.getPlayerRaw(_user_id, {'_id': 1, 'user_id': 1, 'name': 1})
                self.model.items.unpackBetaItems(player_info)
                self.model.spells.unpackBetaSpells(player_info)
                self.model.misc.unpackBetaArtworks(player_info)

            if 'referal' in param:
                getReferalBonus(param['referal'], int(param['id']), param['login_name'])

            try:
                tweet_text = self.balance.REGISTRATION_TWEET + ' http://tweeria.com/invite?' + param['login_name']
                self.model.players.postMentionInvite(player_id, tweet_text)
            except Exception:
                pass

            del new_player

            return self.authorizePlayer({'name': param['login_name'], 'user_id': param['id']}, to_invite_page=True)

        else:
            return self.redirectToTwitter()

    def setSpellActive(self, params):

        if 'id' in params:
            id = params['id']
            builtin = False
        else:
            id = params['uid']
            builtin = True

        active_spells = self.model.spells.getCountActiveSpells(self.cur_player['login_id'])

        if active_spells < self.sbuilder.balance.MAX_ACTIVE_SPELLS:
            result = self.model.spells.moveToBook(self.cur_player['login_id'], id, self.cur_player['login_lvl'],
                                                  builtin)
            changed = result
        else:
            changed = False

        returnHash = {"changed": changed}
        return json.dumps(returnHash)

    def setSpellInactive(self, params):
        if 'id' in params:
            id = params['id']
            builtin = False
        else:
            id = params['uid']
            builtin = True

        self.model.spells.moveFromBook(self.cur_player['login_id'], id, builtin)

        return json.dumps({"changed": True})

    def getFriends(self, params):
        max_players_on_page = 25

        skip = 0
        if 'skip' in params:
            try:
                skip = int(params['skip'])
            except Exception:
                pass

        raw_friends = self.model.players.getFriends(self.cur_player['login_id'])

        friends = []
        count = 0
        if raw_friends:
            for friend in raw_friends:
                if count >= skip and count < (skip + max_players_on_page):
                    friends.append({
                        'name': friend.screen_name,
                        'avatar': friend.profile_image_url,
                        'counte': count
                    })

                count += 1

        cherrypy.response.headers['Content-Type'] = "application/json"
        return json.dumps(friends)

    def resetHero(self, params):

        if not self.cur_player:
            return self.sbuilder.redirect('http://tweeria.com')

        try:
            class_id = int(params['class'])
            faction_id, race_id = map(int, params['race'].split(':'))
        except Exception:
            return False

        player = self.model.players.getPlayerBy_ID(self.cur_player['login_id'], {
            'lvl': 1,
            'resources': 1,
            'exp': 1,
            'stat.lead.current': 1
        })

        record = {
            # lvl restrictions
            'lvl': int(float(player['lvl'] / 2)),
            'exp': 0,

            'race': race_id,
            'class': class_id,
            'faction': faction_id,
            'artworks': {},
            'position': self.balance.started_locations[faction_id]
        }

        if record['lvl'] <= 0:
            record['lvl'] = 1

        stats = {}
        for stat in self.balance.classes_stats[str(record['class'])]:
            value = self.balance.classes_stats[str(record['class'])][stat] * record['lvl']
            stats.update({stat: {'current': value, 'max': value, 'max_dirty': value}})

        lead = player['stat']['lead']['current']
        stats['lead'].update({'current': lead, 'max': lead, 'max_dirty': lead})

        # resource restrictions
        for res_name in player['resources']:
            player['resources'][res_name] = int(float(player['resources'][res_name]) / 2)

        record.update({
            'resources': player['resources'],
            'stat': stats
        })

        self.model.players.resetPlayerData(self.cur_player['login_id'], record)

        self.httpRedirect(params, '?success=reset')

    # --------------------------------------------------------------------------------------------------
    # Print pages

    def printPlayerPage(self, fields, params):

        def getPlayerItems(player, fields):
            all_items = self.model.players.getPlayerHaveItems(player['_id'])
            items = {}
            wealth_items = []
            inventory = []
            ring1_exists = False

            if self.cur_player:
                str_class = str(self.cur_player['login_class'])
            else:
                str_class = False

            authors_ids = Set()
            for item in all_items:
                if "author" in item:
                    authors_ids.add(item['author'])

            players_names = self.model.players.getPlayersList(authors_ids, ['_id', 'name'])
            for item in all_items:
                item['type'] = int(item['type'])

                # после type 100 начинаются неигровые предметы
                # которые учитывать не нужно

                if item['type'] < 100:

                    if 'author' in item:
                        item.update({
                        'img': item['img'] + '_thumb.png',
                        'big_img': item['img'] + '_fit.png'
                        })
                    else:
                        item['img'] = '/data/items/' + item['img'] + '.jpg'

                    if item['equipped'] and item['type'] == 6:
                        if ring1_exists:
                            item['type'] = 66
                        else:
                            ring1_exists = True

                    if 'UID' in item and 'pooled_date' in item and item['img'][:2] != './':
                        item['img'] = '/data/items/' + item['img'][:-10] + '.jpg'

                    if 'UID' in item and not 'author' in item:
                        item_uid_str = str(int(item['UID']))
                        created_by_player = False
                    else:
                        item_uid_str = str(item['_id'])
                        item['color'] = 1
                        created_by_player = True

                    can_use_item = '0'
                    if self.cur_player and 'lvl_min' in item and int(item['lvl_min']) <= int(
                            self.cur_player['login_lvl']):
                        can_use_item = '1'

                    item.update(prettyItemBonus(item, self.balance.stats_name))

                    record = item
                    record.update({
                        'link': '/obj/1/' + item_uid_str + '/' + can_use_item,
                        'id': str(item['_id']),
                        'created_by_player': created_by_player,
                    })

                    if item['type'] == 1 and str_class:
                        if not item['view'] in self.sbuilder.balance.available_weapons[str_class]:
                            item['cant_use'] = True

                    if item['type'] == 1:
                        item['str_type'] = item['view']
                    else:
                        item['str_type'] = self.sbuilder.balance.item_types[item['type'] % 60]

                    for player in players_names:
                        if "author" in item and player['_id'] == item['author']:
                            item['author_name'] = player['name']

                    if item['equipped']:
                        items.update({'slot' + str(item['type']): record})

                    else:
                        inventory.append(record)

                # shop items
                else:
                    wealth_items.append(item)

            fields.update({
                'items': items,
                'inventory': inventory,
                'wealth': wealth_items
            })

        def getCurrentTitle(player, fields):
            for title in player['titles']:
                if 'current' in title and title['current']:
                    fields['player'].update({'current_title': title['name']})
                    fields['player'].update({'name_with_title': re.sub('\{player\}', player['name'], title['desc'])})

                    return True

            fields['player'].update({'name_with_title': fields['player']['name']})
            return False

        def getEventsByPlayer(player, fields):
            if self.cur_player and self.cur_player['login_utc_offset']:
                utc_offset = self.cur_player['login_utc_offset']
            else:
                utc_offset = self.core.server_utc_offset

            events = self.model.events.getEvents(
                player_id=player['_id'],
                query={'upcoming': 1},
                fields={
                    'start_date': 1,
                    'guild_side_name': 1,
                    'sides_names': 1,
                    'target_name': 1,
                    '_id': 1,
                    'finish_date': 1,
                    'type': 1
                }
            )

            current_time = time()
            for event in events:

                event.update({'start_date_f': getRelativeDate(int(event['start_date']) + utc_offset)})

                if event['start_date'] <= current_time <= event['finish_date']:
                    fields.update({
                    'in_progress_event': event
                    })

            fields.update({'events': events})

        def getPlayerStats(player, fields):
            static = self.model.players.getStatisticStaticForPrint()
            buff_players_stats = self.model.players.getPlayerStatistics(player['user_id'])['stats']
            player_stats = []

            group = []
            group_name = ''

            for stat_static in static:
                if stat_static['type'] == 'none':
                    if group_name:
                        player_stats.append({'name': group_name, 'stats': group})

                    group_name = stat_static['text']
                    group = []
                else:
                    if stat_static['visibility']:
                        group.append({
                            'name': stat_static['text'],
                            'value': buff_players_stats[stat_static['name']]
                        })

            fields.update({'statistics': player_stats})

        def getPlayerAchvs(player, fields):

            buff_player_achvs = self.model.players.getPlayerAchvs(player['user_id'])['achvs']
            player_achvs = []

            group = []
            group_name = ''

            for achv_static in self.static:
                if achv_static['type'] == 0:
                    if group_name:
                        player_achvs.append({'name': group_name, 'achvs': group})

                    group_name = achv_static['name']
                    group = []
                else:
                    if achv_static['visibility']:
                        group.append({
                            'name': achv_static['name'],
                            'complete': buff_player_achvs[str(achv_static['UID'])],
                            'UID': achv_static['UID'],
                            'text': achv_static['text'],
                            'img': achv_static['img']
                        })

            player_achvs.append({'name': group_name, 'achvs': group})
            fields.update({'achvs': player_achvs})

        def getPlayerSpells(player, fields):
            spellbook = self.model.spells.getSpellBook(player['_id'])

            spells_ids = []
            for item in spellbook['spells']:
                if 'spell_UID' in item:
                    spells_ids.append(item['spell_UID'])
                else:
                    spells_ids.append(item['spell_id'])

            spells = self.model.spells.getSpellsByIds(spells_ids)

            for spell in spells:
                if 'author' in spell:
                    spell['img'] += '_thumb.png'
                else:
                    spell['img'] = '/' + self.core.IMAGE_SPELL_FOLDER + spell['img'] + '.jpg'

            fields.update({'spells': spells})

        def getArtwork(player, fields):
            # Получаем artwork
            is_artwork = False

            artwork_path = ''
            artwork_id = 0

            if 'artworks' in player:
                for artwork in player['artworks']:
                    if 'current' in artwork and artwork['current']:
                        if 'UID' in artwork:
                            artwork_path = self.core.ARTWORK_PATH + artwork['img'] + '.jpg'
                        else:
                            if artwork['img'] == './data/artwork_delete.jpg':
                                artwork_path = artwork['img']
                            else:
                                artwork_path = artwork['img'] + '_fit.png'

                        is_artwork = True
                        if '_id' in artwork:
                            artwork_id = artwork['_id']
                            break
                        else:
                            artwork_id = 'none'

            if not is_artwork:
                key = str(player['faction']) + str(player['race']) + str(player['class'])
                if key in self.balance.default_artworks:
                    artwork_path = self.core.ARTWORK_PATH + self.balance.default_artworks[key]['src'] + '.jpg'
                    artwork_id = self.balance.default_artworks[key]['_id']
                else:
                    fields.update({'default_artwork': True})

            fields['player'].update({
                'artwork': artwork_path,
                'artwork_id': artwork_id
            })

        def getPlayerBuffs(player, fields):

            fields.update({'stat_names': self.balance.stats_name})

            inactive_count = 0
            for buff in player['buffs']:
                buff['type'] = 'buff'

                buff['minutes'] = int(float(buff['start_time'] + buff['length'] - time()) / 60)

                if buff['minutes'] > 0:

                    if 'buff_uid' in buff:
                        buff['buff_img'] = '/data/spells/' + buff['buff_img'] + '.jpg'

                    for action_name in buff['actions']:
                        if action_name in player['stat']:
                            player['stat'][action_name]['current'] += buff['actions'][action_name]
                            is_buff = buff['actions'][action_name] > 0
                            buff['actions'][action_name] = str(buff['actions'][action_name])
                            if is_buff:
                                buff['actions'][action_name] = '+' + buff['actions'][action_name]
                            else:
                                buff['type'] = 'debuff'

                            player['stat'][action_name]['change'] = is_buff
                else:
                    inactive_count += 1

            if inactive_count != 0 and inactive_count == len(fields['player']['buffs']):
                fields['player']['buffs'] = []

        def getNearPlayers(player, fields):

            def miniFormatPlayers(players):
                for player in players:
                    player.update({
                        'class_name': self.balance.classes[str(player['class'])],
                        'race_name': self.balance.races[player['faction']][player['race']],
                    })
                return players

            rad = 6

            players_count = self.model.players.getNearPlayersCount(
                player['position']['x'],
                player['position']['y'],
                rad,
                player['name']
            )

            raw_records = self.model.players.getNearEnemies(rad, player)
            enemies = miniFormatPlayers(sample(raw_records, min(5, len(raw_records))))

            raw_records = self.model.players.getNearFriends(rad, player)
            friends = miniFormatPlayers(sample(raw_records, min(5, len(raw_records))))

            fields.update({
                'nearby_players': {
                    'count': players_count,
                    'enemies': enemies,
                    'friends': friends
                }
            })

        def getAuthorInfo(player, fields):
            info = self.model.misc.getAuthorLikes(player['_id'], {'likes': 1})

            if not info and 'ugc_enabled' in player and player['ugc_enabled']:
                info = {'likes': 0}

            if info:
                fields.update({'author_info': info})

        player = self.model.players.getPlayer(params['username'], fields='game')

        if not player:
            return self.sbuilder.throwWebError(7001)

        getAuthorInfo(player, fields)

        if 'works' in params:
            fields.update({'player': player})
            return self.printWorksPage(fields, params)

        fields.update({self.title: player['name'] + '\'s profile'})

        lvl_caps = self.model.getLvls()

        cache_need_save = False
        from_cache = False

        if self.cur_player and player['name'] == self.cur_player['login_name']:
            fields.update({'player_self': True})

        if from_cache:
            # fields = dict(loaded['content'].items() + fields.items())
            pass
        else:
            fields.update({'player': player})

            fields['player']['is_sleep'] = not (fields['player']['last_login'] >= time() - self.core.MAX_TIME_TO_SLEEP) 

            # format player's last events messages
            tags = self.model.misc.getTags()
            fields['player']['messages'] = getMessages(fields['player']['messages'], host=self.core.HOST, tags=tags)

            if self.cur_player and 'login_id' in self.cur_player and player and self.cur_player['login_id'] == player['_id']:
                getEventsByPlayer(player, fields)
                getPlayerSpells(player, fields)

            getPlayerBuffs(player, fields)
            getPlayerItems(player, fields)
            getCurrentTitle(player, fields)
            getPlayerStats(player, fields)
            getPlayerAchvs(player, fields)

            if self.cur_player and self.cur_player['login_id'] == player['_id']:
                getNearPlayers(player, fields)

            getPlayerSpells(player, fields)

            if 'pvp' in player and player['pvp'] == 1:
                fields.update({'pvp_mode': 1})

            fields['player'].update({
                'exp_level_cap': '',
                'exp_percent': 0
            })

            if int(player['lvl']) != self.balance.max_lvl:
                lvl_cap = lvl_caps[str(fields['player']['lvl'] + 1)]
                fields['player'].update({
                    'exp_level_cap': str(player['exp']) + ' / ' + str(lvl_cap),
                    'exp_percent': int((float(player['exp']) / float(lvl_cap)) * 100)
                })

            fields['player'].update({
                'HP_percent': int(float(fields['player']['stat']['HP']['current']) / fields['player']['stat']['HP']['max_dirty'] * 100),
                'MP_percent': int(float(fields['player']['stat']['MP']['current']) / fields['player']['stat']['MP']['max_dirty'] * 100)
                }
            )

            # Получаем расу
            fields['player']['race_name'] = self.balance.races[fields['player']['faction']][fields['player']['race']]

            # Получаем название класса
            fields['player']['class_name'] = self.balance.classes[str(fields['player']['class'])]

            # Получаем название пола
            fields['player']['sex_name'] = ['Female', 'Male'][fields['player']['sex']]

            getArtwork(player, fields)

            # получаем гильдию
            guild = self.getPlayersGuild(player['_id'])
            if guild:
                fields.update({'guild': {'name': guild['name'], 'link': guild['link_name']}})

            # Получаем тип урона
            fields['player']['damage_type'] = self.balance.damage_type[str(fields['player']['class'])]

            if self.cur_player:
                inventory_count = self.model.items.getInventoryCount(self.cur_player['login_id'])
            else:
                inventory_count = 0

            fields.update({
                'help': 'help' in params,
                'inventory_count': inventory_count,
                'player_coords': self.core.relativePosition(player['position'])
            })

        if cache_need_save:
            self.cache.cacheSave('!' + player['name'], content=fields)

        return basic.defaultController._printTemplate(self, 'player', fields)

    def printWorksPage(self, fields, params):

        def getLikesDict(items_ids):
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

        def getLike(item_likes, _id):
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

        def formatArtworks(likes, artworks):

            for artwork in artworks:
                artwork.update(getLike(likes, artwork['_id']))

            return miscController.formatArtworks(self, artworks)

        def formatItems(likes, items):
            for item in items:

                item['img'] = '/' + item['img'] + '_fit.png'

                item['author_name'] = player['name']

                item.update(prettyItemBonus(item, self.balance.stats_name))
                if "stat_parsed" in item:
                    item.update({"bonus_parsed": json.dumps(item['stat_parsed'])})

                if "img" in item:
                    item.update({"share_img": item["img"][3:]})

                item.update(getLike(likes, item['_id']))

            return items

        def formatSpells(likes, spells):
            for spell in spells:

                spell['author_name'] = player['name']

                spell['img'] += '_fit.png'
                if "spell_actions" in spell:
                    for action in spell["spell_actions"]:

                        if action["effect"].upper() in self.balance.stats_name:
                            stat = action["effect"].upper()
                        else:
                            stat = action["effect"].lower()

                        action.update({
                        "stat_name": self.balance.stats_name[stat]
                        })

                spell.update(getLike(likes, spell['_id']))

            return spells

        player = fields['player']

        if not ('ugc_enabled' in player and player['ugc_enabled']):
            return self.sbuilder.throwWebError(404)

        fields.update({self.title: player['name'] + '\'s portfolio'})

        artworks = self.model.misc.getActiveArtworksByPlayer(player['_id'])
        items = self.model.items.getActiveItemsByPlayer(player['_id'])
        spells = self.model.spells.getActiveSpellsPattern(player['_id'])

        _ids = Set()
        for thing in artworks + items + spells:
            _ids.add(thing['_id'])

        _likes = getLikesDict(_ids)

        fields.update({
            'items': formatItems(_likes, items),
            'spells': formatSpells(_likes, spells),
            'artworks': formatArtworks(_likes, artworks),
            'stat_names': self.balance.stats_name
        })

        return basic.defaultController._printTemplate(self, 'works', fields)

    def printTopList(self, fields, params):

        fields.update({self.title: 'Top'})

        needed_fields = {'name': 1, 'class': 1, 'race': 1, 'lvl': 1, 'faction': 1, 'pvp_score': 1, 'achv_points': 1,
                         'avatar': 1, '_guild_name': 1}

        no_top = {'lvl': {'$lt': 60},'last_login': {'$gte': time() - self.core.MAX_TIME_TO_SLEEP}} #exclude lvl 60 and sleeping heroes from top rating

        players_by_lvl = self.mongo.getu('players', search=no_top, limit=10, sort={'lvl': -1}, fields=needed_fields)

        for players in [players_by_lvl]:
            for player in players:
                player.update({
                    'class_name': self.balance.classes[str(player['class'])],
                    'race_name': self.balance.races[player['faction']][player['race']],
                })
                player['pvp_score'] = int(player['pvp_score'])
                player['achv_points'] = int(player['achv_points'])
                player['lvl'] = int(player['lvl'])

        top_players_guilds = self.model.guilds.getTopGuildsByPeopleCount(10)

        if self.cur_player:
            guild = self.getPlayersGuild(self.cur_player['login_id'])
            if guild:
                guild = guildsController.formatGuilds(self, [guild])[0]

                fields.update({
                'your_guild': guild
                })

        fields.update({
            'top_by_lvl': players_by_lvl,
            'top_popular_guilds': guildsController.formatGuilds(self, top_players_guilds)
        })

        return basic.defaultController._printTemplate(self, 'top', fields)

    def printTopAuthors(self, fields, params):

        fields.update({self.title: 'Top authors'})

        def getPaginatorData(players_on_page):
            players_count = self.model.misc.getAuthorsCount()

            pages = int(math.ceil(float(players_count) / players_on_page))

            fields.update({
                'total_pages': pages
            })

        def getSortParams():
            if not 'pi' in params:
                fields.update({'param_pi': 1})

            try:
                page_number = int(params['pi'])
            except Exception:
                page_number = 1

            return {
                'page_number': page_number,
                'sort_field': '',
                'sort_order': ''
            }

        authors_on_page = 20

        getPaginatorData(authors_on_page)
        sort_params = getSortParams()

        authors = self.model.misc.getAuthorsLikes(
            authors_on_page,
            skip=(sort_params['page_number'] - 1) * authors_on_page
        )

        author_ids = Set()
        for author in authors:
            author_ids.add(author['author_id'])

        authors_info = self.model.players.getPlayersList2(author_ids, {'name': 1, '_guild_name': 1, 'lvl': 1})
        authors_guilds = {}

        for author in authors_info:
            authors_guilds.update({author['name']: author})

        for author in authors:
            author.update({
                '_guild_name': authors_guilds[author['author_name']]['_guild_name'],
                'lvl': authors_guilds[author['author_name']]['lvl']
            })

        fields.update({
            'authors': authors,
            'display_pages': getDisplayPages(int(fields['param_pi']), fields['total_pages'], 10)
        })

        return basic.defaultController._printTemplate(self, 'all_authors', fields)

    def printSpellbook(self, fields, params):

        fields.update({self.title: 'Spellbook'})

        if not self.cur_player:
            return self.sbuilder.redirect('../')

        fields.update({'stat_names': self.balance.stats_name})

        if 'type_of_form' in params and params['type_of_form'] in ["equip_item", "sell_item", "move_spell_to_book",
                                                                   "move_spell_from_book"]:
            fields.update({"result": self.query_result})
            self.query_result = False
            return self.sbuilder.loadTemplate(self.DIR + 'player-ajax.jinja2', fields)

        spellbook = self.model.spells.getSpellBook(self.cur_player['login_id'])
        available_spells = self.model.spells.getAvailableStandartSpells(self.cur_player['login_lvl'])
        buyed_spells = self.model.spells.getBuyedSpells(self.cur_player['login_id'])

        for spell in available_spells:
            spell['img'] = '/data/spells/' + spell['img'] + '.jpg'

        if buyed_spells:
            available_spells += buyed_spells

        for tmp_spell in available_spells:
            for spell_info in spellbook['spells']:
                if 'UID' in tmp_spell and spell_info['spell_id'] == tmp_spell['UID'] or spell_info['spell_id'] == tmp_spell['_id']:
                    tmp_spell.update({'active': True})

            tmp_spell['can_use'] = tmp_spell['lvl_min'] <= self.cur_player['login_lvl']

        fields.update({'spells': available_spells})

        return basic.defaultController._printTemplate(self, 'spellbook', fields)

    def printInviteCenter(self, fields, params):

        if not self.cur_player:
            return self.sbuilder.redirect('http://tweeria.com')

        #fields.update({'friends': self.getFriends(params)})

        return basic.defaultController._printTemplate(self, 'invite_center', fields)

    def printSettings(self, fields, params):
        if not self.cur_player:
            return self.sbuilder.redirect('http://tweeria.com')

        player_info = self.model.players.getPlayerBy_ID(self.cur_player['login_id'], {
            'pvp': 1,
            'titles': 1,
            'artworks': 1,
            '_id': 1,
            'race': 1,
            'faction': 1,
            'class': 1,
            'sex': 1,
            'post_to_twitter': 1
        })

        # Получаем расу
        player_info.update({
            'race_name': self.balance.races[player_info['faction']][player_info['race']],
            'class_name': self.balance.classes[str(player_info['class'])],
            'sex_name': ['Female', 'Male'][player_info['sex']]
        })

        is_artwork = False
        if 'artworks' in player_info:
            for artwork in player_info['artworks']:
                if 'current' in artwork and artwork['current']:
                    is_artwork = True

        if not is_artwork:
            fields.update({'default_artwork': True})

        fields.update(player_info)
        fields.update(self.balance.classes_and_races)

        return basic.defaultController._printTemplate(self, 'settings', fields)


data = {
    'class': playerController,
    'type': ['default'],
    'urls': ['top', 'registration', 'new', 'spellbook', 'inv', 'settings', 'authors']
}
