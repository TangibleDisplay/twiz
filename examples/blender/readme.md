## blender osc example

taken from https://github.com/frankiezafe/blender-pd

### usage:

start blender and open the .blend file

select "start game engine" from the "game" menus

from the Twiz manager application, send the data to port 23000

the engine expect data on the "/avatar/bone/rot" address, and the
content must be of the form "bone_name,rx,ry,rz" so you must use a
custom format and set e.g:

'testa',rx_d,ry_d,rz_d

to move the head, yes, bones names are in Spanish in the blender file.
You can look at the armature of the model when bge is not started (or
escape to leave it), to see bone names.
