# -*- coding: utf-8 -*-



import __init__
import db
import settings
import site_builder
import re
import time
import cherrypy
from functions import getRelativeDate
from model_basic import DataModel
import __main__


def _profile(method_to_decorate):
    def wrapper(*args, **kwargs):
        t_start = time.time()
        result = method_to_decorate(*args, **kwargs)
        t_all = time.time() - t_start
        print method_to_decorate.__name__, '\t\t', t_all
        return result

    return wrapper


def methods(method_to_decorate):
    def wrapper(self, params={}):
        rules = method_to_decorate(self, params={})
        return defaultController.pageMethods(self, rules, params)

    return wrapper


def printpage(method_to_decorate):
    def wrapper(self, page, params):
        rules = method_to_decorate(self, page, params)
        return defaultController.printPage2(self, page, rules, self.methods, params)

    return wrapper


class defaultClass:
    def __init__(self):
        pass

    def mongoConnect(self):
        try:
            self.mongo
        except:
            self.mongo = db.mongoAdapter()

    def loadSettings(self):
        try:
            self.core
        except:
            self.core = __main__.tweenk_core

    def loadBalance(self):
        try:
            self.balance
        except:
            self.balance = __main__.tweenk_balance


class defaultController(defaultClass):
    OK = {'ok': True}
    DIR = './'
    title = 'page_title_name'

    def __init__(self, preload=True):
        defaultClass.__init__(self)
        self.loadDataModel()
        if preload:
            self.initialize()

    def _printUGCDisablePage(self, fields={}):
        if self.core.debug['create_by_invite'] and not (self.cur_player and self.cur_player['login_ugc_enabled']):
            return self._printTemplate('ugc_disabled_message', fields)
        else:
            return False

    def initialize(self):
        defaultClass.mongoConnect(self)
        defaultClass.loadSettings(self)
        defaultClass.loadBalance(self)

    def isAjax(self):
        return 'X-Requested-With' in cherrypy.request.headers and cherrypy.request.headers[
            'X-Requested-With'] == 'XMLHttpRequest'

    def checkParams(self, params, rules):

        status = {'status': True, 'errors': []}

        for key in rules:
            buff = self.checkParam(params, key, rules[key])
            if not buff['status']:
                for error in buff['errors']:
                    status['errors'].append(error)

                status['status'] = False

        return status

    def thrownCheckError(self, name, error_text):
        return {
            'name': name,
            'desc': error_text
        }

    def checkParam(self, params, name, criteria={}):

        def convert(item):
            try:
                return int(item)
            except Exception:
                return False

        status = True
        errors = []

        if not name in params:
            status = False
            errors.append({'name': name, 'desc': 'null'})

        else:
            errors_count = len(errors)

            if 'min_length' in criteria and criteria['min_length'] > len(params[name]):
                errors.append({'name': name, 'desc': 'min_length_fail'})

            if 'max_length' in criteria and criteria['max_length'] < len(params[name]):
                errors.append({'name': name, 'desc': 'max_length_fail'})

            # x > param
            if 'gt' in criteria and convert(params[name]) and criteria['gt'] >= int(params[name]):
                errors.append({'name': name, 'desc': 'not_greater'})

            # x < param
            if 'lt' in criteria and convert(params[name]) and criteria['lt'] <= int(params[name]):
                errors.append({'name': name, 'desc': 'not_lower'})

            # x => param
            if 'gte' in criteria and convert(params[name]) and criteria['gte'] > int(params[name]):
                errors.append({'name': name, 'desc': 'not_greater_or_equal'})

            # x <= param
            if 'lte' in criteria and convert(params[name]) and criteria['lte'] < int(params[name]):
                errors.append({'name': name, 'desc': 'not_lower_or_equal'})

            if 'not_null' in criteria and params[name] == '':
                errors.append({'name': name, 'desc': 'null'})

            if 'exist' in criteria and not name in params:
                errors.append({'name': name, 'desc': 'not_exist'})

            if 'int' in criteria:
                try:
                    int(params[name])
                except Exception:
                    errors.append({'name': name, 'desc': 'not_int'})

            if 'in' in criteria and convert(params[name]) and not criteria['in'] in params[name]:
                errors.append({'name': name, 'desc': 'not in allowed values'})

            if 'match' in criteria:
                if re.match(criteria['match'], params[name]) == None:
                    errors.append({'name': name, 'desc': 'not_match'})

            if 'not_dublicate' in criteria:
                collection_name = criteria['not_dublicate'].keys()[0]
                field = criteria['not_dublicate'].values()[0]
                if self.model.misc.isDuplicate(collection_name,
                                               {field: re.compile('^' + params[name].strip() + '$', re.I + re.U)}):
                    errors.append({'name': name, 'desc': 'dublicate'})

            # итоговое состояние — если нашли хоть одну ошибку, то статус = False
            if errors_count != len(errors):
                status = False

        return {'status': status, 'errors': errors}

    def loadDataModel(self):
        self.model = DataModel()

    def error(self, name):
        return {'critical_error': name}

    def printPage2(self, page, rules, methods, params={}):

        def runRule(rule):
            if isinstance(rule, dict):
                params.update(rule['params'])
                if rule['method']:
                    return rule['method'](fields, params)
                else:
                    methods(params)
            else:
                return rule(fields, params)

        def getNearestGuildEvent(fields):
            if 'login_guild' in fields and fields['login_guild']:
                event = self.model.events.getGuildEventsByID(fields['login_guild'], limit=1, fields={
                    'target_name': 1,
                    'guild_side_name': 1,
                    'start_date': 1,
                    '_id': 1,
                    'type': 1
                })

                if event:
                    if event[0]['start_date'] < time.time():
                        event[0].update({'in_progress': 1})
                    event[0]['start_date'] = getRelativeDate(event[0]['start_date'] + fields['login_utc_offset'])
                    fields.update({'nearest_guild_event': event[0]})

        def getNearestFactionEvent(fields):
            if 'login_faction' in fields:
                event = self.model.events.getFactionEventsByID(fields['login_faction'], limit=1, fields={
                    'sides': 1,
                    'sides_names': 1,
                    'start_date': 1,
                    '_id': 1,
                    'type': 1
                })

                if event:
                    event[0]['start_date'] = getRelativeDate(event[0]['start_date'] + fields['login_utc_offset'])
                    fields.update({'nearest_faction_event': event[0]})

        self.sbuilder = site_builder.builder()
        fields = {}

        try:
            isinstance(self.mongo, bool)
        except Exception:
            self.initialize()

        self.cur_player = self.sbuilder.playerLogged()
        if self.cur_player:
            fields.update(self.cur_player)

        params.update({'__page__': page, '__query__': cherrypy.request.query_string})

        res = methods(params)

        if res and self.isAjax():
            return res

        if isinstance(res, dict) and 'critical_error' in res:
            fields.update({'critical_error': res['critical_error']})

        if 'errors' in params:
            fields.update({'errors': params['errors']})

        if res and 'ok' in res:
            fields.update({'success': True})

        # disabled из-за проблем с производительностью
        # getNearestGuildEvent(fields)
        # getNearestFactionEvent(fields)

        fields.update(self.paramsConvert(params))

        if 'invites' in self.core.debug and self.core.debug['invites']:
            if self.cur_player:
                pass
            else:
                if page in ['registration', 'new']:
                    pass
                else:
                    return self.sbuilder.loadTemplate('invites/access.jinja2', {})

        # если метод обработчика возвращает страницу, тогда выведем ее
        # не дожидаясь выполнения print page
        if isinstance(res, unicode) or isinstance(res, str):
            return res

        # print page
        for page_name in rules:
            if page_name == page:
                return runRule(rules[page_name])

        if '__default__' in rules:
            return runRule(rules['__default__'])

    def paramsConvert(self, params):
        result = {}
        for param_name in params:
            if param_name[0] != '_':
                result.update({'param_' + param_name: params[param_name]})
            else:
                result.update({param_name: params[param_name]})

        if 'errors' in params:
            error_fields = []
            for error in params['errors']:
                error_fields.append(error['name'])

            result.update({'error_fields': error_fields})

        return result

    def insertMessage(self, text, player, data):
        data.update({'player': player['name'], 'time': time.time()})

        player.update({'message_count': len(player['messages'])})

        record = {'message': text, 'data': data}

        if int(player['message_count']) >= self.balance.max_stored_messages:
            player['message_count'] = int(player['message_count']) - 1
            self.mongo.deleteMessage(int(player['user_id']), 1)

        self.mongo.pushUpdate('players', 'user_id', int(player['user_id']), 'messages', record)

    def pageMethods(self, rules, params):
        for param_name in rules:
            if param_name in params:
                if isinstance(rules[param_name], dict):
                    actions = rules[param_name]
                    for key in actions:
                        if params[param_name] == key:
                            return actions[key](params)
                else:
                    return rules[param_name](params)

    def httpRedirect(self, params, additional=''):
        if 'backlink' in params:
            params['__page__'] = params['backlink']

        self.sbuilder.httpRedirect(params['__page__'] + additional)

    def _printTemplate(self, tmp, fields):
        return self.sbuilder.loadTemplate(self.DIR + tmp + '.jinja2', fields)