import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_godot/godot_controller.dart';
import 'package:flutter_godot/godot_state.dart';

typedef GodotInitCallback = void Function(GodotController controller);

class GodotView extends StatefulWidget {
  final Widget? placeholderWidget;
  final Widget? errorWidget;

  final GodotInitCallback? initCallback;

  final int gameWidth;
  final int gameHeight;

  const GodotView({
    super.key,
    this.placeholderWidget,
    this.errorWidget,
    this.initCallback,
    this.gameHeight = 1920,
    this.gameWidth = 1080,
  });

  @override
  State<GodotView> createState() => _State();
}

class _State extends State<GodotView> {
  late final GodotController _controller;

  int get gameWidth => widget.gameWidth;

  int get gameHeight => widget.gameHeight;

  @override
  void initState() {
    super.initState();
    newTexture();
  }

  @override
  void dispose() {
    unawaited(_controller.dispose());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_failed) return widget.errorWidget ?? const SizedBox.shrink();
    if (_controller.state != GodotState.InitSuccess) {
      if (_controller.state == GodotState.Init) {
        return widget.placeholderWidget ?? Container();
      }
      return widget.errorWidget ?? Container();
    }
    return LayoutBuilder(
      builder: (_, constraints) {
        final widgetSize = Size(constraints.maxWidth, constraints.maxHeight);

        // 简单缩放映射：假设拉伸铺满（无留黑）
        double mapX(double x) => x * (gameWidth / widgetSize.width);
        double mapY(double y) => y * (gameHeight / widgetSize.height);

        return GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTapDown: (details) {
            final local = details.localPosition;
            final gx = mapX(local.dx);
            final gy = mapY(local.dy);
            _controller.sendTap(x: gx, y: gy);
          },
          child: Texture(textureId: _controller.textureId),
        );
      },
    );
  }

  Future<void> newTexture() async {
    _controller = GodotController();
    try {
      await _controller.init(
        gameWidth: widget.gameWidth,
        gameHeight: widget.gameHeight,
      );
      if (!mounted) {
        await _controller.dispose();
        return;
      }
      if (_controller.state == GodotState.InitSuccess) {
        widget.initCallback?.call(_controller);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _failed = true);
      }
      return;
    }
    if (mounted) setState(() {});
  }

  bool _failed = false;
}
