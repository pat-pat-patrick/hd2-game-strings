# HD2 Game Strings

本工具从本机安装的《绝地潜兵2》（Helldivers 2）中读取游戏官方文本，将 15 种语言的同一条文本对照导出为可检索的表格。

[English](README.md)

## 功能

- **支持全部 15 种游戏语言**：英语、英语（英国）、德语、法语、西班牙语、西班牙语（拉丁美洲）、意大利语、波兰语、葡萄牙语、葡萄牙语（巴西）、俄语、日语、韩语、简体中文、繁体中文。
- **官方译文逐条对照**：游戏为每条文本分配一个编号，各语言中编号相同的条目互为官方译文。导出的表格每行对应一个编号，每列对应一种语言。
- **文本覆盖范围**：游戏版本 26568081 中，每种语言含 18,600 至 24,800 条文本，包括敌人、武器、战备与星球名称、菜单文字及语音字幕等。
- **只读、离线运行**：仅读取游戏原始文件，不向游戏文件夹写入任何内容；不读取 MOD 管理器部署的文件，导出结果不含 MOD 修改。

## 运行环境

- Python 3.8 或更高版本。
- `lz4` 包（安装命令：`pip install lz4`）。
- 已安装《绝地潜兵2》。在 Windows、Linux 与 macOS 上，可自动定位通过 Steam 安装的游戏；无法定位时，请使用 `--game` 参数指定。

## 使用方法

以下命令须在 `hd2_game_strings.py` 所在目录中执行。

| 命令 | 说明 |
|---|---|
| `python hd2_game_strings.py export` | 导出全部语言至 `output/hd2_strings_<版本号>_all.csv` |
| `python hd2_game_strings.py export --langs us,cn,tc` | 仅导出英语、简体中文与繁体中文 |
| `python hd2_game_strings.py export --format json` | 以 JSON 格式导出 |
| `python hd2_game_strings.py search 铝热弹` | 在全部语言中检索包含指定文字的条目 |
| `python hd2_game_strings.py langs` | 列出各语言代码及条目数量 |

通用参数：

| 参数 | 说明 |
|---|---|
| `--game "<目录>"` | 《绝地潜兵2》安装目录，即包含 `data\bundles.nxa` 的目录 |
| `--langs us,cn,tc` | 指定输出的语言，以逗号分隔的语言代码表示（见“语言代码”） |
| `--out <目录>` | 输出目录，默认为 `./output`；仅用于 `export` |

在 Windows 上，亦可双击运行 `export_all.bat`。该脚本在缺少 `lz4` 时自动安装，并导出两个文件：全部语言版本，以及英语与简繁中文版本。

### 示例

```
> python hd2_game_strings.py search "Incinerator FRV"
2FAC2673 | INCINERATOR FRV | 炽灼型快速侦察载具 | 焚燒者FRV
F3DC6DF1 | Incinerator FRV | 炽灼型快速侦察载具 | 焚燒者FRV
```

## 输出格式

- **CSV**：UTF-8 编码，带字节顺序标记（BOM），可在 Excel 中正确显示各语言文字。首列为条目编号（8 位十六进制数），其后每列对应一种语言，列标题为语言名称及代码。
- **JSON**：结构为 `{"game_build", "languages", "strings": {编号: {语言代码: 文本}}}`。
- 某语言缺少的条目，对应单元格为空。部分语言的条目数少于英语（版本 26568081：英语 24,840 条；波兰语、俄语、繁体中文各约 18,600 条）。
- 文件名包含游戏的 Steam 版本号，不同版本的导出文件互不覆盖。

文本说明：

- 同一名称可能对应多个条目，其大小写或用途不同，例如 `Thermite`、`9x20mm Thermite`、`15x100mm THERMITE`。使用时应根据其在游戏中的出现位置选择相应条目。
- 部分条目包含由游戏填充或解析的标记，例如占位符 `{0}` 与字幕时间标记 `{0.00->3.85}`。

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

## 文件格式

1. `data/bundles.nxa` 为全部资源包的索引，记录各资源包的分段在 `bundles.NN.nxa` 中的位置。两类文件均为 `DSAR` 容器，内含分块表，每项 32 字节，记录解压后偏移、文件内偏移、数据大小与压缩方式；各分块以 LZ4 压缩或不压缩存储。
2. 文本位于资源包 `9ba626afa44a3aa3` 中。若游戏更新后该资源包变更，本工具将检索全部资源包。
3. 资源包按类型列出其中的资源。类型为 `strings`（类型编号为字符串 `strings` 的 MurmurHash64A 值）的每个资源为一张文本表，结构依次为：16 字节表头（魔数、版本、条目数、语言键），条目数个 32 位编号，条目数个 32 位偏移量；偏移量指向以零结尾的 UTF-8 文本。每种语言共 18 张文本表。
4. 语言键为语言两字母代码（如 `us`、`cn`、`tc`）的 MurmurHash64A 值的高 32 位。

## 法律声明

- 本工具依据 MIT 许可证发布，详见 [LICENSE](LICENSE)。
- **导出的文本为 Arrowhead Game Studios 的作品。** 可用于个人查阅、译文核对，或在 MOD 中引用名称；请勿公开发布导出的表格。
- 本项目与 Arrowhead Game Studios 及 Sony Interactive Entertainment 无任何关联，亦未获其认可。

## 致谢

资源包格式由《绝地潜兵2》MOD 社区研究得出，尤其是 [HD2 SDK Community Edition](https://github.com/Boxofbiscuits97/HD2SDK-CommunityEdition) 与 [filediver](https://github.com/xypwn/filediver)。本工具为独立实现，不包含上述项目的代码。
