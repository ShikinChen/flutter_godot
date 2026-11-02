import 'package:flutter_godot/flutter_godot_platform_interface.dart';
import 'package:flutter_godot/godot_state.dart';

class GodotController {
  GodotState _state = GodotState.Init;

  GodotState get state => _state;

  int _textureId = -1;

  int get textureId => _textureId;

  FlutterGodotPlatform getPlatform() {
    return FlutterGodotPlatform.instance;
  }

  Future<int?> init({required int gameWidth, required int gameHeight}) async {
    if (_textureId >= 0) return _textureId;
    final result = await getPlatform().init(
      gameWidth: gameWidth,
      gameHeight: gameHeight,
    );
    if (result != null) {
      _state = GodotState.InitSuccess;
      _textureId = result;
    } else {
      _state = GodotState.InitFailed;
    }
    return result;
  }

  Future<void> dispose() async {
    final id = _textureId;
    _textureId = -1;
    if (id >= 0) await getPlatform().release(textureId: id);
  }

  Future<bool> sendTap({required double x, required double y}) {
    if (_textureId < 0) return Future.value(false);
    return getPlatform().sendTap(textureId: textureId, x: x, y: y);
  }

  Future<bool> sendPlatformEventMsg({required String msg}) {
    if (_textureId < 0) return Future.value(false);
    return getPlatform().sendPlatformEventMsg(msg: msg);
  }
}
