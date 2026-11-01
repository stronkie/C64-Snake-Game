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

- **Menu:** fire, SPACE or RETURN starts the game. Joystick left/right or A / D sets the speed.
- **Game:** joystick in port 2, or W A S D. You have 3 lives, shown as apples at the top right.
- **After game over:** fire or any key goes back to the menu.

Features:

- Main menu: the Stronkie's Snake artwork as a hi-res bitmap (with "Created By Mark Stronks (C) 2026"), and a panel showing speed, last score, hi-score and controls
- Three speeds: SLOW, NORMAL, FAST
- 3 lives, shown as small red apple sprites; losing one restarts the snake and keeps your score
- Game screen with the title "STRONKIE'S SNAKE" in yellow next to the score
- Sound effects: a rising "bloop" when eating an apple, a crash when you lose a life
- Hi-score saved on the disk as the file HISCORE every time it is beaten, and loaded at start-up.
  Needs a writable disk: a real 1541 disk without write protection, SD2IEC, Pi1541 or an Ultimate.
  Without one the game still works and tells you the hi-score was not saved.
- Menu music: "Sad Song" by Antti Hannula (Flex), 2020, looping until the game starts
- Full stereo music with a second SID at $D500 (Ultimate 64 / UltiSID, SIDFX, dual-SID boards, VICE).
  On a standard single-SID C64 the first SID's three voices play.
  VICE: add 1 extra SID at $D500, or `x64sc -sidextra 1 -sid2address 0xd500 snake_v0.08.d64`
- Reversing into yourself is blocked, so a quick wrong key won't end the game

Version numbers :

The latest version is in the main folder, older ones are in `previous versions`.
Each version has a `.prg` (the program) and a `.d64` (a disk image with the program on it, named SNAKE).
The version number is shown on screen from V0.03 on.

| Version | Files |
|---|---|
| **V0.08** (latest) | `snake_v0.08.prg`, `snake_v0.08.d64` |
| V0.07 | `previous versions/snake_v0.07.prg`, `.d64` |
| V0.06 | `previous versions/snake_v0.06.prg`, `.d64` |
| V0.05 | `previous versions/snake_v0.05.prg`, `.d64` |
| V0.04 | `previous versions/snake_v0.04.prg`, `.d64` |
| V0.03 | `previous versions/snake_v0.03.prg`, `.d64` |
| V0.02 | `previous versions/snake_v0.02.prg`, `.d64` |
| V0.01 | `previous versions/snake_v0.01.prg`, `.d64` |

Change Log:

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
