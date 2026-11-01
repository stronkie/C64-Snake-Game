"""Two-pass 6502 assembler for C64 programs.

Syntax
  ; comment
  NAME = expr                 constant
  label:  [instruction]       label (may share a line with an instruction)
  .org expr                   set program counter
  .basic label                BASIC line "10 SYS <label>" (put right after .org $0801)
  .byte e1, e2, ...           bytes
  .word e1, ...               16-bit little-endian words
  .text "TEXT"                C64 screen codes (upper case set)
  .fill count, expr           count bytes, expr may use i = 0..count-1
  lda #<expr / #>expr         low / high byte
  (zp,x)  (zp),y  (abs)       indirect modes
Numbers: $ff hex, %1010 binary, 123 decimal. Expressions are Python arithmetic.

Usage: python3 asm6502.py source.s out.prg   (also writes .lst listing and .vs VICE labels)
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cpu6502 import OPCODES, SIZE

OPC = {(mn, md): op for op, (mn, md) in OPCODES.items()}
MNEMS = {mn for mn, _ in OPC}


class AsmError(Exception):
    pass


class Unknown(Exception):
    pass


class Syms(dict):
    def __missing__(self, k):
        raise Unknown(k)


def screencode(ch):
    o = ord(ch)
    if 0x40 <= o <= 0x5F: return o - 0x40      # @ A-Z [ \ ] ^ _
    if 0x61 <= o <= 0x7A: return o - 0x60      # lower case -> same letters
    if 0x20 <= o <= 0x3F: return o             # space, digits, punctuation
    raise AsmError('no screen code for %r' % ch)


def split_args(s):
    out, depth, cur, q = [], 0, '', False
    for ch in s:
        if ch == '"': q = not q
        if ch == '(' and not q: depth += 1
        if ch == ')' and not q: depth -= 1
        if ch == ',' and depth == 0 and not q:
            out.append(cur.strip()); cur = ''
        else:
            cur += ch
    if cur.strip(): out.append(cur.strip())
    return out


class Assembler:
    def __init__(self):
        self.syms = Syms()

    def ev(self, expr, extra=None, need=False):
        e = expr.strip()
        lowhi = None
        if e[:1] in '<>':
            lowhi, e = e[0], e[1:]
        py = re.sub(r'\$([0-9A-Fa-f]+)', r'0x\1', e)
        py = re.sub(r'(?<![\w)])%([01]+)', r'0b\1', py)
        env = Syms(self.syms)
        if extra: env.update(extra)
        try:
            v = int(eval(py, {'__builtins__': {}}, env))
        except Unknown as u:
            if need: raise AsmError('unknown symbol %s' % u)
            return None
        if lowhi == '<': v &= 0xFF
        elif lowhi == '>': v = (v >> 8) & 0xFF
        return v

    def parse_operand(self, mn, arg):
        a = arg.strip()
        if a == '' or a.lower() == 'a':
            return ('acc' if (mn, 'acc') in OPC else 'imp'), None
        if a.startswith('#'):
            return 'imm', a[1:]
        m = re.fullmatch(r'\((.+),\s*[xX]\s*\)', a)
        if m: return 'izx', m.group(1)
        m = re.fullmatch(r'\((.+)\)\s*,\s*[yY]', a)
        if m: return 'izy', m.group(1)
        if mn == 'JMP' and re.fullmatch(r'\(.+\)', a):
            return 'ind', a[1:-1]
        m = re.fullmatch(r'(.+),\s*([xXyY])', a)
        if m: return 'idx' + m.group(2).lower(), m.group(1)
        if (mn, 'rel') in OPC: return 'rel', a
        return 'dir', a

    def assemble(self, src):
        lines = src.split('\n')
        self.sizes = {}
        for passno in (1, 2):
            self.pc, out, self.listing = None, {}, []
            for ln, raw in enumerate(lines, 1):
                try:
                    self.line(passno, ln, raw, out)
                except AsmError as e:
                    raise AsmError('line %d: %s\n    %s' % (ln, e, raw.strip()))
        start, end = min(out), max(out) + 1
        data = bytearray(end - start)
        for a, v in out.items():
            data[a - start] = v
        return start, bytes(data)

    def emit(self, out, bytes_, passno):
        for b in bytes_:
            if passno == 2:
                if self.pc in out: raise AsmError('overlap at $%04X' % self.pc)
                out[self.pc] = b & 0xFF
            self.pc += 1

    def line(self, passno, ln, raw, out):
        s, q = '', False
        for ch in raw:                      # cut the comment, but not a ';' inside "..."
            if ch == '"': q = not q
            if ch == ';' and not q: break
            s += ch
        s = s.strip()
        if not s: return
        m = re.match(r'([A-Za-z_]\w*)\s*=\s*(.+)$', s)
        if m:
            v = self.ev(m.group(2), need=(passno == 2))
            if v is not None: self.syms[m.group(1)] = v
            return
        m = re.match(r'([A-Za-z_]\w*):\s*(.*)$', s)
        if m:
            if passno == 1 and m.group(1) in self.syms:
                raise AsmError('label %s defined twice' % m.group(1))
            self.syms[m.group(1)] = self.pc
            s = m.group(2).strip()
            if not s: return
        here = self.pc
        word, _, rest = s.partition(' ')
        w = word.lower()
        need = passno == 2
        if w == '.org':
            self.pc = self.ev(rest, need=True); return
        if self.pc is None: raise AsmError('no .org before code')
        if w == '.basic':
            target = self.ev(rest, need=need) or 0
            nxt = self.pc + 12
            line_ = [nxt & 0xFF, nxt >> 8, 10, 0, 0x9E] + [ord(c) for c in '%04d' % target] + [0, 0, 0]
            if target > 9999: raise AsmError('SYS target too high')
            self.emit(out, line_, passno)
        elif w == '.byte':
            self.emit(out, [self.ev(a, need=need) or 0 for a in split_args(rest)], passno)
        elif w == '.word':
            for a in split_args(rest):
                v = self.ev(a, need=need) or 0
                self.emit(out, [v & 0xFF, v >> 8], passno)
        elif w == '.text':
            t = rest.strip()
            if not (t.startswith('"') and t.endswith('"')): raise AsmError('.text needs "..."')
            self.emit(out, [screencode(c) for c in t[1:-1]], passno)
        elif w == '.fill':
            cnt, expr = split_args(rest)
            n = self.ev(cnt, need=True)
            self.emit(out, [(self.ev(expr, {'i': i}, need=need) or 0) & 0xFF for i in range(n)], passno)
        else:
            mn = w.upper()
            if mn not in MNEMS: raise AsmError('unknown instruction %s' % word)
            mode, arg = self.parse_operand(mn, rest)
            v = self.ev(arg, need=need) if arg is not None else None
            if mode in ('dir', 'idxx', 'idxy'):
                key = (ln, self.pc if passno == 1 else None)
                if passno == 1:
                    zp = v is not None and v < 256
                    suffix = {'dir': '', 'idxx': 'x', 'idxy': 'y'}[mode]
                    zmode, amode = 'zp' + suffix, ('abs' if not suffix else 'ab' + suffix)
                    mode = zmode if zp and (mn, zmode) in OPC else amode
                    self.sizes[ln] = mode
                else:
                    mode = self.sizes[ln]
            if (mn, mode) not in OPC: raise AsmError('%s does not support mode %s' % (mn, mode))
            op = OPC[(mn, mode)]
            n = SIZE[mode]
            if passno == 2:
                if mode == 'rel':
                    off = v - (self.pc + 2)
                    if not -128 <= off <= 127: raise AsmError('branch out of range (%d)' % off)
                    v = off & 0xFF
                if n == 2 and not 0 <= v <= 255: raise AsmError('value $%X too big for a byte' % v)
            bs = [op] + ([] if n == 1 else [(v or 0) & 0xFF] if n == 2 else [(v or 0) & 0xFF, ((v or 0) >> 8) & 0xFF])
            self.emit(out, bs, passno)
        if passno == 2:
            code = ' '.join('%02X' % out[a] for a in range(here, self.pc))
            self.listing.append('%04X  %-24s %s' % (here, code[:24], raw.rstrip()))


def build(src_path, prg_path):
    asm = Assembler()
    start, data = asm.assemble(open(src_path).read())
    with open(prg_path, 'wb') as f:
        f.write(bytes([start & 0xFF, start >> 8]) + data)
    base = os.path.splitext(prg_path)[0]
    open(base + '.lst', 'w').write('\n'.join(asm.listing) + '\n')
    labels = sorted((v, k) for k, v in asm.syms.items() if isinstance(v, int) and start <= v < start + len(data))
    open(base + '.vs', 'w').write(''.join('al C:%04x .%s\n' % (v, k) for v, k in labels))
    return asm, start, data


if __name__ == '__main__':
    try:
        asm, start, data = build(sys.argv[1], sys.argv[2])
    except AsmError as e:
        sys.exit('error: %s' % e)
    print('%s: $%04X-$%04X, %d bytes' % (sys.argv[2], start, start + len(data) - 1, len(data)))
