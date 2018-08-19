#!/usr/bin/python3

import datetime
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from slugify import slugify
import matplotlib as mpl
mpl.use('agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager
import tweepy
from pyvirtualdisplay import Display
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from fifa_ratings_predictor.one_match_simulator import one_match_simulator
from fifa_ratings_predictor.backtesting import calculate_stake
from fifa_ratings_predictor.matching import match_lineups_to_fifa_players, create_feature_vector_from_players
from fifa_ratings_predictor.data_methods import read_player_data
import fifa_ratings_predictor.constants as constants


def deslugify(s):
    return ' '.join(s.split('-')).title()


def get_lineups_from_flashscores():
    flash_scores_url = 'http://www.flashscores.co.uk/football/'

    display = Display(visible=0, size=(1024,768))
    display.start()
    driver = webdriver.Firefox('/usr/local/bin/')
    driver.get(flash_scores_url)
    time.sleep(10)
    html_source = driver.page_source

    soup = BeautifulSoup(html_source, 'lxml')

    t_heads = soup.find_all('thead')

    matches = []

    for t_head in t_heads:
        if t_head.find_all('span', {'class', 'tournament_part'})[0].text == 'Premier League' \
                and t_head.find_all('span', {'class', 'country_part'})[0].text == 'ENGLAND: ':
            matches = t_head.next_sibling

    if not matches:
        driver.quit()
        return []

    match_ids = matches.find_all('tr')
    home_teams = matches.find_all('span', {'class': 'padr'})
    away_teams = matches.find_all('span', {'class': 'padl'})
    times = matches.find_all('td', {'class': 'cell_ad'})

    now = datetime.datetime.now()

    match_info = []

    for id_, home_team, away_team, time_ in zip(match_ids, home_teams, away_teams, times):

        home_team = slugify(home_team.text)
        away_team = slugify(away_team.text)
        time_ = datetime.datetime.combine(datetime.date.today(), datetime.datetime.strptime(time_.text, '%H:%M').time())

        match_id = id_.get('id').split('_')[-1]

        match_url = 'https://www.flashscores.co.uk/match/{}/#lineups;1'.format(match_id)

        time_diff_in_hours = (time_ - now).seconds / 3600

        if 0.1 < time_diff_in_hours < 1:

            driver.get(match_url)
            time.sleep(10)
            html_source = driver.page_source

            soup = BeautifulSoup(html_source, 'lxml')

            body = soup.find_all('tbody')[3]

            home_lineup_names = []
            home_lineup_numbers = []
            home_lineup_nationalities = []

            away_lineup_names = []
            away_lineup_numbers = []
            away_lineup_nationalities = []

            for player in body.find_all('td', {'class': 'summary-vertical fl'})[:11]:
                home_lineup_numbers.append(player.find('div').text)
                home_lineup_nationalities.append(player.find('span').get('title'))
                home_lineup_names.append(slugify(player.find('a').text))

            for player in body.find_all('td', {'class': 'summary-vertical fr'})[:11]:
                away_lineup_numbers.append(player.find('div').text)
                away_lineup_nationalities.append(slugify(player.find('span').get('title')))
                away_lineup_names.append(slugify(player.find('a').text))

            match_dict = {'home_team': home_team, 'home_lineup_names': home_lineup_names,
                          'home_lineup_numbers': home_lineup_numbers,
                          'home_lineup_nationalities': home_lineup_nationalities,
                          'away_team': away_team, 'away_lineup_names': away_lineup_names,
                          'away_lineup_numbers': away_lineup_numbers,
                          'away_lineup_nationalities': away_lineup_nationalities}

            match_info.append(match_dict)

    driver.quit()
    display.stop()
    return match_info


def get_odds_checker_odds(match, league='premier-league'):

    home_team_name = constants.FLASH_SCORES_TEAM_TO_ODDS_CHECKER[match['home_team']]
    away_team_name = constants.FLASH_SCORES_TEAM_TO_ODDS_CHECKER[match['away_team']]
    odds_url = 'https://www.oddschecker.com/football/english/{}/{}-v-{}/winner'.format(league, home_team_name, away_team_name)

    display = Display(visible=0, size=(1024, 768))
    display.start()
    driver = webdriver.Firefox('/usr/local/bin/')
    driver.get(odds_url)
    time.sleep(10)
    html_source = driver.page_source
    driver.quit()
    display.stop()

    soup = BeautifulSoup(html_source, 'lxml')

    home_team_for_soup = deslugify(home_team_name)
    away_team_for_soup = deslugify(away_team_name)

    if home_team_for_soup == 'Cardiff City':
        home_team_for_soup = 'Cardiff City'

    if away_team_for_soup == 'Cardiff City':
        away_team_for_soup = 'Cardiff City'

    home = soup.find('tr', {'data-bname': home_team_for_soup})
    draw = soup.find('tr', {'data-bname': 'Draw'})
    away = soup.find('tr', {'data-bname': away_team_for_soup})

    home_bookies = home.get('data-best-bks')
    home_odds = float(home.get('data-best-dig'))

    draw_bookies = draw.get('data-best-bks')
    draw_odds = float(draw.get('data-best-dig'))

    away_bookies = away.get('data-best-bks')
    away_odds = float(away.get('data-best-dig'))

    return [home_bookies, draw_bookies, away_bookies], [1 / home_odds, 1 / draw_odds, 1 / away_odds]


def plot_bubble_plot(match, my_probs, bookies_probs, bookies, filepath):
    font = {'size': 10}

    mpl.rcParams['figure.dpi'] = 300
    mpl.rc('font', **font)
    mpl.rcParams.update({'text.color': "#333344",
                         'axes.labelcolor': "#333344"})

    flist = matplotlib.font_manager.get_fontconfig_fonts()
    for fname in flist:
        try:
            s = matplotlib.font_manager.FontProperties(fname=fname).get_name()
            if 'bank' in s:
                props = matplotlib.font_manager.FontProperties(fname=fname)
        except RuntimeError:
            pass

    fig = plt.figure()
    ax = plt.axes()
    plt.scatter([1.3, 1.4, 1.5], [1.64] * 3, s=[x * 12000 for x in bookies_probs], c="#113355", label='best bookies')
    plt.scatter([1.3, 1.4, 1.5], [1.6] * 3, s=[x * 12000 for x in my_probs], c="#0055aa", label='model')

    # plt.yticks([1.6, 1.64], ['', f'bookies:{bookies[0]}, {bookies[1]}, {bookies[2]}'], fontproperties=props,
    #            color="#223355")
    plt.yticks([])
    plt.xticks([1.3, 1.4, 1.5], ['1', 'X', '2'], fontproperties=props, color="#223355")
    plt.ylim([1.58, 1.66])
    fig.set_edgecolor('red')
    fig.set_facecolor('#aabbcc')
    ax.set_facecolor('#aabbcc')

    for label, x, y in zip(["{0:.0%}".format(my_probs[0]), "{0:.0%}".format(my_probs[1]), "{0:.0%}".format(my_probs[2]
                                                                                                           )], [1.3,
                                                                                                                1.4,
                                                                                                                1.5],
                           [1.6] * 3):
        plt.annotate(
            label,
            xy=(x, y), xytext=(x, y), ha='center', va='center', color='white', fontproperties=props)
    for label, x, y in zip(["{0:.0%}".format(bookies_probs[0]), "{0:.0%}".format(bookies_probs[1]), "{0:.0%}".format(
            bookies_probs[2])],
                           [1.3,
                            1.4, 1.5],
                           [1.64] * 3):
        plt.annotate(
            label,
            xy=(x, y), xytext=(x, y), ha='center', va='center', color='white', fontproperties=props)

    ax.spines['bottom'].set_color('#aabbcc')
    ax.spines['top'].set_color('#aabbcc')
    ax.spines['right'].set_color('#aabbcc')
    ax.spines['left'].set_color('#aabbcc')
    ax.tick_params(axis=u'both', which=u'both', length=0)
    ax.set_title("{} vs. {}".format(deslugify(match['home_team']), deslugify(match['away_team'])),
                 fontproperties=props,
                 color="#223355", fontsize=12)
    lgnd = ax.legend(loc="best", numpoints=1, fontsize=6)
    lgnd.legendHandles[0]._sizes = [10]
    lgnd.legendHandles[1]._sizes = [10]

    filepath = filepath

    plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    # plt.show()


def tweet_plot(filepath, message=''):
    auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    api.update_with_media(filepath, status=message)


def write_to_google_sheet(row):
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('./client_secret.json', scope)
    client = gspread.authorize(credentials)

    sheet = client.open("2017-2018-PL-tips").sheet1
    sheet.append_row(row)


if __name__ == '__main__':
    data = read_player_data(season='2017-2018')
    cached_players = {}

    for gui, name in data.items():
        if 'pereira' in name['name'] and name['general position'] == 'goalkeeper':
            gui_to_delete = gui

    del data[gui_to_delete]

    matches = get_lineups_from_flashscores()

    for match in matches:

        player_home_team = constants.FLASH_SCORES_TEAM_TO_PLAYER_RATINGS[match['home_team']]
        player_away_team = constants.FLASH_SCORES_TEAM_TO_PLAYER_RATINGS[match['away_team']]

        home_players_matched, cached_players = match_lineups_to_fifa_players(match['home_lineup_names'],
                                                                             match['home_lineup_names'],
                                                                             match['home_lineup_numbers'],
                                                                             match['home_lineup_nationalities'],
                                                                             player_home_team, '2017-2018', data,
                                                                             cached_players)

        away_players_matched, cached_players = match_lineups_to_fifa_players(match['away_lineup_names'],
                                                                             match['away_lineup_names'],
                                                                             match['away_lineup_numbers'],
                                                                             match['away_lineup_nationalities'],
                                                                             player_away_team, '2017-2018', data,
                                                                             cached_players)

        home_feature_vector = create_feature_vector_from_players(home_players_matched)
        away_feature_vector = create_feature_vector_from_players(away_players_matched)

        home_goalkeeper, home_defenders, home_midfielders, home_forwards = home_feature_vector[0], \
                                                                           home_feature_vector[1:7], \
                                                                           home_feature_vector[7:14], \
                                                                           home_feature_vector[14:]

        away_goalkeeper, away_defenders, away_midfielders, away_forwards = away_feature_vector[0], \
                                                                           away_feature_vector[1:7], \
                                                                           away_feature_vector[7:14], \
                                                                           away_feature_vector[14:]

        my_probabilities = one_match_simulator([home_goalkeeper], home_defenders, home_midfielders, home_forwards,
                                            [away_goalkeeper], away_defenders, away_midfielders, away_forwards,
                                               model_name='./deep-models-all/deep')

        _, bookies_probabilities = get_odds_checker_odds(match)

        print(my_probabilities)
        print(bookies_probabilities)

        if 1 / my_probabilities[0] < 1 / bookies_probabilities[0] < 3.2 and 0.02 <= my_probabilities[0] - \
                bookies_probabilities[0]:
            stake = calculate_stake(1 / bookies_probabilities[0], probability=my_probabilities[0], method='kelly')
            selection = 1
            my_odds = 1 / my_probabilities[0]
            bookies_odds = 1 / bookies_probabilities[0]
            sheet_row = [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), match['home_team'], match['away_team'],
                         selection, my_odds, bookies_odds, stake]
            write_to_google_sheet(sheet_row)

        elif 1 / my_probabilities[2] < 1 / bookies_probabilities[2] < 3.2 and 0.02 <= my_probabilities[2] - \
                bookies_probabilities[2]:
            stake = calculate_stake(1 / bookies_probabilities[2], probability=my_probabilities[2], method='kelly')
            selection = 2
            my_odds = 1 / my_probabilities[2]
            bookies_odds = 1 / bookies_probabilities[2]
            sheet_row = [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), match['home_team'], match['away_team'],
                         selection, my_odds, bookies_odds, stake]
            write_to_google_sheet(sheet_row)

        # path = "{}-vs-{}.png".format(match['home_team'], match['away_team'])
        # plot_bubble_plot(match, my_probabilities, bookies_probabilities, _, filepath=path)
        # tweet_plot(path)
