# flutter_config

Godot 游戏项目的初始化与 Flutter 集成配置。将整个 `flutter_config` 目录复制到游戏项目根目录后，即可运行初始化脚本，下载 Godot 引擎源码并配置 C# 编译排除项。

## 环境要求

- Python 3.9 或更新版本，无需安装额外 Python 依赖。
- Git，以及能够访问 GitHub 的网络环境。
- 已有 Godot C# 游戏项目，根目录包含 `project.godot` 和至少一个 `*.csproj` 文件。

## 快速使用

将 `flutter_config` 复制到游戏项目根目录，与 `project.godot` 放在同一级：

```text
my_game/
├── project.godot
├── my_game.csproj
└── flutter_config/
    ├── README.md
    ├── init_project.py
    └── godot_android/
```

在游戏项目根目录执行：

```bash
./flutter_config/init_project.py
```

默认使用 `4.7.2-stable`，相当于在游戏项目根目录执行以下克隆命令，然后更新 C# 项目配置：

```bash
git clone --branch 4.7.2-stable https://github.com/godotengine/godot
```

初始化后，Godot 源码位于 `my_game/godot/`。

如果复制后脚本丢失执行权限，可恢复权限后运行：

```bash
chmod +x ./flutter_config/init_project.py
./flutter_config/init_project.py
```

也可以通过 Python 执行：

```bash
python3 ./flutter_config/init_project.py
```

## 参数

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--branch` | 要克隆的 Godot 分支或标签 | `4.7.2-stable` |
| `--project` | Godot 项目目录或单个 `.csproj` 文件路径 | 从脚本所在目录的上一级向上查找 `project.godot` |
| `-h`、`--help` | 查看帮助 | — |

指定 Godot 分支或标签：

```bash
./flutter_config/init_project.py --branch 4.7.2-stable
```

指定其他游戏项目目录：

```bash
./flutter_config/init_project.py --project /path/to/my_game
```

仅更新指定的 C# 项目文件，同时将源码克隆到该文件所在目录的 `godot/`：

```bash
./flutter_config/init_project.py --project /path/to/my_game/my_game.csproj
```

默认根据脚本位置定位游戏项目，不依赖终端当前目录。显式传入的相对 `--project` 路径则相对于终端当前目录解析。

## 初始化行为

1. 定位游戏项目，查找该目录下的 `*.csproj` 文件，不递归查找子目录。
2. 将指定版本的 Godot 源码克隆到项目的 `godot/` 目录。
3. 为每个选中的 `.csproj` 补充缺少的编译排除项：

```xml
<ItemGroup>
  <!-- 排除不需要编译的目录 -->
  <Compile Remove="android/**" />
  <Compile Remove="flutter/**" />
  <Compile Remove="godot/**" />
</ItemGroup>
```

排除路径相对于 `.csproj` 所在目录，用于避免这些目录中的 C# 源文件参与游戏项目编译。脚本保留其他项目配置、注释、UTF-8 BOM 和原有换行符；重复执行不会重复添加排除项。带有 `Condition` 的排除项不会替代全局排除配置。

如果 `godot/` 已存在且包含 `SConstruct`，脚本会跳过克隆，也支持预先解压的 Godot 源码。此时 `--branch` 不会切换已有源码的版本，脚本也不会自动执行 `git pull`。

初始化是独立步骤，当前构建脚本不会自动调用。重新生成 `.csproj` 后，可以再次运行初始化脚本。

## 常见问题

- **未找到 `project.godot`**：确认 `flutter_config` 位于游戏项目根目录，或通过 `--project` 显式指定项目。
- **没有 `.csproj` 文件**：先在 Godot C# 项目中生成 C# 项目文件，再执行初始化。
- **目标路径已存在，但不是 Godot 源码目录**：检查游戏项目中的 `godot/` 路径，确保其中是完整源码并包含 `SConstruct`。
- **Git 克隆失败**：检查 Git、网络及分支或标签名称。若失败后留下不完整的 `godot/` 目录，先检查并处理该目录，再重新执行。
- **XML 格式错误**：修复对应 `.csproj` 文件后重新执行。

发生路径、克隆或 XML 处理错误时，脚本输出 `[ERROR]` 并以非零状态退出。处理多个 `.csproj` 时，报错前已成功更新的文件会保留修改。

## Android 配置

Android 构建依赖与配置说明见 [godot_android/README.md](godot_android/README.md)。


## Git 忽略规则

初始化脚本会自动补充游戏项目和 `flutter_config` 的 `.gitignore`，保留已有规则，
重复运行不会重复添加。游戏项目忽略 `.godot/`、克隆的 `godot/`、导出的 `android/`、
.NET `bin/` 和 `obj/`、`godot.gdkey` 及签名证书。
`flutter_config` 忽略 Gradle/Python/IDE 缓存、本机 SDK 配置和生成的原生库、AAR。
脚本、Gradle 配置、项目源码和 `.gdignore` 保留在版本管理范围内。

`.gitignore` 仅影响未跟踪文件；已提交的文件不会因新增规则而自动移出版本管理。
