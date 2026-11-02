# flutter_godot

将 Godot 游戏嵌入 Flutter 页面，提供统一的 `GodotView`、控制器和平台消息接口。

- **Android**：通过 OpenGL ES 3 渲染到 Flutter `Texture`。
- **iOS**：通过 `UiKitView` 挂载 Godot 原生视图，使用 CocoaPods 集成引擎与游戏产物。

## 示例与构建工具

| 项目 | 用途 |
| --- | --- |
| [Godot 使用范例](https://github.com/ShikinChen/godot_flutter_example.git) | Godot 游戏工程，配合本插件导出游戏资源和原生产物 |
| [Flutter 示例](example/lib/main.dart) | 嵌入游戏、设置黄色背景、发送切换场景消息 |
| [游戏工程初始化](flutter_config/README.md) | 准备 Godot 源码、C# 编译排除项和构建配置 |
| [Android 构建说明](flutter_config/godot_android/README.md) | 编译引擎、导出游戏、生成 AAR |
| [iOS 构建说明](flutter_config/godot_ios/README.md) | 编译 XCFramework、导出 PCK 和 C# NativeAOT 产物 |

首次获取 Godot 使用范例（已有该工程时无需再次克隆）：

```bash
git clone https://github.com/ShikinChen/godot_flutter_example.git \
  /path/to/godot_flutter_example
```

本插件消费已构建的 Godot 产物，不会在 `flutter run` 时自动编译引擎或导出游戏。原生产物已加入 Git 忽略规则，首次接入或更换游戏时需先准备对应平台的产物。

## 环境要求

| 环境 | 要求 |
| --- | --- |
| Flutter / Dart | 当前开发环境为 Flutter 3.47.9 / Dart 3.13.7；Dart SDK 约束为 `^3.13.7` |
| Android | Android SDK 36、Java 17、最低 API 24；当前使用 AGP 9.1.0 |
| iOS | macOS、Xcode、CocoaPods，最低 iOS 15 |
| 游戏构建 | 按对应平台构建说明准备 Godot、Python、C#/.NET 及原生编译工具 |

游戏导出版本、引擎版本和原生接口必须匹配。当前 Android 引擎为 `custom_build`，使用了 `initEngine`、`renderView`、`GodotLib` 等接口，不能直接用任意官方 AAR 替换。

## flutter_config 使用教程

`flutter_config` 是放在 **Godot 游戏工程内**的构建工具，不是 Flutter 插件依赖。它负责初始化引擎源码、导出游戏资源，并将引擎和游戏打包成 Flutter 可消费的原生产物。

```text
Godot 游戏工程 + flutter_config
  ├── Android 构建 → android/out → 插件 android/godot → Gradle
  └── iOS 构建     → ios/out     → 插件 ios/godot     → CocoaPods
```

### 1. 复制到 Godot 游戏工程

以下示例以 Godot 游戏工程为基准。路径均为占位示例，请替换为实际目录；游戏与 Flutter 插件可以分别存放，无需位于同一目录：

| 工程 | 路径 |
| --- | --- |
| Godot 游戏 | `/path/to/godot_flutter_example` |
| Flutter 插件 | `/path/to/flutter_godot` |

Godot 工程中的目标结构如下：

```text
/path/to/godot_flutter_example/
├── project.godot
├── godot_flutter_example.csproj
├── export_presets.cfg
└── flutter_config/
    ├── init_project.py
    ├── godot_android/
    └── godot_ios/
```

将插件中的配置复制到游戏工程，再进入游戏根目录：

```bash
cp -R /path/to/flutter_godot/flutter_config \
  /path/to/godot_flutter_example/
cd /path/to/godot_flutter_example
```

复制后，`flutter_config` 与 `project.godot` 同级。后续游戏构建命令均在 **Godot 游戏工程根目录**执行；如果游戏已经包含该目录，可检查并更新现有配置，无需重复嵌套复制。

### 2. 初始化 Godot 源码与 C# 工程

准备 Python 3.9+、Git，以及与游戏版本匹配的 Godot .NET 编辑器和 .NET SDK。然后执行：

```bash
cd /path/to/godot_flutter_example
python3 flutter_config/init_project.py
```

初始化脚本默认克隆 `4.7.2-stable` 源码到游戏的 `godot/` 目录，并为根目录中的 `.csproj` 补充 `android/**`、`flutter/**`、`godot/**` 编译排除项，同时补充 Git 忽略规则。

需要指定版本或工程路径时：

```bash
python3 flutter_config/init_project.py --branch 4.7.2-stable
python3 flutter_config/init_project.py --project /path/to/godot_flutter_example
```

已有完整的 `godot/` 源码时会跳过克隆，`--branch` 不会切换已有源码版本。重新生成 `.csproj` 后可以再次执行，已有排除项不会重复添加。该初始化器要求存在 `.csproj`；纯 GDScript 工程不能直接使用此初始化步骤，需自行准备匹配版本的引擎源码。

### 3. 配置游戏导出预设与平台工具

在 Godot 编辑器中打开游戏，创建所需平台的导出预设并保存 `export_presets.cfg`：

| 目标 | 默认预设名 | 构建前准备 |
| --- | --- | --- |
| Android | `Android` | 安装 Android 导出模板、SDK、源码要求版本的 NDK、Java 17 和 SCons；在编辑器中配置 Android SDK/JDK 路径 |
| iOS | `iOS` | macOS、完整 Xcode、SCons 和 CocoaPods；C# 游戏还需匹配的 .NET iOS NativeAOT 支持 |

Android 构建前还需按 [Android 配置说明](flutter_config/godot_android/README.md) 准备 `godot/thirdparty/swappy-frame-pacing` 中的架构库，构建脚本会检查缺失项。

若 Android 构建脚本无法找到编辑器，可指定实际的可执行文件路径：

```bash
export GODOT_BIN=/Applications/Godot_mono.app/Contents/MacOS/Godot
```

iOS 统一入口通过 `--godot /path/to/Godot` 指定其他编辑器。编辑器、导出模板、源码与 C# SDK 版本应保持匹配。

### 4. 构建 Android 产物并交给 Flutter

在游戏根目录执行：

```bash
cd /path/to/godot_flutter_example
python3 flutter_config/godot_android/buildScript/run_android_build.py
```

默认先使用 `apk-debug` 导出准备游戏资源和 .NET 依赖，再通过集成的 Gradle/SCons 模块编译引擎并打包 **debug、release 两套 AAR**。前置步骤会生成 Debug APK，但接入 Flutter 使用的是以下 AAR 目录：

```text
/path/to/godot_flutter_example/android/out/
├── debug/
│   ├── godot_game_lib/
│   └── godot_lib/
└── release/
    ├── godot_game_lib/
    └── godot_lib/
```

若希望构建后直接输出到 Flutter 插件的产物目录，可改用：

```bash
cd /path/to/godot_flutter_example
python3 flutter_config/godot_android/buildScript/run_android_build.py \
  --out-dir /path/to/flutter_godot/android/godot
```

也可以将默认输出中的 `debug`、`release` 目录复制到插件的 `android/godot/` 下。每个模块目录仅保留一份对应 AAR，避免旧游戏产物与新产物混用。随后完成下方的 [Android 接入](#android-接入)，在插件示例目录运行：

```bash
cd /path/to/flutter_godot/example
flutter pub get
flutter run -d <android-device-id>
```

默认资源准备不要求 Release APK 发布签名；显式选择 `--export-mode apk-release` 或 `both` 时需配置签名。`--variant debug` 可只更新调试产物，但当前宿主 settings 会注册四个模块，因此首次接入应先准备完整的 debug/release 目录和 AAR。

### 5. 构建 iOS 产物并交给 Flutter

在游戏根目录执行：

```bash
cd /path/to/godot_flutter_example
python3 flutter_config/godot_ios/buildScript/run_ios_build.py --variant debug --jobs 6
```

脚本导出游戏资源，并编译、打包真机 arm64 与模拟器 arm64 引擎。C# 工程默认自动选择 mono，处理 NativeAOT 框架及相关数据。产物写入游戏的 `ios/out/debug/`；不传 `--variant` 时默认构建 debug/release 两套。

构建完成后，切到插件根目录同步产物，再安装 Pods：

```bash
cd /path/to/flutter_godot
python3 ios/sync_godot.py /path/to/godot_flutter_example/ios/out --variant debug
cd example
flutter pub get
cd ios
GODOT_VARIANT=debug pod install
cd ..
flutter run -d <ios-device-id>
```

首次接入需先完成下方的 [iOS 接入](#ios-接入) 配置；仓库中的 `example` 已包含对应配置。游戏资源导出不需要 IPA 签名，Flutter 真机运行仍需配置开发团队和签名。发布时构建、同步 release 产物，并使用 `GODOT_VARIANT=release pod install`。

### 6. 后续更新与常用参数

| 场景 | 操作 |
| --- | --- |
| Android 资源已导出，只重新编译打包 | Android 统一入口添加 `--skip-export` |
| iOS 只更新游戏资源，复用已有引擎 | iOS 统一入口添加 `--skip-engine`，然后重新同步并安装 Pods |
| iOS 只重新编译引擎，复用已有资源 | iOS 统一入口添加 `--skip-export` |
| iOS 预览构建命令 | 添加 `--dry-run`，不执行编译或写入产物 |
| 修改自定义原生模块或引擎源码 | 重新编译对应引擎，并更新 Flutter 插件中的产物 |
| 修改场景、C# 脚本或游戏资源 | 重新导出、打包并更新产物；Flutter 热重载不会更新 AAR/PCK |

首次引擎编译耗时较长，后续构建可复用 SCons 缓存。所有入口支持 `--help` 查看参数；初始化、平台环境及独立构建步骤详见 [flutter_config 总说明](flutter_config/README.md)、[Android 说明](flutter_config/godot_android/README.md) 和 [iOS 说明](flutter_config/godot_ios/README.md)。

## 快速开始

### 1. 添加依赖

```yaml
dependencies:
  flutter_godot:
    path: /path/to/flutter_godot
```

### 2. 准备原生产物

先按上方 [flutter_config 使用教程](#flutter_config-使用教程) 构建游戏和引擎产物，再按 [Android 接入](#android-接入) 或 [iOS 接入](#ios-接入) 配置宿主。仓库内的 `example` 已包含宿主配置，但仍需准备本地 Godot 产物。

### 3. 在 Flutter 页面显示游戏

```dart
import 'package:flutter/material.dart';
import 'package:flutter_godot/flutter_godot.dart';

class GamePage extends StatefulWidget {
  const GamePage({super.key});

  @override
  State<GamePage> createState() => _GamePageState();
}

class _GamePageState extends State<GamePage> {
  GodotController? _controller;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.yellow,
      body: GodotView(
        gameWidth: 1080,
        gameHeight: 1920,
        placeholderWidget: const Center(child: CircularProgressIndicator()),
        errorWidget: const Center(child: Text('Godot 初始化失败')),
        initCallback: (controller) {
          setState(() => _controller = controller);
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _controller == null
            ? null
            : () async {
                await _controller!.sendPlatformEventMsg(
                  msg: '{"type":"ToScene","data":{"sceneName":"page_a"}}',
                );
              },
        child: const Icon(Icons.play_arrow),
      ),
    );
  }
}
```

`GodotView` 需要有限的宽高约束；放在 `Column` 中时使用 `Expanded` 或 `SizedBox`。`initCallback` 表示 Android 纹理注册成功或 iOS 原生控制器已挂载，不表示游戏首帧或场景消息接收器已就绪。

### 4. 运行示例

```bash
cd example
flutter pub get
flutter devices
flutter run -d <device-id>
```

## Android 接入

### 产物目录

将游戏和引擎 AAR 按构建类型放入插件目录：

```text
android/
├── godot_aar.gradle
└── godot/
    ├── debug/
    │   ├── godot_game_lib/game_lib-mono-debug.aar
    │   └── godot_lib/godot-lib.template_debug.aar
    └── release/
        ├── godot_game_lib/game_lib-mono-release.aar
        └── godot_lib/godot-lib.template_release.aar
```

Debug 与 Release 分别使用配套的游戏和引擎 AAR。四个模块共用 [godot_aar.gradle](android/godot_aar.gradle)，产物目录中无需 `build.gradle`；每个模块目录应仅有一个 AAR。旁边的原始 `.so`、`.a` 等构建文件不会被单独打包。

游戏资源通过 AAR 的 Android assets 合并，无需在 Flutter `pubspec.yaml` 再次声明。重新导出游戏或编译引擎后，更新对应目录的 AAR。

### 宿主 Gradle 配置

在宿主 `android/settings.gradle.kts` 中添加以下配置，将 `godotRoot` 替换为实际的插件产物目录：

```kotlin
val godotRoot = file("/path/to/flutter_godot/android/godot")
include(":godot_game_lib_debug", ":godot_game_lib_release", ":godot_lib_debug", ":godot_lib_release")
project(":godot_game_lib_debug").projectDir = File(godotRoot, "debug/godot_game_lib")
project(":godot_game_lib_release").projectDir = File(godotRoot, "release/godot_game_lib")
project(":godot_lib_debug").projectDir = File(godotRoot, "debug/godot_lib")
project(":godot_lib_release").projectDir = File(godotRoot, "release/godot_lib")

listOf(":godot_game_lib_debug", ":godot_game_lib_release", ":godot_lib_debug", ":godot_lib_release").forEach {
    project(it).buildFileName = "../../../godot_aar.gradle"
}
```

`buildFileName` 相对于各模块的 `projectDir`，上述布局下均指向插件的 `android/godot_aar.gradle`。完整示例见 [settings.gradle.kts](example/android/settings.gradle.kts)。

在宿主 `android/app/build.gradle.kts` 的 `android` 中配置：

```kotlin
android {
    defaultConfig {
        minSdk = 24
    }
    androidResources {
        ignoreAssetsPattern = "!.svn:!.git:!.gitignore:!.ds_store:!*.scc:<dir>_*:!CVS:!thumbs.db:!picasa.ini:!*~"
    }
}
```

该资源规则用于保留 `.godot` 等隐藏导出资源。自定义 Android 构建类型需配置对应的 `matchingFallbacks`。

## iOS 接入

### 同步游戏产物

先按 [iOS 构建说明](flutter_config/godot_ios/README.md) 生成游戏工程的 `ios/out`，再在插件根目录执行：

```bash
python3 ios/sync_godot.py /path/to/godot_flutter_example/ios/out
```

默认同步 debug，`--variant release` 或 `--variant both` 可选择其他产物：

```text
ios/godot/debug/
├── godot_lib/          # GodotEngine.xcframework、隐私清单、许可证
└── godot_game_lib/     # Sources、Resources、Frameworks、BundleFiles
```

[sync_godot.py](ios/sync_godot.py) 只复制产物，不修改 Godot 源项目。同步目标是插件内的实际目录；不要用目录符号链接代替，CocoaPods 的源码扫描器不会递归展开这些链接。

### 配置 CocoaPods

[iOS Podspec](ios/flutter_godot.podspec) 统一声明引擎、游戏源码、PCK、C# AOT 框架和 ICU 数据。宿主无需另加 GodotEngine / GodotGame Pod，也无需登记 Flutter assets 或手动拖入 Xcode。

宿主需关闭 SwiftPM，并在应用的 `pubspec.yaml` 中配置：

```yaml
flutter:
  config:
    enable-swift-package-manager: false
```

在 Flutter 默认 Podfile 的基础上设置最低 iOS 15，并在 Runner target 中使用静态 framework：

```ruby
platform :ios, '15.0'

target 'Runner' do
  use_frameworks! :linkage => :static
  flutter_install_all_ios_pods File.dirname(File.realpath(__FILE__))
end
```

保留 Flutter 默认的其他 Podfile 配置，完整示例见 [Podfile](example/ios/Podfile)。示例的 Debug/Release xcconfig 在 `Generated.xcconfig` 后包含 Pods 配置，以应用 Podspec 的模拟器架构设置。当前产物支持 arm64 真机和 arm64 模拟器；Intel 模拟器需另行构建 x86_64 引擎。

在插件根目录运行：

```bash
cd example
flutter pub get
cd ios
pod install
open Runner.xcworkspace
```

也可以回到 `example` 目录通过 `flutter run -d <ios-device-id>` 启动。真机运行需要配置开发团队与签名。

### Release 与产物更新

在插件根目录执行：

```bash
python3 ios/sync_godot.py /path/to/godot_flutter_example/ios/out --variant release
cd example/ios
GODOT_VARIANT=release pod install
cd ..
GODOT_VARIANT=release flutter build ios --release --no-codesign
```

`--no-codesign` 仅构建未签名产物，不能直接安装到真机。`GODOT_VARIANT` 在 **Pod 安装时**选择游戏和引擎，不会随 Xcode Debug/Release 配置自动切换。默认 debug；切换变体或更新产物后，应重新同步并运行 `pod install`。切回调试时使用 `GODOT_VARIANT=debug pod install`。

## API 与消息

统一入口为 `package:flutter_godot/flutter_godot.dart`。

| 接口 | 说明 |
| --- | --- |
| `GodotView` | 显示游戏，自动管理视图卸载时的释放或解除挂载 |
| `GodotController.sendPlatformEventMsg(msg: ...)` | 向游戏发送字符串，返回是否接受发送 |
| `GodotController.sendTap(x: ..., y: ...)` | 仅 Android；参数为游戏坐标，iOS 使用原生触摸 |
| `GodotController.dispose()` | 手动管理控制器时释放会话资源 |
| `GodotController.state` / `GodotState` | 查询初始化状态 |
| `FlutterGodot().getPlatformVersion()` | 查询平台版本 |

Android 将组件内点击坐标映射至 `gameWidth × gameHeight`，当前按拉伸铺满处理。iOS 尺寸随原生 UIView 布局变化，由 Godot viewport/stretch 配置处理；`textureId` 在 iOS 只是内部会话标识，不能传给 Flutter `Texture`。iOS 必须通过 `GodotView` 创建原生视图，单独调用控制器 `init()` 不会创建视图。

### Flutter → Godot

平台插件名称为 `PlatformEvent`，游戏通过 `platform_event(String)` 信号接收消息。例如 GDScript：

```gdscript
func _ready():
    if Engine.has_singleton("PlatformEvent"):
        var platform = Engine.get_singleton("PlatformEvent")
        platform.connect("platform_event", _on_platform_event)

func _on_platform_event(message: String):
    print(message)
```

Flutter 侧发送：

```dart
final accepted = await controller.sendPlatformEventMsg(
  msg: '{"type":"ToScene","data":{"sceneName":"page_a"}}',
);
```

JSON 是范例游戏的业务协议，插件不负责解析或加载场景；`page_a` 必须由游戏实际提供并处理。返回成功不表示场景已切换。iOS 在场景信号尚未连接时可能返回 `false`，调用方可在游戏就绪后重试。Godot → Flutter 消息尚未暴露为 Dart 公共回调 API。

## 透明背景与使用限制

宿主背景色通过 `Scaffold.backgroundColor` 设置。要透出黄色等宿主背景，Godot 游戏需开启透明 viewport，并避免用不透明的场景背景覆盖；原生渲染层也需保留 Alpha。游戏配置示例：

```ini
[rendering]
viewport/transparent_background=true
environment/defaults/default_clear_color=Color(0, 0, 0, 0)
```

修改游戏工程后需重新导出并更新原生产物，Flutter 热重载不会同步 AAR/PCK 内容。

| 平台 | 当前限制 |
| --- | --- |
| Android | 单进程单 Godot 会话；销毁后需重启应用再创建。固定初始化渲染尺寸，强制 `opengl3` / `gl_compatibility`，不支持 Vulkan；仅转发单次点击，未实现拖动、多点触控或键盘输入 |
| Android 生命周期 | 后台恢复、Surface 重建和配置变化的恢复链路尚不完整，需在目标设备验证 |
| iOS | 同时只能展示一个 Godot 原生视图；卸载时暂停并解除控制器挂载，使用原生触摸；尚未提供 Flutter Texture 渲染 |
| 其他平台 | 暂未实现 Web 和桌面平台 |

## 验证与排错

在插件根目录执行：

```bash
flutter pub get
flutter analyze
flutter test
cd example
flutter test
flutter build apk --debug
```

构建与 Dart 测试不能替代目标设备上的游戏画面、场景消息、输入及生命周期验证。

| 现象 | 检查项 |
| --- | --- |
| Android 模块目录不存在 | 检查 `godotRoot` 和 `debug/godot_lib`、`release/godot_lib` 等路径，不应多一层 `godot/` |
| Android 提示 `No variants exist` | 检查四个模块是否通过 `buildFileName` 使用 `android/godot_aar.gradle` |
| AAR 缺失或重复 | 每个模块目录只放一个对应的 AAR；游戏与引擎版本需匹配 |
| Android 黑屏或资源加载失败 | 查看 logcat 中的 `GodotRenderHandler`、`EGLManager`、`godot` 日志，检查设备 ABI 与隐藏资源是否完整 |
| iOS 提示缺少 Godot 产物 | 先执行 `ios/sync_godot.py`，再运行 `pod install`；确认 `GODOT_VARIANT` 与同步目录一致 |
| 黄色背景没有更新 | 完整停止并重新运行应用；如果修改的是 Godot 内容，还需重新导出游戏产物 |
| iOS 启动白屏、VM Service 发现超时 | 检查设备解锁、USB 连接及应用日志；若同时提示 Device Support 符号缓存异常，按提示重新准备符号，完成后重启调试会话 |
