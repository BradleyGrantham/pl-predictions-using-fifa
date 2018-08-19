import os

import numpy as np
import pandas as pd
from tqdm import tqdm

from fifa_ratings_predictor.data_methods import read_fixtures_data, normalise_features
from fifa_ratings_predictor.model import NeuralNet

PREDICTED_LINEUPS2 = {'afc-bournemouth': np.array([80, 76, 77, 78, 76, 0, 0, 68, 73, 76, 0, 0, 0, 0, 74, 77, 77, 0]),
                      'arsenal': np.array([85, 80, 83, 80, 85, 0, 0, 78, 83, 87, 0, 0, 0, 0, 87, 84, 84, 0]),
                      'brighton-hove-albion': np.array(
                          [78, 76, 76, 73, 74, 0, 0, 76, 72, 78, 75, 0, 0, 0, 78, 79, 0, 0]),
                      'burnley': np.array([78, 79, 76, 78, 80, 0, 0, 78, 78, 74, 77, 0, 0, 0, 77, 77, 0, 0]),
                      'cardiff-city': np.array([72, 74, 75, 75, 71, 0, 0, 72, 74, 74, 0, 0, 0, 0, 72, 75, 75, 0]),
                      'chelsea': np.array([82, 86, 82, 84, 82, 0, 0, 85, 88, 82, 0, 0, 0, 0, 91, 84, 84, 0]),
                      'crystal-palace': np.array([77, 80, 78, 75, 70, 0, 0, 78, 72, 76, 0, 0, 0, 0, 78, 82, 79, 0]),
                      'everton': np.array([80, 81, 80, 79, 80, 0, 0, 80, 81, 80, 0, 0, 0, 0, 80, 79, 78, 0]),
                      'fulham': np.array([80, 72, 75, 75, 77, 0, 0, 82, 75, 78, 0, 0, 0, 0, 79, 74, 70, 0]),
                      'huddersfield-town': np.array([75, 73, 76, 75, 76, 0, 0, 71, 75, 73, 70, 0, 0, 0, 69, 76, 0, 0]),
                      'leicester-city': np.array([82, 75, 73, 79, 76, 0, 0, 80, 84, 81, 75, 0, 0, 0, 82, 77, 0, 0]),
                      'liverpool': np.array([84, 75, 84, 80, 79, 0, 0, 81, 88, 84, 0, 0, 0, 0, 85, 84, 87, 0]),
                      'manchester-city': np.array([85, 84, 85, 85, 79, 0, 0, 85, 91, 89, 0, 0, 0, 0, 85, 89, 85, 0]),
                      'manchester-united': np.array([91, 83, 79, 81, 79, 0, 0, 85, 81, 88, 0, 0, 0, 0, 86, 88, 81, 0]),
                      'newcastle-united': np.array([75, 76, 74, 78, 78, 0, 0, 78, 76, 74, 75, 0, 0, 0, 75, 75, 0, 0]),
                      'southampton': np.array([76, 78, 79, 71, 76, 0, 0, 77, 77, 78, 79, 76, 0, 0, 78, 0, 0, 0]),
                      'tottenham-hotspur': np.array([88, 81, 86, 85, 81, 0, 0, 81, 88, 84, 84, 0, 0, 0, 88, 84, 0, 0]),
                      'watford': np.array([80, 76, 77, 76, 74, 76, 0, 76, 80, 79, 0, 0, 0, 0, 77, 76, 0, 0]),
                      'west-ham-united': np.array([78, 76, 76, 75, 78, 0, 0, 81, 81, 81, 81, 0, 0, 0, 81, 81, 0, 0]),
                      'wolverhampton-wanderers': np.array(
                          [83, 71, 72, 76, 73, 0, 0, 78, 82, 78, 0, 0, 0, 0, 78, 77, 75, 0])}


class SeasonSimulator:

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

    def __init__(self, match_fixtures, predicted_lineups, model_path, write_to_csv=False,
                 csv_filepath=None):
        self.predicted_lineups = predicted_lineups
        self.fixtures = match_fixtures
        self.write_to_csv = write_to_csv
        self.csv_filepath = csv_filepath
        self.model_path = model_path

        self.total_points = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.wins = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.draws = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.losses = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.league_wins = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.relegation = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.top_4 = dict.fromkeys(self.predicted_lineups.keys(), 0)

    def get_match_probabilities(self, match_fixtures, verbose=False):
        feature_vectors = []

        net = NeuralNet()

        for fixture in tqdm(match_fixtures, desc='Getting match probabilities...', disable=not verbose):
            home_team, away_team = fixture['home team'], fixture['away team']
            feature_vectors.append(np.hstack((self.predicted_lineups[home_team], self.predicted_lineups[
                away_team])).reshape(
                (1, 36)))

        predictions = net.predict(np.vstack((x for x in feature_vectors)), model_name=self.model_path)

        match_probabilities = [x for x in predictions]

        return match_probabilities

    def run_season(self, season_fixtures, match_results):
        assert len(season_fixtures) == len(match_results), "Each fixture must have it's '1X2 probabilities"
        league_points = dict.fromkeys(self.predicted_lineups.keys(), 0)

        for fixture, result in zip(season_fixtures, match_results):

            home_team, away_team = fixture['home team'], fixture['away team']

            if result == '1':
                self.total_points[home_team] += 3
                league_points[home_team] += 3
                self.wins[home_team] += 1
                self.losses[away_team] += 1
            elif result == 'X':
                self.total_points[home_team] += 1
                self.total_points[away_team] += 1
                league_points[home_team] += 1
                league_points[away_team] += 1
                self.draws[home_team] += 1
                self.draws[away_team] += 1
            elif result == '2':
                self.total_points[away_team] += 3
                league_points[away_team] += 3
                self.wins[away_team] += 1
                self.losses[home_team] += 1
        league_positions = sorted(league_points.items(), key=lambda x: x[1], reverse=True)
        self.league_wins[league_positions[0][0]] += 1
        for team, points in league_positions[:4]:
            self.top_4[team] += 1
        for team, points in league_positions[-3:]:
            self.relegation[team] += 1

    def normalise_season_values(self, number_of_simulations):
        for k in self.total_points.keys():
            self.total_points[k] = self.total_points[k] / number_of_simulations
            self.wins[k] = self.wins[k] / number_of_simulations
            self.draws[k] = self.draws[k] / number_of_simulations
            self.losses[k] = self.losses[k] / number_of_simulations
            self.league_wins[k] = self.league_wins[k] / number_of_simulations
            self.top_4[k] = self.top_4[k] / number_of_simulations
            self.relegation[k] = self.relegation[k] / number_of_simulations

    def convert_to_pandas(self, write_to_csv=False):
        df = pd.DataFrame(
            [self.total_points, self.wins, self.draws, self.losses, self.league_wins, self.top_4, self.relegation],
            index=['Points', 'Wins',
                   'Draws', 'Losses',
                   '1st Place',
                   'Top 4',
                   'Relegation']).T

        if write_to_csv:
            df.sort_values(by='Points', ascending=False).round(decimals=2).to_csv(
                self.csv_filepath)

        return df.sort_values(by='Points', ascending=False).round(decimals=2)

    @staticmethod
    def get_match_results_from_probabilities(match_probabilities, number_of_simulations):
        return [np.random.choice(['1', 'X', '2'], size=number_of_simulations, p=match_probability) for
                match_probability in match_probabilities]

    def simulate_monte_carlo(self, number_of_simulations, verbose=False, normalise=True):

        for k, v in self.predicted_lineups.items():
            self.predicted_lineups[k] = normalise_features(v)

        probabilities = self.get_match_probabilities(self.fixtures, verbose=verbose)

        results = self.get_match_results_from_probabilities(probabilities, number_of_simulations)

        for i in tqdm(range(number_of_simulations), desc='running_simulations', disable=not verbose):
            self.run_season(self.fixtures, [x[i] for x in results])

        if normalise:
            self.normalise_season_values(number_of_simulations)

        df = self.convert_to_pandas(write_to_csv=self.write_to_csv)

        return df


if __name__ == '__main__':
    fixtures2 = read_fixtures_data()
    sim = SeasonSimulator(fixtures2, PREDICTED_LINEUPS2, model_path='./models/E0/deep')
    print(sim.simulate_monte_carlo(10000, verbose=True))
