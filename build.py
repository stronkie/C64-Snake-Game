"""Build Snake: snake.s -> snake.prg (+ listing, VICE labels) -> snake.d64

    python3 build.py
Then in VICE:  x64sc snake.d64   (or: x64sc -moncommands snake.vs snake.prg  for labels in the monitor)
"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, 'tools'))
from asm6502 import build, AsmError
import d64

os.chdir(here)
try:
    asm, start, data = build('snake.s', 'snake.prg')
except AsmError as e:
    sys.exit('assembly error: %s' % e)
print('snake.prg   $%04X-$%04X  %d bytes  (listing: snake.lst, labels: snake.vs)'
      % (start, start + len(data) - 1, len(data)))

d64.write('snake.d64', 'SNAKE', 'SN', [('SNAKE', open('snake.prg', 'rb').read())])
disk, files, free = d64.read('snake.d64')
assert files[0][2] == open('snake.prg', 'rb').read(), 'disk read-back mismatch'
print('snake.d64   "%s": %s, %d blocks, %d blocks free (read back OK)'
      % (disk, files[0][0], files[0][1], free))
