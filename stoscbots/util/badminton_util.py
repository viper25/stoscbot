import random
from collections import Counter
from itertools import combinations

def generate_badminton_doubles_schedule(player_names: list[str], num_matches: int):
    if len(player_names) < 4:
        raise ValueError("⚠️ There must be at least 4 players to schedule a doubles match")
    # Create all possible pairs
    all_pairs = list(combinations(player_names, 2))

    possible_matches = generate_possible_match_combinations(all_pairs)

    # Initialize match counter for each player
    player_played_match_counter = Counter()

    # Generate a fair schedule
    schedule = []
    for i in range(num_matches):
        # If the number of possible matches reduces to 0 and we have not reached the required number of matches,
        # reseed the possible matches
        if possible_matches == [] and len(schedule) != num_matches:
            possible_matches = generate_possible_match_combinations(all_pairs)
        for match in possible_matches:
            team1, team2 = match

            # Calculate the sum of all player's current matches in this potential match
            total_count = sum(player_played_match_counter[player] for player in team1 + team2)

            if len(schedule) < num_matches and total_count == min(
                    sum(player_played_match_counter[player] for player in m[0] + m[1]) for m in possible_matches
            ):
                schedule.append(match)
                for player in team1 + team2:
                    player_played_match_counter[player] += 1
                possible_matches.remove(match)
                break

    return schedule, player_played_match_counter


def generate_possible_match_combinations(all_pairs):
    # Create all possible matches
    possible_matches = []
    for pair1 in all_pairs:
        for pair2 in all_pairs:
            if len(set(pair1 + pair2)) == 4:  # No repeated players in a match
                possible_matches.append((pair1, pair2))
    random.shuffle(possible_matches)
    return possible_matches


# Main Function
if __name__ == "__main__":

    num_matches = 20

    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip", "Vibin", "Dibu"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip", "Vibin"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh"]
    player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vibin"]
    schedule, player_count = generate_badminton_doubles_schedule(player_names, num_matches)

    # img = create_schedule_image(schedule, player_count, player_names)

    from tabulate import tabulate

    # Display the schedule in table format
    table_data = []
    for i, match in enumerate(schedule):
        table_data.append([i + 1, '|'.join(match[0]), '|'.join(match[1])])
    print(tabulate(table_data, headers=["#", "Team 1", "Team 2"], tablefmt="simple")) # Good
    print(tabulate(table_data, headers=["#", "Team 1", "Team 2"], tablefmt="rst"))  # Good
    print(tabulate(table_data, headers=["#", "Team 1", "Team 2"], tablefmt="simple_grid"))
    print(tabulate(table_data, headers=["#", "Team 1", "Team 2"], tablefmt="presto", maxcolwidths=[1, None, None])) # Good
    print(tabulate(table_data, headers=["#", "Team 1", "Team 2"], tablefmt="orgtbl"))

    print("\n### Player Participation Counts ###")
    data = [(player, count) for player, count in player_count.items()]
    print(tabulate(data, headers=['Player', 'Played'], tablefmt="simple"))
