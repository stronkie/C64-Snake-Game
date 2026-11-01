# C64-Snake-Game
Commodore 64 Snake Game

Info about the Game :

**Stronkie's Snake** is a Snake game for the Commodore 64, written in 6502 assembly.
Steer the snake around the walled playfield, eat the hearts to grow and score,
and don't hit the walls or your own body.

Load it in VICE or on a real C64 (SD2IEC, Kung Fu Flash, Ultimate, Pi1541, or a floppy written from the .d64):

```
LOAD"SNAKE",8
RUN
```

- **Menu:** fire, SPACE or RETURN starts the game. Joystick left/right or A / D sets the speed,
  joystick up/down or W switches wrap-around on or off.
- **Game:** joystick in port 2, or W A S D. You have 3 lives, shown as apples at the top right.
  Eat 10 apples to reach the next level. P, RETURN, F1 or the fire button pauses the game.
- **After game over:** with a Hall of Fame score you type your initials (joystick up/down and fire,
  or the keyboard and RETURN); otherwise fire or any key goes back to the menu.

Features:

- 10 levels, each with its own maze; 10 apples per level, then back to level 1 at your current speed
- A proper snake: head with eyes facing the way it moves, scaled body, rounded corners and a tapered tail
- The snake gets faster every 5 apples
- Bonus stars (worth 5 points) and power-ups appear now and then and vanish after about 4 seconds:
  - **Clock:** the game runs at half speed for 10 seconds
  - **Scissors:** the snake is cut in half (at least 4 pieces stay)
  - **Ghost:** for 6 seconds the snake goes straight through walls and edges
  - An icon on the top line shows a running clock or ghost, blinking just before it ends
- Bonus level after levels 5 and 10: 32 apples to eat in 30 seconds, +25 when you eat them all.
  Running out of time or crashing just ends the bonus level, it never costs a life
- Pause: "-- PAUSED --" blinks on the top line until you press P, RETURN, F1, SPACE or fire
- A heartbeat that beats faster as the snake grows
- Wrap-around option: leave through one edge and come back on the other side
- Hall of Fame: top 10 with initials, saved on the disk; the menu shows it in turn with the title picture
- Little effects: new apples sparkle, the border flashes on a crash, "LEVEL nn" and "GET READY" before each life

- Main menu: the Stronkie's Snake artwork as a hi-res bitmap (with "Created By Mark Stronks (C) 2026"), and a panel showing speed, last score, hi-score and controls
- Three speeds: SLOW, NORMAL, FAST
- 3 lives, shown as small red apple sprites; losing one restarts the snake and keeps your score
- Game screen with the title "STRONKIE'S SNAKE" in yellow next to the score
- Sound effects: a rising "bloop" when eating an apple, a crash when you lose a life
- The Hall of Fame is saved on the disk as the file HISCORE whenever you get in, and loaded at start-up
  (a HISCORE file from V0.07/V0.08 is taken over as "YOU").
  Needs a writable disk: a real 1541 disk without write protection, SD2IEC, Pi1541 or an Ultimate.
  Without one the game still works and tells you the score was not saved.
- Menu music: "Cool Tune" by Charles Deenen (1987, Scoop Designs), looping until the game starts.
  Plays on any C64 (one SID)
- Reversing into yourself is blocked, so a quick wrong key won't end the game

Version numbers :

The latest version is in the main folder, older ones are in `previous versions`.
Each version has a `.prg` (the program) and a `.d64` (a disk image with the program on it, named SNAKE).
The version number is shown on screen from V0.03 on.

| Version | Files |
|---|---|
| **V0.11** (latest) | `snake_v0.11.prg`, `snake_v0.11.d64` |
| V0.10 | `previous versions/snake_v0.10.prg`, `.d64` |
| V0.09 | `previous versions/snake_v0.09.prg`, `.d64` |
| V0.08 | `previous versions/snake_v0.08.prg`, `.d64` |
| V0.07 | `previous versions/snake_v0.07.prg`, `.d64` |
| V0.06 | `previous versions/snake_v0.06.prg`, `.d64` |
| V0.05 | `previous versions/snake_v0.05.prg`, `.d64` |
| V0.04 | `previous versions/snake_v0.04.prg`, `.d64` |
| V0.03 | `previous versions/snake_v0.03.prg`, `.d64` |
| V0.02 | `previous versions/snake_v0.02.prg`, `.d64` |
| V0.01 | `previous versions/snake_v0.01.prg`, `.d64` |

Change Log:

**V0.11** (2026-11-01)
- New menu music: "Cool Tune" by Charles Deenen (1987), one SID, replacing the stereo "Sad Song"
- The tune's zero-page variables were moved ($EB-$FF to $40-$57) so it doesn't clash with the C64's
  keyboard routine and no longer clears $00-$02 when it starts; it sounds exactly the same
- Second-SID detection removed (no longer needed)
- Program down from 74 to 48 blocks: loads much faster

**V0.10** (2026-11-01)
- Title picture compressed (6750 to 4103 bytes): the program is down from 81 to 74 blocks, so it loads faster
- Power-ups: clock (half speed for 10 s), scissors (cut the snake in half), ghost (through walls for 6 s), with icons on the top line
- Pause key: P, RETURN, F1 or fire
- Bonus level after levels 5 and 10: 32 apples in 30 seconds, +25 for clearing it, no life lost

**V0.09** (2026-11-01)
- 10 levels with mazes, 10 apples per level, "LEVEL nn" shown on screen and on the top line
- New snake graphics: head with eyes, body, corners and tail; new apple, bonus star and brick walls
- Speed-up every 5 apples
- Bonus stars worth 5 points, for about 4 seconds
- Heartbeat sound that speeds up as the snake grows
- Wrap-around option in the menu (W or joystick up/down)
- Hall of Fame: top 10 with 3-letter initials, entered by joystick or keyboard, saved as HISCORE
- Menu alternates between the title picture and the Hall of Fame
- Effects: apples sparkle when they appear, the border flashes on a crash, GET READY before each life
- Random numbers now come from the program itself, so all three SID voices are free for sound

**V0.08** (2026-11-01)
- New main menu picture: bigger title, the snake about to eat an apple, and "Created By Mark Stronks (C) 2026" in red and light red
- The picture converter now keeps red lettering (cells can be white, cyan, red or light red on blue)

**V0.07** (2026-11-01)
- Hi-score file HISCORE on the disk: loaded at start-up, saved whenever the hi-score is beaten (old file is scratched first)
- Uses the drive the game was loaded from (device 8 if loaded from tape)
- 3 lives; losing one restarts the snake in the middle and keeps the score
- Lives shown as small red apple sprites (multicolour, with leaf and shine) at the top right
- Title "STRONKIE'S SNAKE" in yellow on the game screen, score in white
- Sound effects: eating an apple, losing a life
- Messages at game over: "NEW HI-SCORE SAVED TO DISK" or "NEW HI-SCORE (NOT SAVED)"

**V0.06** (2026-11-01)
- New main menu: the Stronkie's Snake artwork shown as a C64 hi-res bitmap (white title, cyan drawing on blue)
- Panel on the right with version, speed, last score, hi-score, controls and music credit, in the C64's own font
- Old character-based menu removed
- Program is now 69 blocks (the picture takes about 7 KB)

**V0.05** (2026-11-01)
- Menu music: "Sad Song" by Antti Hannula (Flex), looping until the game starts
- Detects a second SID at $D500: stereo with two SIDs, first SID only on a standard C64
- Music stops when the game starts and starts again from the beginning back in the menu
- Music credit on the menu screen
- New memory layout around the music at $1000 (program is now 46 blocks)

**V0.04** (2026-11-01)
- New main menu screen "Stronkie's Snake", based on artwork: slanted frame, maze with snake and apple, blinking cursor under READY.
- Speed setting: SLOW, NORMAL, FAST
- Last score and hi-score on the menu
- Game over now returns to the menu

**V0.03** (2026-11-01)
- Version number shown on the game screen
- Fixed the BASIC start line's link pointer

**V0.02** (2026-11-01)
- First build with the Python toolchain (starts at 10 SYS 2061)

**V0.01** (2026-11-01)
- First version: walled playfield, snake that grows when it eats, random apples, 4-digit score, game over on walls or own body
- Controls: joystick port 2 or W A S D
