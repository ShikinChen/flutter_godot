import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'flutter_godot_method_channel.dart';

abstract class FlutterGodotPlatform extends PlatformInterface {
  /// 创建 FlutterGodotPlatform 平台接口。
  FlutterGodotPlatform() : super(token: _token);

  static final Object _token = Object();

  static FlutterGodotPlatform _instance = MethodChannelFlutterGodot();

  /// 当前使用的 [FlutterGodotPlatform] 默认实例。
  ///
  /// 默认使用 [MethodChannelFlutterGodot]。
  static FlutterGodotPlatform get instance => _instance;

  /// 各平台实现注册时，应将此实例设置为
  /// 自身继承 [FlutterGodotPlatform] 的实现类。
  static set instance(FlutterGodotPlatform instance) {
    PlatformInterface.verifyToken(instance, _token);
    _instance = instance;
  }

  Future<int?> init({required int gameWidth, required int gameHeight}) {
    throw UnimplementedError('init() has not been implemented.');
  }

  Future<bool> sendTap({
    required int textureId,
    required double x,
    required double y,
  }) {
    throw UnimplementedError('sendTap() has not been implemented.');
  }

  Future<bool> sendPlatformEventMsg({required String msg}) {
    throw UnimplementedError(
      'sendPlatformEventMsg() has not been implemented.',
    );
  }

  Future<void> release({required int textureId}) {
    throw UnimplementedError('release() has not been implemented.');
  }

  Future<String?> getPlatformVersion() {
    throw UnimplementedError('platformVersion() has not been implemented.');
  }
}
