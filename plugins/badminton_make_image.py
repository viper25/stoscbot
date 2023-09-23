import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.colors as mcolors

def create_schedule_image(schedule, player_count, player_names):
    # Create an image with the match schedule
    fig, ax = plt.subplots(figsize=(10, 6))

    # Assign a color for each player
    colors = list(mcolors.CSS4_COLORS.values())[:len(player_names)]
    player_colors = {player: color for player, color in zip(player_names, colors)}

    y_offset = 0
    for i, match in enumerate(schedule):
        # Draw the match info
        text = f"{i+1}. {' & '.join(match[0])} vs {' & '.join(match[1])}"
        ax.text(0.1, y_offset, text, verticalalignment='top')

        # Color each player's name
        for player in match[0] + match[1]:
            start = text.find(player)
            end = start + len(player)
            ax.add_patch(Rectangle((0.1 + start * 0.045, y_offset), len(player) * 0.045, 0.15, color=player_colors[player], clip_on=False))

        y_offset -= 0.2

        # Highlight the sets of games
        if (i+1) % len(player_names) == 0:
            ax.add_patch(Rectangle((0, y_offset + 0.05), 1, len(player_names) * 0.2 - 0.05, fill=False, edgecolor='black', lw=2, linestyle='--'))

    # Show the total number of matches played by each player
    y_offset -= 0.4
    for player, count in player_count.items():
        ax.text(0.1, y_offset, f"{player}: {count} matches", verticalalignment='top', color=player_colors[player])
        y_offset -= 0.2

    ax.axis('off')
    plt.tight_layout()

    # Save the image
    plt.savefig("match_schedule.png", dpi=300, bbox_inches='tight')
    plt.show()