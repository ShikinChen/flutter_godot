// This is a basic Flutter integration test.
//
// Since integration tests run in a full Flutter application, they can interact
// with the host side of a plugin implementation, unlike Dart unit tests.
//
// For more information about Flutter integration tests, please see
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
    // The version string depends on the host platform running the test, so
    // just assert that some non-empty string is returned.
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
