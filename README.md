# HD2 Game Strings

This tool reads the official text of Helldivers 2 from a locally installed copy of the game and exports each line in all 15 languages side by side, as a searchable table.

[中文说明](README.zh-CN.md)

## Features

- **All 15 game languages**: English, English (UK), German, French, Spanish, Spanish (Latin America), Italian, Polish, Portuguese, Portuguese (Brazil), Russian, Japanese, Korean, Simplified Chinese and Traditional Chinese.
- **Official translations line by line**: the game assigns an id to each line of text, and lines with the same id in different languages are official translations of each other. The exported table has one row per id and one column per language.
- **Coverage**: in game build 26568081, each language contains 18,600 to 24,800 lines, including the names of enemies, weapons, stratagems and planets, menu text and voice subtitles.
- **Read-only and offline**: only the game's original files are read, and nothing is written to the game folder. Files deployed by mod managers are not read, so the export contains no modified text.

## Requirements

- Python 3.8 or later.
- The `lz4` package (`pip install lz4`).
- An installed copy of Helldivers 2. Steam installations are located automatically on Windows, Linux and macOS; otherwise, specify the folder with `--game`.

## Usage

Run the commands from the folder that contains `hd2_game_strings.py`.

| Command | Description |
|---|---|
| `python hd2_game_strings.py export` | Exports all languages to `output/hd2_strings_<build>_all.csv` |
| `python hd2_game_strings.py export --langs us,cn,tc` | Exports English, Simplified Chinese and Traditional Chinese only |
| `python hd2_game_strings.py export --format json` | Exports in JSON format |
| `python hd2_game_strings.py search Thermite` | Lists the lines that contain the given text, in any language |
| `python hd2_game_strings.py langs` | Lists the language codes and the number of lines in each |

Common options:

| Option | Description |
|---|---|
| `--game "<folder>"` | The Helldivers 2 installation folder, which contains `data\bundles.nxa` |
| `--langs us,cn,tc` | The languages to output, as comma-separated language codes (see Language codes) |
| `--out <folder>` | The output folder; default `./output`. `export` only |

On Windows, `export_all.bat` can be run by double-clicking. It installs `lz4` if it is missing and exports two files: one with all languages, and one with English, Simplified Chinese and Traditional Chinese.

### Example

```
> python hd2_game_strings.py search "Incinerator FRV"
2FAC2673 | INCINERATOR FRV | 炽灼型快速侦察载具 | 焚燒者FRV
F3DC6DF1 | Incinerator FRV | 炽灼型快速侦察载具 | 焚燒者FRV
```

## Output format

- **CSV**: UTF-8 with a byte order mark (BOM), so that Excel displays every script correctly. The first column is the line id (8 hexadecimal digits); each further column holds one language, titled with the language name and code.
- **JSON**: `{"game_build", "languages", "strings": {id: {language code: text}}}`.
- A line that is missing in a language leaves an empty cell. Some languages contain fewer lines than English (build 26568081: English 24,840; Polish, Russian and Traditional Chinese about 18,600 each).
- File names include the game's Steam build number, so exports from different game versions do not overwrite each other.

Notes on the text:

- One name may appear in several lines that differ in case or use, for example `Thermite`, `9x20mm Thermite` and `15x100mm THERMITE`. Select the line that matches the place where the name appears in the game.
- Some lines contain markup that the game fills in or interprets, such as the placeholder `{0}` and subtitle timings such as `{0.00->3.85}`.

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

## File format

1. `data/bundles.nxa` is the index of all packages; it records where the parts of each package are stored in `bundles.NN.nxa`. Both are `DSAR` containers with a chunk table of 32-byte entries (uncompressed offset, file offset, sizes and compression method); each chunk is either LZ4-compressed or stored uncompressed.
2. The text is in package `9ba626afa44a3aa3`. If a game update moves it, the tool searches all packages.
3. A package lists its resources by type. Each resource of type `strings` (type id: MurmurHash64A of the string `strings`) is one text table, consisting of a 16-byte header (magic, version, line count, language key), the line ids as 32-bit values, and the same number of 32-bit offsets to zero-terminated UTF-8 text. Each language has 18 such tables.
4. The language key is the high 32 bits of the MurmurHash64A of the language's two-letter code (for example `us`, `cn`, `tc`).

## Legal notice

- This tool is released under the MIT License; see [LICENSE](LICENSE).
- **The exported text is the work of Arrowhead Game Studios.** It may be used for personal reference, translation review, or quoting names in mods; do not publish the exported tables.
- This project is not affiliated with or endorsed by Arrowhead Game Studios or Sony Interactive Entertainment.

## Acknowledgements

The package format was documented by the Helldivers 2 modding community, in particular [HD2 SDK Community Edition](https://github.com/Boxofbiscuits97/HD2SDK-CommunityEdition) and [filediver](https://github.com/xypwn/filediver). This tool is an independent implementation and contains no code from those projects.
