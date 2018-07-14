import numpy as np
import pandas as pd
from tqdm import tqdm

from data_methods import read_fixtures_data, normalise_features
from model import NeuralNet

NUMBER_OF_SIMULATIONS = 10000

# cardiff, fulham and wolves are identical to burnley at the moment

PREDICTED_LINEUPS = {'afc-bournemouth': np.array([80, 76, 75, 77, 78, 75, 0, 75, 73, 75, 0, 0, 0, 0, 77, 69, 0, 0]),
                     'arsenal': np.array([84, 81, 83, 73, 0, 0, 0, 68, 82, 84, 77, 87, 76, 0, 87, 0, 0, 0]),
                     'brighton-hove-albion': np.array(
                         [78, 75, 74, 76, 76, 0, 0, 72, 76, 77, 78, 78, 0, 0, 74, 0, 0, 0]),
                     'burnley': np.array([78, 78, 76, 79, 80, 0, 0, 78, 78, 74, 75, 77, 0, 0, 77, 0, 0, 0]),
                     'cardiff-city': np.array([78, 78, 76, 79, 80, 0, 0, 78, 78, 74, 75, 77, 0, 0, 77, 0, 0, 0]),
                     'chelsea': np.array([89, 79, 82, 82, 82, 86, 0, 85, 88, 0, 0, 0, 0, 0, 82, 84, 91, 0]),
                     'crystal-palace': np.array([73, 75, 74, 78, 72, 65, 0, 78, 78, 76, 0, 0, 0, 0, 79, 71, 0, 0]),
                     'everton': np.array([80, 81, 80, 79, 80, 0, 0, 74, 81, 80, 79, 77, 0, 0, 80, 0, 0, 0]),
                     'fulham': np.array([78, 78, 76, 79, 80, 0, 0, 78, 78, 74, 75, 77, 0, 0, 77, 0, 0, 0]),
                     'huddersfield-town': np.array([75, 73, 76, 75, 76, 0, 0, 71, 75, 73, 70, 0, 0, 0, 69, 76, 0, 0]),
                     'leicester-city': np.array([82, 75, 73, 79, 76, 0, 0, 80, 84, 81, 75, 0, 0, 0, 82, 77, 0, 0]),
                     'liverpool': np.array([80, 75, 79, 80, 84, 0, 0, 81, 81, 80, 0, 0, 0, 0, 85, 87, 84, 0]),
                     'manchester-city': np.array([85, 84, 85, 83, 70, 0, 0, 85, 91, 89, 0, 0, 0, 0, 84, 89, 85, 0]),
                     'manchester-united': np.array([91, 83, 79, 81, 78, 0, 0, 85, 68, 88, 81, 0, 0, 0, 86, 88, 0, 0]),
                     'newcastle-united': np.array([75, 76, 74, 78, 78, 0, 0, 78, 76, 74, 75, 0, 0, 0, 75, 75, 0, 0]),
                     'southampton': np.array([76, 78, 79, 71, 76, 0, 0, 77, 77, 76, 79, 76, 0, 0, 75, 0, 0, 0]),
                     'tottenham-hotspur': np.array([88, 81, 81, 82, 86, 0, 0, 81, 88, 84, 84, 84, 0, 0, 88, 0, 0, 0]),
                     'watford': np.array([80, 76, 77, 76, 74, 76, 0, 76, 80, 79, 0, 0, 0, 0, 77, 76, 0, 0]),
                     'west-ham-united': np.array([78, 76, 74, 75, 78, 0, 0, 76, 76, 81, 81, 0, 0, 0, 79, 81, 0, 0]),
                     'wolverhampton-wanderers': np.array(
                         [78, 78, 76, 79, 80, 0, 0, 78, 78, 74, 75, 77, 0, 0, 77, 0, 0, 0])}

TOTAL_POINTS = dict.fromkeys(PREDICTED_LINEUPS.keys(), 0)
WINS = dict.fromkeys(PREDICTED_LINEUPS.keys(), 0)
DRAWS = dict.fromkeys(PREDICTED_LINEUPS.keys(), 0)
LOSSES = dict.fromkeys(PREDICTED_LINEUPS.keys(), 0)
LEAGUE_WINS = dict.fromkeys(PREDICTED_LINEUPS.keys(), 0)
RELEGATION = dict.fromkeys(PREDICTED_LINEUPS.keys(), 0)
TOP_4 = dict.fromkeys(PREDICTED_LINEUPS.keys(), 0)


def get_match_probabilities(match_fixtures):
    feature_vectors = []

    net = NeuralNet()

    for fixture in tqdm(match_fixtures, desc='Getting match probabilities...'):
        home_team, away_team = fixture['home team'], fixture['away team']
        feature_vectors.append(np.hstack((PREDICTED_LINEUPS[home_team], PREDICTED_LINEUPS[away_team])).reshape((1, 36)))

    predictions = net.predict(np.vstack((x for x in feature_vectors)))

    match_probabilities = [x for x in predictions]

    return match_probabilities


def run_season(season_fixtures, fixture_probabilities):
    assert len(season_fixtures) == len(fixture_probabilities), "Each fixture must have it's '1X2 probabilities"
    league_points = dict.fromkeys(PREDICTED_LINEUPS.keys(), 0)
    for fixture, match_probabilities in zip(season_fixtures, fixture_probabilities):

        home_team, away_team = fixture['home team'], fixture['away team']

        result = np.random.choice(['1', 'X', '2'], p=match_probabilities)

        if result == '1':
            TOTAL_POINTS[home_team] += 3
            league_points[home_team] += 3
            WINS[home_team] += 1
            LOSSES[away_team] += 1
        elif result == 'X':
            TOTAL_POINTS[home_team] += 1
            TOTAL_POINTS[away_team] += 1
            league_points[home_team] += 1
            league_points[away_team] += 1
            DRAWS[home_team] += 1
            DRAWS[away_team] += 1
        elif result == '2':
            TOTAL_POINTS[away_team] += 3
            league_points[away_team] += 3
            WINS[away_team] += 1
            LOSSES[home_team] += 1
    league_positions = sorted(league_points.items(), key=lambda x: x[1], reverse=True)
    LEAGUE_WINS[league_positions[0][0]] += 1
    for team, points in league_positions[:4]:
        TOP_4[team] += 1
    for team, points in league_positions[-3:]:
        RELEGATION[team] += 1


def normalise_season_values():
    for k in TOTAL_POINTS.keys():
        TOTAL_POINTS[k] = TOTAL_POINTS[k] / NUMBER_OF_SIMULATIONS
        WINS[k] = WINS[k] / NUMBER_OF_SIMULATIONS
        DRAWS[k] = DRAWS[k] / NUMBER_OF_SIMULATIONS
        LOSSES[k] = LOSSES[k] / NUMBER_OF_SIMULATIONS
        LEAGUE_WINS[k] = LEAGUE_WINS[k] / NUMBER_OF_SIMULATIONS
        TOP_4[k] = TOP_4[k] / NUMBER_OF_SIMULATIONS
        RELEGATION[k] = RELEGATION[k] / NUMBER_OF_SIMULATIONS


def convert_to_pandas(write_to_csv=True, return_df=False):
    df = pd.DataFrame([TOTAL_POINTS, WINS, DRAWS, LOSSES, LEAGUE_WINS, TOP_4, RELEGATION], index=['Points', 'Wins',
                                                                                                  'Draws', 'Losses',
                                                                                                  '1st Place',
                                                                                                  'Top 4',
                                                                                                  'Relegation']).T

    if write_to_csv:
        df.sort_values(by='Points', ascending=False).round(decimals=2).to_csv('./data/results/18-19-league-table-2.csv')

    if return_df:
        return df.sort_values(by='Points', ascending=False).round(decimals=2)


def main():
    fixtures = read_fixtures_data()

    for k, v in PREDICTED_LINEUPS.items():
        PREDICTED_LINEUPS[k] = normalise_features(v)

    probabilities = get_match_probabilities(fixtures)

    for _ in tqdm(range(NUMBER_OF_SIMULATIONS), desc='running_simulations'):
        run_season(fixtures, probabilities)

    normalise_season_values()

    convert_to_pandas()


if __name__ == '__main__':
    main()

