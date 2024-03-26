from collections import defaultdict, deque

import pytest

from stoscbots.util.badminton_util import generate_badminton_doubles_schedule


# Utility function to convert schedule output to a testable format
def get_schedule_str(schedule):
    return [" ".join(["{" + ", ".join(team) + "}" for team in match]) for match in schedule]


# Test fewer than 5 players raises ValueError
@pytest.mark.parametrize("num_players", [1, 2, 3, 4])
def test_fewer_than_five_players(num_players):
    players = ['Player' + str(i) for i in range(num_players)]
    with pytest.raises(ValueError):
        generate_badminton_doubles_schedule(players, 5)


# Test 0 or negative matches raises ValueError
@pytest.mark.parametrize("num_matches", [0, -1])
def test_zero_or_negative_matches(num_matches):
    players = ['Player1', 'Player2', 'Player3', 'Player4', 'Player5']
    with pytest.raises(ValueError):
        generate_badminton_doubles_schedule(players, num_matches)


@pytest.mark.parametrize(
    "player_names,num_matches",
    [
        (['Anub', 'Jubin', 'Simon'], 1),  # less than 4 players
        (['Anub', 'Jubin', 'Simon', 'Ajsh'], 0),  # num_matches == 0
    ],
)
def test_invalid_inputs(player_names, num_matches):
    with pytest.raises(ValueError):
        generate_badminton_doubles_schedule(player_names, num_matches)


def test_num_matches_greater_than_possible():
    players = ["A", "B", "C", "D", "E"]
    schedule = generate_badminton_doubles_schedule(players, 100)
    '''This asserts that the length of the schedule list is 100, meaning the function is capable of scheduling the 
    requested number of matches, even if it's greater than the unique possible combinations.
    '''
    assert len(schedule) == 100


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


def generate_players(n):
    """Utility function to generate list of n player names"""
    return [chr(65 + i) for i in range(n)]


@pytest.mark.skip
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
    players = [1, 2, 3, 4, 5]
    num_matches = 5
    schedule = generate_badminton_doubles_schedule(players, num_matches)
    assert len(schedule) == num_matches


@pytest.mark.parametrize("num_players, num_matches, expected_continuity_rules", [
    (5, 5, {"three_continues": True}),
    (6, 6, {"three_continues": True}),
    (7, 7, {"one_continues": True, "sits_two": False}),
    (8, 8, {"one_continues": True, "sits_two": True}),
    (9, 9, {"four_rotate": True, "sits_two": True}),
    (9, 9, {"sits_two": True}),
    # For num_matches, set as same as num_players because we randomize players after every num_players matches
])
def test_specific_players_num_matches(num_players, num_matches, expected_continuity_rules):
    players = ['Player' + str(i) for i in range(1, num_players + 1)]
    schedule = generate_badminton_doubles_schedule(players, num_matches)

    if expected_continuity_rules.get("one_continues"):
        # Test that exactly one player from the previous match continues to the next
        for i in range(len(schedule) - 1):
            current_match = set(schedule[i][0])  # Current match's playing players
            next_match = set(schedule[i + 1][0])  # Next match's playing players

            # Find the intersection of current and next matches to get continuing players
            continuing_players = current_match.intersection(next_match)

            # Assert that exactly one player continues to the next match
            assert len(
                continuing_players) == 1, f"Expected exactly 1 player to continue between matches {i + 1} and {i + 2}, but found {len(continuing_players)}"

    if expected_continuity_rules.get("three_continues"):
        # Test that three players continue to play in the next game
        for i in range(len(schedule) - 1):
            current_match = set(schedule[i][0])  # Current match's playing players
            next_match = set(schedule[i + 1][0])  # Next match's playing players

            # Find the intersection of current and next matches to get continuing players
            continuing_players = current_match.intersection(next_match)

            # Assert that exactly one player continues to the next match
            assert len(
                continuing_players) == 3, f"Expected exactly 3 players to continue between matches {i + 1} and {i + 2}, but found {len(continuing_players)}"

    if expected_continuity_rules.get("sits_two"):
        # Test that one player sits out two games consecutively (for 7 or 8 players)
        consecutive_sitting = False  # Flag to check if the condition is met at least once

        # Iterate over the schedule, except for the last two matches,
        # because we need to check the current match and the next two matches for the sitting condition.
        for i in range(len(schedule) - 2):
            current_sitting = set(schedule[i][1])  # Players sitting out in the current match
            next_sitting = set(schedule[i + 1][1])  # Players sitting out in the next match
            next_next_sitting = set(schedule[i + 2][1])  # Players sitting out in the match after the next

            # Check if any player from the current sitting list sits out in the next two matches
            if any(player in next_sitting for player in current_sitting):
                consecutive_sitting = True
                break  # We've found at least one instance of consecutive sitting, no need to check further

        # Assert that the condition of sitting out consecutively is met at least once
        assert consecutive_sitting, "Expected at least one player to sit out two consecutive games, but none did."

    if expected_continuity_rules.get("four_rotate"):
        # Test that 4 players rotate from sitting out to playing (for 9 players)
        for i in range(len(schedule) - 1):
            current_match = set(schedule[i][0])  # Current match's playing players
            next_match = set(schedule[i + 1][0])  # Next match's playing players

            # Find the intersection of current and next matches to get continuing players
            continuing_players = current_match.intersection(next_match)

            # Assert that no player continues to the next match
            assert len(
                continuing_players) == 0, f"Expected no player to continue between matches {i + 1} and {i + 2}, but found {len(continuing_players)}"

    # You can also add checks for the number of games played, ensuring the schedule length matches num_matches
    assert len(schedule) == num_matches, "The number of matches scheduled does not match the requested number."

@pytest.mark.parametrize("num_players", [5, 6, 7, 8, 9])
def test_no_repeated_matches(num_players):
    num_matches = num_players  # Define the number of matches based on the number of players
    players = ['Player' + str(i) for i in range(1, num_players + 1)]
    schedule = generate_badminton_doubles_schedule(players, num_matches)

    matches_set = set()

    for match in schedule:
        # For each match, we take the 'playing' players (first item in each tuple)
        playing_players = match[0]

        # Convert the list of playing players to a frozenset to make it hashable and comparable
        # Frozenset is used because the order of players does not matter, only their combination
        playing_set = frozenset(playing_players)

        # Ensure this combination hasn't been added before
        assert playing_set not in matches_set, "Found a repeated match, which violates the no repeated matches constraint."

        # Add the current combination to the set of matches
        matches_set.add(playing_set)

@pytest.mark.parametrize("num_players", [5, 6, 7, 8, 9])
def test_fairness_in_games_played(num_players):
    # Choose a multiplier for the number of games.
    # This ensures the total number of games is a multiple of the number of players.
    # The choice of 2 is arbitrary but ensures a reasonable number of games for testing.
    games_multiplier = 3
    num_matches = num_players * games_multiplier
    players = ['Player' + str(i) for i in range(1, num_players + 1)]
    schedule = generate_badminton_doubles_schedule(players, num_matches)

    # Initialize a dictionary to count games played by each player
    games_played_by_player = defaultdict(int)

    # Count the games played by each player
    for match in schedule:
        for player in match[0]:  # Assuming match[0] contains the list of playing players
            games_played_by_player[player] += 1

    # Extract the counts into a list to make comparison easier
    games_played_counts = list(games_played_by_player.values())

    # Check that the difference in games played between any two players does not exceed 1
    max_games = max(games_played_counts)
    min_games = min(games_played_counts)

    assert max_games - min_games <= 1, "The difference in games played between some players exceeded 1."

@pytest.mark.parametrize("num_players", [5, 6, 7, 8, 9])
def test_no_player_sits_out_more_than_two_consecutive_games(num_players):
    # Assuming a reasonable number of games for testing
    games_multiplier = 2
    num_matches = num_players * games_multiplier
    players = ['Player' + str(i) for i in range(1, num_players + 1)]
    schedule = generate_badminton_doubles_schedule(players, num_matches)

    # Initialize a dictionary to track the last two game statuses for each player (play/sit)
    player_statuses = {player: deque([True, True], maxlen=2) for player in players}  # True indicates playing, False indicates sitting out

    # Update status for each game
    for match in schedule:
        playing_players = set(match[0])  # Assuming match[0] contains the list of playing players
        for player in players:
            player_statuses[player].append(player in playing_players)

    # Check that no player has sat out more than two consecutive games
    for player, status in player_statuses.items():
        for i in range(len(status) - 2):
            # If three consecutive statuses are False (sat out), then the test fails
            assert not (status[i] == status[i+1] == status[i+2] == False), f"{player} sat out more than two consecutive games."