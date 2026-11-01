"""Play-test snake.prg in the Python C64 emulator.

    python3 test_snake.py         (run build.py first)
Writes shots/boot.png, shots/playing.png, shots/gameover.png
"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, 'tools'))
os.chdir(here)
from asm6502 import Assembler
from c64sim import C64

asm = Assembler(); asm.assemble(open('snake.s').read())
S = asm.syms
PRG = open('snake.prg', 'rb').read()
os.makedirs('shots', exist_ok=True)

UP, DOWN, LEFT, RIGHT = 3, 2, 1, 0
JOY = {UP: 0xFE, DOWN: 0xFD, LEFT: 0xFB, RIGHT: 0xF7}
DXY = {RIGHT: (1, 0), LEFT: (-1, 0), DOWN: (0, 1), UP: (0, -1)}
BODY, APPLE, WALL, SPACE = 0x51, 0x53, 0xA0, 0x20
fails = 0


def check(ok, msg):
    global fails
    print(('  ok   ' if ok else '  FAIL ') + msg)
    fails += not ok


def head(c): return c.mem[S['headx']], c.mem[S['heady']]
def score(c): return c.row_text(0)[6:10]
def length(c): return (c.mem[S['headidx']] - c.mem[S['tailidx']]) % 256 + 1
def is_over(c): return 'GAME OVER - FIRE OR KEY' in c.row_text(12)
def in_gameover(c): return S['go_pause'] <= c.cpu.pc < S['setptr']


def boot(seed=1):
    c = C64(PRG, seed)
    ok = c.run_until(lambda: c.cpu.pc == S['mainloop'], 50)
    assert ok, 'never reached mainloop'
    return c


def step(c):
    """Run until the snake has moved once (or the game ended). Returns frames used."""
    h0, c0 = c.mem[S['headidx']], c.cpu.cycles
    c.run_until(lambda: c.mem[S['headidx']] != h0 or in_gameover(c), 30)
    c.run_until(lambda: c.cpu.pc == S['mainloop'] or in_gameover(c), 30)   # finish drawing
    return (c.cpu.cycles - c0) / (63 * 312)


print('1. Boot')
c = boot()
check(score(c) == '0000' and c.row_text(0).startswith('SCORE 0000'), 'score line reads "SCORE 0000"')
check(all(c.char(x, 1) == WALL and c.char(x, 24) == WALL for x in range(40)) and
      all(c.char(0, y) == WALL and c.char(39, y) == WALL for y in range(1, 25)), 'walls on all four sides')
check([p for p in c.find(BODY)] == [(17, 12), (18, 12), (19, 12), (20, 12)], 'snake of 4 at row 12, x 17-20')
apples = c.find(APPLE)
check(len(apples) == 1 and 1 <= apples[0][0] <= 38 and 2 <= apples[0][1] <= 23, 'one apple inside the field at %s' % apples)
check(c.mem[0xD020] == 0 and c.mem[0xD021] == 0, 'black border and background')
c.screenshot('shots/boot.png')
frames = step(c)
check(head(c) == (21, 12), 'moves right on its own -> head %s' % (head(c),))
check(5.5 <= frames <= 6.5, 'one step every %.1f frames (SPEED = 6)' % frames)

print('2. Keyboard')
c = boot(); c.keys = [0x53]                       # S
step(c); check(head(c) == (20, 13), 'S turns down -> head %s' % (head(c),))
c = boot(); c.keys = [0x41]                       # A = reverse while going right
step(c); check(head(c) == (21, 12), 'A (reverse) is ignored -> head %s' % (head(c),))
c = boot(); c.keys = [0x57]; step(c)              # W
check(head(c) == (20, 11), 'W turns up -> head %s' % (head(c),))
c.keys = [0x44]; step(c)                          # D
check(head(c) == (21, 11), 'D turns right -> head %s' % (head(c),))

print('3. Autopilot with the joystick: eat 10 apples')
c = boot(seed=7)
steps = 0
while score(c) != '0010' and steps < 2000 and not is_over(c):
    hx, hy = head(c)
    ax, ay = c.find(APPLE)[0]
    cur = c.mem[S['dir']]
    def good(d):
        nx, ny = hx + DXY[d][0], hy + DXY[d][1]
        return d != cur ^ 1 and c.char(nx, ny) in (SPACE, APPLE)
    options = sorted([d for d in DXY if good(d)], key=lambda d: abs(hx + DXY[d][0] - ax) + abs(hy + DXY[d][1] - ay))
    c.joy = JOY[options[0]] if options else 0xFF
    step(c); steps += 1
    if steps % 40 == 0 and score(c) == '0005':
        c.screenshot('shots/playing.png')
c.joy = 0xFF
check(score(c) == '0010', 'score 0010 after %d steps' % steps)
check(length(c) == 14, 'snake grew to %d segments (4 + 10)' % length(c))
check(len(c.find(BODY)) == 14, '%d body pieces drawn on screen' % len(c.find(BODY)))
check(len(c.find(APPLE)) == 1, 'exactly one apple on screen')
check(not is_over(c), 'still alive')
c.screenshot('shots/playing.png')
print(c.ascii({BODY: 'o', APPLE: '*', WALL: '#', SPACE: ' '}))

print('4. Running into its own body')
cur = c.mem[S['dir']]
hx, hy = head(c)
for p in (cur ^ 2, cur ^ 3):                       # the two perpendicular directions
    c1 = (hx + DXY[p][0], hy + DXY[p][1])
    c2 = (c1[0] - DXY[cur][0], c1[1] - DXY[cur][1])
    if c.char(*c1) == SPACE and c.char(*c2) == SPACE: break
neck = (hx - DXY[cur][0], hy - DXY[cur][1])
check(c.char(*neck) == BODY, 'body segment right behind the head at %s' % (neck,))
for d in (p, cur ^ 1, p ^ 1):                      # turn, come back, turn into the neck
    c.joy = JOY[d]; step(c)
c.joy = 0xFF
check(is_over(c), 'U-turn into the body ends the game')
check(head(c) == c2, 'head stopped next to the body at %s' % (head(c),))

print('5. Running into a wall')
c = boot(); c.joy = JOY[UP]
n = 0
while not is_over(c) and n < 30:
    step(c); n += 1
c.joy = 0xFF
check(is_over(c) and head(c) == (20, 2), 'game over at the top wall after %d steps, head %s' % (n, head(c)))
check(c.row_text(12)[8:31] == 'GAME OVER - FIRE OR KEY', 'message: "%s"' % c.row_text(12)[8:31])
c.screenshot('shots/gameover.png')

print('6. Restart')
c.run_frames(30)
check(is_over(c), 'still waiting after 30 frames (50-frame pause)')
c.run_frames(30); c.keys = [0x58]                 # X
c.run_until(lambda: c.cpu.pc == S['mainloop'], 20)
check(not is_over(c) and score(c) == '0000' and len(c.find(BODY)) == 4, 'any key starts a new game')
c = boot(); c.joy = JOY[UP]
while not is_over(c): step(c)
c.joy = 0xEF                                      # hold fire from the crash on
c.run_frames(80)
check(is_over(c), 'fire held through the crash does not restart')
c.joy = 0xFF; c.run_frames(2); c.joy = 0xEF
c.run_until(lambda: c.cpu.pc == S['mainloop'], 20); c.joy = 0xFF
check(not is_over(c) and score(c) == '0000', 'release + press fire starts a new game')

print('\n%s' % ('ALL TESTS PASSED' if not fails else '%d TEST(S) FAILED' % fails))
sys.exit(1 if fails else 0)
