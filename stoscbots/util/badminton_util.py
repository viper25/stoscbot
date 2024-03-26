import random
from collections import Counter
from collections import deque
from itertools import combinations
from typing import Tuple, List, Set


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


def print_schedule(s: List[Tuple[str, str, str, str]], print_last_match: bool = False):
    pass
    if print_last_match:
        print(f"# {len(s)}: Playing: {s[-1][0]}, Sitting: {s[-1][1]}")
    else:
        total_players = sum(len(list) for list in s[0])
        for i, match in enumerate(s):
            print(f"# {i + 1}: Playing: {match[0]}, Sitting: {match[1]}")
            # Add a line after every len(s) matches
            if (i + 1) % total_players == 0:
                print("----------------------")



# Main Function
def generate_badminton_doubles_schedule_v2(all_players, num_matches) -> List[Tuple[List[str], List[str]]]:
    """
    With 6: Three players continue to play in the next game. 1 player is rotated.
    With 7 : One player continues to play in the next game. The other 3 players are rotated.
    With 8 : Same rule as 7. 3 players are rotated. One continues to play. So one player sits out 2 games consecutively
    """

    if len(all_players) <= 4 or num_matches < 1:
        raise ValueError("⚠️ There must be at least 4 players to schedule a doubles match")

    num_players = len(all_players)
    schedule = []
    players = deque(all_players)

    # Choose any 4 players to play:
    playing = list(players)[:4]
    sitting = list(players)[4:]
    schedule.append((playing, sitting))
    print_schedule(schedule, print_last_match=True)

    for game_no in range(num_matches-1):

        # Shuffle the players after each set of num_players games
        if len(schedule) % num_players == 0:
            # Shuffle the players randomly
            random.shuffle(players)
            playing = list(players)[:4]
            sitting = list(players)[4:]

        if num_players == 5:
            next_sitting = [playing[0]]
            playing = playing[1:] + [sitting[0]]
            sitting = next_sitting

            schedule.append((playing, sitting))
            print_schedule(schedule, print_last_match=True)

        if num_players == 6:
            next_sitting = [sitting[1]] + [playing[0]]
            playing = playing[1:] + [sitting[0]]
            sitting = next_sitting

            schedule.append((playing, sitting))
            print_schedule(schedule, print_last_match=True)

        if num_players == 7:
            next_sitting = playing[:3]
            playing = [playing[3]] + sitting[:3]
            sitting = next_sitting

            schedule.append((playing, sitting))
            print_schedule(schedule, print_last_match=True)

        elif num_players == 8:
            next_sitting = [sitting[3]] + playing[:3]
            playing = [playing[3]] + sitting[:3]
            sitting = next_sitting

            schedule.append((playing, sitting))
            print_schedule(schedule, print_last_match=True)

        elif num_players == 9:
            '''
            4 play and 5 sit out, then 4 of the 5 sitting out play and 4 of the 4 playing sit out
            '''
            next_sitting = [sitting[4]] + playing[:4]
            playing = sitting[:4]
            sitting = next_sitting

            schedule.append((playing, sitting))
            print_schedule(schedule, print_last_match=True)
    return schedule


if __name__ == "__main__":

    num_matches = 20

    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip", "Vibin"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip", "Vibin", "Dibu"]
    player_names = ["Anub", "Shiju", "Vincent", "Johnny", "Vibin"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Johnson", "Vibin"]
    player_names = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    player_names = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]
    player_names = ["P1", "P2", "P3", "P4", "P5", "P6"]
    player_names = ["P1", "P2", "P3", "P4", "P5"]
    player_names = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
    schedule = generate_badminton_doubles_schedule_v2(player_names, num_matches)
    print_schedule(schedule)

    from tabulate import tabulate

    # Display the schedule in table format
    table_data = []
    for i, match in enumerate(schedule):
        table_data.append([i + 1, ', '.join(match[0])])

    print(tabulate(table_data, headers=["#", "Players"], tablefmt="simple"))  # Good
    print(tabulate(table_data, headers=["#", "Players"], tablefmt="rst"))  # Good
    print(tabulate(table_data, headers=["#", "Players"], tablefmt="presto",
                   maxcolwidths=[1, None, None]))  # Good

