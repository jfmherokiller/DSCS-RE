"""Minimal EXPA (.mbe) reader for DSCS text/data tables: prints rows matching a needle.

usage: python mbe.py <file.mbe> [needle]
"""
import struct
import sys


def read_expa(path):
    b = open(path, "rb").read()
    assert b[:4] == b"EXPA", "not an EXPA file"
    count = struct.unpack_from("<I", b, 4)[0]
    o, tables = 8, []
    for _ in range(count):
        nl = struct.unpack_from("<I", b, o)[0]
        name = b[o + 4:o + 4 + nl].rstrip(b"\0").decode()
        o += 4 + nl
        es, cnt = struct.unpack_from("<II", b, o)
        o = (o + 8 + 7) & ~7
        tables.append((name, o, es, cnt))
        o = (o + es * cnt + 7) & ~7
    assert b[o:o + 4] == b"CHNK", b[o:o + 4]
    n = struct.unpack_from("<I", b, o + 4)[0]
    p, strs = o + 8, {}
    for _ in range(n):
        off, sz = struct.unpack_from("<II", b, p)
        strs[off] = b[p + 8:p + 8 + sz].split(b"\0")[0].decode("utf8", "replace")
        p += 8 + sz
    out = {}
    for name, base, es, cnt in tables:
        rows = []
        for i in range(cnt):
            e = base + i * es
            ints = list(struct.unpack_from("<%dI" % (es // 4), b, e))
            texts = {k: strs[e + k] for k in range(0, es, 4) if e + k in strs}
            rows.append((ints, texts))
        out[name] = (es, rows)
    return out


if __name__ == "__main__":
    tabs = read_expa(sys.argv[1])
    needle = sys.argv[2] if len(sys.argv) > 2 else None
    for name, (es, rows) in tabs.items():
        print(f"== {name}: entrySize={es} rows={len(rows)}")
        for ints, texts in rows:
            line = f"{ints[:6]} {list(texts.values())}"
            if needle is None or needle.lower() in line.lower():
                print(line)
