# Godot iOS / CocoaPods

仿照 `godot_android`，将引擎、游戏资源、平台消息封装与原生测试 demo 分开。
默认从脚本所在目录定位游戏项目，不依赖终端工作目录。所有构建产物放在
`<游戏项目>/ios/out`，不写入 Android 目录。

## 环境

- macOS、完整 Xcode（包含 iOS 和 Simulator SDK），已接受 Xcode 许可。
- Python 3.9+、SCons、CocoaPods。
- 与游戏项目版本一致的 Godot 源码，放在项目根目录的 `godot/`。
- Godot 编辑器，默认 `/Applications/Godot_mono.app/Contents/MacOS/Godot`。
- C# 游戏还需要匹配 Godot SDK 的 .NET SDK / iOS NativeAOT 支持，及可访问 NuGet 的网络。

```sh
brew install scons cocoapods
python3 flutter_config/init_project.py
xcodebuild -version
pod --version
```

游戏的 `export_presets.cfg` 中需要名为 `iOS` 的 iOS 导出预设，可在 Godot 编辑器中添加。
资源导出使用 `--export-pack`，无需开发者团队、描述文件或 IPA 签名。
真机运行 demo 时，需要在 Xcode 中给 demo target 配置自己的 Signing Team。

## 一键构建

在游戏项目根目录执行：

```sh
python3 flutter_config/godot_ios/buildScript/run_ios_build.py

# 首次调试可仅构建 debug，默认真机 arm64 + 模拟器 arm64
python3 flutter_config/godot_ios/buildScript/run_ios_build.py --variant debug --jobs 6

# 额外支持 Intel Mac 模拟器，模拟器架构将通过 lipo 合并
python3 flutter_config/godot_ios/buildScript/run_ios_build.py --simulator-archs arm64 x86_64

# 查看命令，不执行编译或写入产物
python3 flutter_config/godot_ios/buildScript/run_ios_build.py --variant debug --dry-run
```

默认 `--variant both`，分别生成 debug/release 包。`--edition auto` 在项目根目录有
`.csproj` 时选择 mono，否则选择 standard；可显式指定 `--edition mono|standard`。
standard 模式发现场景或资源直接引用 C# 时会报错，避免导出无法执行脚本的包。
动态加载的 C# 脚本也需要 mono，请勿对 C# 游戏强制选择 standard。

```text
ios/out/
├── debug/
│   ├── godot_lib/
│   │   ├── GodotEngine.podspec
│   │   ├── GodotEngine.xcframework
│   │   ├── Headers/
│   │   ├── PrivacyInfo.xcprivacy
│   │   ├── LICENSE.txt
│   │   └── COPYRIGHT.txt
│   └── godot_game_lib/
│       ├── GodotGame.podspec
│       ├── Sources/
│       ├── Resources/game.pck
│       ├── Frameworks/<游戏程序集>.xcframework   # mono
│       └── BundleFiles/icudt.dat                # mono，导出有此文件时
└── release/
    └── ...
```

独立步骤与参数：

```sh
python3 flutter_config/godot_ios/buildScript/export_project.py --variant debug
python3 flutter_config/godot_ios/buildScript/build_godot_ios_lib.py --variant debug

# .a 已生成时，仅重新打包 CocoaPods 引擎产物
python3 flutter_config/godot_ios/buildScript/build_godot_ios_lib.py --variant debug --skip-compile

# 自定义编辑器、导出预设、项目和输出路径
python3 flutter_config/godot_ios/buildScript/run_ios_build.py \
  --project /path/to/game --out-dir /path/to/dist/ios \
  --godot /path/to/Godot --preset iOS --variant debug

# 复用已有引擎，仅更新资源（或使用 --skip-export 仅编译引擎）
python3 flutter_config/godot_ios/buildScript/run_ios_build.py --variant debug --skip-engine
```

导出和编译使用同一 edition。修改自定义引擎模块后需要重新编译引擎；修改场景、
C# 或游戏资源后需要重新导出。切换变体或更新产物后重新执行 `pod install` 并构建宿主。
初次完整引擎编译时间较长，需要足够磁盘空间；SCons 后续会增量编译。

## CocoaPods 引用

在宿主 Podfile 中同时声明两个本地 Pod（路径指向生成目录）：

```ruby
platform :ios, '15.0'
target 'YourApp' do
  pod 'GodotEngine', :path => '/path/to/game/ios/out/debug/godot_lib'
  pod 'GodotGame', :path => '/path/to/game/ios/out/debug/godot_game_lib'
end
```

执行 `pod install` 后打开 `.xcworkspace`。发布宿主时改用 `release` 路径并重新安装 Pods。
一份 Pod 安装选择一个游戏变体，不能同时链接两份 Godot 引擎。
不要额外链接官方导出模板中的 `libgodot`，不要使用 `-all_load` 强制加载整个引擎归档。
CocoaPods 会处理 XCFramework 的设备选择、C# 动态框架嵌入和资源复制。

Objective-C 宿主嵌入示例（在主线程调用）：

```objc
#import <GodotGame/GodotGame.h>

NSError *error = nil;
UIViewController *game = [GodotGame.shared startWithError:&error];
if (game) {
    [self addChildViewController:game];
    game.view.frame = self.view.bounds;
    game.view.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    [self.view addSubview:game.view];
    [game didMoveToParentViewController:self];
} else {
    NSLog(@"%@", error);
}
```

当前封装一个进程只启动一个引擎，重复调用返回同一控制器。不要同时挂到多个父控制器；
保留并复用它，暂不支持销毁后重启。启动失败需要重启应用再试。
封装监听应用前后台通知并转发给 Godot，宿主无需继承 Godot 的 AppDelegate；
不要再转发一遍，也不要在宿主 Info.plist 添加 `godot_cmdline`。

## 平台消息（与 Android 保持一致）

自定义引擎模块注册 `Engine.GetSingleton("PlatformEvent")`，提供：

- `platform_event(json)` 信号：iOS → Godot。
- `onGodotEventMsg(json)` 方法：Godot → iOS，另提供 `send_event(json)` 别名。

现有 `PlatformEventNode.cs` 可以继续使用同样接口。

```objc
BOOL queued = [GodotGame.shared sendPlatformEvent:
    @"{\"type\":\"ToScene\",\"data\":{\"sceneName\":\"page_a\"}}"];
// queued=NO: 场景桥接尚未就绪或 JSON 无效；由调用方稍后重试。

[[NSNotificationCenter defaultCenter] addObserverForName:GodotGameEventNotification
    object:nil queue:NSOperationQueue.mainQueue usingBlock:^(NSNotification *note) {
        NSLog(@"Godot -> iOS: %@", note.userInfo[@"json"]);
    }];

[GodotGame.shared pause];
[GodotGame.shared resume];
```

消息以 JSON 字符串传输。入队成功表示桥接已接收，不代表游戏业务处理成功。
`pause` 停止帧循环，`resume` 在应用处于前台时恢复；后台切回前台不会覆盖手动暂停状态。

## 测试 demo

demo 是原生 UIKit App，通过 CocoaPods 引用生成库，不需要 Flutter SDK。
包含 page_a/main 消息按钮、暂停/恢复、宿主底色切换、Godot 回调显示。
切换场景需要游戏包含对应场景和 `PlatformEvent` 信号处理器，当前示例项目已具备这些接口。

```sh
# 先生成 debug 产物，再安装 Pods 并进行无签名模拟器构建
python3 flutter_config/godot_ios/buildScript/test_demo.py

# 自定义产物目录 / Release
python3 flutter_config/godot_ios/buildScript/test_demo.py \
  --out-dir /path/to/dist/ios --variant release

open flutter_config/godot_ios/demo/GodotIOSDemo.xcworkspace

# 可选 UI 冒烟测试：启动引擎、消息入队、暂停/恢复、背景切换并保存截图
python3 flutter_config/godot_ios/buildScript/test_demo.py --ui-test \
  --destination 'platform=iOS Simulator,id=<模拟器 UDID>'
```

在 Xcode 选择模拟器运行。真机运行时选择自己的团队和设备。
也可手动在 `demo/` 下执行 `pod install`，环境变量 `GODOT_VARIANT=release` 选择 release，
`GODOT_IOS_OUT=/absolute/path/to/ios/out` 更改输出根目录。
仓库已包含 Xcode 工程，`generate_project.rb` 仅用于重新生成，需 Ruby `xcodeproj` gem。

验收：游戏正常出现；page_a/main 能互切；游戏发出的消息显示在底部；暂停后动画停止；
切回前台可恢复；切换宿主底色时游戏透明区域应跟随变化。引擎日志可在 Xcode 控制台查看。

## 渲染与范围

本版本统一使用 Godot Compatibility / OpenGL ES 3，支持真机与模拟器，避免额外引入
MoltenVK，并在启动参数中覆盖项目默认的 Mobile 渲染器。依赖 Mobile/Forward+ 特性的
游戏需要另行适配，不能直接用此配置验证其效果。相机模块和 SDL 手柄驱动当前关闭，
未接入 `.gdip` 插件。打包会从引擎静态归档中移除上游独立 SwiftUI App 入口，
并统一设备/模拟器切片的库名为 `libGodotEngine.a`，供 CocoaPods 正确链接。
引擎显式使用 `disable_path_overrides=no`，允许宿主通过 `--main-pack` 加载 Pod 资源包中的 PCK。

游戏项目需设置 `rendering/viewport/transparent_background=true`；封装在视图就绪后将
UIKit 和 GLES 渲染层设置为非 opaque。当前是 UIViewController 嵌入，
**尚未实现 Flutter Texture / CVPixelBuffer 输出**；接入 Flutter Texture 时还需单独实现
纹理共享、Alpha 保留及帧通知。不能将原生视图透明测试视为纹理透明测试。

C# 通过 Godot 的 iOS 导出触发 NativeAOT，将生成的 dylib 切片转换为动态 Framework，
由 Pod 嵌入。打包附带 ICU 数据。只支持 Godot 默认 `.godot/mono/temp/bin` 输出布局，
自定义 .NET 输出路径、第三方原生插件及额外运行时文件需要相应扩展脚本。

脚本检查：

```sh
python3 -m unittest discover -s flutter_config/godot_ios/tests -v
```

参考：[Godot iOS 编译说明](https://docs.godotengine.org/en/latest/engine_details/development/compiling/compiling_for_ios.html)、
[Apple XCFramework 打包说明](https://developer.apple.com/documentation/xcode/creating-a-multi-platform-binary-framework-bundle)。
