"""Small MOS 6502 emulator (official opcodes, NMOS decimal mode).

mem      : bytearray(65536)
read_io  : optional f(addr) -> value or None, called for $D000-$DFFF reads
hooks    : {pc: f(cpu)} run instead of the instruction at pc (used to fake KERNAL calls)
cycles   : approximate cycle counter (good enough for raster timing)
"""

ALU = ['imm', 'zp', 'zpx', 'abs', 'abx', 'aby', 'izx', 'izy']
SHF = ['acc', 'zp', 'zpx', 'abs', 'abx']
RMW = ['zp', 'zpx', 'abs', 'abx']

def _build():
    t = {}
    def put(mn, modes, codes):
        for m, c in zip(modes, codes):
            t[c] = (mn, m)
    for mn, base in (('ORA', 0x00), ('AND', 0x20), ('EOR', 0x40), ('ADC', 0x60),
                     ('LDA', 0xA0), ('CMP', 0xC0), ('SBC', 0xE0)):
        put(mn, ALU, [base + o for o in (0x09, 0x05, 0x15, 0x0D, 0x1D, 0x19, 0x01, 0x11)])
    put('STA', ALU[1:], [0x85, 0x95, 0x8D, 0x9D, 0x99, 0x81, 0x91])
    for mn, base in (('ASL', 0x00), ('ROL', 0x20), ('LSR', 0x40), ('ROR', 0x60)):
        put(mn, SHF, [base + o for o in (0x0A, 0x06, 0x16, 0x0E, 0x1E)])
    put('DEC', RMW, [0xC6, 0xD6, 0xCE, 0xDE])
    put('INC', RMW, [0xE6, 0xF6, 0xEE, 0xFE])
    put('LDX', ['imm', 'zp', 'zpy', 'abs', 'aby'], [0xA2, 0xA6, 0xB6, 0xAE, 0xBE])
    put('LDY', ['imm', 'zp', 'zpx', 'abs', 'abx'], [0xA0, 0xA4, 0xB4, 0xAC, 0xBC])
    put('STX', ['zp', 'zpy', 'abs'], [0x86, 0x96, 0x8E])
    put('STY', ['zp', 'zpx', 'abs'], [0x84, 0x94, 0x8C])
    put('CPX', ['imm', 'zp', 'abs'], [0xE0, 0xE4, 0xEC])
    put('CPY', ['imm', 'zp', 'abs'], [0xC0, 0xC4, 0xCC])
    put('BIT', ['zp', 'abs'], [0x24, 0x2C])
    put('JMP', ['abs', 'ind'], [0x4C, 0x6C])
    t[0x20] = ('JSR', 'abs')
    for mn, c in (('BPL', 0x10), ('BMI', 0x30), ('BVC', 0x50), ('BVS', 0x70),
                  ('BCC', 0x90), ('BCS', 0xB0), ('BNE', 0xD0), ('BEQ', 0xF0)):
        t[c] = (mn, 'rel')
    for mn, c in (('BRK', 0x00), ('PHP', 0x08), ('CLC', 0x18), ('PLP', 0x28), ('SEC', 0x38),
                  ('RTI', 0x40), ('PHA', 0x48), ('CLI', 0x58), ('RTS', 0x60), ('PLA', 0x68),
                  ('SEI', 0x78), ('DEY', 0x88), ('TXA', 0x8A), ('TYA', 0x98), ('TXS', 0x9A),
                  ('TAY', 0xA8), ('TAX', 0xAA), ('CLV', 0xB8), ('TSX', 0xBA), ('INY', 0xC8),
                  ('DEX', 0xCA), ('CLD', 0xD8), ('INX', 0xE8), ('NOP', 0xEA), ('SED', 0xF8)):
        t[c] = (mn, 'imp')
    return t

OPCODES = _build()
SIZE = {'imp': 1, 'acc': 1, 'imm': 2, 'zp': 2, 'zpx': 2, 'zpy': 2, 'izx': 2, 'izy': 2,
        'rel': 2, 'abs': 3, 'abx': 3, 'aby': 3, 'ind': 3}
BASECYC = {'imp': 2, 'acc': 2, 'imm': 2, 'zp': 3, 'zpx': 4, 'zpy': 4, 'abs': 4, 'abx': 4,
           'aby': 4, 'izx': 6, 'izy': 5, 'rel': 2, 'ind': 5}
EXTRA = {'JSR': 4, 'RTS': 4, 'RTI': 4, 'BRK': 5, 'PHA': 1, 'PHP': 1, 'PLA': 2, 'PLP': 2}


class CPU:
    def __init__(self, mem, read_io=None):
        self.mem, self.read_io = mem, read_io
        self.a = self.x = self.y = 0
        self.sp = 0xFF
        self.pc = 0
        self.c = self.z = self.i = self.d = self.v = self.n = 0
        self.cycles = 0
        self.hooks = {}

    # ---- memory ----
    def rd(self, a):
        if 0xD000 <= a < 0xE000 and self.read_io:
            r = self.read_io(a)
            if r is not None:
                return r
        return self.mem[a]

    def wr(self, a, v):
        self.mem[a] = v & 0xFF

    def push(self, v):
        self.mem[0x100 + self.sp] = v & 0xFF
        self.sp = (self.sp - 1) & 0xFF

    def pull(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.mem[0x100 + self.sp]

    def rts(self):
        lo = self.pull(); hi = self.pull()
        self.pc = ((hi << 8 | lo) + 1) & 0xFFFF
        self.cycles += 6

    def nz(self, v):
        self.z = int(v == 0); self.n = v >> 7
        return v

    def getp(self):
        return (self.n << 7 | self.v << 6 | 0x30 | self.d << 3 | self.i << 2 | self.z << 1 | self.c)

    def setp(self, p):
        self.n, self.v, self.d, self.i, self.z, self.c = (p >> 7 & 1, p >> 6 & 1, p >> 3 & 1,
                                                          p >> 2 & 1, p >> 1 & 1, p & 1)

    # ---- arithmetic ----
    def adc(self, m):
        a, c = self.a, self.c
        if self.d:
            lo = (a & 0x0F) + (m & 0x0F) + c
            if lo > 9: lo += 6
            hi = (a >> 4) + (m >> 4) + (lo > 0x0F)
            self.z = int(((a + m + c) & 0xFF) == 0)
            self.n = (hi << 4 >> 7) & 1
            self.v = int((~(a ^ m) & (a ^ (hi << 4)) & 0x80) != 0)
            if hi > 9: hi += 6
            self.c = int(hi > 0x0F)
            self.a = ((hi << 4) | (lo & 0x0F)) & 0xFF
        else:
            r = a + m + c
            self.v = int((~(a ^ m) & (a ^ r) & 0x80) != 0)
            self.c = int(r > 0xFF)
            self.a = self.nz(r & 0xFF)

    def sbc(self, m):
        a, b = self.a, 1 - self.c
        r = a - m - b
        self.v = int(((a ^ m) & (a ^ r) & 0x80) != 0)
        if self.d:
            lo = (a & 0x0F) - (m & 0x0F) - b
            hi = (a >> 4) - (m >> 4)
            if lo < 0: lo -= 6; hi -= 1
            if hi < 0: hi -= 6
            res = ((hi << 4) | (lo & 0x0F)) & 0xFF
        else:
            res = r & 0xFF
        self.c = int(r >= 0)
        self.nz(r & 0xFF)
        self.a = res

    def cmp(self, reg, m):
        r = reg - m
        self.c = int(r >= 0)
        self.nz(r & 0xFF)

    # ---- one instruction ----
    def step(self):
        pc = self.pc
        h = self.hooks.get(pc)
        if h:
            h(self); return
        op = self.mem[pc]
        if op not in OPCODES:
            raise RuntimeError('illegal opcode $%02X at $%04X' % (op, pc))
        mn, mode = OPCODES[op]
        rd = self.rd
        addr = None
        if mode == 'imm': addr = pc + 1
        elif mode == 'zp': addr = self.mem[pc + 1]
        elif mode == 'zpx': addr = (self.mem[pc + 1] + self.x) & 0xFF
        elif mode == 'zpy': addr = (self.mem[pc + 1] + self.y) & 0xFF
        elif mode in ('abs', 'abx', 'aby', 'ind'):
            addr = self.mem[pc + 1] | self.mem[pc + 2] << 8
            if mode == 'abx': addr = (addr + self.x) & 0xFFFF
            elif mode == 'aby': addr = (addr + self.y) & 0xFFFF
            elif mode == 'ind':
                addr = self.mem[addr] | self.mem[(addr & 0xFF00) | ((addr + 1) & 0xFF)] << 8
        elif mode == 'izx':
            zp = (self.mem[pc + 1] + self.x) & 0xFF
            addr = self.mem[zp] | self.mem[(zp + 1) & 0xFF] << 8
        elif mode == 'izy':
            zp = self.mem[pc + 1]
            addr = ((self.mem[zp] | self.mem[(zp + 1) & 0xFF] << 8) + self.y) & 0xFFFF
        elif mode == 'rel':
            off = self.mem[pc + 1]
            addr = (pc + 2 + (off - 256 if off > 127 else off)) & 0xFFFF
        self.pc = (pc + SIZE[mode]) & 0xFFFF
        self.cycles += BASECYC[mode] + EXTRA.get(mn, 0)

        if mn == 'LDA': self.a = self.nz(rd(addr))
        elif mn == 'LDX': self.x = self.nz(rd(addr))
        elif mn == 'LDY': self.y = self.nz(rd(addr))
        elif mn == 'STA': self.wr(addr, self.a)
        elif mn == 'STX': self.wr(addr, self.x)
        elif mn == 'STY': self.wr(addr, self.y)
        elif mn == 'ADC': self.adc(rd(addr))
        elif mn == 'SBC': self.sbc(rd(addr))
        elif mn == 'AND': self.a = self.nz(self.a & rd(addr))
        elif mn == 'ORA': self.a = self.nz(self.a | rd(addr))
        elif mn == 'EOR': self.a = self.nz(self.a ^ rd(addr))
        elif mn == 'CMP': self.cmp(self.a, rd(addr))
        elif mn == 'CPX': self.cmp(self.x, rd(addr))
        elif mn == 'CPY': self.cmp(self.y, rd(addr))
        elif mn == 'BIT':
            m = rd(addr); self.z = int((self.a & m) == 0); self.n = m >> 7; self.v = m >> 6 & 1
        elif mn in ('ASL', 'LSR', 'ROL', 'ROR'):
            m = self.a if mode == 'acc' else rd(addr)
            if mn == 'ASL': self.c = m >> 7; m = (m << 1) & 0xFF
            elif mn == 'LSR': self.c = m & 1; m >>= 1
            elif mn == 'ROL': c = self.c; self.c = m >> 7; m = ((m << 1) | c) & 0xFF
            else: c = self.c; self.c = m & 1; m = (m >> 1) | (c << 7)
            self.nz(m)
            if mode == 'acc': self.a = m
            else: self.wr(addr, m); self.cycles += 2
        elif mn == 'INC': self.wr(addr, self.nz((rd(addr) + 1) & 0xFF)); self.cycles += 2
        elif mn == 'DEC': self.wr(addr, self.nz((rd(addr) - 1) & 0xFF)); self.cycles += 2
        elif mn == 'INX': self.x = self.nz((self.x + 1) & 0xFF)
        elif mn == 'INY': self.y = self.nz((self.y + 1) & 0xFF)
        elif mn == 'DEX': self.x = self.nz((self.x - 1) & 0xFF)
        elif mn == 'DEY': self.y = self.nz((self.y - 1) & 0xFF)
        elif mn == 'TAX': self.x = self.nz(self.a)
        elif mn == 'TAY': self.y = self.nz(self.a)
        elif mn == 'TXA': self.a = self.nz(self.x)
        elif mn == 'TYA': self.a = self.nz(self.y)
        elif mn == 'TSX': self.x = self.nz(self.sp)
        elif mn == 'TXS': self.sp = self.x
        elif mn == 'PHA': self.push(self.a)
        elif mn == 'PHP': self.push(self.getp())
        elif mn == 'PLA': self.a = self.nz(self.pull())
        elif mn == 'PLP': self.setp(self.pull())
        elif mn == 'JMP': self.pc = addr; self.cycles -= 1
        elif mn == 'JSR':
            ret = (self.pc - 1) & 0xFFFF
            self.push(ret >> 8); self.push(ret & 0xFF); self.pc = addr
        elif mn == 'RTS': self.pc = ((self.pull() | self.pull() << 8) + 1) & 0xFFFF
        elif mn == 'RTI': self.setp(self.pull()); self.pc = self.pull() | self.pull() << 8
        elif mode == 'rel':
            flag = {'BPL': not self.n, 'BMI': self.n, 'BVC': not self.v, 'BVS': self.v,
                    'BCC': not self.c, 'BCS': self.c, 'BNE': not self.z, 'BEQ': self.z}[mn]
            if flag: self.pc = addr; self.cycles += 1
        elif mn == 'CLC': self.c = 0
        elif mn == 'SEC': self.c = 1
        elif mn == 'CLI': self.i = 0
        elif mn == 'SEI': self.i = 1
        elif mn == 'CLD': self.d = 0
        elif mn == 'SED': self.d = 1
        elif mn == 'CLV': self.v = 0
        elif mn == 'NOP': pass
        elif mn == 'BRK': raise RuntimeError('BRK at $%04X' % pc)
