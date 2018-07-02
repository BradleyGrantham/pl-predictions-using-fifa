# The idea of this script is to test how much money we would have made or lost
# by using the 2017-2018 season and betting to make £2 whenever we find value

from collections import namedtuple

import numpy as np

from data_methods import read_match_data, read_player_data, convert_date_to_datetime_object

# calculate odds based on lineup
# if value -> place bet to make £2
# take amount from 'bank'
# then check score, if win, add to 'bank'
# do this for all games


Bet = namedtuple('Bet', ['odds', 'stake', 'profit'])


class BetTracker:
    def __init__(self):
        self.invested = 0
        self.pending_bet = None
        self.completed_bets = []
        self.profit = 0

    def make_bet(self, bet):
        self.pending_bet = bet
        self.invested += bet.stake

    def bet_won(self):
        self.profit += self.pending_bet.profit
        self.completed_bets.append((self.pending_bet, 'W'))
        self.pending_bet = None

    def bet_lost(self):
        self.completed_bets.append((self.pending_bet, 'L'))
        self.pending_bet = None

    @property
    def roi(self):
        return self.profit / self.invested


def calculate_profit(bet):
    return bet.stake * bet.odds - bet.stake


def calculate_stake(odds, method='constant profit', constant_profit=2):
    stake = constant_profit / (odds - 1)
    return stake


def main():

    bet_tracker = BetTracker()

    match_data = read_match_data()
    for match in match_data:
        match['info']['datetime'] = convert_date_to_datetime_object(match['info']['date'])

    match_data = sorted(match_data, key=lambda x: x['info']['datetime'])

    for match in match_data:
        home_odds = match['info']['home odds']
        if home_odds < 2.0:
            stake = calculate_stake(home_odds, method='2 pound profit')
            bet = Bet(odds=match['info']['home odds'], stake=stake, profit=2)
            bet_tracker.make_bet(bet)
            if match['info']['home goals'] > match['info']['away goals']:
                bet_tracker.bet_won()
                bet_tracker.bet_lost()

    return bet_tracker


if __name__ == '__main__':
    data = main()
