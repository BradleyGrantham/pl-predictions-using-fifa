# The idea of this script is to test how much money we would have made or lost
# by using the 2017-2018 season and betting to make £2 whenever we find value

from collections import namedtuple
import os

import numpy as np

import constants
from data_methods import read_match_data, read_player_data, normalise_features
from matching import match_lineups_to_fifa_players, create_feature_vector_from_players
from model import NeuralNet
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

    match_data = read_match_data(season='2017-2018')

    player_data = read_player_data(season='2017-2018')

    net = NeuralNet()

    for match in match_data:

        print(match['info']['date'], match['info']['home team'], match['info']['away team'])

        home_players_matched = match_lineups_to_fifa_players(match['info']['home lineup names'],
                                                             match['info']['home lineup numbers'],
                                                             match['info']['home lineup nationalities'],
                                                             constants.LINEUP_TO_PLAYER_TEAM_MAPPINGS['ALL'][
                                                                 match['info']['home team']], match['info']['season'],
                                                             player_data)
        away_players_matched = match_lineups_to_fifa_players(match['info']['away lineup names'],
                                                             match['info']['away lineup numbers'],
                                                             match['info']['away lineup nationalities'],
                                                             constants.LINEUP_TO_PLAYER_TEAM_MAPPINGS['ALL'][
                                                                 match['info']['away team']], match['info']['season'],
                                                             player_data)

        home_feature_vector = create_feature_vector_from_players(home_players_matched)
        away_feature_vector = create_feature_vector_from_players(away_players_matched)

        feature_vector = np.array(home_feature_vector + away_feature_vector).reshape(-1, 36)

        feature_vector = normalise_features(feature_vector)

        probabilties = net.predict(feature_vector)

        pred_home_odds, pred_draw_odds, pred_away_odds = [1 / x for x in probabilties[0]]

        home_odds, draw_odds, away_odds = match['info']['home odds'], match['info']['draw odds'], match['info'][
            'away odds']

        if pred_home_odds < home_odds < 3.2 and 0.05 <= home_odds - pred_home_odds <= 0.4:
            stake = calculate_stake(home_odds, probability=1 / pred_home_odds, method='kelly') * bet_tracker.bankroll
            profit = stake * home_odds - stake
            bet = Bet(true_odds=home_odds, predicted_odds=pred_home_odds, stake=stake, profit=profit, match=match,
                      type='home')
            bet_tracker.make_bet(bet)
            if match['info']['home goals'] > match['info']['away goals']:
                bet_tracker.bet_won()
            else:
                bet_tracker.bet_lost()
        elif pred_away_odds < away_odds < 3.2 and 0.05 <= away_odds - pred_away_odds >= 0.4:
            stake = calculate_stake(away_odds, probability=1 / pred_away_odds, method='kelly') * bet_tracker.bankroll
            profit = stake * away_odds - stake
            bet = Bet(true_odds=away_odds, predicted_odds=pred_away_odds, stake=stake, profit=profit, match=match,
                      type='away')
            bet_tracker.make_bet(bet)
            if match['info']['home goals'] < match['info']['away goals']:
                bet_tracker.bet_won()
            else:
                bet_tracker.bet_lost()

    return bet_tracker


if __name__ == '__main__':
    tracker = main()
