#!/usr/bin/env python3
"""HD2 Game Strings: export the official in-game text of Helldivers 2 in all
15 languages from your own installed copy of the game.

    python hd2_game_strings.py export                    every language, one CSV
    python hd2_game_strings.py export --langs us,cn,tc   English, Simplified and Traditional Chinese
    python hd2_game_strings.py export --format json
    python hd2_game_strings.py search Thermite           strings containing a word, in any language
    python hd2_game_strings.py langs                     the language codes and how many strings each has

Options: --game <Helldivers 2 folder> (found through Steam when left out),
--out <folder> (default: ./output).

Only the game's own files are read; the folder is never written to. Files
deployed by mod managers (*.patch_*) are not read, so the text is the game's.
Requires Python 3.8+ and the lz4 package (pip install lz4). MIT licence.
"""

import argparse
import csv
import json
import os
import re
import struct
import sys

try:
    import lz4.block
except ImportError:  # pragma: no cover
    sys.exit("This tool needs the lz4 package: pip install lz4")

__version__ = "1.0.0"

APP_ID = "553850"
STRINGS_PACKAGE = "9ba626afa44a3aa3"   # where the game keeps its text (2026); every package is searched if it moves

# code, title; the key in the files is the high 32 bits of murmur64(code)
LANGUAGES = [
    ("us", "English"),
    ("gb", "English (UK)"),
    ("de", "Deutsch"),
    ("fr", "Français"),
    ("es", "Español"),
    ("ms", "Español (Latinoamérica)"),
    ("it", "Italiano"),
    ("pl", "Polski"),
    ("pt", "Português"),
    ("bp", "Português (Brasil)"),
    ("ru", "Русский"),
    ("jp", "日本語"),
    ("ko", "한국어"),
    ("cn", "简体中文"),
    ("tc", "繁體中文"),
]


# ---------------------------------------------------------------- hashing

def murmur64(data, seed=0):
    """MurmurHash64A, the hash the engine names its resources and types with."""
    m, r, mask = 0xC6A4A7935BD1E995, 47, 0xFFFFFFFFFFFFFFFF
    h = (seed ^ (len(data) * m)) & mask
    whole = len(data) // 8 * 8
    for i in range(0, whole, 8):
        k = int.from_bytes(data[i:i + 8], "little")
        k = (k * m) & mask
        k ^= k >> r
        k = (k * m) & mask
        h ^= k
        h = (h * m) & mask
    tail = data[whole:]
    if tail:
        h ^= int.from_bytes(tail, "little")
        h = (h * m) & mask
    h ^= h >> r
    h = (h * m) & mask
    h ^= h >> r
    return h


STRINGS_TYPE = murmur64(b"strings")
LANGUAGE_KEYS = {murmur64(code.encode()) >> 32: code for code, _title in LANGUAGES}


# ---------------------------------------------------------------- the game's archives

class Container:
    """One compressed archive file of the game (magic DSAR): a table of chunks,
    each LZ4-compressed or stored, laid end to end in one uncompressed space."""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            head = f.read(0x20)
            if head[:4] != b"DSAR":
                raise ValueError("not an archive: %s" % path)
            count = struct.unpack_from("<I", head, 8)[0]
            table = f.read(0x20 * count)
        self.chunks = []      # (uncompressed offset, file offset, size, stored size, compressed)
        for i in range(count):
            uoff, foff, usize, ssize, method = struct.unpack_from("<QQIIB", table, i * 0x20)
            self.chunks.append((uoff, foff, usize, ssize, method == 3))
        self.index_of = {c[0]: i for i, c in enumerate(self.chunks)}

    def _chunk(self, f, i):
        _uoff, foff, usize, ssize, compressed = self.chunks[i]
        f.seek(foff)
        raw = f.read(ssize)
        return lz4.block.decompress(raw, uncompressed_size=usize) if compressed else raw

    def read(self, offset, size):
        """`size` uncompressed bytes from `offset`, which starts a chunk."""
        i = self.index_of.get(offset)
        if i is None:
            raise ValueError("%s: no chunk starts at %d" % (self.path, offset))
        parts, got = [], 0
        with open(self.path, "rb") as f:
            while got < size and i < len(self.chunks):
                d = self._chunk(f, i)
                parts.append(d)
                got += len(d)
                i += 1
        return b"".join(parts)[:size]

    def read_all(self):
        with open(self.path, "rb") as f:
            return b"".join(self._chunk(f, i) for i in range(len(self.chunks)))


class GameData:
    """The game's data folder: bundles.nxa lists every package and where its
    pieces lie in bundles.NN.nxa."""

    def __init__(self, data_dir):
        self.dir = data_dir
        index = Container(os.path.join(data_dir, "bundles.nxa")).read_all()
        count = struct.unpack_from("<I", index, 0x10)[0]
        self.packages = {}
        for k in range(count):
            at = 0x18 + k * 0x18
            size, name_at, pieces, pieces_at = struct.unpack_from("<QIII", index, at)
            name = index[name_at:index.index(b"\0", name_at)].decode("ascii")
            items = []
            for i in range(pieces):
                p = pieces_at + i * 0x10
                package_offset = struct.unpack_from("<Q", index, p)[0]
                bundle_offset = struct.unpack_from("<I", index, p + 8)[0]
                bundle = index[p + 0x0F]
                items.append((package_offset, bundle, bundle_offset))
            self.packages[name] = (size, items)
        self._bundles = {}

    def _bundle(self, n):
        if n not in self._bundles:
            self._bundles[n] = Container(os.path.join(self.dir, "bundles.%02d.nxa" % n))
        return self._bundles[n]

    def package(self, name, limit=None):
        """A package's bytes (only the first `limit` when given)."""
        size, items = self.packages[name]
        want = size if limit is None else min(size, limit)
        out = bytearray(want)
        for i, (poff, bundle, boff) in enumerate(items):
            if poff >= want:
                break
            end = items[i + 1][0] if i + 1 < len(items) else size
            n = min(end, want) - poff
            out[poff:poff + n] = self._bundle(bundle).read(boff, n)
        return bytes(out)


# ---------------------------------------------------------------- packages and strings

def resources(package, of_type):
    """The bytes of each resource of a type in a package."""
    _magic, types, files = struct.unpack_from("<III", package, 0)
    base = 0x48 + types * 32
    for i in range(files):
        at = base + i * 80
        _fid, tid, offset = struct.unpack_from("<QQQ", package, at)
        if tid == of_type:
            size = struct.unpack_from("<I", package, at + 56)[0]
            yield package[offset:offset + size]


def has_type(head, of_type):
    _magic, types, _files = struct.unpack_from("<III", head, 0)
    for i in range(types):
        if struct.unpack_from("<Q", head, 0x48 + i * 32 + 8)[0] == of_type:
            return True
    return False


def read_strings(game):
    """{language code: {string id: text}}."""
    names = [STRINGS_PACKAGE] if STRINGS_PACKAGE in game.packages else []
    tables = _strings_of(game, names)
    if not tables:   # moved in a later game version: look in every package
        names = [n for n in game.packages if _is_strings_package(game, n)]
        tables = _strings_of(game, names)
    if not tables:
        sys.exit("No text found in the game's data. A game update may have changed the format.")
    return tables


def _is_strings_package(game, name):
    try:
        head = game.package(name, 0x48)
        types = struct.unpack_from("<I", head, 4)[0]
        return types < 4096 and has_type(game.package(name, 0x48 + types * 32), STRINGS_TYPE)
    except (ValueError, struct.error, OSError):
        return False


def _strings_of(game, names):
    tables = {}
    for name in names:
        for res in resources(game.package(name), STRINGS_TYPE):
            if len(res) < 16:
                continue
            _magic, _version, n, key = struct.unpack_from("<4I", res, 0)
            code = LANGUAGE_KEYS.get(key, "%08x" % key)
            ids = struct.unpack_from("<%dI" % n, res, 16)
            offsets = struct.unpack_from("<%dI" % n, res, 16 + 4 * n)
            table = tables.setdefault(code, {})
            for sid, off in zip(ids, offsets):
                table[sid] = res[off:res.index(b"\0", off)].decode("utf-8", "replace")
    return tables


# ---------------------------------------------------------------- finding the game

def steam_libraries():
    roots = []
    if sys.platform == "win32":
        try:
            import winreg
            for hive, key in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                              (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
                try:
                    with winreg.OpenKey(hive, key) as k:
                        for value in ("SteamPath", "InstallPath"):
                            try:
                                roots.append(winreg.QueryValueEx(k, value)[0])
                            except OSError:
                                pass
                except OSError:
                    pass
        except ImportError:
            pass
    home = os.path.expanduser("~")
    roots += [os.path.join(home, ".steam", "steam"), os.path.join(home, ".local", "share", "Steam"),
              os.path.join(home, "Library", "Application Support", "Steam")]
    libraries = []
    for root in roots:
        vdf = os.path.join(root, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf):
            text = open(vdf, encoding="utf-8", errors="replace").read()
            libraries += [p.replace("\\\\", "\\") for p in re.findall(r'"path"\s+"([^"]+)"', text)]
        libraries.append(root)
    seen, out = set(), []
    for lib in libraries:
        key = os.path.normcase(os.path.abspath(lib))
        if key not in seen:
            seen.add(key)
            out.append(lib)
    return out


def find_game(given=None):
    """The Helldivers 2 folder (the one holding data\\bundles.nxa)."""
    candidates = [given] if given else []
    if os.environ.get("HD2_GAME_DIR"):
        candidates.append(os.environ["HD2_GAME_DIR"])
    candidates += [os.path.join(lib, "steamapps", "common", "Helldivers 2") for lib in steam_libraries()]
    for c in candidates:
        if c and os.path.exists(os.path.join(c, "data", "bundles.nxa")):
            return c
    if given:
        sys.exit("No data\\bundles.nxa in %s: give the Helldivers 2 folder." % given)
    sys.exit("Helldivers 2 was not found through Steam. Give its folder: --game \"<path>\"")


def build_id(game_dir):
    acf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(game_dir))), "appmanifest_%s.acf" % APP_ID)
    if os.path.exists(acf):
        m = re.search(r'"buildid"\s+"(\d+)"', open(acf, encoding="utf-8", errors="replace").read())
        if m:
            return m.group(1)
    return "unknown"


# ---------------------------------------------------------------- commands

def chosen(tables, langs):
    codes = [c for c, _t in LANGUAGES if c in tables] + sorted(c for c in tables if c not in dict(LANGUAGES))
    if langs:
        want = [c.strip() for c in langs.split(",") if c.strip()]
        bad = [c for c in want if c not in tables]
        if bad:
            sys.exit("Unknown language code(s): %s. Run: python hd2_game_strings.py langs" % ", ".join(bad))
        codes = want
    return codes


def rows(tables, codes):
    ids = sorted(set().union(*(tables[c].keys() for c in codes)))
    for sid in ids:
        yield "%08X" % sid, [tables[c].get(sid, "") for c in codes]


def cmd_export(args):
    game_dir = find_game(args.game)
    tables = read_strings(GameData(os.path.join(game_dir, "data")))
    codes = chosen(tables, args.langs)
    titles = dict(LANGUAGES)
    os.makedirs(args.out, exist_ok=True)
    suffix = "all" if not args.langs else "-".join(codes)
    path = os.path.join(args.out, "hd2_strings_%s_%s.%s" % (build_id(game_dir), suffix, args.format))
    n = 0
    if args.format == "csv":
        with open(path, "w", encoding="utf-8-sig", newline="") as f:   # BOM: Excel reads it as UTF-8
            w = csv.writer(f)
            w.writerow(["id"] + ["%s (%s)" % (titles.get(c, c), c) for c in codes])
            for sid, texts in rows(tables, codes):
                w.writerow([sid] + texts)
                n += 1
    else:
        out = {}
        for sid, texts in rows(tables, codes):
            out[sid] = dict(zip(codes, texts))
            n += 1
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"game_build": build_id(game_dir), "languages": codes, "strings": out}, f, ensure_ascii=False, indent=1)
    print("%s  (%d strings, %d languages)" % (path, n, len(codes)))


def cmd_search(args):
    game_dir = find_game(args.game)
    tables = read_strings(GameData(os.path.join(game_dir, "data")))
    codes = chosen(tables, args.langs or "us,cn,tc")
    needle = args.text.lower()
    found = 0
    for sid, texts in rows(tables, list(tables)):
        if any(needle in t.lower() for t in texts):
            shown = [tables[c].get(int(sid, 16), "") for c in codes]
            print(sid + " | " + " | ".join(shown))
            found += 1
    print("%d found" % found, file=sys.stderr)


def cmd_langs(args):
    game_dir = find_game(args.game)
    tables = read_strings(GameData(os.path.join(game_dir, "data")))
    print("game build %s, %s" % (build_id(game_dir), game_dir))
    for code, title in LANGUAGES:
        print("  %-3s %-26s %6d strings" % (code, title, len(tables.get(code, {}))))
    for code in sorted(c for c in tables if c not in dict(LANGUAGES)):
        print("  %-3s %-26s %6d strings" % (code, "(unknown)", len(tables[code])))


def main(argv=None):
    p = argparse.ArgumentParser(prog="hd2_game_strings", description="Export Helldivers 2's official in-game text in all languages.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--game", help="the Helldivers 2 folder (found through Steam when left out)")
    common.add_argument("--langs", help="comma-separated language codes, e.g. us,cn,tc (default: all)")
    e = sub.add_parser("export", parents=[common], help="write the text to a CSV or JSON file")
    e.add_argument("--out", default="output", help="output folder (default: ./output)")
    e.add_argument("--format", choices=("csv", "json"), default="csv")
    s = sub.add_parser("search", parents=[common], help="print the strings that contain a text")
    s.add_argument("text")
    sub.add_parser("langs", parents=[common], help="list the languages and their string counts")
    args = p.parse_args(argv)
    if args.command == "export":
        cmd_export(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "langs":
        cmd_langs(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
