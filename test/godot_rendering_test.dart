import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_godot/flutter_godot.dart';
import 'package:flutter_godot/flutter_godot_method_channel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('flutter_godot');
  final calls = <MethodCall>[];

  setUp(() {
    calls.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          calls.add(call);
          switch (call.method) {
            case 'initGodot':
              return {'textureId': 7};
            case 'release':
              return null;
            default:
              return true;
          }
        });
  });

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  test('channel sends dimensions, coordinates, messages and release', () async {
    final platform = MethodChannelFlutterGodot();
    expect(await platform.init(gameWidth: 100, gameHeight: 200), 7);
    expect(calls.last.arguments, {'gameWidth': 100, 'gameHeight': 200});
    expect(await platform.sendTap(textureId: 7, x: 12, y: 34), isTrue);
    expect(calls.last.arguments, {'textureId': 7, 'x': 12.0, 'y': 34.0});
    expect(await platform.sendPlatformEventMsg(msg: 'hello'), isTrue);
    expect(calls.last.arguments, {'platformEventMsg': 'hello'});
    await platform.release(textureId: 7);
    expect(calls.last.arguments, {'textureId': 7});
    await expectLater(
      platform.init(gameWidth: 0, gameHeight: 200),
      throwsArgumentError,
    );
  });

  testWidgets('view maps taps to game coordinates and releases texture', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Center(
          child: SizedBox(
            width: 100,
            height: 200,
            child: GodotView(gameWidth: 1000, gameHeight: 2000),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byType(Texture), findsOneWidget);
    await tester.tapAt(
      tester.getTopLeft(find.byType(Texture)) + const Offset(25, 50),
    );
    await tester.pump();
    final tap = calls.singleWhere((call) => call.method == 'sendTap');
    expect(tap.arguments, {'textureId': 7, 'x': 250.0, 'y': 500.0});
    await tester.pumpWidget(const SizedBox());
    await tester.pump();
    expect(calls.where((call) => call.method == 'release'), hasLength(1));
  });

  testWidgets('initialization exceptions show error widget', (tester) async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (_) async {
          throw PlatformException(code: 'godot_init_failed');
        });
    await tester.pumpWidget(
      const MaterialApp(home: GodotView(errorWidget: Text('failed'))),
    );
    await tester.pumpAndSettle();
    expect(find.text('failed'), findsOneWidget);
  });
}
