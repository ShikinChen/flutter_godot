import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_godot_example/main.dart';

void main() {
  testWidgets('shows initialization failure when native Godot is unavailable', (
    tester,
  ) async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(const MethodChannel('flutter_godot'), (
          _,
        ) async {
          throw PlatformException(code: 'unavailable');
        });
    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();
    expect(find.text('Godot Texture 示例'), findsOneWidget);
    expect(find.textContaining('Godot 初始化失败'), findsOneWidget);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(const MethodChannel('flutter_godot'), null);
  });
}
