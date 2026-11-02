import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'flutter_godot_method_channel.dart';

abstract class FlutterGodotPlatform extends PlatformInterface {
  /// Constructs a FlutterGodotPlatform.
  FlutterGodotPlatform() : super(token: _token);

  static final Object _token = Object();

  static FlutterGodotPlatform _instance = MethodChannelFlutterGodot();

  /// The default instance of [FlutterGodotPlatform] to use.
  ///
  /// Defaults to [MethodChannelFlutterGodot].
  static FlutterGodotPlatform get instance => _instance;

  /// Platform-specific implementations should set this with their own
  /// platform-specific class that extends [FlutterGodotPlatform] when
  /// they register themselves.
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
