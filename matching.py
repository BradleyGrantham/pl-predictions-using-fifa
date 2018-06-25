import json

import constants


def read_player_data():
    with open('./data/players_new_new.json') as json_file:
        data = json.load(json_file)

    return data


def read_match_data():
    with open('./data/matchlineups.json') as json_file:
        data = json.load(json_file)

    return data


def lineup_matching(lineup_names, lineup_numbers, lineup_nationalities, team, fifa_data):
    all_fifa_players = [player['name'] for _, player in fifa_data.items()]

    probability_dict = {lineup_name: dict.fromkeys(all_fifa_players, 0) for lineup_name in home_lineup_names}

    for lineup_name, lineup_number, lineup_nationality in zip(home_lineup_names, home_lineup_numbers,
                                                              home_lineup_nationalities):

        for guid, player in fifa_data.items():
            probability_dict[lineup_name][guid] = assign_probability(player, lineup_name, lineup_number,
                                                                     lineup_nationality,
                                                                     home_team)

    max_prob_dict = {max(v, key=v.get): k for k, v in probability_dict.items()}

    assert len(max_prob_dict.keys()) == 11, 'We need 11 players, retrieved {}'.format(len(max_prob_dict.keys()))

    probabilities = [probability_dict[v][k] for k, v in max_prob_dict.items()]

    if any(probabilities) < 0.5:
        print('Warning, lowest probability is {}'.format(min(probabilities)))

    x = [fifa_data[guid] for guid, _ in max_prob_dict.items()]

    return x


def assign_probability(player, name, number, nationality, team):
    name_probability = constants.NAME_PROBABILITY * match_name(name, player['name'])
    team_probability = constants.TEAM_PROBABILITY * exact_match(team, player['info']['team'])
    nationality_probability = constants.NATIONALITY_PROBABILITY * exact_match(nationality,
                                                                              player['info']['nationality'])
    number_probability = constants.NUMBER_PROBABILITY * exact_match(int(number), int(player['info']['kit number']))

    return sum([name_probability, team_probability, nationality_probability, number_probability])


def exact_match(object1, object2):
    if object1 == object2:
        return 1.0
    else:
        return 0.0


def match_name(name1, name2):
    name1 = set(remove_length_one_strings(name1.split('-')))
    name2 = set(remove_length_one_strings(name2.split('-')))
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
        if player['info']['general position'] == 'goalkeeper':
            goalkeeper.append(int(player['info']['rating']))
        elif player['info']['general position'] == 'defence':
            defence.append(int(player['info']['rating']))
        elif player['info']['general position'] == 'midfield':
            midfield.append(int(player['info']['rating']))
        elif player['info']['general position'] == 'attack':
            attack.append(int(player['info']['rating']))
        else:
            print("Error")

    assert len(goalkeeper) == 1, "Need exactly 1 goalkeeper"
    assert len(defence) <= 6, "No more than 6 defenders allowed, there is {}".format(len(defence))
    assert len(midfield) <= 6, "No more than 6 midfielders allowed, there is {}".format(len(midfield))
    assert len(attack) <= 4, "No more than 4 attackes allowed, there is {}".format(len(attack))

    defence = defence + [0] * (6 - len(defence))
    midfield = midfield + [0] * (6 - len(midfield))
    attack = attack + [0] * (4 - len(attack))

    return goalkeeper + defence + midfield + attack


if __name__ == '__main__':
    errors = []

    data = read_player_data()

    match_lineups = read_match_data()

    test_match = match_lineups[97]

    home_lineup_names = test_match['info']['home lineup names']
    home_team = constants.TEAM_MAPPINGS['17-18'][test_match['info']['home team']]
    away_lineup_names = test_match['info']['away lineup names']
    away_team = test_match['info']['away team']
    home_lineup_numbers = test_match['info']['home lineup numbers']
    away_lineup_numbers = test_match['info']['away lineup numbers']
    home_lineup_nationalities = test_match['info']['home lineup nationalities']
    away_lineup_nationalities = test_match['info']['away lineup nationalities']

    if len(home_lineup_names) != 11:
        print('error')

    players_matched = lineup_matching(home_lineup_names, home_lineup_numbers, home_lineup_nationalities,
                                             home_team, data)

    print(create_feature_vector_from_players(players_matched))

    for i, test_match in enumerate(match_lineups):

        # test_match = match_lineups[150]

        home_lineup_names = test_match['info']['home lineup names']
        home_team = constants.TEAM_MAPPINGS['17-18'][test_match['info']['home team']]
        away_lineup_names = test_match['info']['away lineup names']
        away_team = test_match['info']['away team']
        home_lineup_numbers = test_match['info']['home lineup numbers']
        away_lineup_numbers = test_match['info']['away lineup numbers']
        home_lineup_nationalities = test_match['info']['home lineup nationalities']
        away_lineup_nationalities = test_match['info']['away lineup nationalities']

        if len(home_lineup_names) != 11:
            print('error')

        players_matched = lineup_matching(home_lineup_names, home_lineup_numbers, home_lineup_nationalities, home_team, data)

        create_feature_vector_from_players(players_matched)
        # print(i)
    #     if len(players_matched) != 11:
    #         print(i)
    #         print(len(players_matched))
    #         print(players_matched)
    #         print(home_lineup_names)
    #         print(home_lineup_numbers)
    #         errors.append(1)
    #         # time.sleep(10)
    # print(len(errors))
