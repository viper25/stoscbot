import os
import random
from collections import deque
from typing import Tuple, List

from colorama import Fore, Style
from matplotlib import pyplot as plt


def print_schedule(schedule: List[Tuple[List[str], List[str]]], highlight_player: str = None,
                   print_last_match: bool = False, all_players: List[str] = None):
    # Initialize dictionaries to count matches played and sat out for each player
    matches_played = {player: 0 for player in all_players}
    matches_sat_out = {player: 0 for player in all_players}
    total_players = sum(len(list) for list in schedule[0])

    if print_last_match:
        print(f"{len(schedule)}: Playing: {', '.join(schedule[-1][0])}, Sitting: {', '.join(schedule[-1][1])}")
    else:
        for i, match in enumerate(schedule, start=1):

            # Count matches played
            for player in match[0]:  # Players who are playing
                matches_played[player] += 1
            for player in match[1]:  # Players who are sitting out
                matches_sat_out[player] += 1

            playing_text = ', '.join(
                [f"{Fore.RED}{player_name}{Style.RESET_ALL}" if player_name == highlight_player else player_name for
                 player_name in match[0]])
            sitting_text = ', '.join(
                [f"{Fore.RED}{player_name}{Style.RESET_ALL}" if player_name == highlight_player else player_name for
                 player_name in match[1]])
            print(f"{i:02}: Playing: {playing_text}, Sitting: {sitting_text}")

            if i % len(schedule[0][0]) == 0:
                print("----------------------")

    print("\nMatches Played:")
    for player, count in matches_played.items():
        print(f"{player}: {count}")


# Main Function
def generate_badminton_doubles_schedule(all_players, num_matches) -> List[Tuple[List[str], List[str]]]:
    """
    With 6: Three players continue to play in the next game. 1 player is rotated.
    With 7 : One player continues to play in the next game. The other 3 players are rotated.
        No player sits out 2 games consecutively
    With 8 : Same rule as 7. 3 players are rotated. One continues to play. One player sits out 2 games
        consecutively
    """

    if len(all_players) < 5 or num_matches < 1 or len(all_players) > 9:
        raise ValueError("⚠️ There must be between 5-9 players to generate a schedule")

    players = deque(all_players)
    schedule = []
    num_players = len(all_players)

    # Choose any 4 players to play:
    playing = list(players)[:4]
    sitting = list(players)[4:]
    schedule.append((playing, sitting))
    # print_schedule(schedule, print_last_match=True)

    for game_no in range(num_matches - 1):

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
            # print_schedule(schedule, print_last_match=True)

        if num_players == 6:
            next_sitting = [sitting[1]] + [playing[0]]
            playing = playing[1:] + [sitting[0]]
            sitting = next_sitting

            schedule.append((playing, sitting))
            # print_schedule(schedule, print_last_match=True)

        if num_players == 7:
            next_sitting = playing[:3]
            playing = [playing[3]] + sitting[:3]
            sitting = next_sitting

            schedule.append((playing, sitting))
            # print_schedule(schedule, print_last_match=True)

        elif num_players == 8:
            next_sitting = [sitting[3]] + playing[:3]
            playing = [playing[3]] + sitting[:3]
            sitting = next_sitting

            schedule.append((playing, sitting))
            # print_schedule(schedule, print_last_match=True, highlight_player="P1")

        elif num_players == 9:
            '''
            4 play and 5 sit out, then 4 of the 5 sitting out play and 4 of the 4 playing sit out
            '''
            next_sitting = [sitting[4]] + playing[:4]
            playing = sitting[:4]
            sitting = next_sitting

            schedule.append((playing, sitting))
            # print_schedule(schedule, print_last_match=True)
    return schedule


def get_image(data):
    '''
    Function to display a table in a plot
    data = [['P1', 'P2', 'P3', 'P4'], ['P4', 'P5', 'P6', 'P7']]
    '''

    # Extract all unique players from data
    unique_players = set(player for row in data for player in row)
    # Sort the unique players to ensure consistent order
    sorted_unique_players = sorted(unique_players)

    # Define a darker color palette
    dark_colors = ['#00429d', '#93003a', '#1d6996', '#cc503e', '#164242', '#0f8554', '#de0db8', '#b2872e', '#cc503e',
                   '#94346e', '#6f4070']

    # Ensure there are enough colors for the players, repeat the palette if necessary
    if len(sorted_unique_players) > len(dark_colors):
        dark_colors = dark_colors * (len(sorted_unique_players) // len(dark_colors) + 1)

    # Dynamically assign a color to each player
    player_colors = {player: color for player, color in zip(sorted_unique_players, dark_colors)}

    # Default color for odd rows
    odd_row_color = "#f2f2f2"

    # Add headers and index column
    data = [['# ', 'P-1', 'P-2', 'P-3', 'P-4']] + [["{:02d}".format(i + 1)] + row for i, row in enumerate(data)]

    # Initialize plot
    fig, ax = plt.subplots()
    # Hide axes
    ax.axis('tight')
    ax.axis('off')

    # Create the table
    table = ax.table(cellText=data, loc='center', cellLoc='left')

    # Remove table border
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    table.auto_set_column_width(col=list(range(len(data[0]))))

    # Set line width to 0 to remove border
    for key, cell in table.get_celld().items():
        cell.set_linewidth(0)

    # Color player font and maintain odd row background color
    for i in range(len(data)):
        for j in range(len(data[i])):
            cell = table[i, j]
            player = data[i][j]
            if player in player_colors:
                # Apply player-specific font color
                cell.get_text().set_color(player_colors[player])
            if i % 2 == 0:
                # Optionally, if you still want odd rows to have a different background, uncomment the next line
                cell.set_facecolor(odd_row_color)

    # Bold every new set of games to identify them easily
    for key, cell in table.get_celld().items():
        cell.set_linewidth(0)
        # Draw a line after every 4 rows
        if (key[0] == 1) or (
                key[0] % (len(sorted_unique_players) + 1) == 0 and key[0] != 0):  # Adjust for 0-based indexing
            cell.get_text().set_weight('bold')

    # Adjust the figure size or layout before saving to ensure the table fits well
    # plt.tight_layout()
    fig_width, fig_height = fig.get_size_inches()
    fig.set_size_inches(fig_width * 0.5, fig_height)

    # Save the image as a file in the app root directory
    file_path = os.path.join(os.getcwd(), "_table_image.png")
    plt.savefig(file_path, bbox_inches='tight', dpi=200)

    # plt.show()
    return file_path


if __name__ == "__main__":
    num_matches = 20

    player_names = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    player_names = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]
    player_names = ["P1", "P2", "P3", "P4", "P5", "P6"]
    player_names = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
    player_names = ["P1", "P2", "P3", "P4", "P5"]
    player_names = ["Vibin", "Jithin", "Simon", "Vincent", "Pradeep", "Ajish", "Liju", "Johnson"]
    schedule = generate_badminton_doubles_schedule(player_names, num_matches)
    print_schedule(schedule, highlight_player="P1", all_players=player_names)

    img = get_image([match[0] for match in schedule])

    # # Display the schedule in table format
    # table_data = []
    # for i, match in enumerate(schedule):
    #     table_data.append([i + 1, ', '.join(match[0])])
    #
    # print(tabulate(table_data, headers=["#", "Players"], tablefmt="simple"))  # Good
    # print(tabulate(table_data, headers=["#", "Players"], tablefmt="rst"))  # Good
    # print(tabulate(table_data, headers=["#", "Players"], tablefmt="presto", maxcolwidths=[1, None, None]))  # Good
