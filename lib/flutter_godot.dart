export 'godot_controller.dart';
export 'godot_state.dart';
export 'godot_view.dart';

import 'flutter_godot_platform_interface.dart';

class FlutterGodot {
  Future<String?> getPlatformVersion() {
    return FlutterGodotPlatform.instance.getPlatformVersion();
  }
}
