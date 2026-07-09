# My NEA
My A-level Computer Science NEA
### Requirements
pygame-ce
## What I've done so far
So far, I am in the middle of implementing line of sight into the code. I plan to have some objects not viewable through the walls while others, like the background, are viewable.
The way I'm implementing it is by utilising the pygame.draw libary. Once a wall has entered the screen, a line is drawn from the corner of the wall to off-screen. This line is relative the players position.
I then check if an object that I wish to hide lies in this shadow; if so, I cover it up so it cannot be seen.
