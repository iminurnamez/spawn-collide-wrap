# Spawn, Collide, Wrap   
This is a challenge designed for [/r/pygame](https://www.reddit.com/r/pygame/)  
[Link to challenge thread.](https://www.reddit.com/r/pygame/not_posted_yet)

As per request, this challenge uses essentially the same base code as the previous challenge.  This challenge continues from the completed state of the previous challenge (using dirty sprites).  

### Challenge:  
A group of obstacles have been added to our map.  
Please implement the following features:
* Sprites should not spawn inside walls.
* All sprites should correctly collide with all walls.  NPCs should consider changing direction if a wall collision occurs.
* Instead of clamping sprites to the screen, sprites that exit the screen should wrap to the other side.
* All sprites should use a collision box smaller than their image rect.  This collision box should be the "footprint" of the sprite, allowing the head of sprites to slightly overlap obstacles.


### Base code:  
Running `main.py` will give you a screen with a number of NPCs running around and one user controlled character (with the arrow keys).   All of the sprites are members of a single sprite group (obstacles and player included) called `App.all_Sprites`.  


### Suggestions:    
Implementing all of these features will require, at the least, editing the files `main.py` and `actors.py`.  You may find investigating custom collision callbacks for the sprite collision functions useful.  Obstacles and NPCs also have groups containing just their own sprites.  These may be useful when doing the collision.


### Notes:    
As always, feel free to ignore as much of my code as you like and implement everything yourself if you so desire.

