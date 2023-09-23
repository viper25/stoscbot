import pytest

from stoscbots.util.badminton_util import generate_badminton_doubles_schedule


def test_correct_number_of_matches():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 5
    schedule, _ = generate_badminton_doubles_schedule(players, num_matches)
    assert len(schedule) == num_matches


def test_no_repeated_players_in_match():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 5
    schedule, _ = generate_badminton_doubles_schedule(players, num_matches)
    for match in schedule:
        assert len(set(match[0] + match[1])) == 4


def test_player_participation():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 10
    _, player_count = generate_badminton_doubles_schedule(players, num_matches)
    max_participation = max(player_count.values())
    min_participation = min(player_count.values())

    # Assuming a tolerance of 1 match difference for fairness
    assert max_participation - min_participation <= 1


def test_minimum_number_of_players():
    players = ["A", "B", "C"]
    num_matches = 5
    with pytest.raises(ValueError):
        generate_badminton_doubles_schedule(players, num_matches)


def test_generated_games_count_5_matches():
    players = ["A", "B", "C", "D"]
    num_matches = 5
    schedule, _ = generate_badminton_doubles_schedule(players, num_matches)
    assert len(schedule) == num_matches

def test_generated_games_count_20_matches():
    players = ["A", "B", "C", "D"]
    num_matches = 20
    schedule, _ = generate_badminton_doubles_schedule(players, num_matches)
    assert len(schedule) == num_matches

def test_no_three_consecutive_games():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 10
    schedule, _ = generate_badminton_doubles_schedule(players, num_matches)

    for i in range(len(schedule) - 2):
        game_1_players = set(schedule[i][0] + schedule[i][1])
        game_2_players = set(schedule[i+1][0] + schedule[i+1][1])
        game_3_players = set(schedule[i+2][0] + schedule[i+2][1])

        for player in players:
            consecutive_count = sum(
                1 for game_players in [game_1_players, game_2_players, game_3_players] if player in game_players
            )
            assert consecutive_count < 3