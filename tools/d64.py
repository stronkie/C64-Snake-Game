"""Write and read 1541 disk images (.d64, 35 tracks).

  python3 d64.py write disk.d64 "DISK NAME" ID file1.prg[=NAME] ...
  python3 d64.py list  disk.d64
"""
import sys

SPT = [21] * 17 + [19] * 7 + [18] * 6 + [17] * 5          # sectors per track 1..35


def offset(t, s):
    return (sum(SPT[:t - 1]) + s) * 256


def petscii_name(name):
    b = name.upper().encode('ascii')[:16]
    return b + b'\xa0' * (16 - len(b))


def write(path, disk_name, disk_id, files):
    img = bytearray(sum(SPT) * 256)
    used = {t: set() for t in range(1, 36)}
    used[18] |= {0, 1}
    # allocation order: tracks nearest the directory first, interleave 10 like the 1541
    order = [t for d in range(1, 18) for t in (18 - d, 18 + d) if 1 <= t <= 35]
    entries = []
    for fname, data in files:
        blocks = [data[i:i + 254] for i in range(0, len(data), 254)] or [b'']
        chain = []
        for _ in blocks:
            for t in order:
                free = [s for s in range(SPT[t - 1]) if s not in used[t]]
                if free:
                    s0 = (chain[-1][1] + 10) % SPT[t - 1] if chain and chain[-1][0] == t else 0
                    s = min(free, key=lambda s: (s - s0) % SPT[t - 1])
                    used[t].add(s); chain.append((t, s)); break
            else:
                raise SystemExit('disk full')
        for i, ((t, s), blk) in enumerate(zip(chain, blocks)):
            o = offset(t, s)
            if i + 1 < len(chain):
                img[o], img[o + 1] = chain[i + 1]
            else:
                img[o], img[o + 1] = 0, len(blk) + 1
            img[o + 2:o + 2 + len(blk)] = blk
        entries.append((fname, chain[0], len(chain)))
    if len(entries) > 8:
        raise SystemExit('this simple writer supports up to 8 files')
    # directory sector 18/1
    d = offset(18, 1)
    img[d], img[d + 1] = 0, 0xFF
    for i, (fname, (t, s), n) in enumerate(entries):
        e = d + i * 32
        img[e + 2] = 0x82                                # closed PRG
        img[e + 3], img[e + 4] = t, s
        img[e + 5:e + 21] = petscii_name(fname)
        img[e + 30], img[e + 31] = n & 0xFF, n >> 8
    # BAM 18/0
    b = offset(18, 0)
    img[b:b + 4] = bytes([18, 1, 0x41, 0])
    for t in range(1, 36):
        bits = 0
        for s in range(SPT[t - 1]):
            if s not in used[t]:
                bits |= 1 << s
        img[b + 4 * t:b + 4 * t + 4] = bytes([SPT[t - 1] - len(used[t]), bits & 0xFF, bits >> 8 & 0xFF, bits >> 16])
    img[b + 0x90:b + 0xA0] = petscii_name(disk_name)
    img[b + 0xA0:b + 0xAB] = b'\xa0\xa0' + disk_id.upper().encode()[:2].ljust(2) + b'\xa02A\xa0\xa0\xa0\xa0'
    open(path, 'wb').write(img)


def read(path):
    """Return (disk name, [(name, blocks, data)]) by following the real link chains."""
    img = open(path, 'rb').read()
    b = offset(18, 0)
    disk = img[b + 0x90:b + 0xA0].rstrip(b'\xa0').decode('ascii', 'replace')
    files, (t, s) = [], (18, 1)
    while t:
        o = offset(t, s)
        for i in range(8):
            e = o + i * 32
            if img[e + 2] & 7 == 2:
                name = img[e + 5:e + 21].rstrip(b'\xa0').decode('ascii', 'replace')
                data, (ft, fs) = b'', (img[e + 3], img[e + 4])
                while ft:
                    fo = offset(ft, fs)
                    nt, ns = img[fo], img[fo + 1]
                    data += img[fo + 2:fo + 256] if nt else img[fo + 2:fo + ns + 1]
                    ft, fs = nt, ns
                files.append((name, img[e + 30] | img[e + 31] << 8, data))
        t, s = img[o], img[o + 1]
    free = sum(img[b + 4 * t] for t in range(1, 36) if t != 18)
    return disk, files, free


if __name__ == '__main__':
    if sys.argv[1] == 'write':
        path, name, did = sys.argv[2:5]
        fl = []
        for a in sys.argv[5:]:
            p, _, n = a.partition('=')
            fl.append((n or p.rsplit('/', 1)[-1].rsplit('.', 1)[0], open(p, 'rb').read()))
        write(path, name, did, fl)
    disk, files, free = read(sys.argv[2])
    print('0 "%-16s"' % disk)
    for n, blk, data in files:
        print('%-4d "%s"  PRG  (%d bytes, load $%04X)' % (blk, n, len(data), data[0] | data[1] << 8))
    print('%d BLOCKS FREE.' % free)
