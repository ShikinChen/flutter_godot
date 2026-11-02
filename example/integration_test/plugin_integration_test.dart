// Flutter 基础集成测试。
//
// 集成测试运行于完整的 Flutter 应用中，
// 因此可以调用插件宿主端实现；Dart 单元测试不具备此能力。
//
// Flutter 集成测试说明参见：
// https://flutter.dev/to/integration-testing

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';

import 'dart:io';

import 'package:integration_test/integration_test.dart';

import 'package:flutter_godot/flutter_godot.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('getPlatformVersion test', (WidgetTester tester) async {
    final FlutterGodot plugin = FlutterGodot();
    final String? version = await plugin.getPlatformVersion();
    // 版本字符串取决于运行测试的宿主平台，
    // 因此这里只验证返回值不是空字符串。
    expect(version?.isNotEmpty, true);
  });

  testWidgets('iOS embeds Godot and sends scene messages', (tester) async {
    GodotController? controller;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          backgroundColor: Colors.yellow,
          body: GodotView(initCallback: (value) => controller = value),
        ),
      ),
    );
    await tester.pumpAndSettle(const Duration(milliseconds: 100));
    expect(controller, isNotNull);
    expect(find.byType(UiKitView), findsOneWidget);
    for (final scene in ['page_a', 'main']) {
      var sent = false;
      for (var attempt = 0; attempt < 50; attempt++) {
        sent = await controller!.sendPlatformEventMsg(
          msg: '{"type":"ToScene","data":{"sceneName":"$scene"}}',
        );
        if (sent) break;
        await tester.pump(const Duration(milliseconds: 100));
      }
      expect(
        sent,
        isTrue,
        reason: 'Game signal must be connected before sending $scene',
      );
      await tester.pump(const Duration(milliseconds: 300));
    }
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
  }, skip: !Platform.isIOS);
}
