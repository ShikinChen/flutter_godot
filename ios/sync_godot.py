#!/usr/bin/env python3
"""将 Godot iOS 产物复制到插件内，供 flutter_godot.podspec 使用。"""
import argparse
import os
from pathlib import Path
import shutil
import tempfile


def main():
    plugin_ios = Path(__file__).resolve().parent
    default = plugin_ios / '../../../../workspace_godot/mydemo/godot_flutter_example/ios/out'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out_dir', nargs='?', default=os.environ.get('GODOT_IOS_OUT', str(default)))
    parser.add_argument('--variant', choices=('debug', 'release', 'both'), default='debug')
    args = parser.parse_args()
    source = Path(args.out_dir).expanduser().resolve()
    destination = plugin_ios / 'godot'
    if source == destination.absolute() or destination.absolute() in source.parents:
        parser.error('Source must be outside the plugin output directory')
    variants = ('debug', 'release') if args.variant == 'both' else (args.variant,)
    # 修改本地产物前，先验证所有选定构建类型的源文件。
    for variant in variants:
        for relative in ('godot_lib/GodotEngine.xcframework/Info.plist',
                         'godot_game_lib/Sources/GodotGame.h',
                         'godot_game_lib/Resources/game.pck'):
            if not (source / variant / relative).is_file():
                parser.error(f'Missing Godot artifact: {source / variant / relative}')
    # 仅移除旧版目录符号链接，不删除链接指向的外部目录。
    if destination.is_symlink():
        destination.unlink()
    destination.mkdir(parents=True, exist_ok=True)
    for variant in variants:
        with tempfile.TemporaryDirectory(prefix='.sync-', dir=destination) as staging:
            package = Path(staging) / variant
            shutil.copytree(source / variant, package)
            target = destination / variant
            if target.is_symlink():
                target.unlink()
            elif target.exists():
                shutil.rmtree(target)
            package.rename(target)
            print(f'{source / variant} -> {target}')


if __name__ == '__main__':
    main()
