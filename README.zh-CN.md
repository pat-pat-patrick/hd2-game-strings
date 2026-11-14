# HD2 Game Strings

从你自己安装的《绝地潜兵2》（Helldivers 2）里导出游戏的官方文本，15 种语言并排放在一张可搜索的表格里。

[English](README.md)

- **游戏自带的全部语言**：英语、英语（英国）、德语、法语、西班牙语、西班牙语（拉丁美洲）、意大利语、波兰语、葡萄牙语、葡萄牙语（巴西）、俄语、日语、韩语、简体中文、繁体中文。
- **官方翻译逐条对照**：游戏给每一句文本一个编号，同一个编号在不同语言里就是同一句话的官方翻译。表格里每个编号一行，每种语言一列。
- **每种语言约 2.5 万条**（游戏版本 26568081）：敌人、武器、战备、星球的名称，菜单，语音字幕等。
- **只读、离线**：只读取游戏自己的文件，不往游戏文件夹里写任何东西。MOD 管理器部署进去的文件不读，所以导出的是游戏原本的文本，不会混进 MOD 的内容。

## 需要什么

- Python 3.8 或更新版本。
- `lz4` 包：`pip install lz4`。
- 已安装《绝地潜兵2》。在 Windows、Linux、macOS 上，Steam 安装的游戏会自动找到；找不到时用 `--game` 指定。

## 用法

在 `hd2_game_strings.py` 所在的文件夹里运行。

| 命令 | 作用 |
|---|---|
| `python hd2_game_strings.py export` | 把全部语言写到 `output/hd2_strings_<版本号>_all.csv` |
| `python hd2_game_strings.py export --langs us,cn,tc` | 只导出英语、简体中文、繁体中文 |
| `python hd2_game_strings.py export --format json` | 导出为 JSON 而不是 CSV |
| `python hd2_game_strings.py search 铝热弹` | 列出所有包含这段文字的条目，任何语言都能搜 |
| `python hd2_game_strings.py langs` | 列出语言代码和每种语言的条数 |

所有命令都可以加的选项：

- `--game "<文件夹>"`：《绝地潜兵2》的安装文件夹，也就是里面有 `data\bundles.nxa` 的那个。
- `--langs us,cn,tc`：要显示哪些语言，填代码（见下表）。
- `--out <文件夹>`（仅 export）：输出位置，默认 `./output`。

Windows 上也可以直接双击 `export_all.bat`。它会在缺少 `lz4` 时自动安装，然后写出两个文件：全部语言一份，英语加简繁中文一份。

### 示例

```
> python hd2_game_strings.py search "Incinerator FRV"
2FAC2673 | INCINERATOR FRV | 炽灼型快速侦察载具 | 焚燒者FRV
F3DC6DF1 | Incinerator FRV | 炽灼型快速侦察载具 | 焚燒者FRV
```

## 输出

- **CSV**：UTF-8 编码并带 BOM，用 Excel 打开中文、日文、韩文都不会乱码。第一列是条目编号（8 位十六进制），后面每种语言一列，列名写着语言名称和代码。
- **JSON**：`{"game_build", "languages", "strings": {编号: {代码: 文本}}}`。
- 某种语言缺少的条目是空格子。有几种语言的条数比英语少（版本 26568081：英语 24,840 条；波兰语、俄语、繁体中文约 18,600 条）。
- 文件名里带着游戏的 Steam 版本号，不同版本导出的文件不会互相覆盖。

关于文本本身：

- 同一个名字常有好几条，大小写或用法不同（如 `Thermite`、`9x20mm Thermite`、`15x100mm THERMITE`），按你要用的场合挑。
- 有些条目里带着游戏要填充或解析的标记，例如 `{0}`，或者字幕时间 `{0.00->3.85}`。

## 语言代码

| 代码 | 语言 | 代码 | 语言 |
|---|---|---|---|
| `us` | 英语 | `gb` | 英语（英国） |
| `de` | 德语 | `fr` | 法语 |
| `es` | 西班牙语 | `ms` | 西班牙语（拉丁美洲） |
| `it` | 意大利语 | `pl` | 波兰语 |
| `pt` | 葡萄牙语 | `bp` | 葡萄牙语（巴西） |
| `ru` | 俄语 | `jp` | 日语 |
| `ko` | 韩语 | `cn` | 简体中文 |
| `tc` | 繁体中文 | | |

## 原理

想自己读这些文件的话：

1. `data/bundles.nxa` 是全部资源包的索引，记录每个包的各部分在 `bundles.NN.nxa` 里的位置。两者都是 `DSAR` 容器：一张 32 字节一项的分块表（解压后偏移、文件内偏移、大小、压缩方式），每块用 LZ4 压缩或原样存放。
2. 文本在 `9ba626afa44a3aa3` 这个包里。如果以后游戏更新把它挪了地方，工具会搜索全部包。
3. 包里按类型列出资源。类型为 `strings` 的资源（类型编号是 `strings` 的 MurmurHash64A）每个是一张表：16 字节的表头（魔数、版本、条数、语言键），然后是 `条数` 个 32 位编号，再是 `条数` 个 32 位偏移，指向以 0 结尾的 UTF-8 文本。每种语言有 18 张这样的表。
4. 语言键是语言两字母代码（`us`、`cn`、`tc` 等）的 MurmurHash64A 的高 32 位。

## 法律说明

- 本工具以 MIT 许可证发布（见 [LICENSE](LICENSE)）。
- **导出的文本是 Arrowhead Game Studios 的作品。** 可以自己查阅、核对翻译，或在 MOD 里引用名称；请不要公开发布导出的表格。
- 本项目与 Arrowhead Game Studios 及 Sony Interactive Entertainment 无关，也未获得其认可。

## 致谢

资源包格式是《绝地潜兵2》MOD 社区摸索出来的，特别是 [HD2 SDK Community Edition](https://github.com/Boxofbiscuits97/HD2SDK-CommunityEdition) 和 [filediver](https://github.com/xypwn/filediver)。本工具是独立实现，不包含它们的代码。
