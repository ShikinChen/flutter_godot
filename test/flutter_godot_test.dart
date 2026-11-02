import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_godot/flutter_godot.dart';
import 'package:flutter_godot/flutter_godot_platform_interface.dart';
import 'package:flutter_godot/flutter_godot_method_channel.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

class MockFlutterGodotPlatform extends FlutterGodotPlatform
    with MockPlatformInterfaceMixin {
  @override
  Future<String?> getPlatformVersion() => Future.value('42');
}

void main() {
  final FlutterGodotPlatform initialPlatform = FlutterGodotPlatform.instance;
  tearDown(() => FlutterGodotPlatform.instance = initialPlatform);

  test('$MethodChannelFlutterGodot is the default instance', () {
    expect(initialPlatform, isInstanceOf<MethodChannelFlutterGodot>());
  });

  test('getPlatformVersion', () async {
    FlutterGodot flutterGodotPlugin = FlutterGodot();
    MockFlutterGodotPlatform fakePlatform = MockFlutterGodotPlatform();
    FlutterGodotPlatform.instance = fakePlatform;

    expect(await flutterGodotPlugin.getPlatformVersion(), '42');
  });
}
