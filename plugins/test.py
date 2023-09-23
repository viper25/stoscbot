from itertools import combinations
from collections import Counter
import random

from PIL import Image, ImageDraw, ImageFont


def generate_fair_schedule(player_names, num_matches):
    # Create all possible pairs
    all_pairs = list(combinations(player_names, 2))

    # Create all possible matches
    possible_matches = []
    for pair1 in all_pairs:
        for pair2 in all_pairs:
            if len(set(pair1 + pair2)) == 4:  # No repeated players in a match
                possible_matches.append((pair1, pair2))
    random.shuffle(possible_matches)

    # Initialize match counter for each player
    player_count = Counter()

    # Generate a fair schedule
    schedule = []
    for i in range(num_matches):
        for match in possible_matches:
            team1, team2 = match

            # Calculate the sum of all player's current matches in this potential match
            total_count = sum(player_count[player] for player in team1 + team2)

            if len(schedule) < num_matches and total_count == min(
                sum(player_count[player] for player in m[0] + m[1]) for m in possible_matches
            ):
                schedule.append(match)
                for player in team1 + team2:
                    player_count[player] += 1
                possible_matches.remove(match)
                break

    return schedule, player_count

# Number of matches and player names
booking_time = 120  # minutes
avg_time_per_match = (10 + 14) // 2  # Average between 10 and 14 minutes per match
num_matches = booking_time // avg_time_per_match  # Number of matches to be played

player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip", "Vibin", "Dibu"]
player_names = ["Anub", "Jubin", "Simon", "Ajsh", "Vinct", "Liju", "Jithin", "Prdip", "Vibin"]
schedule, player_count = generate_fair_schedule(player_names, num_matches)


from tabulate import tabulate
# Display the schedule in table format
table_data = []
for i, match in enumerate(schedule):
    table_data.append([i+1, '|'.join(match[0]), 'vs', '|'.join(match[1])])
print(tabulate(table_data, headers=["#", "Team 1", "", "Team 2"]))




# Create image representation of the schedule
font = ImageFont.truetype("arial.ttf", size=20)
width, height = 800, 50 + 40 * (len(schedule) + 1)  # Calculate the size dynamically based on number of matches

img = Image.new("RGB", (width, height), color="white")
d = ImageDraw.Draw(img)

header = ["Match #", "Team 1", "vs", "Team 2"]
d.text((10, 10), header[0], fill="black", font=font)
d.text((100, 10), header[1], fill="black", font=font)
d.text((360, 10), header[2], fill="black", font=font)
d.text((420, 10), header[3], fill="black", font=font)

for i, match in enumerate(schedule, start=1):
    y_pos = 50 + i * 40
    d.text((10, y_pos), str(i), fill="black", font=font)
    d.text((100, y_pos), ' & '.join(match[0]), fill="black", font=font)
    d.text((360, y_pos), "vs", fill="black", font=font)
    d.text((420, y_pos), ' & '.join(match[1]), fill="black", font=font)

img.save("schedule.png")



# Display the schedule
print("### Match Schedule ###")
for i, match in enumerate(schedule):
    print(f"{i+1}. {' & '.join(match[0])} vs {' & '.join(match[1])}")

# Display the number of matches for each player
print("\n### Player Participation Counts ###")
for player, count in player_count.items():
    print(f"{player}: {count} matches")
