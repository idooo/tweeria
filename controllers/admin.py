# -*- coding: UTF-8 -*-

import basic
from functions import prettyItemBonus, formatOutput, getReadbleTime, getRelativeDate, formatTextareaInput
from misc import miscController
from sets import Set
import time
import math
import json
from bson import json_util, ObjectId
from email.mime.text import MIMEText
from subprocess import Popen, PIPE


class sendMailController():
    back_address = "no-reply@tweeria.com"

    def __init__(self):
        pass

    def send(self, to, subject, body):
        msg = MIMEText(body)
        msg["From"] = self.back_address
        msg["To"] = to
        msg["Subject"] = subject
        p = Popen(["/usr/sbin/sendmail", "-t"], stdin=PIPE)
        p.communicate(msg.as_string())


class adminController(basic.defaultController):
    DIR = './admin/'
    sendMail = sendMailController()

    message_result_types = ['messages_OK', 'messages_FAIL', 'callback_OK', 'callback_FAIL']

    @basic.methods
    def methods(self, params={}):
        return {
        'type_of_form': {
        # approve
        'approve_item': self.approveItem,
        'approve_artwork': self.approveArtwork,
        'approve_spell': self.approveSpell,
        'reject_item': self.rejectItem,
        'reject_artwork': self.rejectArtwork,
        'reject_spell': self.rejectSpell,

        # misc
        'featured': self.setFeaturedArtwork,
        'change_tag': self.changeTag,

        # misc
        'admin_change_item': self.changeItem,
        'take_achv': self.takeAchv,
        'get_timeline': self.getTimeline,

        'ban_player': self.banPlayer,
        'change_level': self.changeLevel,
        'ugc_disable': self.disableContentCreating,
        'ugc_enable': self.enableContentCreating,

        # messages
        'save_edit_message': self.messageEdit,
        'add_message': self.messageAdd,
        'delete_message': self.messageDelete,

        # ugc adding rights
        'request_apply': self.applyRequest,
        'request_decline': self.declineRequest,

        'ugc_force_enable': self.enableForceContentCreating,
        'ugc_force_disable': self.disableForceContentCreating,

        # tips
        'add_tip': self.addTip,
        'tip_disable': self.disableTip,
        'tip_enable': self.enableTip,
        'tip_delete': self.deleteTip,

        # tags
        'add_tag': self.addTag,
        'tag_delete': self.deleteTag,

        # user management
        'invite_user': self.inviteUser,
        'reject_invite': self.rejectInvite,
        'promote_to_moderator': self.promoteToModerator,
        'reject_from_moderator': self.rejectFromModerator,

        'artworks_delete': self.removeArtworks,

        }
        }

    @basic.printpage
    def printPage(self, page, params):

        params.update({'admin_zone': True})

        return {
            'index': self.printAdminIndex,
            '': self.printAdminIndex,

            'approvements': self.printApprovementsPage,
            'approve_items': self.printApproveItems,
            'approve_spells': self.printApproveSpells,
            'approve_artworks': self.printApproveArtworks,

            'artists': self.printArtistsPage,
            'moderators': self.printModeratorsPage,
            'people': self.printBadPeoplePage,

            'rejected_items': self.printRejectedItemsPage,
            'rejected_spells': self.printRejectedSpellsPage,
            'rejected_artworks': self.printRejectedArtworksPage,

            'reported_items': self.printReportedItemsPage,
            'reported_spells': self.printReportedSpellsPage,
            'reported_artworks': self.printReportedArtworksPage,

            'deleted': self.printDeleted,

            'invites': self.printUsersInvitePage,

            'messages': self.printMessagesList,
            'get_ajax_messages': self.ajaxGetMessages,
            'add_message': self.printMessageAdd,
            'm': self.printMessageEdit,

            'artwork': self.printFeaturedArtworkSelect,
            'item': self.printItemAdminPage,
            'approve_rules': self.printApproveHelpPage,

            'achvs': self.printAchvTakePage,
            'ban': self.printBanPage,
            'timeline': self.printGetTimelimePage,
            'level': self.printSetLevelPage,

            'tips': self.printTipsPage,
            'artworks_delete': self.printArtworksDelete,

            'tags': self.printTags
        }

    # --------------------------------------------------------------------------------------------------
    # Misc

    def _getPlayersItems(self, items=[], rejected=False, sorting={'create_time': 1}, limit=0, skip=0):

        if items:
            players_items = items
        else:
            players_items = self.model.items.getWaitingItems(rejected=rejected, sorting=sorting, limit=limit, skip=skip)

        authors_ids = Set()
        for item in players_items:
            authors_ids.add(item['author'])

        players_names = self.model.players.getPlayersList(authors_ids, ['_id', 'name'])
        for item in players_items:
            for player in players_names:
                if player['_id'] == item['author']:
                    item['author_name'] = player['name']

            item['img'] = '/' + item['img'] + '_fit.png'

            response = ''
            for stat in ['int', 'str', 'dex', 'luck', 'HP', 'MP', 'DMG', 'DEF']:
                if stat in item['bonus'] and item['bonus'][stat] != 0:
                    response += "<s>""+" + str(int(item['bonus'][stat])) + " " + self.balance.stats_name[stat] + "</s>"

            item['bonus_stats'] = response

            item.update(prettyItemBonus(item, self.balance.stats_name))

        return players_items

    def _getArtworks(self, rejected=False, sorting={'create_time': 1}, limit=0, skip=0):

        artworks = self.model.misc.getAllArtworks(approved=False, rejected=rejected, sort_query=sorting, limit=limit,
                                                  skip=skip)

        authors_ids = Set()
        for item in artworks:
            authors_ids.add(item['author'])

        players_names = self.model.players.getPlayersList(authors_ids, ['_id', 'name'])

        for artwork in artworks:

            artwork['race_name'] = self.balance.races[artwork['faction']][artwork['race']]
            artwork['class_name'] = self.balance.classes[str(artwork['class'])]

            if 'builtin' in artwork:
                artwork['img'] = self.core.ARTWORK_SHOP_PATH + artwork['img'] + '.jpg'
            else:
                for player in players_names:
                    if player['_id'] == artwork['author']:
                        artwork['author_name'] = player['name']

        return artworks

    def _getSpells(self, rejected=False, sorting={'create_time': 1}, limit=0, skip=0):

        spells = self.model.spells.getWaitingSpells(rejected=rejected, sorting=sorting, limit=limit, skip=skip)

        authors_ids = Set()
        for spell in spells:
            authors_ids.add(spell['author'])

        players_names = self.model.players.getPlayersList(authors_ids, ['_id', 'name'])
        for spell in spells:

            for player in players_names:
                if player['_id'] == spell['author']:
                    spell['author_name'] = player['name']

        return spells

    def _isPlayerAdmin(self):
        is_logged = self.cur_player

        if is_logged:
            is_admin = self.model.players.isPlayerAdmin(self.cur_player['login_id'])
        else:
            is_admin = False

        return is_admin

    def _isPlayerModerator(self, tp=-1):

        # tp = types (0 - item, 1 - spell, 2 - artwork)

        is_logged = self.cur_player

        if is_logged:
            is_moderator = self._isPlayerAdmin()
            if not is_moderator:
                is_moderator = self.model.players.isPlayerModerator(self.cur_player['login_id'])

                if tp >= 0:
                    if 'moderator_rights' in is_moderator and is_moderator['moderator_rights'][tp]:
                        pass
                    else:
                        is_moderator = False
        else:
            is_moderator = False

        return is_moderator

    def setFeaturedArtwork(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'set' in params and 'n' in params:
            try:
                n = int(params['n'])
            except Exception:
                n = 0

            self.model.misc.setFeaturedArtwork(params['set'], n)

        self.httpRedirect(params)

    def _getModeratorRights(self):
        return self.model.players.getPlayerBy_ID(self.cur_player['login_id'], {
            'moderator_rights': 1,
        })

    def _qsort(self, list, field='reports'):
        if list == []:
            return []
        else:
            pivot = list[0]
            lesser = self._qsort([x for x in list[1:] if x[field] >= pivot[field]], field)
            greater = self._qsort([x for x in list[1:] if x[field] < pivot[field]], field)
            return lesser + [pivot] + greater

    def removeArtworks(self, params):

        def deleteFromPlayers(artworks_to_delete):

            players = self.model.players.getPlayersRaw({}, {'_id': 1, 'name': 1, 'artworks': 1, 'resources': 1})

            modified_players = []

            for player in players:
                need_update = False
                new_artworks = []

                for artwork in player['artworks']:
                    to_delete = False
                    for _art in artworks_to_delete:
                        if artwork['name'] == _art['name']:
                            need_update = True
                            to_delete = True
                            player['resources']['gold'] += _art['cost']
                            print player['name'], '>', _art['name']
                            break

                    if to_delete:
                        if len(new_artworks):
                            new_artworks[0]['current'] = True
                        else:
                            if 'current' in artwork and artwork['current']:
                                artwork['img'] = self.core.DELETED_ARTWORK_IMG
                                if 'UID' in artwork:
                                    del artwork['UID']

                                new_artworks.append(artwork)
                    else:
                        new_artworks.append(artwork)

                if need_update:
                    player['artworks'] = new_artworks
                    modified_players.append(player)

            for player in modified_players:
                player_id = player['_id']
                del player['_id']
                self.model.players.updatePlayerData(player_id, player)


        _ids = Set()
        for param in params:
            if param[:3] == 'id_':
                str_id = param[3:]
                _ids.add(ObjectId(str_id))

        print _ids
        query = {'_id': {'$in': list(_ids)}}

        artworks_to_delete = self.model.misc.getRawArtworks(query)

        paths = []
        for artwork in artworks_to_delete:
            paths.append(artwork['img'])

        deleteFromPlayers(artworks_to_delete)

        self.model.misc.deleteRawArtworks(query)
        self.model.misc.saveDeletedArtworksPaths(paths)

    # ---------------------------------
    # UGC adding rights and requests

    def applyRequest(self, params):
        # проверка на админа внутри:
        self.enableForceContentCreating(params, redirect=False)
        self.model.misc.markAuthRequestById(params['request_id'], 'apply')
        self.model.misc.delAuthRequestsByPlayerId(params['_id'], params['request_id'])

        mail_body = 'Hi, ' + params['fullname'] + '.\n\nYour content creation request in Tweeria was applied. Now you can create things in Tweeria!'
        mail_body += '\n\nLink to creation: http://tweeria.com/u/create'

        try:
            self.sendMail.send(
                to=params['email'],
                subject='Tweeria: Content creation rights were granted to you!',
                body=mail_body
            )
        except Exception:
            pass

        self.httpRedirect(params, '?success=apply&aname=' + params['username'])

    def declineRequest(self, params):

        reason_id = params['reasons']

        if reason_id == '...':
            reason = formatTextareaInput(params['reasons2'])
        else:
            for _r in self.balance.decline_reasons:
                if _r['name'] == reason_id:
                    reason = _r['value']
                    break
            else:
                reason = ''

        self.model.misc.markAuthRequestById(params['request_id'], 'decline', {'reason': reason})

        try:
            self.sendMail.send(
                to=params['email'],
                subject='Tweeria: Your content creation request was declined',
                body='Hi, ' + params[
                    'fullname'] + '.\n\nYour content creation request in Tweeria was declined by administrator with reason: ' + reason
            )
        except Exception:
            pass

        self.httpRedirect(params, '?success=decline&aname=' + params['username'])

    def disableContentCreating(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'name' in params:
            self.model.players.updatePlayerData(params['name'], {'ugc_disabled': True})

        if '_id' in params:
            self.model.players.updatePlayerData(params['_id'], {'ugc_disabled': True})

        self.httpRedirect(params)

    def enableContentCreating(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if '_id' in params:
            self.model.players.rawUpdatePlayerData(params['_id'], {
            '$unset': {'ugc_disabled': True}
            })

        self.httpRedirect(params)

    def disableForceContentCreating(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if '_id' in params:
            self.model.players.rawUpdatePlayerData(params['_id'], {
            '$unset': {'ugc_enabled': True}
            })

        self.httpRedirect(params)

    def enableForceContentCreating(self, params, redirect=True):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'name' in params:
            self.model.players.updatePlayerData(params['name'], {'ugc_enabled': True})

        elif '_id' in params:
            self.model.players.updatePlayerData(params['_id'], {'ugc_enabled': True})

        if redirect:
            self.httpRedirect(params)

    # ---------------------------------
    # Approve

    def _increaseModeratorStats(self, player_id, action_type, thing_type):
        if thing_type in ['items', 'spells', 'artworks'] and action_type in ['approve', 'reject']:
            self.model.players.increaseModeratorStats(player_id, action_type, thing_type, time.time())

    def approveItem(self, params):
        ajax = False
        if "ajax" in params and int(params['ajax']) == 1:
            ajax = True

        if not self._isPlayerModerator(0):
            if ajax:
                return json.dumps({"error": 1, "message": "WHAT A HACK! U CANT MODERATE ITEMS!!!!!!"})
            else:
                return self.sbuilder.throwWebError(1001)

        if '_id' in params:
            if 'tag' in params:
                tag = params['tag'].strip()
            else:
                tag = ''

            if tag:
                self.model.items.approveCraftedItem(params['_id'], self.cur_player['login_id'], tag=tag)
                self._increaseModeratorStats(self.cur_player['login_id'], 'approve', 'items')

        if ajax:
            return json.dumps({"success": 1})
        else:
            self.sbuilder.httpRedirect(params['__page__'])

    def approveSpell(self, params):
        ajax = False
        if "ajax" in params and int(params['ajax']) == 1:
            ajax = True

        if not self._isPlayerModerator(1):
            if ajax:
                return json.dumps({"error": 1, "message": "WHAT A HACK! U CANT MODERATE ITEMS!!!!!!"})
            else:
                return self.sbuilder.throwWebError(1001)

        if '_id' in params:

            if 'tag' in params:
                tag = params['tag'].strip()
            else:
                tag = ''

            if tag:
                self.model.spells.approveSpellPattern(params['_id'], self.cur_player['login_id'], tag=tag)
                self._increaseModeratorStats(self.cur_player['login_id'], 'approve', 'spells')

        if ajax:
            return json.dumps({"success": 1})
        else:
            self.sbuilder.httpRedirect(params['__page__'])

    def approveArtwork(self, params):
        ajax = False
        if "ajax" in params and int(params['ajax']) == 1:
            ajax = True

        if not self._isPlayerModerator(2):
            if ajax:
                return json.dumps({"error": 1, "message": "WHAT A HACK! U CANT MODERATE ITEMS!!!!!!"})
            else:
                return self.sbuilder.throwWebError(1001)
        if '_id' in params:

            if 'tag' in params:
                tag = params['tag'].strip()
            else:
                tag = ''

            if tag:
                self.model.misc.approveArtwork(params['_id'], self.cur_player['login_id'], tag=tag)
                self._increaseModeratorStats(self.cur_player['login_id'], 'approve', 'artworks')

        if ajax:
            return json.dumps({"success": 1})
        else:
            self.sbuilder.httpRedirect(params['__page__'])

    # ---------------------------------
    # Reject

    def _getReasons(self, params):

        reject_reason = ''
        for i in range(0, 20):
            if 'reject_reason' + str(i) in params:
                reject_reason += self.balance.rejected_reasons[i] + '. '

        if 'reject_reason' in params and params['reject_reason']:
            reject_reason += params['reject_reason'].strip()

        return reject_reason

    def rejectItem(self, params):
        ajax = False
        if "ajax" in params and int(params['ajax']) == 1:
            ajax = True

        if not self._isPlayerModerator(0):
            if ajax:
                return json.dumps({"error": 1, "message": "WHAT A HACK! U CANT MODERATE ITEMS!!!!!!"})
            else:
                return self.sbuilder.throwWebError(1001)

        rules = {
            '_id': {'not_null': 1},
        }

        status = self.checkParams(params, rules)

        if status['status']:

            reject_reason = self._getReasons(params)

            if reject_reason:
                self.model.items.rejectCraftedItem(params['_id'], self.cur_player['login_id'], reject_reason)
                self._increaseModeratorStats(self.cur_player['login_id'], 'reject', 'items')
                self.model.players.updateRejectInfo(params['_id'], 0)

                if 'force_delete' in params:
                    item = self.model.items.getCraftedItem(params['_id'])
                    if item:
                        self.model.items.deleteItem(item, self.cur_player['login_name'])

        if ajax:
            return json.dumps({"success": 1})
        else:
            self.sbuilder.httpRedirect(params['__page__'])

    def rejectSpell(self, params):
        ajax = False
        if "ajax" in params and int(params['ajax']) == 1:
            ajax = True

        if not self._isPlayerModerator(1):
            if ajax:
                return json.dumps({"error": 1, "message": "WHAT A HACK! U CANT MODERATE ITEMS!!!!!!"})
            else:
                return self.sbuilder.throwWebError(1001)

        rules = {
            '_id': {'not_null': 1},
        }

        status = self.checkParams(params, rules)

        if status['status']:
            reject_reason = self._getReasons(params)

            if reject_reason:
                self.model.spells.rejectSpellPattern(params['_id'], self.cur_player['login_id'], reject_reason)
                self._increaseModeratorStats(self.cur_player['login_id'], 'reject', 'spells')
                self.model.players.updateRejectInfo(params['_id'], 1)

                if 'force_delete' in params:
                    spell = self.model.spells.getSpellPatternByID(params['_id'])
                    if spell:
                        self.model.spells.deleteSpell(spell, self.cur_player['login_name'])

        if ajax:
            return json.dumps({"success": 1})
        else:
            self.sbuilder.httpRedirect(params['__page__'])

    def rejectArtwork(self, params):
        ajax = False
        if "ajax" in params and int(params['ajax']) == 1:
            ajax = True

        if not self._isPlayerModerator(2):
            if ajax:
                return json.dumps({"error": 1, "message": "WHAT A HACK! U CANT MODERATE ITEMS!!!!!!"})
            else:
                return self.sbuilder.throwWebError(1001)

        rules = {
            '_id': {'not_null': 1},
        }

        status = self.checkParams(params, rules)

        if status['status']:
            reject_reason = self._getReasons(params)
            if reject_reason:
                self.model.misc.rejectArtwork(params['_id'], self.cur_player['login_id'], reject_reason)
                self._increaseModeratorStats(self.cur_player['login_id'], 'reject', 'artworks')
                self.model.players.updateRejectInfo(params['_id'], 2)

                if 'force_delete' in params:
                    artwork = self.model.misc.getArtworkById(params['_id'])
                    if artwork:
                        self.model.misc.deleteArtwork(artwork, self.cur_player['login_name'])

        if ajax:
            return json.dumps({"success": 1})
        else:
            self.sbuilder.httpRedirect(params['__page__'])

    # Messages

    def messageEdit(self, params):

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        rules = {
            'text': {'min_length': 4},
            '_id': {'not_null': 1}
        }

        status = self.checkParams(params, rules)

        if status['status']:

            try:
                p = int(params['p'])
            except Exception:
                p = 0

            data = {
                'message': formatTextareaInput(params['text']),
                'p': p
            }

            self.model.misc.saveMessageData(params['_id'], data)

            params['__page__'] = '/a/messages'
            self.httpRedirect(params, '?action_name=' + params['a'] + '&success=edit')

    def messageDelete(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if '_id' in params:
            self.model.misc.deleteMessage(params['_id'])

            params['__page__'] = '/a/messages'
            self.httpRedirect(params, '?action_name=' + params['a'] + '&success=delete')

    def messageAdd(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        rules = {
            'text': {'min_length': 4},
            'action_name': {'not_null': 1},
            'message_type': {'not_null': 1}
        }

        status = self.checkParams(params, rules)

        if status['status']:
            action = self.model.misc.getActionByName(params['action_name'])

            if action and params['message_type'] in action:
                message_type = action[params['message_type']]

                try:
                    p = int(params['p'])
                except Exception:
                    p = 0

                data = {
                    'message': formatTextareaInput(params['text']),
                    'p': p,
                    'type': message_type
                }

                self.model.misc.addNewMessage(data)

                params['__page__'] = '/a/messages'
                self.httpRedirect(params, '?action_name=' + params['action_name'] + '&success=add')

            # ---------------------------------

    # Other

    def changeItem(self, params):

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        changed_data = {}

        try:
            item_type_data = params['item_type'].split(':')
            if len(item_type_data) > 1:
                changed_data['type'] = int(item_type_data[0])
                changed_data['view'] = item_type_data[1]
            else:
                changed_data['type'] = int(params['item_type'])
                changed_data['view'] = self.balance.item_types[int(params['item_type'])]
        except Exception:
            pass

        if changed_data:
            self.model.items.updateItemData(params['_id'], changed_data)

        self.httpRedirect(params)

    def changeTag(self, params):

        rlz = {'item': 0, 'spell': 1, 'artwork': 2}

        if 'thing_type' in params and params['thing_type'] in rlz:
            tp = rlz[params['thing_type']]

            if not self._isPlayerModerator(tp):
                return self.sbuilder.throwWebError(1001)

            if '_id' in params:
                if tp == 0:
                    self.model.items.updateItem(params['_id'], {'tag': params['new_tag']})
                elif tp == 1:
                    self.model.spells.updateSpell(params['_id'], {'tag': params['new_tag']})
                elif tp == 2:
                    self.model.misc.updateArtwork(params['_id'], {'tag': params['new_tag']})

        self.httpRedirect(params)

    def takeAchv(self, params):

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        name = params['user_name'].strip()
        if name[0] == '@':
            name = name[1:]

        name = params['user_name']

        if name:
            result = self.model.players.takeAchv(name, params['achv'])
            if result:
                name = '?success=1&take=' + name + '&achv=' + params['achv']
            else:
                name = '?fail=1'

        self.httpRedirect(params, name)

    def banPlayer(self, params):

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'sure' in params:
            if 'user_name' in params and params['user_name']:
                if params['user_name'][0] == '@':
                    params['user_name'] = params['user_name'][1:]

                name = params['user_name']

                if not params['reason']:
                    params['reason'] = 'Not a human'

                result = self.model.players.banPlayer(name, self.cur_player['login_name'], params['reason'])

                if result:
                    self.httpRedirect(params, '?success=1&name=' + name + '&re=' + params['reason'])
                else:
                    self.httpRedirect(params, '?error=unknown&name=' + name)
        else:
            self.httpRedirect(params, '?error=not_sure')

    def changeLevel(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'user_name' in params and params['user_name']:
            if params['user_name'][0] == '@':
                params['user_name'] = params['user_name'][1:]

            name = params['user_name']

            if not params['reason']:
                params['reason'] = 'No reason given'

            if 'new_level' in params:
                level = int(params['new_level'])

                is_ok = self.model.players.changeLevelByName(
                    name,
                    level,
                    params['reason'],
                    self.cur_player['login_id'],
                    self.cur_player['login_name']
                )

                if is_ok:
                    self.httpRedirect(params, '?success=1')

        self.httpRedirect(params, '?error=1')

    def getTimeline(self, params):

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'user_name' in params and params['user_name']:
            if params['user_name'][0] == '@':
                params['user_name'] = params['user_name'][1:]

            name = params['user_name']

        else:
            name = ''
            return False

        result = self.model.players.getUserTimeline(name)

        if result[0]:
            params['timeline'] = result[1]
            params['req_name'] = name
        else:
            if result[1]:
                self.httpRedirect(params, '?error=' + result[1] + '&user=' + name)

    # ---------------------------------
    # Tips

    def addTip(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        name = '?fail=1'

        if 'content' in params:
            content = formatTextareaInput(params['content'])

            if content:
                is_tips_data_exists = self.model.misc.isTipsExists()
                self.model.misc.addTip(
                    content,
                    self.cur_player['login_id'],
                    self.cur_player['login_name'],
                    is_tips_data_exists
                )

                name = '?success=1'

        self.httpRedirect(params, name)

    def disableTip(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'uid' in params:
            uid = int(params['uid'])

            tips = self.model.misc.getTips()
            for tip in tips:
                if tip['uid'] == uid:
                    if tip['enable']:
                        tip['enable'] = False
                        self.model.misc.updateTips(tips)
                        break

        params['__page__'] = '/a/tips'
        self.httpRedirect(params)

    def enableTip(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'uid' in params:
            uid = int(params['uid'])

            tips = self.model.misc.getTips()
            for tip in tips:
                if tip['uid'] == uid:
                    if not tip['enable']:
                        tip['enable'] = True
                        self.model.misc.updateTips(tips)
                        break

        params['__page__'] = '/a/tips'
        self.httpRedirect(params)

    def deleteTip(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'uid' in params:
            uid = int(params['uid'])

            tips = self.model.misc.getTips()
            new_tips = []
            for tip in tips:
                if tip['uid'] != uid:
                    new_tips.append(tip)

            if len(new_tips) != len(tips):
                self.model.misc.updateTips(new_tips)

        params['__page__'] = '/a/tips'
        self.httpRedirect(params)

    # ---------------------------------
    # Tags

    def addTag(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        name = '?fail=1'

        if 'name' in params and 'variable' in params:
            name = params['name'].strip()
            variable = params['variable'].strip()

            if name and variable:
                self.model.misc.addTag(
                    name,
                    variable,
                    self.cur_player['login_id'],
                    self.cur_player['login_name']
                )

                name = '?success=1'

        self.httpRedirect(params, name)

    def deleteTag(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'uid' in params:
            uid = int(params['uid'])
            self.model.misc.deleteTags(uid)

        params['__page__'] = '/a/tags'
        self.httpRedirect(params)

    # ---------------------------------
    # User control

    def inviteUser(self, params):

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        name = params['user_name'].strip()
        if name:
            self.model.players.invitePlayer(params['user_name'])
            name = '?success=1&invite=' + name

        self.httpRedirect(params, name)

    def rejectInvite(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        name = params['user_name'].strip()

        if name and not self.model.players.isUserAdmin(name):
            self.model.players.rejectInvite(params['user_name'])
            name = '?success=1&reject=' + name
        else:
            name = ''

        self.httpRedirect(params, name)

    def promoteToModerator(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        name = params['user_name'].strip()
        if name:

            is_items = 'approve_items' in params
            is_spells = 'approve_spells' in params
            is_artworks = 'approve_artworks' in params

            if is_items or is_spells or is_artworks:
                rights = [is_items, is_spells, is_artworks]
            else:
                rights = [True, True, True]

            self.model.players.promoteToModerator(params['user_name'], rights)
            name = '?success=1&promote=' + name

        self.httpRedirect(params, name)

    def rejectFromModerator(self, params):
        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        name = params['user_name'].strip()
        if name:
            self.model.players.rejectFromModerator(params['user_name'])
            name = '?success=1&reject=' + name

        self.httpRedirect(params, name)

    # ---------------------------------
    # Print pages

    def printAdminIndex(self, fields, params):
        fields.update({self.title: 'Admin\'s corner'})

        if not self._isPlayerModerator():
            return self.sbuilder.throwWebError(1001)

        player_info = self._getModeratorRights()

        if player_info:
            fields.update(player_info)

        fields.update({
            'waiting_items': self.model.items.getApprovedItemsCount(),
            'waiting_spells': self.model.spells.getApprovedSpellsCount(),
            'waiting_artworks': self.model.misc.getApprovedArtworksCount(),
            'waiting_requests': self.model.misc.getAuthRequestsCount()
        })

        return basic.defaultController._printTemplate(self, 'admin_index', fields)

    def printUsersInvitePage(self, fields, params):

        fields.update({self.title: 'Invite page'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        invited_users = self.model.players.getInvitedList()
        current_players = self.model.players.getPlayersList(fields_names=['name', 'lvl'])
        for invited_user in invited_users:
            for cur_player in current_players:
                if invited_user['name'] == cur_player['name']:
                    invited_user.update({'lvl': cur_player['lvl']})
                    del cur_player
                    break

        fields.update({'invited_users': invited_users})

        return basic.defaultController._printTemplate(self, 'user_invites', fields)

    def printApproveHelpPage(self, fields, params):
        fields.update({self.title: 'Approvement help'})
        return basic.defaultController._printTemplate(self, 'approve_rules', fields)

    def printFeaturedArtworkSelect(self, fields, params):

        WEEK = 604800

        if 'wk' in params:
            try:
                int_wk = int(params['wk'])
                WEEK *= int_wk
            except Exception:
                int_wk = 1
        else:
            int_wk = 1

        fields.update({'wk': int_wk})
        fields.update({self.title: 'Featured artwork'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        artworks = self.model.misc.getAllArtworks(
            approved=True,
            users_only=True,
            search={'approve.time': {'$gte': time.time() - WEEK}},
            sort_query={'approve.time': -1}
        )
        featured_artworks = self.model.misc.getFeaturedArtwork()

        featured = [0, 0, 0]
        if featured_artworks:
            for i in range(0, 3):
                if 'artwork_id' in featured_artworks[i]:
                    featured[i] = featured_artworks[i]['artwork_id']

        if featured:
            for artwork in artworks:
                if artwork['_id'] in featured:
                    for i in range(0, 3):
                        if artwork['_id'] == featured[i]:
                            artwork.update({'select': i})
                            break

        fields.update({'artworks': miscController.formatArtworks(self, artworks)})

        return basic.defaultController._printTemplate(self, 'featured_artwork', fields)

    def printItemAdminPage(self, fields, params):

        fields.update({self.title: 'Item\'s page'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'id' in params:
            try:
                item = self.model.items.getCraftedItem(params['id'])
            except Exception:
                item = False
        else:
            item = False

        if not item:
            self.sbuilder.httpRedirect('/a/index')

        fields.update({'item': self._getPlayersItems([item])[0]})

        return basic.defaultController._printTemplate(self, 'item_admin_page', fields)

    def printAchvTakePage(self, fields, params):
        fields.update({self.title: 'Take achievement page'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        rare_achvs = self.model.misc.getRareAchvs()
        if 'achv' in params:
            try:
                achv = self.model.misc.getAchv(int(params['achv']))
                fields.update({'achv': formatOutput(achv['name'])})
            except Exception:
                pass

        fields.update({'achvs': rare_achvs})

        return basic.defaultController._printTemplate(self, 'take_achv', fields)

    def printGetTimelimePage(self, fields, params):
        fields.update({self.title: 'Get timeline page'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'timeline' in params:
            timeline = []
            for tweet in params['timeline']:
                timeline.append(tweet.text)

            fields.update({'timeline': timeline})

        return basic.defaultController._printTemplate(self, 'get_timeline', fields)

    def printBanPage(self, fields, params):
        fields.update({self.title: 'Banhammer page'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        players = self.model.players.getBannedPlayers()

        fields.update({'banned_players': players})

        return basic.defaultController._printTemplate(self, 'ban_player', fields)

    def printDeleted(self, fields, params):
        fields.update({self.title: 'Deleted control'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        deleted_things = self.model.items.getDeletedThings()

        for item in deleted_things:
            if 'deleted_time' in item:
                item['deleted_time'] = getRelativeDate(item['deleted_time'])

        fields.update({
            'deleted': deleted_things
        })

        return basic.defaultController._printTemplate(self, 'deleted', fields)

    def printTipsPage(self, fields, params):
        fields.update({self.title: 'Tips control'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        tips = self.model.misc.getTips()

        fields.update({'tips': tips})

        return basic.defaultController._printTemplate(self, 'tips', fields)

    def printSetLevelPage(self, fields, params):
        fields.update({self.title: 'Set level control'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        levels = self.model.misc.getChangeLevels()
        for level in levels:
            level.update({'time_f': getReadbleTime(level['time'])})

        fields.update({'levels': self._qsort(levels, 'time')})

        return basic.defaultController._printTemplate(self, 'set_level', fields)

    # edit messages

    def ajaxGetMessages(self, fields, params):

        actions = self.model.misc.getActions()

        grouped_messages = []

        if 'action_name' in params:

            selected_action = None
            for action in actions:
                if params['action_name'] == action['name']:
                    selected_action = action
                    break

            if selected_action:
                raw_messages = self.model.misc.getMessagesByAction(selected_action)
                fields.update({'selected_action_name': selected_action['name']})
                grouped_messages = {}
                for message_type in self.message_result_types:
                    grouped_messages.update({message_type: []})

                for message in raw_messages:
                    for key in self.message_result_types:
                        if selected_action[key] == message['type']:
                            grouped_messages[key].append(message)

        for group in grouped_messages:
            sum_p = 0
            for message in grouped_messages[group]:
                sum_p += message['p']

            for message in grouped_messages[group]:
                message.update({'p_f': round(float(message['p']) / sum_p * 100, 1)})

        fields.update({
            'message_groups': grouped_messages,
            'actions': actions
        })

        if self.isAjax():
            return basic.defaultController._printTemplate(self, 'messages/messages_list', fields)
        else:
            return fields

    def printMessagesList(self, fields, params):

        fields.update({self.title: 'Messages control'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        if 'action_name' in params:
            fields.update(self.ajaxGetMessages(fields, params))
        else:
            actions = self.model.misc.getActions()
            fields.update({'actions': actions})

        return basic.defaultController._printTemplate(self, 'messages/messages', fields)

    def printMessageAdd(self, fields, params):

        fields.update({self.title: 'New message'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        actions = self.model.misc.getActions()
        tags = self.model.misc.getTags()
        fields.update({
            'actions': actions,
            'tags': tags
        })

        return basic.defaultController._printTemplate(self, 'messages/message_new', fields)

    def printMessageEdit(self, fields, params):

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        message = False
        if 'id' in params:
            message = self.model.misc.getMessageById(params['id'])

        if not message:
            return self.sbuilder.throwWebError(5004)
        else:
            fields.update(message)

        if 'a' in params:
            action = self.model.misc.getActionByName(params['a'])
            if action:
                for key in self.message_result_types:
                    if action[key] == message['type']:
                        fields.update({'message_type_name': key})

                fields.update({'action': action})

        tags = self.model.misc.getTags()

        fields.update({
            self.title: 'Messages edit',
            'tags': tags
        })

        return basic.defaultController._printTemplate(self, 'messages/message_edit', fields)

    # tags

    def printTags(self, fields, params):
        fields.update({self.title: 'Tags control'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        tags = self.model.misc.getTags()

        fields.update({'tags': tags})

        return basic.defaultController._printTemplate(self, 'tags/tags', fields)

    # reported pages

    def printReportedItemsPage(self, fields, params):

        def getReportedItems():
            reported_info = self.model.misc.getReportThings('item')

            ids_ = Set()
            for info in reported_info:
                ids_.add(info['item_id'])

            items = self.model.items.getItems(ids_, {
                '_id': 1,
                'name': 1,
                'type': 1,
                'view': 1,
                'approve.approved': 1,
                'reject.rejected': 1
            })

            if not items:
                return []

            for item in items:
                for info in reported_info:
                    if info['item_id'] == item['_id']:
                        item.update({'reports': len(info['people'])})
                        del info
                        break

            return items

        fields.update({self.title: 'Reported items page'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        fields.update({
            'items': self._qsort(getReportedItems())
        })

        return basic.defaultController._printTemplate(self, 'reported_items', fields)

    def printReportedSpellsPage(self, fields, params):

        def getReportedSpells():
            reported_info = self.model.misc.getReportThings('spell')

            ids_ = Set()
            for info in reported_info:
                ids_.add(info['item_id'])

            spells = self.model.spells.getSpellPatternsByIDs(ids_, {
                'name': 1,
                '_id': 1,
                'approve.approved': 1,
                'reject.rejected': 1
            })

            if not spells:
                return []

            for spell in spells:
                for info in reported_info:
                    if info['item_id'] == spell['_id']:
                        spell.update({'reports': len(info['people'])})
                        del info
                        break

            return spells

        fields.update({self.title: 'Reported spells page'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        fields.update({
            'spells': self._qsort(getReportedSpells())
        })

        return basic.defaultController._printTemplate(self, 'reported_spells', fields)

    def printArtworksDelete(self, fields, params):

        fields.update({self.title: 'Artworks delete'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        artworks = self.model.misc.getAllArtworks(approved='all', users_only=False)
        for artwork in artworks:
            if 'builtin' in artwork:
                artwork['img'] = self.core.ARTWORK_SHOP_PATH + artwork['img'] + '.jpg'
            else:
                artwork['img'] += '_fit.png'

        fields.update({'artworks': artworks})

        return basic.defaultController._printTemplate(self, 'artworks_delete', fields)

    def printReportedArtworksPage(self, fields, params):

        def getReportedArtworks():
            reported_info = self.model.misc.getReportThings('artwork')

            ids_ = Set()
            for info in reported_info:
                ids_.add(info['item_id'])

            artworks = self.model.misc.getArtworksByIds(ids_, {
                'name': 1,
                '_id': 1,
                'approve.approved': 1,
                'reject.rejected': 1
            })

            if not artworks:
                return []

            for artwork in artworks:
                for info in reported_info:
                    if info['item_id'] == artwork['_id']:
                        artwork.update({'reports': len(info['people'])})
                        del info
                        break

            return artworks

        fields.update({self.title: 'Reported artworks page'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        fields.update({
        'artworks': self._qsort(getReportedArtworks())
        })

        return basic.defaultController._printTemplate(self, 'reported_artworks', fields)

    # approvements pages

    def printApprovementsPage(self, fields, params):

        fields.update({self.title: 'Approvement page'})

        if not self._isPlayerModerator():
            return self.sbuilder.throwWebError(1001)

        fields.update({
            'items': self._getPlayersItems(),
            'artworks': self._getArtworks(),
            'spells': self._getSpells(),
            'stat_names': self.balance.stats_name
        })

        return basic.defaultController._printTemplate(self, 'approvements', fields)

    def printApproveItems(self, fields, params):
        fields.update({self.title: 'Item\'s approvement page'})

        if not self._isPlayerModerator(0):
            return self.sbuilder.throwWebError(1001)

        fields.update({
            'items': self._getPlayersItems(),
            'stat_names': self.balance.stats_name,
            'reasons': self.balance.getRejectReasons(self.balance.item_reject_reasons),
            'categories': self.balance.categories
        })

        return basic.defaultController._printTemplate(self, 'approve_items', fields)

    def printApproveSpells(self, fields, params):
        fields.update({self.title: 'Spell\'s approvement page'})

        if not self._isPlayerModerator(1):
            return self.sbuilder.throwWebError(1001)

        fields.update({
            'spells': self._getSpells(),
            'stat_names': self.balance.stats_name,
            'reasons': self.balance.getRejectReasons(self.balance.spell_reject_reasons),
            'categories': self.balance.categories
        })

        return basic.defaultController._printTemplate(self, 'approve_spells', fields)

    def printApproveArtworks(self, fields, params):
        fields.update({self.title: 'Artwork\'s approvement page'})

        if not self._isPlayerModerator(2):
            return self.sbuilder.throwWebError(1001)

        fields.update({
            'artworks': self._getArtworks(),
            'stat_names': self.balance.stats_name,
            'reasons': self.balance.getRejectReasons(self.balance.artwork_reject_reasons),
            'categories': self.balance.categories
        })

        return basic.defaultController._printTemplate(self, 'approve_artworks', fields)

    # people

    def printArtistsPage(self, fields, params):

        fields.update({self.title: 'Artists control'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        players = self.model.players.getUGCEnabledPlayers()
        requests = self.model.misc.getAuthRequests()

        for request in requests:
            request['time_f'] = getReadbleTime(request['time'])

        fields.update({
            'players': players,
            'requests': requests,
            'reasons': self.balance.decline_reasons
        })

        return basic.defaultController._printTemplate(self, 'artists', fields)

    def printModeratorsPage(self, fields, params):

        fields.update({self.title: 'Moderator\'s control'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        moderators = self.model.players.getModerators()
        for player in moderators:
            if not 'moderator_rights' in player:
                rights = [True, True, True]
            else:
                rights = player['moderator_rights']

            player.update({
                'app_items': rights[0],
                'app_spells': rights[1],
                'app_artworks': rights[2],
            })

            if not 'moderator_stats' in player:
                player.update({
                    'moderator_stats': {
                        'items': '-',
                        'spells': '-',
                        'artworks': '-',
                        'time': '-'
                    }
                })

            else:
                player['moderator_stats']['time'] = getReadbleTime(player['moderator_stats']['time'])

        fields.update({'moderators': moderators})

        return basic.defaultController._printTemplate(self, 'user_moderators', fields)

    def printBadPeoplePage(self, fields, params):

        fields.update({self.title: 'Bad people\'s control'})

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        info = self.model.players.getRejectInfo()
        authors_ids = Set()

        record_hash = {}
        for record in info:
            record_hash.update({
            str(record['player_id']): record
            })
            authors_ids.add(record['player_id'])

        disabled = self.model.players.getUGCDisabled()
        disabled_hash = {}
        for record in disabled:
            disabled_hash.update({
            str(record['_id']): record
            })
            authors_ids.add(record['_id'])

        buff_players = self.model.players.getPlayersList2(authors_ids, {
            'name': 1,
            '_id': 1,
            'banned': 1,
            'ugc_disabled': 1
        })

        players = {}
        for buff in buff_players:
            players.update({
                str(buff['_id']): {
                    '_id': buff['_id'],
                    'name': buff['name'],
                    'banned': 'banned' in buff,
                    'ugc_disabled': 'ugc_disabled' in buff
                    }
                }
            )

        final_records = []
        for _id in authors_ids:
            str_id = str(_id)

            if str_id in players:
                record = False
                if str_id in record_hash:
                    record = record_hash[str_id]
                elif str_id in disabled_hash:
                    record = disabled_hash[str_id]

                if record:
                    record.update(players[str_id])

                    final_records.append(record)

        fields.update({'players': final_records})

        return basic.defaultController._printTemplate(self, 'people', fields)

    # rejected pages

    def printRejectedItemsPage(self, fields, params):

        fields.update({self.title: 'Rejected items page'})

        items_on_page = 100
        page = 0
        if 'p' in params:
            try:
                page = int(params['p'])
            except Exception:
                pass

        items = self._getPlayersItems(
            rejected=True,
            sorting={'reject.time': -1},
            limit=items_on_page,
            skip=page * items_on_page
        )

        for item in items:
            item['reject_date'] = getRelativeDate(item['reject']['time'] + self.cur_player['login_utc_offset'])

        fields.update({
            'items': items,
            'p': page,
            'stat_names': self.balance.stats_name
        })

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        return basic.defaultController._printTemplate(self, 'rejected_items', fields)

    def printRejectedSpellsPage(self, fields, params):

        fields.update({self.title: 'Rejected spells page'})

        items_on_page = 100
        page = 0
        if 'p' in params:
            try:
                page = int(params['p'])
            except Exception:
                pass

        spells = self._getSpells(
            rejected=True,
            sorting={'reject.time': -1},
            limit=items_on_page,
            skip=page * items_on_page
        )

        for spell in spells:
            spell['reject_date'] = getRelativeDate(spell['reject']['time'] + self.cur_player['login_utc_offset'])

        fields.update({
            'spells': spells,
            'p': page,
            'stat_names': self.balance.stats_name
        })

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        return basic.defaultController._printTemplate(self, 'rejected_spells', fields)

    def printRejectedArtworksPage(self, fields, params):

        fields.update({self.title: 'Rejected artworks page'})

        items_on_page = 100
        page = 0
        if 'p' in params:
            try:
                page = int(params['p'])
            except Exception:
                pass

        artworks = self._getArtworks(
            rejected=True,
            sorting={'reject.time': -1},
            limit=items_on_page,
            skip=page * items_on_page
        )

        for artwork in artworks:
            artwork.update({
                'reject_date': getRelativeDate(artwork['reject']['time'] + self.cur_player['login_utc_offset']),
                'race_name': self.balance.races[artwork['faction']][artwork['race']],
                'class_name': self.balance.classes[str(artwork['class'])]
            })

        fields.update({
            'artworks': artworks,
            'p': page
        })

        if not self._isPlayerAdmin():
            return self.sbuilder.throwWebError(1001)

        return basic.defaultController._printTemplate(self, 'rejected_artworks', fields)


data = {
    'class': adminController,
    'type': ['a'],
    'urls': ['index', '',
             'approve_items', 'approve_spells', 'approve_artworks', 'approvements',
             'rejected_items', 'rejected_spells', 'rejected_artworks',
             'reported_items', 'reported_spells', 'reported_artworks',
             'invites', 'people', 'deleted',
             'moderators', 'rejected', 'approve_rules',
             'artwork', 'item', 'achvs', 'tips', 'level',
             'timeline', 'ban', 'artists', 'artworks_delete',
             'messages', 'm', 'get_ajax_messages', 'add_message',
             'tags'
    ]
}
