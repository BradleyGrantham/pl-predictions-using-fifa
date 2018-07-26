import numpy as np
import pandas as pd
from tqdm import tqdm

from data_methods import read_fixtures_data, normalise_features
from model import NeuralNet

NUMBER_OF_SIMULATIONS2 = 1000

PREDICTED_LINEUPS2 = {'afc-bournemouth': np.array([80, 76, 75, 77, 78, 75, 0, 75, 73, 75, 0, 0, 0, 0, 77, 69, 0, 0]),
                      'arsenal': np.array([84, 81, 83, 73, 0, 0, 0, 68, 82, 84, 77, 87, 76, 0, 87, 0, 0, 0]),
                      'brighton-hove-albion': np.array(
                          [78, 75, 74, 76, 76, 0, 0, 72, 76, 77, 78, 78, 0, 0, 74, 0, 0, 0]),
                      'burnley': np.array([78, 78, 76, 79, 80, 0, 0, 78, 78, 74, 75, 77, 0, 0, 77, 0, 0, 0]),
                      'cardiff-city': np.array([72, 74, 75, 75, 71, 0, 0, 72, 74, 74, 0, 0, 0, 0, 72, 75, 75, 0]),
                      'chelsea': np.array([82, 79, 82, 82, 82, 86, 0, 85, 88, 0, 0, 0, 0, 0, 91, 84, 84, 0]),
                      'crystal-palace': np.array([73, 75, 74, 78, 72, 65, 0, 78, 78, 76, 0, 0, 0, 0, 79, 71, 0, 0]),
                      'everton': np.array([80, 81, 80, 79, 80, 0, 0, 74, 81, 80, 79, 77, 0, 0, 80, 0, 0, 0]),
                      'fulham': np.array([73, 73, 69, 71, 75, 0, 0, 74, 79, 75, 0, 0, 0, 0, 76, 79, 81, 0]),
                      'huddersfield-town': np.array([75, 73, 76, 75, 76, 0, 0, 71, 75, 73, 70, 0, 0, 0, 69, 76, 0, 0]),
                      'leicester-city': np.array([82, 75, 73, 79, 76, 0, 0, 80, 84, 81, 75, 0, 0, 0, 82, 77, 0, 0]),
                      'liverpool': np.array([80, 75, 79, 80, 84, 0, 0, 81, 81, 80, 0, 0, 0, 0, 85, 87, 84, 0]),
                      'manchester-city': np.array([85, 84, 85, 83, 70, 0, 0, 85, 91, 89, 0, 0, 0, 0, 84, 89, 85, 0]),
                      'manchester-united': np.array([91, 83, 79, 81, 78, 0, 0, 85, 82, 88, 81, 0, 0, 0, 86, 88, 0, 0]),
                      'newcastle-united': np.array([75, 76, 74, 78, 78, 0, 0, 78, 76, 74, 75, 0, 0, 0, 75, 75, 0, 0]),
                      'southampton': np.array([76, 78, 79, 71, 76, 0, 0, 77, 77, 76, 79, 76, 0, 0, 75, 0, 0, 0]),
                      'tottenham-hotspur': np.array([88, 81, 81, 82, 86, 0, 0, 81, 88, 84, 84, 84, 0, 0, 88, 0, 0, 0]),
                      'watford': np.array([80, 76, 77, 76, 74, 76, 0, 76, 80, 79, 0, 0, 0, 0, 77, 76, 0, 0]),
                      'west-ham-united': np.array([78, 76, 74, 75, 78, 0, 0, 76, 76, 81, 81, 0, 0, 0, 79, 81, 0, 0]),
                      'wolverhampton-wanderers': np.array(
                          [72, 74, 72, 74, 78, 74, 0, 77, 82, 0, 0, 0, 0, 0, 75, 82, 78, 0])}


class SeasonSimulator:

    def __init__(self, match_fixtures, predicted_lineups, number_of_simulations, write_to_csv=False):
        self.predicted_lineups = predicted_lineups
        self.number_of_simulations = number_of_simulations
        self.fixtures = match_fixtures
        self.write_to_csv = write_to_csv

        self.total_points = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.wins = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.draws = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.losses = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.league_wins = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.relegation = dict.fromkeys(self.predicted_lineups.keys(), 0)
        self.top_4 = dict.fromkeys(self.predicted_lineups.keys(), 0)

    def get_match_probabilities(self, match_fixtures):
        feature_vectors = []

        net = NeuralNet()

        for fixture in tqdm(match_fixtures, desc='Getting match probabilities...'):
            home_team, away_team = fixture['home team'], fixture['away team']
            feature_vectors.append(np.hstack((self.predicted_lineups[home_team], self.predicted_lineups[
                away_team])).reshape(
                (1, 36)))

        predictions = net.predict(np.vstack((x for x in feature_vectors)), model_name='deep-models-all/deep')

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

    def normalise_season_values(self):
        for k in self.total_points.keys():
            self.total_points[k] = self.total_points[k] / self.number_of_simulations
            self.wins[k] = self.wins[k] / self.number_of_simulations
            self.draws[k] = self.draws[k] / self.number_of_simulations
            self.losses[k] = self.losses[k] / self.number_of_simulations
            self.league_wins[k] = self.league_wins[k] / self.number_of_simulations
            self.top_4[k] = self.top_4[k] / self.number_of_simulations
            self.relegation[k] = self.relegation[k] / self.number_of_simulations

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
                './data/results/18-19-league-table-trained-on-all.csv')

        return df.sort_values(by='Points', ascending=False).round(decimals=2)

    def get_match_results_from_probabilities(self, match_probabilities):
        return [np.random.choice(['1', 'X', '2'], size=self.number_of_simulations, p=match_probability) for
                match_probability in match_probabilities]

    def simulate_monte_carlo(self):

        for k, v in self.predicted_lineups.items():
            self.predicted_lineups[k] = normalise_features(v)

        probabilities = self.get_match_probabilities(self.fixtures)

        results = self.get_match_results_from_probabilities(probabilities)

        for i in tqdm(range(self.number_of_simulations), desc='running_simulations'):
            self.run_season(self.fixtures, [x[i] for x in results])

        self.normalise_season_values()

        df = self.convert_to_pandas(write_to_csv=self.write_to_csv)

        return df


if __name__ == '__main__':
    fixtures2 = read_fixtures_data()
    sim = SeasonSimulator(fixtures2, PREDICTED_LINEUPS2, NUMBER_OF_SIMULATIONS2)
    d = sim.simulate_monte_carlo()
