# TinyPICO_V2_snake_on_Explorer_Shield_micropython

This is a ```Work-in-progress```
It contains an existing snake game ported to an Unexpected Maker Explorer Shield
with Unexpected Maker TinyPICO V2.
It works with MicroPython v1.19.1.

```DISCLAIMER:```
The intention is to have in ```main.py``` the possibility to display at boot time a bitmap image, using framebuf.Framebuffer() but I am thusfar not successful to realize this. For this reason I added in line 23 a boolean flag ```use_bmp```. In this moment
this flag is set to ```True``` in which case a TinyPICO logo will be read from an 
external .bmp file instead of the added bitmaps.py file.

```INSTALL:```

Copy all the files from the ```src``` folder to the root of the TinyPICO V2.
This can, for example, be done using the Thonny IDE.

At boot time of the microcontroller the game will automatically start.

```FLAGS:```
The main.py script has various global boolean variables:
```use_bmp``` to control the use of a bitmaps.py file or the use of an external .bmp logo file. This flag is currently set to True.

```my_debug``` to control debug output to REPL. This flag is default set to False.
Despite this flag the game will print some game info to the REPL. Also invitations to press button 2 to start a new game is (also) printed to REPL.

```use_sound``` to control wheter one wants game sounds or not. Default value: True


```
The following buttons are used for the game:
LEFT, RIGHT, UP, DOWN, 2 and Y.
Button 2 to (re)start the game.
Button Y to End the game.

A blinking text at the bottom of the screen will invite to press button 2 to (re)start.
Wait until this text has disappeared. At this moment one can also press the 'Y-button' to end the game instead of (re)starting a game.
```

For an example of the REPL output see the file ```REPL_output.txt``` in the ```docs``` folder.

LICENSE: MIT. See attached LICENSE file
