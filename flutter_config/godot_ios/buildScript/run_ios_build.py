#!/usr/bin/env python3
"""统一构建入口，明确将未知参数作为错误处理。"""
import sys
from pathlib import Path
from common import main_guard, parser, run


def main():
    cli = parser("统一构建 iOS 引擎、游戏资源和 CocoaPods 本地库")
    cli.add_argument("--skip-export", action="store_true")
    cli.add_argument("--skip-engine", action="store_true")
    cli.add_argument("--godot", default="/Applications/Godot_mono.app/Contents/MacOS/Godot")
    cli.add_argument("--preset", default="iOS")
    cli.add_argument("--jobs", type=int, default=4)
    cli.add_argument("--simulator-archs", nargs="+", choices=("arm64", "x86_64"), default=["arm64"])
    args = cli.parse_args()
    base = Path(__file__).resolve().parent
    shared = ["--variant", args.variant, "--edition", args.edition]
    for flag in ("project", "out_dir"):
        if getattr(args, flag):
            shared.extend(["--" + flag.replace("_", "-"), getattr(args, flag)])
    if args.dry_run:
        shared.append("--dry-run")
    if not args.skip_export:
        run([sys.executable, base / "export_project.py", *shared, "--godot", args.godot, "--preset", args.preset])
    if not args.skip_engine:
        run([sys.executable, base / "build_godot_ios_lib.py", *shared, "--jobs", args.jobs,
             "--simulator-archs", *args.simulator_archs])


if __name__ == "__main__":
    main_guard(main)
