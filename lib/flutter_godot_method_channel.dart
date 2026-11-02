import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'flutter_godot_platform_interface.dart';

/// 通过方法通道实现 [FlutterGodotPlatform]。
class MethodChannelFlutterGodot extends FlutterGodotPlatform {
  /// 用于与原生平台通信的方法通道。
  @visibleForTesting
  final methodChannel = const MethodChannel('flutter_godot');

  @override
  Future<int?> init({required int gameWidth, required int gameHeight}) async {
    if (gameWidth <= 0 || gameHeight <= 0) {
      throw ArgumentError('Godot render dimensions must be positive.');
    }
    final result = await methodChannel.invokeMapMethod<String, dynamic>(
      'initGodot',
      {'gameWidth': gameWidth, 'gameHeight': gameHeight},
    );
    final id = result?['textureId'];
    return id is int && id >= 0 ? id : null;
  }

  @override
  Future<bool> sendTap({
    required int textureId,
    required double x,
    required double y,
  }) async {
    return await methodChannel.invokeMethod<bool>('sendTap', {
          'textureId': textureId,
          'x': x,
          'y': y,
        }) ??
        false;
  }

  @override
  Future<bool> sendPlatformEventMsg({required String msg}) async {
    return await methodChannel.invokeMethod<bool>('sendPlatformEventMsg', {
          'platformEventMsg': msg,
        }) ??
        false;
  }

  @override
  Future<void> release({required int textureId}) async {
    await methodChannel.invokeMethod<void>('release', {'textureId': textureId});
  }

  @override
  Future<String?> getPlatformVersion() async {
    final version = await methodChannel.invokeMethod<String>(
      'getPlatformVersion',
    );
    return version;
  }
}
