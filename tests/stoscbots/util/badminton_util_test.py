import pytest

from stoscbots.util.badminton_util import generate_badminton_doubles_schedule_v1


@pytest.mark.parametrize(
    "player_names,num_matches",
    [
        (['Anub', 'Jubin', 'Simon'], 1),  # less than 4 players
        (['Anub', 'Jubin', 'Simon', 'Ajsh'], 0),  # num_matches == 0
    ],
)
def test_invalid_inputs(player_names, num_matches):
    with pytest.raises(ValueError):
        generate_badminton_doubles_schedule_v1(player_names, num_matches)


def test_num_matches_greater_than_possible():
    players = ["A", "B", "C", "D"]
    schedule, counter = generate_badminton_doubles_schedule_v1(players, 100)
    '''This asserts that the length of the schedule list is 100, meaning the function is capable of scheduling the 
    requested number of matches, even if it's greater than the unique possible combinations.
    '''
    assert len(schedule) == 100
    '''The test checks if all players are present in the first scheduled match. With 4 players, this is expected as 
    they form two doubles pairs in a match.
    '''
    assert set(schedule[0]) == set(players)
    '''
    This loop iterates over each player in the counter (which keeps track of the number of matches each player has 
    played) to check that each player is one of the originally listed players. This ensures the counter doesn't have 
    any unexpected or extra players.
    '''
    for player, count in counter:
        assert player in players


"""
tests whether there are any repeated matches in the generated schedule by checking if the length of the schedule is 
equal to the length of the set of the schedule. The set would eliminate any duplicate entries.

Given the implementation of the generate_badminton_doubles_schedule() function, it's designed to prioritize unique 
matches, and it will replenish the pool of possible matches when it runs out. However, because the function shuffles 
and selects matches based on the number of matches each player has already played, it's possible to end up with 
repeated matches in the schedule when the number of requested matches exceeds the total number of unique possible 
matches.

With 6 players, the number of unique doubles matches (2 vs. 2 without considering order) is 15. If you request exactly 
15 matches, all should be unique. But if you request more than that, repetitions will occur, and the test should fail.
"""


def test_no_repeated_matches():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 15
    schedule, counter = generate_badminton_doubles_schedule_v1(players, num_matches)
    assert len(schedule) == len(set(schedule))


# To ensure all players play the same number of matches as much as possible
# No one should play more than any other player by more than 1 match
def test_player_participation():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 10
    _, player_count = generate_badminton_doubles_schedule_v1(players, num_matches)
    max_participation = max(player_count, key=lambda x: x[1])[1]
    min_participation = min(player_count, key=lambda x: x[1])[1]

    # Assuming a tolerance of 1 match difference for fairness
    assert max_participation - min_participation <= 1


def generate_players(n):
    """Utility function to generate list of n player names"""
    return [chr(65 + i) for i in range(n)]


def test_correct_number_of_matches_6_players_5_matches():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 5
    schedule, _ = generate_badminton_doubles_schedule_v1(players, num_matches)
    assert len(schedule) == num_matches


def test_generated_games_count_4_players_5_matches():
    players = ["A", "B", "C", "D"]
    num_matches = 5
    schedule, _ = generate_badminton_doubles_schedule_v1(players, num_matches)
    assert len(schedule) == num_matches


def test_generated_games_count_20_matches():
    players = ["A", "B", "C", "D"]
    num_matches = 20
    schedule, _ = generate_badminton_doubles_schedule_v1(players, num_matches)
    assert len(schedule) == num_matches


@pytest.mark.skip
def test_no_three_consecutive_games():
    players = ["A", "B", "C", "D", "E", "F"]
    num_matches = 10
    schedule, _ = generate_badminton_doubles_schedule_v1(players, num_matches)

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
        generate_badminton_doubles_schedule_v1(players, num_matches)


def test_non_string_players():
    players = [1, 2, 3, 4]
    num_matches = 5
    schedule, _ = generate_badminton_doubles_schedule_v1(players, num_matches)
    assert len(schedule) == num_matches


# Ensure that a set of matches (equal to the number of players), there are no duplicate matches.
def test_unique_matches_for_n_players():
    # Generate a list of 15 players
    players = [f"Player_{i}" for i in range(15)]
    num_matches = 80
    schedule, _ = generate_badminton_doubles_schedule_v1(players, num_matches)

    n = len(players)
    grouped_matches = [schedule[i:i + n] for i in range(0, len(schedule), n)]

    unique_groups = set()
    for group in grouped_matches:
        # Here, we're sorting each match, then sorting the groups of matches,
        # and then converting them to a tuple, so they can be added to a set.
        sorted_group = tuple(sorted(tuple(sorted(match)) for match in group))
        unique_groups.add(sorted_group)

    assert len(unique_groups) == len(grouped_matches)
