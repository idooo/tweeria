# -*- coding: utf-8 -*-

# General functions for web part and parser

import datetime
import time
import re

RE_MESSAGE_VARS = re.compile('(\{([^\}]*)\})')
RE_TAGS = re.compile('<[^<]+?>', re.U + re.I + re.M)
RE_PARAGRAPH = re.compile('\n', re.U + re.I + re.MULTILINE)
RE_OUT_FORMAT = re.compile('(\'|`)', re.U + re.I + re.M)


# others

def plural(n, text):
    countString = ""

    if (n > 0 and len(text) == 3):
        if (n % 10 == 1 and n % 100 != 11):
            countString = text[0]
        elif (n % 10 >= 2 and n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20)):
            countString = text[1]
        else:
            countString = text[2]
    return countString


def pluralEnd(n, text):
    countString = ""
    if len(text) == 3:
        n = int(n)

        if n % 10 in (0, 1, 4, 5, 6, 9) or 9 < n < 21:
            countString = text[0]
        elif n % 10 in (2, 6, 7, 8):
            countString = text[1]
        elif n % 10 == 3:
            countString = text[2]

    return countString


def format_datetime(value, format='medium'):
    if format == 'full':
        format = "EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format = "EE dd.MM.y HH:mm"
    return datetime.datetime.fromtimestamp(int(value)).strftime('%d-%m-%Y %H:%M:%S')


def summAr(array, attribute=False):
    total = 0
    for val in array:
        if attribute:
            total += int(array[val][attribute])
        else:
            total += array[val]
    return total


def getReadbleTime(incoming_time):
    if incoming_time == 0:
        return "At the Beginning"

    cur_time = time.time()
    event_time = cur_time - int(incoming_time)

    time_array = [
        {'second': event_time},
        {'minute': event_time / 60},
        {'hour': event_time / 3600},
        {'day': event_time / 86400},
        {'week': event_time / 604800},
        {'month': event_time / 2592000},
        {'year': event_time / 31536000},
    ]

    timestring = ' '
    for i in time_array:
        if i.values()[0] >= 1:
            timestring = str(int(i.values()[0])) + ' ' + i.keys()[0]
            if i.values()[0] >= 2:
                timestring += 's'

    if timestring == ' ':
        timestring = 'Right now'
    else:
        timestring = str(timestring) + ' ago'

    return timestring


def getMessages(messages, with_time=True, host='', tags=None):

    # format tags array to dict for fast search
    tags_dict = {}
    if tags:
        for tag in tags:
            tags_dict.update({tag['variable']: tag['name']})

    count = 0
    messages = messages[::-1]
    for item in messages:
        if 'data' in item:
            count += 1
            text = item['message']
            clear_text = text
            data = item['data']

            res = re.findall(RE_MESSAGE_VARS, text)

            for m in res:
                pattern = ''
                clear_pattern = ''

                if m[1][0:3] == 'tag':
                    params = m[1].split('=', 2)
                    if len(params) > 1:
                        variable = params[1].strip()
                        if variable in tags_dict:
                            tag = '#' + tags_dict[variable]

                            clear_pattern = tag

                            if len(params) > 2 and params[2].strip() == 'show':
                                pattern = tag


                if m[1][0:3] == 'url':
                    params = m[1].split('=', 2)

                    if len(params) > 1:
                        pattern = '<a href="{0}">{1}</a>'
                        if len(params) > 2:
                            url = params[2].strip()
                            name = params[1].strip()
                        else:
                            url = params[1].strip()
                            name = url

                        pattern = pattern.format(url, name)
                        clear_pattern = url

                elif m[0] == '{playerpage}':
                    clear_pattern = host + data['player']

                elif m[1] in data:
                    if m[0] == '{monster}':
                        pattern = '<span class="monster" rel="obj/2/' + str(int(data['monster_UID'])) + '">' + data['monster'] + '</span>'
                        clear_pattern = data['monster']

                    elif m[0] == '{player}':
                        pattern = '<a href="/' + data['player'] + '" class="player">' + data['player'] + '</a>'
                        clear_pattern = '@' + data['player']

                    elif m[0] == '{party}':
                        is_player = 'is_player' in data and data['is_player']
                        pattern = '<a href="/' + data['party'] + '" class="player is-player-' + str(is_player) + '">' + data['party'] + '</a>'
                        clear_pattern = '@' + data['party']

                    elif m[0] == '{lvl}':
                        pattern = str(int(data['lvl']))

                    elif m[0] == '{dungeon}':
                        pattern = '<span rel="obj/3/' + str(int(data['dungeon_UID'])) + '" class="dungeon">' + data['dungeon'] + '</span>'
                        clear_pattern = pattern

                    elif m[0] == '{item}':
                        if 'item_UID' in data:
                            pattern = '<a rel="obj/1/' + str(int(data['item_UID'])) + '" class="looted-item-normal">[' + data['item'] + ']</a>'
                        else:
                            pattern = '<a rel="obj/1/' + str(data['item_id']) + '" class="looted-item">[' + data['item'] + ']</a>'

                        clear_pattern = data['item']

                    elif m[0] == '{achv}':
                        pattern = '<a class="achv" rel="/obj/5/' + str(data['achv_UID']) + '">[' + data['achv'] + ']</a>'
                        clear_pattern = pattern

                    elif m[0] == '{spell}':
                        pattern = '<a class="achv" rel="/obj/10/' + str(data['spell_UID']) + '">[' + data['spell'] + ']</a>'

                    elif m[0] == '{poi}':
                        pattern = '<span class="poi" rel="/obj/9/' + str(data['poi_UID']) + '">[' + data['poi'] + ']</span>'

                    elif m[0] == '{quest}':
                        pattern = '<span class="quest" rel="/obj/13/' + str(data['quest_UID']) + '">[' + data['quest'] + ']</span>'

                    elif m[0] == '{winner_guild}':
                        pattern = '<span class="guild" rel="/obj/11/' + str(data['winner_guild']) + '">[' + data['winner_guild_name'] + ']</span>'

                    elif m[0] == '{looser_guild}':
                        pattern = '<span class="guild" rel="/obj/11/' + str(data['looser_guild']) + '">[' + data['looser_guild_name'] + ']</span>'

                    elif m[0] == '{winner_faction}':
                        pattern = '<span class="guild" rel="/obj/12/' + str(data['winner_faction']) + '">[' + data['winner_faction_name'] + ']</span>'

                    elif m[0] == '{looser_faction}':
                        pattern = '<span class="guild" rel="/obj/12/' + str(data['looser_faction']) + '">[' + data['looser_faction_name'] + ']</span>'

                    if not clear_pattern:
                        clear_pattern = pattern

                clear_text = re.sub(m[0], clear_pattern, clear_text)
                text = re.sub(m[0], pattern, text)

            item['message'] = text
            item['clear_message'] = clear_text

            item['id'] = count
            if with_time:
                item['time'] = getReadbleTime(item['data']['time'])

    return messages


def prettyItemBonus(item, stats_names):
    primary = ''

    if item['type'] in [1, 2, 3]:
        primary_stat = 'DMG'
    else:
        primary_stat = 'DEF'

    if primary_stat in item['bonus']:
        if primary_stat == 'DMG':
            primary = str(item['bonus'][primary_stat] - 1) + ' &#8212; ' + str(
                item['bonus'][primary_stat] + 1) + ' Damage'
        else:
            primary = str(item['bonus'][primary_stat]) + ' Armor'

        del item['bonus'][primary_stat]

    bonus_data = []
    for statname in item['bonus']:
        if int(item['bonus'][statname]) > 0:
            bonus_data.append({
            'name': stats_names[statname],
            'value': int(item['bonus'][statname])
            })

    response = '<pri>' + primary + '</pri>'

    for stat in bonus_data:
        if int(stat['value']) > 0:
            response += "<s>+" + str(stat['value']) + " " + stat['name'] + "</s>"

    return {'stat_parsed': bonus_data, 'primary': primary, 'bonus_stats': response}


def formatTextareaInput(text):
    tags_removed = re.sub(RE_TAGS, '', text).strip()
    return re.sub(RE_PARAGRAPH, '<br>', tags_removed)


def getRelativeDate(input, utc_offset=0):
    date = datetime.datetime.fromtimestamp(input + utc_offset)
    localtime = datetime.datetime.fromtimestamp(utc_offset + time.time())

    datef = '%d %b'
    strf = ' %H:%M'

    if date.month == localtime.month:
        if date.day == localtime.day:
            datef = 'Today'
        elif date.day - localtime.day == 1:
            datef = 'Tomorrow'

    return date.strftime(datef + strf)


def getDisplayPages(current_page, total_pages, max):
    if total_pages > 1:

        if current_page > total_pages:
            current_page = 1

        display_pages = []
        if current_page == 1:
            for i in range(1, max + 1):
                if i <= total_pages:
                    display_pages.append(i)

        elif current_page == total_pages:
            for i in range(1, max + 1):
                if (total_pages - 10 + i) >= 1:
                    display_pages.append(total_pages - 10 + i)

        else:
            for i in range(1, max + 1):
                if current_page - 5 + i > 0:
                    if current_page - 5 + i <= total_pages:
                        display_pages.append(current_page - 5 + i)

        if display_pages[1] != 2:
            display_pages = [1, '.'] + display_pages

        if display_pages[-2] != total_pages - 1:
            display_pages = display_pages + ['.', total_pages]

    else:
        display_pages = [1]

    return display_pages


def formatOutput(text):
    return re.sub(RE_OUT_FORMAT, '%27', text)


def inCircle(center_x, center_y, radius, x, y):
    square_dist = (center_x - x) ** 2 + (center_y - y) ** 2
    return square_dist <= radius ** 2

