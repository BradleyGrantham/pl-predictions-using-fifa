# The idea of this script is to test how much money we would have made or lost
# by using the 2017-2018 season and betting to make £2 whenever we find value

from collections import namedtuple
import os

import numpy as np
import matplotlib.pyplot as plt

import fifa_ratings_predictor.constants as constants
from fifa_ratings_predictor.data_methods import read_match_data, read_player_data, normalise_features, \
    assign_odds_to_match, read_all_football_data
from fifa_ratings_predictor.matching import match_lineups_to_fifa_players, create_feature_vector_from_players
from fifa_ratings_predictor.model import NeuralNet

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

Bet = namedtuple('Bet', ['true_odds', 'predicted_odds', 'stake', 'type', 'profit', 'match'])


class BetTracker:
    def __init__(self):
        self.invested = 0
        self.pending_bet = None
        self.completed_bets = []
        self.profit = 0
        self.bankroll = 100

    def make_bet(self, bet):
        self.pending_bet = bet
        self.invested += bet.stake
        self.bankroll -= bet.stake

    def bet_won(self):
        self.profit += self.pending_bet.profit
        self.bankroll += self.pending_bet.stake + self.pending_bet.profit
        self.completed_bets.append((self.pending_bet, 'W'))
        self.pending_bet = None

    def bet_lost(self):
        self.profit -= self.pending_bet.stake
        self.completed_bets.append((self.pending_bet, 'L'))
        self.pending_bet = None

    @property
    def roi(self):
        return self.profit / self.invested


def calculate_profit(bet):
    return bet.stake * bet.odds - bet.stake


def calculate_stake(odds, method='constant profit', constant_profit=2, probability=None):
    assert method in ['constant_profit', 'kelly']
    if method == 'constant_profit':
        stake = constant_profit / (odds - 1)
    elif method == 'kelly':
        stake = ((odds * probability) - 1) / (odds - 1)
    return stake


def main():
    bet_tracker = BetTracker()

    league = 'F1'

    match_data = read_match_data(season='2017-2018', league=league)

    match_data = assign_odds_to_match(match_data, read_all_football_data(league=league))

    player_data = read_player_data(season='2017-2018')

    net = NeuralNet()

    bank = [100]

    all_odds = []

    errors = []

    cached_players = {}

    feature_vectors = []

    for match in match_data:

        try:

            home_players_matched, cached_players = match_lineups_to_fifa_players(match['info']['home lineup names'],
                                                                                 match['info']['home lineup raw names'],
                                                                                 match['info']['home lineup numbers'],
                                                                                 match['info'][
                                                                                     'home lineup nationalities'],
                                                                                 constants.LINEUP_TO_PLAYER_TEAM_MAPPINGS[
                                                                                     'ALL'][
                                                                                     match['info']['home team']],
                                                                                 match['info']['season'],
                                                                                 player_data, cached_players)

            away_players_matched, cached_players = match_lineups_to_fifa_players(match['info']['away lineup names'],
                                                                                 match['info']['away lineup raw names'],
                                                                                 match['info']['away lineup numbers'],
                                                                                 match['info'][
                                                                                     'away lineup nationalities'],
                                                                                 constants.LINEUP_TO_PLAYER_TEAM_MAPPINGS[
                                                                                     'ALL'][
                                                                                     match['info']['away team']],
                                                                                 match['info']['season'],
                                                                                 player_data, cached_players)

            home_feature_vector = create_feature_vector_from_players(home_players_matched)
            away_feature_vector = create_feature_vector_from_players(away_players_matched)

            feature_vector = np.array(home_feature_vector + away_feature_vector).reshape(-1, 36)

            feature_vectors.append(normalise_features(feature_vector))

        except Exception as exception:
            print(match['info']['date'], match['info']['home team'], match['info']['away team'])
            print(exception)
            errors.append(match['match number'])

    feature_vectors = np.vstack((x for x in feature_vectors))

    probabilities = net.predict(feature_vectors, model_name='./models/' + league + '-backtest/deep')

    match_data = [match for match in match_data if match['match number'] not in errors]

    for match, probability in zip(match_data, probabilities):

        # print(match['info']['date'], match['info']['home team'], match['info']['away team'])

        pred_home_odds, pred_draw_odds, pred_away_odds = [1 / x for x in probability]

        home_odds, draw_odds, away_odds = match['info']['home odds'], match['info']['draw odds'], match['info'][
            'away odds']

        all_odds.append((pred_home_odds, home_odds))
        all_odds.append((pred_away_odds, away_odds))

        if pred_home_odds < home_odds < 3.2 and 0.02 <= probability[0] - 1 / home_odds:
            stake = calculate_stake(home_odds, probability=1 / pred_home_odds, method='kelly',
                                    constant_profit=20) * bet_tracker.bankroll
            profit = stake * home_odds - stake
            bet = Bet(true_odds=home_odds, predicted_odds=pred_home_odds, stake=stake, profit=profit, match=match,
                      type='home')
            bet_tracker.make_bet(bet)
            if match['info']['home goals'] > match['info']['away goals']:
                bet_tracker.bet_won()
            else:
                bet_tracker.bet_lost()
            bank.append(bet_tracker.bankroll)
        elif pred_away_odds < away_odds < 3.2 and 0.02 <= probability[2] - 1 / away_odds:
            stake = calculate_stake(away_odds, probability=1 / pred_away_odds, method='kelly',
                                    constant_profit=20) * bet_tracker.bankroll
            profit = stake * away_odds - stake
            bet = Bet(true_odds=away_odds, predicted_odds=pred_away_odds, stake=stake, profit=profit, match=match,
                      type='away')
            bet_tracker.make_bet(bet)
            if match['info']['home goals'] < match['info']['away goals']:
                bet_tracker.bet_won()
            else:
                bet_tracker.bet_lost()
            bank.append(bet_tracker.bankroll)

    return bet_tracker, bank, all_odds


def plot_backtest(bankroll, roi, plot_title, name='graph.png'):
    import matplotlib.font_manager
    import matplotlib as mpl

    font = {'size': 6}

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

    propies = dict(boxstyle='round', facecolor='#225599')
    fig = plt.figure()
    ax = plt.axes()
    plt.plot(np.arange(len(bankroll)), bankroll, c='#113355')
    ax.text(0.05, 0.95, 'ROI: {0:.2%}'.format(roi), transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=propies, fontproperties=props, color='white')
    fig.set_facecolor('#aabbcc')
    ax.set_facecolor('#aabbcc')
    ax.set_title(plot_title, fontproperties=props, color="#223355")
    plt.savefig(name, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())


if __name__ == '__main__':
    tracker, bankroll, odds = main()
