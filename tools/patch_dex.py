"""Turn off FongMi's self-update check without touching its logic.

Updater.checkRelease() fetches Github.getReleases(), the constant
"https://api.github.com/repos/FongMi/Release/releases?per_page=100". This rewrites that one string
in place to a host that cannot resolve; the request fails, Updater swallows the error and never
shows the update dialog (manual checks from Settings fail the same quiet way).

The edit keeps the string's length and its position in the dex's sorted string table, then
recomputes the header SHA-1 and Adler-32. If upstream changes the URL the anchor is not found
and the build stops, rather than shipping with updates silently back on.

    python -I tools/patch_dex.py <dir with classes*.dex>
"""

import hashlib
import struct
import sys
import zlib
from pathlib import Path

OLD = "https://api.github.com/repos/FongMi/Release/releases?per_page=100"
NEW = "https://api.github.coz/repos/FongMi/Release/releases?per_page=100"  # .coz: no such TLD


def uleb128(buf, off):
    result = shift = 0
    while True:
        b = buf[off]
        off += 1
        result |= (b & 0x7F) << shift
        shift += 7
        if b < 0x80:
            return result, off


def strings(buf):
    size, off = struct.unpack_from("<II", buf, 0x38)
    for i in range(size):
        data_off = struct.unpack_from("<I", buf, off + 4 * i)[0]
        _, start = uleb128(buf, data_off)
        end = buf.index(b"\0", start)
        yield i, start, end


def decode(buf, start, end):
    return buf[start:end].decode("utf-8", errors="surrogatepass")


def patch(path):
    buf = bytearray(path.read_bytes())
    table = list(strings(buf))
    hit = [(i, s, e) for i, s, e in table if buf[s:e] == OLD.encode()]
    if not hit:
        return False
    i, s, e = hit[0]
    prev = decode(buf, *table[i - 1][1:]) if i > 0 else ""
    nxt = decode(buf, *table[i + 1][1:]) if i + 1 < len(table) else "￿"
    if not (prev < NEW < nxt):
        raise SystemExit(f"patch_dex: {NEW!r} would break the string order ({prev!r} .. {nxt!r})")
    buf[s:e] = NEW.encode()
    buf[12:32] = hashlib.sha1(bytes(buf[32:])).digest()
    struct.pack_into("<I", buf, 8, zlib.adler32(bytes(buf[12:])) & 0xFFFFFFFF)
    path.write_bytes(bytes(buf))
    return True


def main(folder):
    done = [p.name for p in sorted(Path(folder).glob("classes*.dex")) if patch(p)]
    if not done:
        raise SystemExit("patch_dex: update URL not found; upstream changed Github.getReleases(), update the patch")
    print(f"  patch: self-update check off ({', '.join(done)})")


if __name__ == "__main__":
    main(sys.argv[1])
