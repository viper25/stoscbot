import itertools


def schedule_games(players, total_games):
    # Initialize counters for each player
    player_counters = {player: 0 for player in players}
    scheduled_games = []
    prev_combinations = []
    recent_pairs = []

    for _ in range(total_games):
        # Sort players based on counter values
        sorted_players = sorted(player_counters, key=player_counters.get)

        # Get all possible combinations of 4 players from the sorted list
        combinations = list(itertools.combinations(sorted_players[:8], 4))

        # Filter out combinations that have been used before
        combinations = [comb for comb in combinations if comb not in prev_combinations]

        # If all combinations have been exhausted, reset prev_combinations
        if not combinations:
            prev_combinations = []
            combinations = list(itertools.combinations(sorted_players[:8], 4))

        # Prioritize combinations where players haven't played together recently
        combinations.sort(
            key=lambda comb: sum(1 for i in range(4) for j in range(i + 1, 4) if (comb[i], comb[j]) in recent_pairs),
            reverse=False)

        # Schedule the first combination
        scheduled_game = combinations[0]
        scheduled_games.append(scheduled_game)

        # Update player counters
        for player in scheduled_game:
            player_counters[player] += 1

        # Remember the combination to avoid repetition and update recent pairs
        prev_combinations.append(scheduled_game)
        for i in range(4):
            for j in range(i + 1, 4):
                recent_pairs.append((scheduled_game[i], scheduled_game[j]))

        # Keep track of only the last few recent pairs to avoid memory overflow
        recent_pairs = recent_pairs[-20:]

    # Print the schedule and player counters
    for i, game in enumerate(scheduled_games, 1):
        print(f"Game {i}: {', '.join(game)}")

    print("\nNumber of matches each player played:")
    for player, count in player_counters.items():
        print(f"{player}: {count} matches")


# Example usage
players = ["Player 1", "Player 2", "Player 3", "Player 4", "Player 5", "Player 6", "Player 7", "Player 8"]
total_games = 10
schedule_games(players, total_games)
