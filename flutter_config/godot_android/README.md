# Godot Android 配置

项目初始化方式、参数及常见问题见 [flutter_config 使用说明](../README.md)。

```shell
brew install scons
brew install --cask dotnet-sdk
```
初始化脚本会自动将指定版本的 Godot 源码克隆到目标 Godot 项目的 `godot/` 目录。

 .bashrc 或者 .zshrc
```shell
export ANDROID_HOME=/Users/$(whoami)/Library/Android/sdk
```

## 初始化 Godot 源码与 C# 编译排除目录

Godot C# 项目默认会收集项目目录下的 C# 源文件。首次构建前，运行
`flutter_config/init_project.py`，将 `android/**`、`flutter/**`、`godot/**`
加入 `*.csproj` 的编译排除配置，避免这些目录中的 C# 文件参与当前项目编译。
排除路径相对于各个 `.csproj` 所在目录，不会删除目录或文件。

需要 Python 3.9 或更新版本，无需安装额外依赖。将整个 `flutter_config` 目录
复制到游戏项目根目录（与 `project.godot` 同级），然后在游戏项目根目录执行：

```shell
# 自动定位 flutter_config 所在的游戏项目，默认克隆 4.7.2-stable
./flutter_config/init_project.py

# 指定 Godot 项目目录，处理该目录下所有 *.csproj
./flutter_config/init_project.py --project /path/to/godot_project

# 指定其他分支或标签
./flutter_config/init_project.py --branch 4.7.2-stable

# 克隆源码，并仅处理指定的 .csproj 文件
./flutter_config/init_project.py --project /path/to/godot_project/bodygroups.csproj
```

项目定位以脚本位置为准，不依赖终端当前目录。源码会放到游戏项目根目录的 `godot/`。

克隆需要安装 Git 并能访问 GitHub。`--branch` 默认是 `4.7.2-stable`。
已有 `godot/` 源码目录（包含 `SConstruct`，也支持解压的源码）时跳过克隆，
不会自动拉取或切换版本；已有同名非源码路径时会报错。克隆失败时以非零状态退出。

脚本仅补充缺少的排除项，保留其他项目配置、注释、UTF-8 BOM 和原有换行符，
重复运行不会重复添加。已有的带 `Condition` 的排除项不会替代全局排除配置。
仅处理项目目录下的直接子文件，不递归查找 `.csproj`。
自动查找不到 Godot 项目时，可通过 `--project` 指定路径；路径不存在、没有
`.csproj` 或 XML 格式错误时，脚本会输出错误并以非零状态退出。

这是独立的初始化步骤，当前构建脚本不会自动调用；重新生成 `.csproj` 后可以再次执行。

脚本补充的配置如下：
```xml
  <ItemGroup>
    <!-- 排除不需要编译的目录 -->
    <Compile Remove="android/**" />
    <Compile Remove="flutter/**" />
    <Compile Remove="godot/**" />
  </ItemGroup>
```
```xml
<Project Sdk="Godot.NET.Sdk/4.6.0">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <TargetFramework Condition=" '$(GodotTargetPlatform)' == 'android' ">net9.0</TargetFramework>
    <EnableDynamicLoading>true</EnableDynamicLoading>
    <RootNamespace>bodygroups</RootNamespace>
  </PropertyGroup>
  <ItemGroup>
    <Folder Include="introductory\" />
  </ItemGroup>
  <ItemGroup>
    <!-- 排除不需要编译的目录 -->
    <Compile Remove="android/**" />
    <Compile Remove="flutter/**" />
    <Compile Remove="godot/**" />
  </ItemGroup>
</Project>
```

[https://docs.godotengine.org/en/latest/engine_details/development/compiling/compiling_with_script_encryption_key.html#step-by-step]
[https://github.com/godotengine/godot-swappy/releases]

解压godot-swappy.zip将arm64-v8 armeabi-v7a x86 x86_64文件夹复制到godot/thirdparty/swappy-frame-pacing



代码加密
生成加密的key
```shell
openssl rand -hex 32 > godot.gdkey
```

```shell
cat godot.gdkey
```


```gradle
 defaultConfig {
        applicationId = "com.xxx.xxxx"

        // 关键配置：不要忽略 .godot 等隐藏文件
        androidResources {
            ignoreAssetsPattern "!.svn:!.git:!.gitignore:!.ds_store:!*.scc:<dir>_*:!CVS:!thumbs.db:!picasa.ini:!*~"
        }

        ndk {
            abiFilters 'arm64-v8a','armeabi-v7a'
        }
    }
```


## Gradle 集成模块

`buildScript/build_android_lib.py` 在打包前会自动为 `android/build/settings.gradle`
注册 `:godot:lib` 和 `:godot_android:game_lib`，分别指向 `flutter_config/godot_android`
中的引擎库和游戏库目录，并补充 Android library 插件版本。重复执行不会重复注册。
Godot 重新安装 Android 构建模板后，再次运行打包脚本即可恢复注册。

引擎库会通过 SCons 编译 Godot 源码，首次构建需要源码要求的 NDK 版本；
仅有其他版本的 NDK 时仍需安装指定版本。产物按构建类型和 ABI 复制，避免混用不同架构。
游戏库 AAR 从集成模块自身的 `game_lib/build/outputs/aar` 目录收集。


统一构建入口的 `--export-mode` 默认是 `apk-debug`，用于准备游戏资源和 .NET 依赖，
最终打包并复制 Debug、Release 两种 AAR，无需配置 Release APK 的发布签名。
在游戏项目根目录执行：

```shell
python3 flutter_config/godot_android/buildScript/run_android_build.py
```

当前前置导出步骤仍会生成一个 Debug APK，最终使用 `android/out` 下的 AAR。
已有导出资源和依赖时，可加 `--skip-export` 直接打包 AAR；`--variant` 默认仍为 `both`。
如显式选择 `--export-mode apk-release` 或 `both`，则需要配置 Release APK 的发布签名。
`flutter_config/.gdignore` 用于避免将集成脚本及 Gradle 构建产物作为游戏资源导入和导出。


默认产物目录固定为游戏项目根目录下的 `android/out`，不受执行目录或 Android
Gradle 工程位置影响；统一入口与单独运行 `build_android_lib.py` 使用相同默认值。

```text
android/out/
├── debug/godot/
│   ├── godot_game_lib/    # 游戏库 AAR 和引用配置
│   └── godot_lib/         # 引擎 AAR 和依赖库
└── release/godot/
    ├── godot_game_lib/
    └── godot_lib/
```

如需其他输出位置，可通过 `--out-dir` 指定，仍按 `debug`、`release` 分目录。
