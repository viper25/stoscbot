import random
from collections import Counter
from itertools import combinations

def generate_badminton_doubles_schedule(player_names: list[str], num_matches: int):
    # Ensure there are at least 4 players to schedule a doubles match.
    if len(player_names) < 4:
        raise ValueError("⚠️ There must be at least 4 players to schedule a doubles match")
    # Generate all possible pairs of players.
    all_pairs = list(combinations(player_names, 2))
    random.shuffle(all_pairs)

    # Generate all possible match combinations given the pairs.
    possible_matches = generate_possible_match_combinations(all_pairs)

    # Create a counter to track how many matches each player has played.
    player_played_match_counter = Counter()

    # Sort possible matches by fewest total appearances to prioritize match-ups
    possible_matches = sorted(list(possible_matches), key=lambda x: len(set(x[0]) & set(x[1])))

    # List to store the scheduled matches.
    schedule = []
    for i in range(num_matches):
        # If all possible matches are exhausted and we still need more matches,
        # regenerate the possible matches.
        if possible_matches == [] and len(schedule) != num_matches:
            possible_matches = generate_possible_match_combinations(all_pairs)
        for match in possible_matches:
            team1, team2 = match

            #  Calculate the sum of matches played by all players in this potential match.
            total_count = sum(player_played_match_counter[player] for player in team1 + team2)

            # Check if this match has the minimum match count among the possible matches.
            # This ensures fairness in match allocation.
            if len(schedule) < num_matches and total_count == min(
                    sum(player_played_match_counter[player] for player in m[0] + m[1]) for m in possible_matches
            ):
                # Schedule this match.
                schedule.append(match)
                # Update match counts for each player in this match.
                for player in team1 + team2:
                    player_played_match_counter[player] += 1
                # Remove this match from the possible matches.
                possible_matches.remove(match)
                break

    random.shuffle(schedule)
    return schedule, player_played_match_counter


def generate_possible_match_combinations(all_pairs):
    # Create all possible doubles matches without player repetition.
    possible_matches = set()
    for pair1 in all_pairs:
        for pair2 in all_pairs:
            if len(set(pair1 + pair2)) == 4:  # No repeated players in a match
                possible_matches.add((pair1, pair2))
    return possible_matches


# Main Function
if __name__ == "__main__":

    num_matches = 8

    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip", "Vibin", "Dibu"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip", "Vibin"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vibin", "Saman"]
    schedule, player_count = generate_badminton_doubles_schedule(player_names, num_matches)

    # img = create_schedule_image(schedule, player_count, player_names)

    from tabulate import tabulate

    # Display the schedule in table format
    table_data = []
    for i, match in enumerate(schedule):
        table_data.append([i + 1, ', '.join([item for sublist in match for item in sublist])])
    # print(tabulate(table_data, headers=["#", "Team 1", "Team 2"], tablefmt="simple")) # Good
    # print(tabulate(table_data, headers=["#", "Team 1", "Team 2"], tablefmt="rst"))  # Good
    print(tabulate(table_data, headers=["#", "Players"], tablefmt="presto", maxcolwidths=[1, None, None])) # Good

    print("\n### Player Participation Counts ###")
    data = [(player, count) for player, count in player_count.items()]
    print(tabulate(data, headers=['Player', 'Played'], tablefmt="simple"))
