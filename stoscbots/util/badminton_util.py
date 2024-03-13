import random
from collections import Counter
from itertools import combinations
from typing import Tuple, List, Set
from collections import deque

def generate_badminton_doubles_schedule_v1(player_names: list[str], num_matches: int) -> Tuple[
    List[Tuple[str, str, str, str]], List[Tuple[str, int]]]:
    # Ensure there are at least 4 players to schedule a doubles match.
    if len(player_names) < 4 or num_matches < 1:
        raise ValueError("⚠️ There must be at least 4 players to schedule a doubles match")
    # Generate all possible pairs of players.
    all_pairs = list(combinations(player_names, 2))
    random.shuffle(all_pairs)
    # Generate all possible match combinations given the pairs.
    possible_matches = generate_possible_match_combinations(all_pairs)

    # Create a counter to track how many matches each player has played.
    player_played_match_counter = Counter()

    # Keep a copy of the generated possible matches to reuse.
    # This is done to restore the pool of possible matches if they run out.
    possible_matches_copy = possible_matches.copy()

    # List to store the scheduled matches.
    schedule = []
    for i in range(num_matches):
        if not possible_matches:
            # If we have scheduled all possible matches, refill the list with the original matches.
            possible_matches = possible_matches_copy.copy()

        # Find the minimum match count among all possible matches.
        # This is done to prioritize matches with players who've played the least.
        min_match_count = min(
            sum(player_played_match_counter[player] for player in m[0] + m[1]) for m in possible_matches)

        for match in possible_matches:
            team1, team2 = match

            #  Calculate the sum of matches played by all players in this potential match.
            total_count = sum(player_played_match_counter[player] for player in team1 + team2)

            if (len(schedule) < num_matches) and (total_count == min_match_count):
                # Schedule this match.
                schedule.append(tuple(item for sublist in match for item in sublist))
                # Update match counts for each player in this match.
                for player in team1 + team2:
                    player_played_match_counter[player] += 1
                # Remove this match from the possible matches.
                possible_matches.remove(match)
                break

    _x = [(player, count) for player, count in player_played_match_counter.items()]
    return schedule, _x


def generate_possible_match_combinations(all_pairs: List[Tuple[str, str]]) -> Set[
    Tuple[Tuple[str, str], Tuple[str, str]]]:
    # Create all possible doubles matches without player repetition.
    possible_matches = set()
    for pair1 in all_pairs:
        for pair2 in all_pairs:
            if len(set(pair1 + pair2)) == 4:  # No repeated players in a match
                possible_matches.add((pair1, pair2))
    return possible_matches


# Main Function
def generate_badminton_doubles_schedule_v2(all_players, num_matches):

    """
    With 6: Three players continue to play in the next game. 1 player is rotated.
    With 7 : One player continues to play in the next game. The other 3 players are rotated.
    """
    num_players = len(all_players)
    schedule = []
    players = deque(all_players)

    for _ in range(num_matches):
        # Shuffle the players for each set of 5 games
        if _ % num_players == 0:
            # Shuffle the players randomly
            random.shuffle(players)
        # The first 4 players are playing, the last one is sitting out
        playing = list(players)[:4]
        # The remaining players sit out
        sitting_out = list(players)[4:]
        schedule.append((playing, sitting_out))
        # Rotate the players for the next game
        players.rotate(1)

    return schedule




    # if len(all_players) == 5:
    #     '''
    #     Randomize players. One player sits out while other 4 play. In the next game, one of the players who have played,
    #     sits out. Since there are 5 players, each player will sit out once in 5 games. % games is one set of games. In
    #     the next set of games i.e. from GAme 6 to Game 10, the same process is repeated. But ensure that the players
    #     playing in Game 6 is not the same as the players playing in Game 1. This is to ensure that the same set of
    #     players don't play together in the next set of games.
    #
    #     Generate a list of games with playing players and sitting out players.
    #     '''
    #
    #     schedule = []
    #     players = deque(all_players)
    #
    #     for _ in range(num_matches):
    #         # Shuffle the players for each set of 5 games
    #         if _ % 5 == 0:
    #             # Shuffle the players randomly
    #             random.shuffle(players)
    #         # The first 4 players are playing, the last one is sitting out
    #         playing = list(players)[:4]
    #         sitting_out = list(players)[4]
    #         schedule.append((playing, sitting_out))
    #         # Rotate the players for the next game
    #         players.rotate(1)
    #
    #     return schedule



if __name__ == "__main__":

    num_matches = 12

    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip", "Vibin"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip", "Vibin", "Dibu"]
    player_names = ["Anub", "Shiju", "Vincent", "Johnny", "Vibin"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Johnson", "Vibin"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Johnson", "Vibin", "Liju"]
    # schedule, player_count = generate_badminton_doubles_schedule_v1(player_names, num_matches)
    schedule, player_count = generate_badminton_doubles_schedule_v2(player_names, num_matches)

    from tabulate import tabulate

    # Display the schedule in table format
    table_data = []
    for i, match in enumerate(schedule):
        table_data.append([i + 1, ', '.join(match)])

    print(tabulate(table_data, headers=["#", "Players"], tablefmt="simple"))  # Good
    print(tabulate(table_data, headers=["#", "Players"], tablefmt="rst"))  # Good
    print(tabulate(table_data, headers=["#", "Players"], tablefmt="presto",
                   maxcolwidths=[1, None, None]))  # Good

    print("\n### Player Participation Counts ###")
    print(tabulate(player_count, headers=['Player', 'Played'], tablefmt="simple"))
