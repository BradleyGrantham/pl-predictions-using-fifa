import fifa_ratings_predictor.constants as constants
import numpy as np
from fifa_ratings_predictor.data_methods import (
    assign_odds_to_match,
    get_goals,
    get_lineup_names,
    get_lineup_nationalities,
    get_lineup_numbers,
    get_match_odds,
    get_season,
    get_teams,
    read_all_football_data,
    read_match_data,
    read_player_data,
)


def match_lineups_to_fifa_players(lineup_names, raw_names, lineup_numbers,
                                  lineup_nationalities, team, season,
                                  fifa_data, cached):

    all_fifa_players = [player["name"] for _, player in fifa_data.items()]

    probability_dict = {raw_name: dict.fromkeys(all_fifa_players, 0)
                        for raw_name in raw_names}

    for lineup_name, raw_name, lineup_number, lineup_nationality in zip(
        lineup_names, raw_names, lineup_numbers, lineup_nationalities
    ):

        try:
            probability_dict[raw_name][cached[raw_name]] = 1.0
        except KeyError:

            for guid, player in fifa_data.items():
                probability_dict[raw_name][guid] = assign_probability(
                    player, lineup_name, lineup_number, lineup_nationality, team, season
                )

    max_prob_dict = {max(v, key=v.get): k for k, v in probability_dict.items()}
    players_to_cache = {v: k for k, v in max_prob_dict.items()}

    msg = "We need 11 players, retrieved {}".format(len(max_prob_dict.keys()))
    assert len(max_prob_dict.keys()) == 11, msg

    probabilities = [probability_dict[v][k] for k, v in max_prob_dict.items()]

    if any(probabilities) < 0.5:
        print("Warning, lowest probability is {}".format(min(probabilities)))
        # TODO - custom warning

    x = [fifa_data[guid] for guid, _ in max_prob_dict.items()]

    cached = {**cached, **players_to_cache}

    return x, cached


def assign_probability(player, name, number, nationality, team, season):
    name_probability = constants.NAME_PROBABILITY * match_name(name, player["name"])
    team_probability = constants.TEAM_PROBABILITY * fuzzy_team_match(
        team, player["team"]
    )
    nationality_probability = constants.NATIONALITY_PROBABILITY * exact_match(
        nationality, player["nationality"]
    )
    number_probability = constants.NUMBER_PROBABILITY * exact_match(
        int(number), int(player["number"])
    )
    season_probability = constants.SEASON_PROBABILITY * exact_match(
        season, player["season"]
    )
    return sum(
        [
            name_probability,
            team_probability,
            nationality_probability,
            number_probability,
            season_probability,
        ]
    )


def exact_match(object1, object2):
    if object1 == object2:
        return 1.0
    else:
        return 0.0


def fuzzy_team_match(match_team, player_team):
    if player_team == match_team:
        return 1.0
    elif player_team in constants.NATIONALITIES:
        return 0.5
    else:
        return 0.0


def match_name(name1, name2):
    name1 = set(remove_length_one_strings(name1.split("-")))
    name2 = set(remove_length_one_strings(name2.split("-")))
    smallest_length = min(len(name1), len(name2))

    return len(name1.intersection(name2)) / smallest_length


def remove_length_one_strings(li):
    return [x for x in li if len(x) > 1]


def create_feature_vector_from_players(players):
    goalkeeper = []
    defence = []
    midfield = []
    attack = []

    for player in players:
        if player["general position"] == "goalkeeper":
            goalkeeper.append(int(player["rating"]))
        elif player["general position"] == "defence":
            defence.append(int(player["rating"]))
        elif player["general position"] == "midfield":
            midfield.append(int(player["rating"]))
        elif player["general position"] == "attack":
            attack.append(int(player["rating"]))
        else:
            print("Error")

    assert len(goalkeeper) == 1, "Need exactly 1 goalkeeper, you have {}".format(
        len(goalkeeper)
    )
    assert len(defence) <= 6, "No more than 6 defenders allowed, there is {}".format(
        len(defence)
    )
    assert len(midfield) <= 7, "No more than 7 midfielders allowed, there is {}".format(
        len(midfield)
    )
    assert len(attack) <= 4, "No more than 4 attackers allowed, there is {}".format(
        len(attack)
    )

    defence = defence + [0] * (6 - len(defence))
    midfield = midfield + [0] * (7 - len(midfield))
    attack = attack + [0] * (4 - len(attack))

    return goalkeeper + defence + midfield + attack


if __name__ == "__main__":
    errors = []

    data = read_player_data()

    match_data = read_match_data(league="SP1", season="2013-2014")

    football_data = read_all_football_data(league="SP1")

    match_data = assign_odds_to_match(match_data, football_data)

    feature_vectors = []
    targets = []

    cached_players = {}

    for i, test_match in enumerate(reversed(match_data)):

        season = get_season(test_match)
        home_team, away_team = get_teams(test_match)
        home_goals, away_goals = get_goals(test_match)
        home_lineup_names, away_lineup_names = get_lineup_names(test_match)
        home_lineup_raw_names, away_lineup_raw_names = (
            test_match["info"]["home lineup raw names"],
            test_match["info"]["away lineup raw names"],
        )
        home_lineup_numbers, away_lineup_numbers = get_lineup_numbers(test_match)
        home_lineup_nationalities, away_lineup_nationalities = get_lineup_nationalities(
            test_match
        )
        home_odds, draw_odds, away_odds = get_match_odds(test_match)

        print(i, season, "{} vs. {}".format(home_team, away_team))

        if len(home_lineup_names) != 11:
            print("error")

        try:
            home_players_matched, cached_players = match_lineups_to_fifa_players(
                home_lineup_names,
                home_lineup_raw_names,
                home_lineup_numbers,
                home_lineup_nationalities,
                home_team,
                season,
                data,
                cached_players,
            )
            away_players_matched, cached_players = match_lineups_to_fifa_players(
                away_lineup_names,
                away_lineup_raw_names,
                away_lineup_numbers,
                away_lineup_nationalities,
                away_team,
                season,
                data,
                cached_players,
            )

            home_feature_vector = create_feature_vector_from_players(
                home_players_matched
            )
            away_feature_vector = create_feature_vector_from_players(
                away_players_matched
            )

            feature_vectors.append(home_feature_vector + away_feature_vector)
            targets.append([home_odds, draw_odds, away_odds])

        except Exception as exception:
            print("There is an issues with the above match")
            print(exception)
            test_match["error"] = exception
            errors.append(test_match)

    feature_vectors = np.array(feature_vectors)
    targets = np.array(targets)

    np.save("feature-vectors-13-14.npy", feature_vectors)
    np.save("targets-13-14.npy", targets)
