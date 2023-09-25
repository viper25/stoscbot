import pytest

from stoscbots.util.badminton_util import generate_badminton_doubles_schedule


def test_no_repeated_players_in_match():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 5
    schedule, _ = generate_badminton_doubles_schedule(players, num_matches)
    for match in schedule:
        assert len(set(match[0] + match[1])) == 4


# To ensure all players play the same number of matches as much as possible
# No one should play more than any other player by more than 1 match
def test_player_participation():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 10
    _, player_count = generate_badminton_doubles_schedule(players, num_matches)
    max_participation = max(player_count.values())
    min_participation = min(player_count.values())

    # Assuming a tolerance of 1 match difference for fairness
    assert max_participation - min_participation <= 1


# To test that there are at least 4 players
def test_minimum_number_of_players_3():
    players = ["A", "B", "C"]
    num_matches = 5
    with pytest.raises(ValueError):
        generate_badminton_doubles_schedule(players, num_matches)


def test_correct_number_of_matches_6_players_5_matches():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 5
    schedule, _ = generate_badminton_doubles_schedule(players, num_matches)
    assert len(schedule) == num_matches


def test_generated_games_count_4_players_5_matches():
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
        game_2_players = set(schedule[i + 1][0] + schedule[i + 1][1])
        game_3_players = set(schedule[i + 2][0] + schedule[i + 2][1])

        for player in players:
            consecutive_count = sum(
                1 for game_players in [game_1_players, game_2_players, game_3_players] if player in game_players
            )
            assert consecutive_count < 3


def test_repeated_player_names():
    players = ["A", "A", "B", "B"]
    num_matches = 5
    with pytest.raises(ValueError):  # Or whichever exception you expect
        generate_badminton_doubles_schedule(players, num_matches)


def test_non_string_players():
    players = [1, 2, 3, 4]
    num_matches = 5
    schedule, _ = generate_badminton_doubles_schedule(players, num_matches)
    assert len(schedule) == num_matches

def test_zero_matches():
    players = ["A", "B", "C", "D"]
    num_matches = 0
    schedule, _ = generate_badminton_doubles_schedule(players, num_matches)
    assert len(schedule) == num_matches

# Ensure that a set of matches (equal to the number of players), there are no duplicate matches.
def test_unique_matches_for_n_players():
    # Generate a list of 15 players
    players = [f"Player {i}" for i in range(15)]
    num_matches = 80
    schedule, _ = generate_badminton_doubles_schedule(players, num_matches)

    n = len(players)
    grouped_matches = [schedule[i:i + n] for i in range(0, len(schedule), n)]

    unique_groups = set()
    for group in grouped_matches:
        # Here, we're sorting each match, then sorting the groups of matches,
        # and then converting them to a tuple so they can be added to a set.
        sorted_group = tuple(sorted(tuple(sorted(match[0] + match[1])) for match in group))
        unique_groups.add(sorted_group)

    assert len(unique_groups) == len(grouped_matches)
