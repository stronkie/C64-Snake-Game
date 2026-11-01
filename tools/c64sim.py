"""Minimal C64 around cpu6502 for testing games that use the text screen.

Emulated: RAM, raster counter ($D011/$D012), SID voice 3 noise ($D41B), joystick port 2 ($DC00),
KERNAL GETIN ($FFE4, from a key queue) and clear screen ($E544). No real ROMs, no interrupts.
"""
import random
from cpu6502 import CPU

CYC_LINE, LINES = 63, 312                     # PAL
PALETTE = ['000000', 'FFFFFF', '68372B', '70A4B2', '6F3D86', '588D43', '352879', 'B8C76F',
           '6F4F25', '433900', '9A6759', '444444', '6C6C6C', '9AD284', '6C5EB5', '959595']


class C64:
    def __init__(self, prg, seed=1):
        self.mem = bytearray(65536)
        self.rng = random.Random(seed)
        self.joy = 0xFF                       # all bits high = nothing pressed
        self.keys = []
        self.cpu = CPU(self.mem, self.read_io)
        load = prg[0] | prg[1] << 8
        self.mem[load:load + len(prg) - 2] = prg[2:]
        self.mem[0xD020], self.mem[0xD021] = 14, 6
        self.cpu.hooks[0xFFE4] = self.getin
        self.cpu.hooks[0xE544] = self.clrscr
        # find "SYS nnnn" in the BASIC line and start there, returning to $FFFF if it ever exits
        txt = bytes(self.mem[0x0801:0x0820])
        sys_at = txt.index(0x9E)
        self.cpu.pc = int(txt[sys_at + 1:txt.index(0, sys_at)].decode())
        self.cpu.push(0xFF); self.cpu.push(0xFE)

    def raster(self):
        return (self.cpu.cycles // CYC_LINE) % LINES

    def read_io(self, a):
        if a == 0xD012: return self.raster() & 0xFF
        if a == 0xD011: return (self.mem[a] & 0x7F) | (0x80 if self.raster() > 255 else 0)
        if a == 0xD41B: return self.rng.getrandbits(8)
        if 0xDC00 <= a < 0xDD00 and a & 0x0F == 0: return self.joy
        return None

    def getin(self, cpu):
        cpu.a = self.keys.pop(0) if self.keys else 0
        cpu.nz(cpu.a); cpu.c = 0
        cpu.rts()

    def clrscr(self, cpu):
        self.mem[0x0400:0x07E8] = b'\x20' * 1000
        self.mem[0xD800:0xDBE8] = bytes([self.mem[0x0286] or 14]) * 1000
        cpu.rts()

    def run_cycles(self, n):
        end = self.cpu.cycles + n
        step = self.cpu.step
        while self.cpu.cycles < end:
            step()

    def run_frames(self, n):
        self.run_cycles(n * CYC_LINE * LINES)

    def run_until(self, cond, max_frames=200):
        end = self.cpu.cycles + max_frames * CYC_LINE * LINES
        step = self.cpu.step
        while not cond():
            step()
            if self.cpu.cycles > end:
                return False
        return True

    # ---- screen helpers ----
    def char(self, x, y):
        return self.mem[0x0400 + y * 40 + x]

    def row_text(self, y):
        out = ''
        for x in range(40):
            c = self.char(x, y) & 0x7F
            out += chr(c + 0x40) if 1 <= c <= 26 else chr(c) if 0x20 <= c <= 0x3F else '@' if c == 0 else '?'
        return out

    def find(self, code):
        return [(i % 40, i // 40) for i in range(1000) if self.mem[0x0400 + i] == code]

    def ascii(self, legend):
        return '\n'.join(''.join(legend.get(self.char(x, y), None) or
                                 self.row_text(y)[x] for x in range(40)) for y in range(25))

    def screenshot(self, path, scale=3):
        """Render the text screen. Letters use a stand-in font; blocks/ball/heart are drawn shapes."""
        from PIL import Image, ImageDraw, ImageFont
        cell, bord = 8 * scale, 16 * scale
        img = Image.new('RGB', (40 * cell + 2 * bord, 25 * cell + 2 * bord),
                        '#' + PALETTE[self.mem[0xD020] & 15])
        d = ImageDraw.Draw(img)
        d.rectangle([bord, bord, bord + 40 * cell - 1, bord + 25 * cell - 1], fill='#' + PALETTE[self.mem[0xD021] & 15])
        try:
            font = ImageFont.truetype('DejaVuSansMono-Bold.ttf', int(cell * 0.95))
        except OSError:
            font = ImageFont.load_default()
        for y in range(25):
            for x in range(40):
                c = self.char(x, y)
                col = '#' + PALETTE[self.mem[0xD800 + y * 40 + x] & 15]
                x0, y0 = bord + x * cell, bord + y * cell
                if c == 0x20: continue
                if c == 0xA0:
                    d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=col)
                elif c == 0x51:
                    m = scale
                    d.ellipse([x0 + m, y0 + m, x0 + cell - 1 - m, y0 + cell - 1 - m], fill=col)
                elif c == 0x53:
                    s = cell
                    d.ellipse([x0 + s * .08, y0 + s * .12, x0 + s * .52, y0 + s * .55], fill=col)
                    d.ellipse([x0 + s * .48, y0 + s * .12, x0 + s * .92, y0 + s * .55], fill=col)
                    d.polygon([(x0 + s * .1, y0 + s * .42), (x0 + s * .9, y0 + s * .42), (x0 + s * .5, y0 + s * .92)], fill=col)
                else:
                    ch = self.row_text(y)[x]
                    d.text((x0 + cell / 2, y0 + cell / 2), ch, fill=col, font=font, anchor='mm')
        img.save(path)
