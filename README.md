# HD2 Game Strings

Export the official in-game text of Helldivers 2 in all 15 languages, from your own installed copy of the game, as a spreadsheet you can search.

[中文说明](README.zh-CN.md)

- **Every language the game ships**: English, English (UK), German, French, Spanish, Spanish (Latin America), Italian, Polish, Portuguese, Portuguese (Brazil), Russian, Japanese, Korean, Simplified Chinese and Traditional Chinese.
- **Official translations side by side**: the game gives each line an id, and the same id in two languages is the same line translated. One row per id, one column per language.
- **About 25,000 lines per language** (game build 26568081): enemy, weapon, stratagem and planet names, menus, voice subtitles and more.
- **Read-only and offline**: it reads the game's own files and writes nothing into the game folder. Files deployed by mod managers are ignored, so you get the game's text, not a mod's.

## Requirements

- Python 3.8 or newer.
- The `lz4` package: `pip install lz4`.
- Helldivers 2 installed. Steam installs are found automatically on Windows, Linux and macOS; otherwise pass `--game`.

## Usage

Run the commands in the folder that holds `hd2_game_strings.py`.

| Command | What it does |
|---|---|
| `python hd2_game_strings.py export` | Writes every language to `output/hd2_strings_<build>_all.csv` |
| `python hd2_game_strings.py export --langs us,cn,tc` | Only English, Simplified and Traditional Chinese |
| `python hd2_game_strings.py export --format json` | JSON instead of CSV |
| `python hd2_game_strings.py search Thermite` | Prints every line that contains the text, in any language |
| `python hd2_game_strings.py langs` | Lists the language codes and how many lines each has |

Options for every command:

- `--game "<folder>"`: the Helldivers 2 folder, the one that holds `data\bundles.nxa`.
- `--langs us,cn,tc`: the languages to show, by code (see the table below).
- `--out <folder>` (export only): where to write; default `./output`.

On Windows you can also double-click `export_all.bat`. It installs `lz4` when it is missing and writes two files: all languages, and English with both Chinese scripts.

### Example

```
> python hd2_game_strings.py search "Incinerator FRV"
2FAC2673 | INCINERATOR FRV | 炽灼型快速侦察载具 | 焚燒者FRV
F3DC6DF1 | Incinerator FRV | 炽灼型快速侦察载具 | 焚燒者FRV
```

## Output

- **CSV**: UTF-8 with a byte-order mark, so Excel opens every script correctly. The first column is the line's id (8 hex digits); then one column per language, titled with its name and code.
- **JSON**: `{"game_build", "languages", "strings": {id: {code: text}}}`.
- A line missing in a language is an empty cell. Some languages have fewer lines than English (build 26568081: English 24,840; Polish, Russian and Traditional Chinese about 18,600).
- The file name carries the game's Steam build, so exports from different game versions do not overwrite each other.

Notes on the text itself:

- One name often appears several times with different case or context (`Thermite`, `9x20mm Thermite`, `15x100mm THERMITE`). Pick the one used where you need it.
- Some lines contain markup the game fills in or interprets, such as `{0}` or subtitle timings like `{0.00->3.85}`.

## Language codes

| Code | Language | Code | Language |
|---|---|---|---|
| `us` | English | `gb` | English (UK) |
| `de` | German | `fr` | French |
| `es` | Spanish | `ms` | Spanish (Latin America) |
| `it` | Italian | `pl` | Polish |
| `pt` | Portuguese | `bp` | Portuguese (Brazil) |
| `ru` | Russian | `jp` | Japanese |
| `ko` | Korean | `cn` | Simplified Chinese |
| `tc` | Traditional Chinese | | |

## How it works

For people who want to read the files themselves:

1. `data/bundles.nxa` is an index of every package in the game and where its pieces lie in `bundles.NN.nxa`. Both are `DSAR` containers: a table of 32-byte chunk entries (uncompressed offset, file offset, sizes, compression), each chunk LZ4-compressed or stored.
2. The text is in the package `9ba626afa44a3aa3`. If a game update moves it, the tool searches every package.
3. A package lists its resources by type. Resources of type `strings` (the type id is MurmurHash64A of `strings`) hold one table each: a 16-byte header (magic, version, count, language key), then `count` 32-bit ids, then `count` 32-bit offsets to zero-terminated UTF-8 text. The game has 18 such tables per language.
4. The language key is the high 32 bits of MurmurHash64A of the language's two-letter code (`us`, `cn`, `tc`, ...).

## Legal

- The tool is MIT-licensed (see [LICENSE](LICENSE)).
- **The text it exports is Arrowhead Game Studios' work.** Use it for your own reference, translation checks or mods that quote names; do not publish the exported tables.
- This project is not affiliated with or endorsed by Arrowhead Game Studios or Sony Interactive Entertainment.

## Credits

The archive format was worked out by the Helldivers 2 modding community, notably the [HD2 SDK Community Edition](https://github.com/Boxofbiscuits97/HD2SDK-CommunityEdition) and [filediver](https://github.com/xypwn/filediver). This tool is an independent implementation and contains none of their code.
