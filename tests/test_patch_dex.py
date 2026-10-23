"""patch_dex rewrites one string in a dex in place and fixes the header checksums."""

import hashlib
import struct
import zlib

import pytest

import patch_dex


def mutf8_len(n):
    return bytes([n]) if n < 0x80 else bytes([0x80 | (n & 0x7F), n >> 7])


def make_dex(strings):
    """A minimal dex: 0x70 header, string_ids table, string_data items. Strings must be sorted."""
    header_size = 0x70
    ids_off = header_size
    data_off = ids_off + 4 * len(strings)
    data = bytearray()
    offsets = []
    for s in strings:
        offsets.append(data_off + len(data))
        raw = s.encode("utf-8", errors="surrogatepass")
        data += mutf8_len(len(s)) + raw + b"\0"
    buf = bytearray(b"dex\n035\0") + bytearray(header_size - 8)
    struct.pack_into("<I", buf, 0x20, header_size + 4 * len(strings) + len(data))  # file_size
    struct.pack_into("<II", buf, 0x38, len(strings), ids_off)
    for off in offsets:
        buf += struct.pack("<I", off)
    buf += data
    buf[12:32] = hashlib.sha1(bytes(buf[32:])).digest()
    struct.pack_into("<I", buf, 8, zlib.adler32(bytes(buf[12:])) & 0xFFFFFFFF)
    return bytes(buf)


def checksums_ok(buf):
    return (buf[12:32] == hashlib.sha1(buf[32:]).digest()
            and struct.unpack_from("<I", buf, 8)[0] == zlib.adler32(buf[12:]) & 0xFFFFFFFF)


def test_strings_table_roundtrip():
    names = ["", "a", "hello", "https://x", "中文", "\U0001f308"]  # includes an astral char (surrogate pair)
    buf = make_dex(sorted(names, key=lambda s: s.encode("utf-16-be")))
    got = [patch_dex.decode(buf, s, e) for _, s, e in patch_dex.strings(buf)]
    assert sorted(got, key=lambda s: s.encode("utf-16-be", "surrogatepass")) == got
    assert "hello" in got and "中文" in got


def test_patch_replaces_url_and_fixes_checksums(tmp_path):
    before = sorted([patch_dex.OLD, "aaa", "zzz", "https://api.github.com/a"])
    dex = tmp_path / "classes.dex"
    dex.write_bytes(make_dex(before))
    assert patch_dex.patch(dex) is True
    buf = dex.read_bytes()
    assert patch_dex.OLD.encode() not in buf
    assert patch_dex.NEW.encode() in buf
    assert checksums_ok(buf)
    assert len(buf) == len(make_dex(before)), "patch must not change the file size"


def test_patch_leaves_other_files_alone(tmp_path):
    dex = tmp_path / "classes2.dex"
    original = make_dex(["aaa", "bbb"])
    dex.write_bytes(original)
    assert patch_dex.patch(dex) is False
    assert dex.read_bytes() == original


def test_patch_refuses_to_break_sort_order(tmp_path):
    # neighbours that sort between OLD ("...com/repos...") and NEW ("...coz/...") must stop the patch
    for neighbour in ("https://api.github.cot", "https://api.github.com/zzz"):
        dex = tmp_path / "classes.dex"
        dex.write_bytes(make_dex(sorted([patch_dex.OLD, neighbour])))
        with pytest.raises(SystemExit, match="string order"):
            patch_dex.patch(dex)


def test_main_fails_loudly_when_anchor_missing(tmp_path):
    (tmp_path / "classes.dex").write_bytes(make_dex(["nothing here"]))
    with pytest.raises(SystemExit, match="update URL not found"):
        patch_dex.main(tmp_path)


def test_new_url_same_length_and_same_prefix():
    assert len(patch_dex.NEW) == len(patch_dex.OLD)
    assert patch_dex.NEW.split("/")[2].endswith(".coz")  # an unregistered TLD
