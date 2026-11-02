import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'flutter_godot_platform_interface.dart';

/// An implementation of [FlutterGodotPlatform] that uses method channels.
class MethodChannelFlutterGodot extends FlutterGodotPlatform {
  /// The method channel used to interact with the native platform.
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
