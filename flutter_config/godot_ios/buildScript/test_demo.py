#!/usr/bin/env python3
"""Install local Pods and build demo without requiring signing."""
import argparse
import os
import platform
import subprocess
from common import INTEGRATION, main_guard, run


def main():
    cli = argparse.ArgumentParser(description="pod install 并构建 iOS 测试 demo")
    cli.add_argument("--variant", choices=("debug", "release"), default="debug")
    cli.add_argument("--out-dir", help="已有 ios/out 产物根目录")
    cli.add_argument("--destination", default="generic/platform=iOS Simulator")
    cli.add_argument("--skip-pod-install", action="store_true")
    cli.add_argument("--arch", choices=("arm64", "x86_64"), default=platform.machine())
    cli.add_argument("--ui-test", action="store_true", help="运行 UI 冒烟测试，需用 --destination 指定具体模拟器")
    args = cli.parse_args()
    if args.ui_test and args.destination.startswith("generic/"):
        raise ValueError("UI 测试需要具体模拟器，例如 --destination 'platform=iOS Simulator,id=<UDID>'")
    demo = INTEGRATION / "demo"
    env = dict(os.environ, GODOT_VARIANT=args.variant)
    if args.out_dir:
        from pathlib import Path
        env["GODOT_IOS_OUT"] = str(Path(args.out_dir).expanduser().resolve())
    if not args.skip_pod_install:
        subprocess.run(["pod", "install"], cwd=demo, env=env, check=True)
    run(["xcodebuild", "-workspace", demo / "GodotIOSDemo.xcworkspace", "-scheme", "GodotIOSDemo",
         "-configuration", "Debug" if args.variant == "debug" else "Release",
         "-destination", args.destination, "-derivedDataPath", demo / "build", f"ARCHS={args.arch}", "CODE_SIGNING_ALLOWED=NO", "test" if args.ui_test else "build"])


if __name__ == "__main__":
    main_guard(main)
