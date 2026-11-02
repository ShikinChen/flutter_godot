import 'package:flutter/material.dart';
import 'package:flutter_godot/flutter_godot.dart';

void main() => runApp(const MyApp());

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  GodotController? _controller;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        backgroundColor: Colors.yellow,
        appBar: AppBar(title: const Text('Godot Texture 示例')),
        body: GodotView(
          gameWidth: 1080,
          gameHeight: 1920,
          placeholderWidget: const Center(child: CircularProgressIndicator()),
          errorWidget: const Center(child: Text('Godot 初始化失败，请检查 Android 日志与游戏资源')),
          initCallback: (controller) => setState(() => _controller = controller),
        ),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: _controller == null
              ? null
              : () async {
                  await _controller!.sendPlatformEventMsg(msg: '{"type":"ToScene","data":{"sceneName":"page_a"}}');
                },
          label: const Text('切换场景'),
          icon: const Icon(Icons.play_arrow),
        ),
      ),
    );
  }
}
