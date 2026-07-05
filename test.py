import sys

import pygame

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Define the two points that make up the line
line_a = (100, 400)
line_b = (700, 200)

# Colors
COLOR_ABOVE = (0, 255, 0)  # Green
COLOR_BELOW = (255, 0, 0)  # Red
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def is_below_line(p, a, b):
    """
    Checks if point 'p' is visually below the line segment from 'a' to 'b'.
    Accounts for Pygame's inverted Y-axis.
    """
    # Prevent division by zero if the line is perfectly vertical
    if b[0] - a[0] == 0:
        return p[0] > a[0]

        # Calculate the slope (m) and y-intercept (c) of the line: y = mx + c
    slope = (b[1] - a[1]) / (b[0] - a[0])
    y_intercept = a[1] - slope * a[0]

    # Find the expected Y coordinate on the line at the point's X coordinate
    expected_y = slope * p[0] + y_intercept

    # Because Pygame's Y increases DOWNWARDS, 
    # the point is visually "below" the line if its Y is GREATER than expected_y.
    return p[1] > expected_y


# Main game loop
while True:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Get the current mouse position as our test point
    mouse_pos = pygame.mouse.get_pos()

    # Check the position and determine the color
    if is_below_line(mouse_pos, line_a, line_b):
        point_color = COLOR_BELOW
    else:
        point_color = COLOR_ABOVE

    # Draw the line
    pygame.draw.line(screen, WHITE, line_a, line_b, 3)

    # Draw the tracking point (circle)
    pygame.draw.circle(screen, point_color, mouse_pos, 10)

    pygame.display.flip()
    clock.tick(60)
