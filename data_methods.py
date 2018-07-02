import json
import datetime

import constants


def read_player_data():
    with open('./data/players-by-team.json') as json_file:
        data = json.load(json_file)

    return data


def read_match_data():
    with open('./data/matchlineups-pi.json') as json_file:
        data = json.load(json_file)

    return data


def convert_date_to_datetime_object(date):
    return datetime.datetime.strptime(date, '%d %B %Y')


def assign_season_to_match(date):

    date = convert_date_to_datetime_object(date)

    year = date.year
    month = date.month
    if month in [7, 8, 9, 10, 11, 12]:
        season = str(year) + '-' + str(year + 1)
    else:
        season = str(year - 1) + '-' + str(year)
    return season


def assign_season_to_player(url):
    url = url.split('/')[-2]
    season = constants.PLAYER_URL_TO_SEASON.get(url, '2017-2018')
    return season


def assign_guids(data):
    for i, player in enumerate(data):
        player['guid'] = i
    guid_conversion = {player['guid']: player for player in data}
    return guid_conversion


def assign_general_position(position):
    return constants.EXACT_TO_GENERIC[position]


def assign_odds_to_match():
    # TODO
    pass
