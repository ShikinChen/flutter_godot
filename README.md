# flutter_godot

将 Godot 游戏嵌入 Flutter 页面：Android 使用 `Texture`，iOS 使用 `UiKitView`。保留当前 Android 包名 `me.shiki.flutter_godot` 和 MethodChannel 名称 `flutter_godot`。

## 支持范围

- Android：Godot 引擎初始化、OpenGL ES 3 渲染、Flutter Texture 显示、点击输入、Flutter → Godot 字符串消息。
- iOS：通过 CocoaPods 引入 GodotEngine / GodotGame，以 UIKit 原生视图显示游戏，支持原生触摸和 Flutter → Godot 消息。尚未实现 iOS Flutter Texture；其他桌面平台和 Web 尚未实现。
- 当前为单进程单 Godot 会话，只能创建一个 `GodotView`。销毁后需要重启应用再创建，不能同时展示多个实例。

## 环境与依赖

本项目使用 Flutter 3.47.9 / Dart 3.13.7、Android SDK 36、Java 17，Android 最低 API 24。Android 使用当前项目的 AGP 9.1.0 配置。

`android/godot/` 按构建类型分别存放游戏和引擎 AAR，与 Godot 构建脚本的按变体输出目录对应：

```text
android/godot/
├── debug/
│   ├── godot_game_lib/    # game_lib-mono-debug.aar
│   └── godot_lib/         # godot-lib.template_debug.aar
└── release/
    ├── godot_game_lib/    # game_lib-mono-release.aar
    └── godot_lib/         # godot-lib.template_release.aar
```

Debug 同时使用 debug 游戏和引擎，Release 同时使用 release 游戏和引擎，避免混用游戏资源与原生运行时。四个模块统一使用产物目录之外的 `android/godot_aar.gradle`，因此导出目录无需包含 `build.gradle`，替换产物也不会丢失模块配置。每个模块目录只放一个 AAR，缺少或重复时会明确报错。引擎模块仅导出对应 AAR，旁边的 `arm64-v8a/` 原始构建文件不会额外参与打包。

当前引擎 AAR 的 manifest 标记为 `custom_build`，渲染适配层已实现其 `blockingExitRenderer(timeout)` 接口。游戏与引擎的实际版本以当前 AAR 为准；重新构建时需统一游戏导出版本、引擎版本与 `flutter_config` 初始化脚本使用的源码版本。

这些是源项目现有的构建产物，包含的 ABI 取决于 AAR 内容。使用自己的游戏时，替换游戏 AAR，并保证游戏、Godot Java 接口和原生引擎版本匹配。不要直接替换为任意官方 AAR：当前实现依赖 `initEngine`、`renderView`、`GodotLib` 等接口及输入处理器反射访问。

游戏资源随游戏 AAR 的 Android assets 合并，无需在 Flutter `pubspec.yaml` 再登记。若另行提供 Android assets，必须包含导出游戏所需的完整文件和隐藏目录。

## 接入 Android 应用

添加本地依赖：

```yaml
dependencies:
  flutter_godot:
    path: ../flutter_godot
```

在宿主 `android/settings.gradle.kts` 中加入下面的模块声明。路径相对于宿主的 `android/` 目录，请按实际目录调整；本仓库的 example 已配置完成。

```kotlin
val godotRoot = file("../../flutter_godot/android/godot")
include(":godot_game_lib_debug", ":godot_game_lib_release", ":godot_lib_debug", ":godot_lib_release")
project(":godot_game_lib_debug").projectDir = File(godotRoot, "debug/godot_game_lib")
project(":godot_game_lib_release").projectDir = File(godotRoot, "release/godot_game_lib")
project(":godot_lib_debug").projectDir = File(godotRoot, "debug/godot_lib")
project(":godot_lib_release").projectDir = File(godotRoot, "release/godot_lib")

listOf(":godot_game_lib_debug", ":godot_game_lib_release", ":godot_lib_debug", ":godot_lib_release").forEach {
    project(it).buildFileName = "../../../godot_aar.gradle"
}
```

`buildFileName` 相对于各模块的 `projectDir`，上述布局下均指向插件的 `android/godot_aar.gradle`。

宿主 `android/app/build.gradle.kts` 的 `android` 中配置：

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

保留 `.godot` 等导出资源，否则可能出现资源加载失败或黑屏。插件依据 debug/release 构建类型选择游戏及引擎 AAR；自定义构建类型需配置对应的 `matchingFallbacks`。

## 接入 iOS：在插件 Podspec 引入 Godot

引擎、游戏源码、PCK、C# AOT 动态框架和 ICU 数据统一由
[ios/flutter_godot.podspec](ios/flutter_godot.podspec) 声明。宿主 Podfile 只需要 Flutter 默认的
`flutter_install_all_ios_pods`，无需额外声明 GodotEngine / GodotGame，也无需登记 Flutter assets 或手动拖入 Xcode。

CocoaPods 文件路径相对于插件目录，因此先将游戏的 `ios/out` 同步到插件的 `ios/godot`：

```sh
# 在 flutter_godot 插件根目录执行
python3 ios/sync_godot.py \
  /Users/shiki/Workspace/workspace_godot/mydemo/godot_flutter_example/ios/out
```

默认同步 debug，产物目录如下；`ios/godot` 为生成目录，已加入 Git 忽略规则。

```text
ios/godot/debug/
├── godot_lib/          # GodotEngine.xcframework、隐私清单、许可证
└── godot_game_lib/     # Sources、Resources、Frameworks、BundleFiles
```

同步脚本只复制产物，不修改 Godot 源项目。需要完整本地目录，目录符号链接不会被 CocoaPods 的源码扫描器递归展开。
重新导出游戏或编译引擎后，重新执行同步脚本，再运行 `pod install`。

Podspec 中的关键配置：

```ruby
godot_variant = ENV.fetch('GODOT_VARIANT', 'debug')
godot_root = "godot/#{godot_variant}"
# 在 Pod::Spec.new 中
s.source_files = 'flutter_godot/Sources/flutter_godot/**/*.swift',
                 "#{godot_root}/godot_game_lib/Sources/*.{h,mm}"
s.vendored_frameworks = "#{godot_root}/godot_lib/GodotEngine.xcframework",
                        "#{godot_root}/godot_game_lib/Frameworks/*.xcframework"
```

当前 iOS 使用 CocoaPods，最低 iOS 15。example 的 `pubspec.yaml` 已关闭此应用的 SwiftPM，
并使用 `use_frameworks! :linkage => :static`。在其他 Flutter 宿主复用时也需要启用 CocoaPods。
示例的 `Flutter/Debug.xcconfig` 和 `Release.xcconfig` 在 `Generated.xcconfig` 后包含 Pods 配置，
使 Podspec 自动计算的模拟器架构配置生效。当前引擎支持 arm64 真机和 arm64 模拟器；
Intel 模拟器需要先构建包含 x86_64 的引擎产物。

运行 example：

```sh
flutter pub get
cd example/ios
pod install
open Runner.xcworkspace
# 或回到 example 目录执行 flutter run -d <设备ID>
```

Release 需先生成 Godot 的 `ios/out/release`，再执行：

```sh
# 插件根目录
python3 ios/sync_godot.py /path/to/game/ios/out --variant release
cd example/ios
GODOT_VARIANT=release pod install
cd ..
GODOT_VARIANT=release flutter build ios --release --no-codesign
```

`--variant both` 可同步 debug 和 release；Podspec 的 `GODOT_VARIANT` 选择是 **Pod 安装时选择**，
不是 Xcode 自动切换。默认 debug，切换或更新产物后需重新安装 Pods。

Flutter 中继续使用同一个 `GodotView` 和 `GodotController.sendPlatformEventMsg`。
iOS 通过原生触摸接收点击/拖动，`sendTap` 只适用于 Android；iOS 画面尺寸随 UIView 布局变化，
由 Godot 的 viewport/stretch 配置处理。控制器的 `textureId` 在 iOS 仅作内部会话标识，不能交给 `Texture`。
iOS 需要通过 `GodotView` 创建原生视图，直接调用控制器 `init` 不会创建视图。

初始化回调表示原生控制器已挂载；场景信号尚未连接时发送消息会返回 false，调用方可稍后重试。
宿主背景色通过 `Scaffold.backgroundColor` 设置；游戏需开启透明 viewport，原生库需设置非 opaque 渲染层。
当前游戏已配置透明背景。原生库处理前后台暂停/恢复，插件在卸载时暂停并解除控制器挂载。
Godot → Flutter 回调尚未接入 Dart 公共 API。

参考：[CocoaPods Podspec 文件声明](https://guides.cocoapods.org/syntax/podspec.html)、
[Flutter iOS 原生视图](https://docs.flutter.dev/platform-integration/ios/platform-views)。

## Flutter 使用

统一导入入口为 `lib/flutter_godot.dart`，导出 `GodotView`、`GodotController` 和 `GodotState`：

```dart
import 'package:flutter/material.dart';
import 'package:flutter_godot/flutter_godot.dart';

class GamePage extends StatelessWidget {
  const GamePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: GodotView(
        gameWidth: 1080,
        gameHeight: 1920,
        placeholderWidget: const Center(child: CircularProgressIndicator()),
        errorWidget: const Center(child: Text('Godot 初始化失败')),
        initCallback: (controller) {
          // 控制器可在此保存，供按钮发送消息。
        },
      ),
    );
  }
}
```

`GodotView` 需要有限的宽高约束；放在 `Column` 中时使用 `Expanded` 或 `SizedBox`。画面按组件区域拉伸，点击坐标按实际组件尺寸映射至 `gameWidth × gameHeight`。Android 当前仅转发单次点击（DOWN/UP），未实现拖动、多点触控或键盘输入；iOS 使用原生视图直接接收触摸。

`initCallback` 在纹理注册成功后调用，比源项目在初始化前回调更晚；它不表示 Godot 已渲染首帧。Dart 初始化异常会显示 `errorWidget`，渲染线程中的引擎/EGL 错误需查看 Android 日志。

```dart
await controller.sendTap(x: 540, y: 960); // 游戏坐标
await controller.sendPlatformEventMsg(
  msg: '{"type":"ToScene","data":{"sceneName":"show_scene"}}',
);
```

`GodotView` 在卸载时自动释放 Android 纹理或解除 iOS 原生视图挂载。Android 中自行调用 `GodotController.init()` 管理纹理的使用者，需要自行 `await controller.dispose()`。Android 渲染尺寸在创建时确定，不支持运行中修改。

## Godot 消息约定

Android 注册名为 `PlatformEvent` 的 Godot 插件，通过 `platform_event(String)` 信号向游戏发送消息。JSON 只是示例业务协议，插件不会解析 JSON，场景名和消息处理由游戏实现。例如在 GDScript 中：

```gdscript
func _ready():
    if Engine.has_singleton("PlatformEvent"):
        var platform = Engine.get_singleton("PlatformEvent")
        platform.connect("platform_event", _on_platform_event)

func _on_platform_event(message: String):
    print(message)
```

游戏调用 `PlatformEvent.onGodotEventMsg` 当前只写入 Android 日志，没有向 Dart 回调的公开接口。源项目中未接通的 Dart 回调映射没有作为可用功能暴露。

## 渲染链路与迁移内容

```text
GodotView → GodotController → MethodChannel flutter_godot
  → FlutterGodotPlugin → SurfaceProducer / Surface
  → GodotRenderHandlerThread → Godot.initEngine
  → EGL / GodotLib.step → Flutter Texture
```

- `lib/godot_*.dart`：视图、状态和控制器；`flutter_godot.dart` 保留 `FlutterGodot.getPlatformVersion()`。
- `android/src/main/kotlin/me/shiki/flutter_godot/`：引擎宿主、渲染线程、EGL/FBO 工具、输入和消息插件。
- `android/godot/`：本地引擎与游戏 AAR；`example/android/settings.gradle.kts` 提供模块配置样例。
- 修复原实现初始化异常不回复 MethodChannel、无效参数处理和销毁时未停止绘制/释放 EGL 的问题。帧绘制使用 EGL window surface，避免仅绘制到未复制到窗口的离屏 FBO。
- 未迁入源项目中未使用的 `Test.kt` 实验渲染器。现有 `flutter_config/` 保留，用于游戏工程初始化和 Android 构建，详见 [配置说明](flutter_config/README.md) 和 [Android 构建说明](flutter_config/godot_android/README.md)。

当前渲染器强制 `opengl3` / `gl_compatibility`，不支持 Vulkan。源项目的后台暂停、Surface 重建和配置变化恢复没有完整实现，当前也不能保证后台恢复稳定；生产接入前需在目标设备验证这些生命周期场景。

## 运行与验证

```bash
flutter pub get
flutter analyze
flutter test
cd example
flutter test
flutter run -d <android-device-id>
# 只构建 APK
flutter build apk --debug
```

Dart 测试覆盖通道参数、点击坐标缩放、错误展示、释放调用和原有版本查询。实际画面、C# 运行时加载、消息触发场景切换及生命周期恢复需使用匹配 ABI 的 Android 设备验证。示例的“切换场景”按钮依赖游戏处理 `ToScene` 协议及包含 `show_scene` 场景。

出现黑屏时，先检查 logcat 中 `GodotRenderHandler`、`EGLManager`、`godot` 的错误，再确认 AAR 版本、设备 ABI 和资源完整性。若 Gradle 提示找不到 `godot_game_lib_debug` 或 `godot_game_lib_release`，检查宿主 settings 中的模块路径。

初次迁移验证（旧目录）：`flutter analyze` 无问题，插件 6 项测试与示例 1 项测试通过，`example` 的 `flutter build apk --debug` 成功。尚未进行 Android 真机画面与消息联调。

新目录适配验证：示例 `flutter build apk --debug` 与 `flutter build apk --release` 均成功，分别使用对应构建类型的游戏和引擎模块。新 AAR 的真机渲染及退出流程尚未联调。
