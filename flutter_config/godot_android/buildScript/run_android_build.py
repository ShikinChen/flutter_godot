#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
run_android_build.py - 顺序执行：
1) export_project.py 使用 apk-debug 准备游戏资源与依赖
2) build_android_lib.py 打包并复制 game_lib 产物（默认 both）

用法示例：
  # 默认使用 apk-debug 准备资源，再生成 Debug、Release AAR
  python run_android_build.py

  # 只导出 release APK，且只打包 release 的 game_lib
  python run_android_build.py --export-mode apk-release --variant release

  # 指定导出输出 APK 路径（both 模式会生成 -debug/-release 两个）
  python run_android_build.py --export-output /abs/path/to/android.apk

  # 指定 Android 工程目录（包含 gradlew），并指定 out 根目录
  python run_android_build.py --android-dir /abs/path/to/android --out-dir /abs/path/to/out

  # 指定 Godot 导出预设名（export_presets.cfg 中）
  python run_android_build.py --export-preset Android

  # 跳过某一步
  python run_android_build.py --skip-export
  python run_android_build.py --skip-lib
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List

# 颜色输出类
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color
    
    @staticmethod
    def is_supported():
        """检查终端是否支持颜色"""
        return sys.stdout.isatty() and os.name != 'nt'
    
    @classmethod
    def disable_if_unsupported(cls):
        """如果不支持颜色则禁用"""
        if not cls.is_supported():
            cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.NC = ''

# 初始化颜色支持
Colors.disable_if_unsupported()

def print_info(msg: str) -> None:
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {msg}")

def print_warn(msg: str) -> None:
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def print_err(msg: str) -> None:
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}", file=sys.stderr)

def script_root() -> Path:
    # 本脚本建议放在 android/build/godot/buildScript/
    return Path(__file__).resolve().parent


def find_project_root(start: Path) -> Path:
    p = start.expanduser().resolve()
    for cand in (p, *p.parents):
        if (cand / "project.godot").exists():
            return cand
    raise FileNotFoundError(f"未找到 project.godot（从 {p} 向上搜索）")

def run(cmd: List[str], cwd: Optional[Path] = None) -> int:
    print_info(f"执行命令: {' '.join(cmd)}")
    try:
        # 继承父进程的环境和输出
        env = os.environ.copy()
        # 打印实时日志
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
        proc.wait()
        return proc.returncode
    except KeyboardInterrupt:
        print_warn("用户中断")
        return 130
    except FileNotFoundError as e:
        print_err(f"命令未找到: {e}")
        return 127
    except Exception as e:
        print_err(str(e))
        return 1

def parse_args():
    parser = argparse.ArgumentParser(
        description="顺序执行 export_project.py 与 build_android_lib.py 的统一入口",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # 流程控制
    parser.add_argument("--skip-export", action="store_true", help="跳过 export_project.py 步骤")
    parser.add_argument("--skip-lib", action="store_true", help="跳过 build_android_lib.py 步骤")

    # export_project.py 参数
    parser.add_argument("--export-mode",
                        choices=["both", "apk-debug", "apk-release"],
                        default="apk-debug",
                        help="资源准备使用的导出模式（默认 apk-debug，最终产物为 AAR）")
    parser.add_argument("--export-preset",
                        default="Android",
                        help="export_project.py 预设名（export_presets.cfg）")
    parser.add_argument("--export-output",
                        default=None,
                        help="export_project.py 输出 APK 路径（both 会生成 -debug/-release）")
    parser.add_argument("--project",
                        default=None,
                        help="Godot 项目根目录（包含 project.godot），默认自动推断")

    # build_android_lib.py 参数
    parser.add_argument("--variant",
                        choices=["debug", "release", "both"],
                        default="both",
                        help="game_lib 构建变体（默认 both）")
    parser.add_argument("--android-dir",
                        default=None,
                        help="Android 工程目录（包含 gradlew），默认自动从脚本位置推断")
    parser.add_argument("--module-path",
                        default=":godot_android:game_lib",
                        help="Gradle 模块路径（默认 :godot_android:game_lib）")
    parser.add_argument("--out-dir",
                        default=None,
                        help="AAR/目录/依赖库复制到该目录下的按变体子目录（android/out/<variant>/godot_game_lib 和 godot_lib）")
    parser.add_argument("--no-daemon",
                        action="store_true",
                        help="Gradle --no-daemon")

    return parser.parse_args()

def main() -> int:
    args = parse_args()
    root = script_root()

    export_py = root / "export_project.py"
    lib_py = root / "build_android_lib.py"

    # 在导出项目之前生成 .gdignore 文件防止被资源化
    try:
        project_root = Path(args.project).resolve() if args.project else find_project_root(root)
    except Exception as e:
        print_warn(f"{e}，将跳过生成 .gdignore")
        project_root = None
    if project_root is not None:
        godot_dir = project_root / "godot"
        gdignore_file = godot_dir / ".gdignore"
        if godot_dir.exists():
            try:
                gdignore_file.write_text("")
                print_info(f"已生成 .gdignore 文件: {gdignore_file}")
            except Exception as e:
                print_warn(f"生成 .gdignore 文件失败: {e}")
        else:
            print_warn(f"未找到项目根目录的 godot 目录: {godot_dir}")

    # 步骤 1：导出 APK
    if not args.skip_export:
        if not export_py.exists():
            print_err(f"未找到 export_project.py: {export_py}")
            return 2

        export_cmd: List[str] = [sys.executable, str(export_py)]
        # export_project.py 支持的参数
        export_cmd += ["--mode", args.export_mode]
        export_cmd += ["--preset", args.export_preset]
        if args.export_output:
            export_cmd += ["--output", args.export_output]
        if args.project:
            export_cmd += ["--project", args.project]

        print_info("步骤 1/2: 导出 APK（export_project.py）")
        rc = run(export_cmd, cwd=export_py.parent)
        if rc != 0:
            print_err(f"export_project.py 失败，退出码: {rc}")
            return rc
    else:
        print_warn("跳过步骤 1：export_project.py")

    # 步骤 2：打包/复制 game_lib
    if not args.skip_lib:
        if not lib_py.exists():
            print_err(f"未找到 build_android_lib.py: {lib_py}")
            return 2

        lib_cmd: List[str] = [sys.executable, str(lib_py)]
        if project_root is not None:
            lib_cmd += ["--project", str(project_root)]
        # build_android_lib.py 支持的参数
        lib_cmd += ["--variant", args.variant]
        lib_cmd += ["--module-path", args.module_path]
        if args.android_dir:
            lib_cmd += ["--android-dir", args.android_dir]
        if args.out_dir:
            lib_cmd += ["--out-dir", str(Path(args.out_dir).expanduser().resolve())]
        elif project_root is not None:
            lib_cmd += ["--out-dir", str(project_root / "android" / "out")]
        if args.no_daemon:
            lib_cmd += ["--no-daemon"]

        print_info("步骤 2/2: 打包/复制 game_lib（build_android_lib.py）")
        rc = run(lib_cmd, cwd=lib_py.parent)
        if rc != 0:
            print_err(f"build_android_lib.py 失败，退出码: {rc}")
            return rc
    else:
        print_warn("跳过步骤 2：build_android_lib.py")

    # 打印 android/out 目录
    out_dir = args.out_dir
    if not out_dir:
        # 如果没有指定 out-dir，使用默认的 android/out 目录
        if project_root is None:
            print_warn("无法推断项目根目录，且未指定 --out-dir；将跳过输出目录展示")
            out_dir = None
        else:
            out_dir = project_root / "android" / "out"
    else:
        out_dir = Path(out_dir).expanduser().resolve()

    if out_dir is not None and out_dir.exists():
        print_info(f"android/out 目录: {out_dir}")
        # 列出目录内容
        try:
            items = list(out_dir.iterdir())
            if items:
                print_info(f"目录内容:")
                for item in sorted(items):
                    if item.is_dir():
                        print_info(f"  📁 {item.name}/")
                    else:
                        print_info(f"  📄 {item.name}")
            else:
                print_info("目录为空")
        except Exception as e:
            print_warn(f"无法列出目录内容: {e}")
    elif out_dir is not None:
        print_warn(f"android/out 目录不存在: {out_dir}")
    
    print_info("全部完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())
