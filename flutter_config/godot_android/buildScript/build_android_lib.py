#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_android_lib.py - 仅使用 Gradle 打包 :godot:game_lib AAR

用法示例:
  # 同时打包 Debug 和 Release（默认）
  python build_android_lib.py

  # 仅打 Debug
  python build_android_lib.py --variant debug

  # 仅打 Release
  python build_android_lib.py --variant release

  # 指定 Android 工程目录（包含 gradlew）
  python build_android_lib.py --android-dir /path/to/android

  # 指定模块路径（如果不是 :godot_android:game_lib）
  python build_android_lib.py --module-path :godot_android:game_lib

  # 打包完成后复制 AAR 到指定输出目录的按变体子目录
  python build_android_lib.py --out-dir ./dist/android
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import shutil
import hashlib
from typing import Optional, List

# ========== 彩色输出 ==========
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

    @staticmethod
    def is_supported():
        return sys.stdout.isatty() and os.name != 'nt'

    @classmethod
    def disable_if_unsupported(cls):
        if not cls.is_supported():
            cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.NC = ''

Colors.disable_if_unsupported()

def print_header(text): print(f"\n{Colors.GREEN}{text}{Colors.NC}")
def print_error(text):  print(f"{Colors.RED}{text}{Colors.NC}", file=sys.stderr)
def print_warn(text):   print(f"{Colors.YELLOW}{text}{Colors.NC}")
def print_info(text):   print(f"{Colors.BLUE}{text}{Colors.NC}")

# ========== 参数解析 ==========
def parse_args():
    parser = argparse.ArgumentParser(
        description="仅使用 Gradle 打包 :godot:game_lib AAR",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--project",
        default=None,
        help="Godot 游戏项目根目录（包含 project.godot）；默认从 Android 工程和脚本目录向上查找",
    )
    parser.add_argument(
        "--variant",
        choices=["debug", "release", "both"],
        default="both",
        help="Gradle 构建变体",
    )
    parser.add_argument(
        "--android-dir",
        default=None,
        help="Android 工程根目录（包含 gradlew）。若不提供，将从脚本路径向上推断",
    )
    parser.add_argument(
        "--module-path",
        default=":godot_android:game_lib",
        help="Gradle 模块路径（例如 :godot_android:game_lib）",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="产物输出根目录，默认 <Godot项目>/android/out，按 debug/release 分目录",
    )
    parser.add_argument(
        "--no-daemon",
        action="store_true",
        help="禁用 Gradle daemon",
    )
    return parser.parse_args()

# ========== 工具函数 ==========
def find_project_root(android_dir: Path, provided: Optional[str] = None) -> Path:
    if provided:
        root = Path(provided).expanduser().resolve()
        if not (root / "project.godot").is_file():
            raise FileNotFoundError(f"Godot 项目目录中未找到 project.godot: {root}")
        return root
    for start in (Path(__file__).resolve().parent, android_dir.resolve()):
        for candidate in (start, *start.parents):
            if (candidate / "project.godot").is_file():
                return candidate
    raise FileNotFoundError("未找到 project.godot，请用 --project 指定 Godot 游戏项目目录")


def find_android_dir(provided: Optional[str]) -> Path:
    if provided:
        p = Path(provided).expanduser().resolve()
        return p

    # 从当前脚本开始向上查找包含 gradlew 的目录
    start = Path(__file__).resolve()
    for parent in [start.parent, *start.parents]:
        gradlew = parent / ("gradlew.bat" if os.name == "nt" else "gradlew")
        if gradlew.exists():
            return parent

    project_root = find_project_root(start.parent)
    android_build = project_root / "android" / "build"
    gradlew = android_build / ("gradlew.bat" if os.name == "nt" else "gradlew")
    if gradlew.is_file():
        return android_build
    raise FileNotFoundError(
        f"未找到 Android Gradle 构建模板: {gradlew}；请先导出 APK 安装模板，或用 --android-dir 指定工程"
    )

def configure_integration_modules(android_dir: Path) -> None:
    """将集成模块注册到 Godot 导出的标准 Gradle 工程，重复运行不重复添加。"""
    settings = android_dir / "settings.gradle"
    text = settings.read_text()
    module_root = Path(__file__).resolve().parent.parent
    if "include ':godot:lib', ':godot_android:game_lib'" in text:
        return
    if "id 'com.android.library' version" not in text:
        application = "id 'com.android.application' version versions.androidGradlePlugin"
        if application not in text:
            raise ValueError(f"无法识别 Android 插件配置: {settings}")
        text = text.replace(application, application + "\n        id 'com.android.library' version versions.androidGradlePlugin", 1)
    def relative(directory):
        return os.path.relpath(directory, android_dir).replace(os.sep, '/').replace("'", "\\'")
    text += (
        "\n// Flutter Godot integration modules.\n"
        "include ':godot:lib', ':godot_android:game_lib'\n"
        f"project(':godot').projectDir = file('{relative(module_root)}')\n"
        f"project(':godot_android').projectDir = file('{relative(module_root)}')\n"
        f"project(':godot:lib').projectDir = file('{relative(module_root / 'lib')}')\n"
        f"project(':godot_android:game_lib').projectDir = file('{relative(module_root / 'game_lib')}')\n"
    )
    settings.write_text(text)
    print_info(f"已注册 Godot 引擎及游戏库 Gradle 模块: {settings}")


def run_gradle(android_dir: Path, task: str, no_daemon: bool) -> int:
    gradlew = "gradlew.bat" if os.name == "nt" else "./gradlew"
    gradlew_path = android_dir / gradlew
    if not gradlew_path.exists():
        print_error(f"未找到 gradlew: {gradlew_path}")
        return 2

    cmd = [str(gradlew_path), task]
    if no_daemon:
        cmd.append("--no-daemon")

    print_warn(f"执行命令: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=str(android_dir), check=True)
        return 0
    except subprocess.CalledProcessError as e:
        return e.returncode

def aar_output_paths(android_dir: Path, module_path: str, variant: str) -> List[Path]:
    # 典型输出: <android_dir>/<module>/build/outputs/aar/<module>-<variant>.aar
    module_name = module_path.split(":")[-1] or "game_lib"
    candidates: List[Path] = []
    integration_root = Path(__file__).resolve().parent.parent
    for edition in ('mono', 'standard'):
        candidates.append(integration_root / 'game_lib' / 'build' / 'outputs' / 'aar' / f'game_lib-{edition}-{variant}.aar')

    # 常见路径 1：godot/<module_name>
    candidates.append(android_dir / "godot_android" / module_name / "build" / "outputs" / "aar" / f"{module_name}-{variant}.aar")
    # 常见路径 2：godot/game_lib
    if module_name != "game_lib":
        candidates.append(android_dir / "godot_android" / "game_lib" / "build" / "outputs" / "aar" / f"game_lib-{variant}.aar")
    # 兼容 standard 变体命名（Godot 常见导出名）：game_lib-standard-<variant>.aar
    candidates.append(android_dir / "godot_android" / "game_lib" / "build" / "outputs" / "aar" / f"game_lib-standard-{variant}.aar")
    # 常见路径 3：直接模块目录（若不在 godot/ 子目录）
    candidates.append(android_dir / module_name / "build" / "outputs" / "aar" / f"{module_name}-{variant}.aar")

    return candidates

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def copy_if_needed(src: Path, out_dir: Path) -> Optional[Path]:
    try:
        ensure_dir(out_dir)
        dst = out_dir / src.name
        shutil.copy2(src, dst)
        return dst
    except Exception as e:
        print_warn(f"复制到 {out_dir} 失败: {e}")
        return None

def copy_dir_variant(src_dir: Path, out_root: Path, variant: str) -> Optional[Path]:
    """将目录按变体复制到 android/out/<variant>/ 下，返回目标路径。"""
    try:
        dest_dir = out_root / variant / src_dir.name
        shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
        return dest_dir
    except Exception as e:
        print_warn(f"复制目录失败: {src_dir} -> {out_root} ({e})")
        return None

def copy_dir_contents(src_dir: Path, dst_dir: Path) -> Optional[Path]:
    """将 src_dir 下的所有内容合并复制到 dst_dir（保留目录结构，存在则覆盖）。"""
    try:
        ensure_dir(dst_dir)
        for root, dirs, files in os.walk(src_dir):
            rel = Path(root).relative_to(src_dir)
            target_root = dst_dir / rel
            ensure_dir(target_root)
            for d in dirs:
                ensure_dir(target_root / d)
            for f in files:
                src_file = Path(root) / f
                dst_file = target_root / f
                shutil.copy2(src_file, dst_file)
        return dst_dir
    except Exception as e:
        print_warn(f"复制目录内容失败: {src_dir} -> {dst_dir} ({e})")
        return None

def get_file_hash(file_path: Path) -> str:
    """计算文件的 MD5 哈希值。"""
    if not file_path.exists():
        return ""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print_warn(f"计算文件哈希失败: {file_path} ({e})")
        return ""

def check_and_clear_if_needed(project_root: Path, out_root: Path) -> bool:
    """检查 godot.gdkey 是否变化，如需要则清除 bin 目录。"""
    godot_key_file = project_root / "godot.gdkey"
    recorded_key_file = out_root / "godot.gdkey.recorded"
    
    if not godot_key_file.exists():
        return True
    
    current_key = get_file_hash(godot_key_file)
    recorded_key = ""
    
    if recorded_key_file.exists():
        try:
            recorded_key = recorded_key_file.read_text().strip()
        except Exception as e:
            print_warn(f"读取记录的 godot.gdkey 失败: {e}")
    
    if current_key == recorded_key:
        print_info("godot.gdkey 未变化，跳过清除 bin 目录")
        return True
    
    print_info(f"godot.gdkey 已变化，清除 godot bin 目录")
    
    # 清除 godot bin 目录
    godot_bin_dir = project_root / "godot" / "bin"
    if godot_bin_dir.exists():
        try:
            shutil.rmtree(godot_bin_dir)
            print_info(f"已清除 godot bin 目录: {godot_bin_dir}")
        except Exception as e:
            print_warn(f"清除 godot bin 目录失败: {e}")
            return False
    
    return True

def record_godot_key(project_root: Path, out_root: Path) -> None:
    """记录当前的 godot.gdkey 哈希值。"""
    godot_key_file = project_root / "godot.gdkey"
    recorded_key_file = out_root / "godot.gdkey.recorded"
    
    if godot_key_file.exists():
        current_key = get_file_hash(godot_key_file)
        try:
            ensure_dir(out_root)
            recorded_key_file.write_text(current_key)
            print_info(f"已记录新的 godot.gdkey: {recorded_key_file}")
        except Exception as e:
            print_warn(f"记录 godot.gdkey 失败: {e}")

def check_swappy_libraries(project_root: Path) -> bool:
    """检查 swappy-frame-pacing 架构库是否存在，缺少时提示下载。"""
    swappy_dir = project_root / "godot" / "thirdparty" / "swappy-frame-pacing"
    if not swappy_dir.exists():
        print_warn(f"未找到 swappy-frame-pacing 目录: {swappy_dir}")
        print_error(f"请从 https://github.com/godotengine/godot-swappy/releases 下载并解压到: {swappy_dir}")
        return False
    
    # 检查常见的 Android 架构库
    arch_libs = [
        "arm64-v8a",
        "armeabi-v7a", 
        "x86_64",
        "x86"
    ]
    
    missing_archs = []
    found_archs = []
    
    for arch in arch_libs:
        arch_dir = swappy_dir / arch
        if arch_dir.exists() and any(arch_dir.iterdir()):
            found_archs.append(arch)
        else:
            missing_archs.append(arch)
    
    if found_archs:
        print_info(f"找到 swappy-frame-pacing 架构库: {', '.join(found_archs)}")
    
    if missing_archs:
        print_warn(f"缺少 swappy-frame-pacing 架构库: {', '.join(missing_archs)}")
        print_error(f"请从 https://github.com/godotengine/godot-swappy/releases 下载并解压到: {swappy_dir}")
        return False
    
    return True

# ========== 主流程 ==========
def main() -> int:
    print_header("Gradle 打包 :godot:game_lib AAR")
    args = parse_args()

    try:
        android_dir = find_android_dir(args.android_dir)
    except FileNotFoundError as exc:
        print_error(str(exc))
        return 2
    print_info(f"Android 工程目录: {android_dir}")

    # 检查 godot.gdkey 并在需要时清除 bin 目录
    try:
        project_root = find_project_root(android_dir, args.project)
    except FileNotFoundError as exc:
        print_error(str(exc))
        return 1
    print_info(f"Godot 项目目录: {project_root}")
    out_root = Path(args.out_dir).expanduser().resolve() if args.out_dir else project_root / "android" / "out"
    print_info(f"产物输出目录: {out_root}")
    if not check_and_clear_if_needed(project_root, out_root):
        print_error("清除 bin 目录失败，退出")
        return 1
    
    # 检查 swappy-frame-pacing 架构库
    if not check_swappy_libraries(project_root):
        print_error("swappy-frame-pacing 库检查失败，请下载所需架构库后重试")
        return 1

    try:
        configure_integration_modules(android_dir)
    except (OSError, ValueError) as exc:
        print_error(str(exc))
        return 2

    tasks: List[str]
    if args.variant == "debug":
        tasks = [":godot:lib:assembleTemplateDebug", f"{args.module_path}:assembleDebug"]
    elif args.variant == "release":
        tasks = [":godot:lib:assembleTemplateRelease", f"{args.module_path}:assembleRelease"]
    else:
        tasks = [":godot:lib:assembleTemplateDebug", ":godot:lib:assembleTemplateRelease", f"{args.module_path}:assembleDebug", f"{args.module_path}:assembleRelease"]

    for t in tasks:
        rc = run_gradle(android_dir, t, no_daemon=args.no_daemon)
        if rc != 0:
            print_error(f"✗ 任务失败: {t}")
            return rc

        variant = "debug" if t.endswith("Debug") else "release"
        
        # 如果是模板编译任务完成，记录新的 godot.gdkey
        if "assembleTemplate" in t:
            record_godot_key(project_root, out_root)

        # 1) 定位 AAR 并仅复制到 android/out/<variant>/godot_game_lib（不再复制到 out 根目录）
        found = False
        for cand in aar_output_paths(android_dir, args.module_path, variant):
            if cand.exists():
                print_info(f"AAR 输出({variant}): {cand}")
                variant_lib_dir = out_root / variant / "godot_game_lib"
                dst2 = copy_if_needed(cand, variant_lib_dir)
                if dst2:
                    print_info(f"已复制到: {dst2}")
                found = True
                break
        if not found and "assembleTemplate" not in t:
            print_error(f"未找到 AAR 文件（{variant}），请检查模块路径与构建输出目录。")
            return 1

        # 2) 复制目录 buildScript/godot/godot_game_lib -> android/out/<variant>/godot_game_lib
        script_base = Path(__file__).resolve().parent
        src_game_lib_dir = script_base / "godot" / "godot_game_lib"
        if src_game_lib_dir.exists():
            copied_path = copy_dir_variant(src_game_lib_dir, out_root, variant)
            if copied_path:
                print_info(f"已复制目录({variant}): {copied_path}")
        else:
            print_warn(f"未找到目录: {src_game_lib_dir}")

        # 3) 复制依赖库 android/build/godot/game_lib/libs/<variant> -> android/out/<variant>/godot_lib
        # 处理 android_dir 可能已是 .../android/build 的情况，避免出现 build/build
        build_root = android_dir if android_dir.name == "build" else (android_dir / "build")
        src_libs_variant = android_dir / "libs" / variant
        dst_libs_dir = out_root / variant / "godot_lib"
        if src_libs_variant.exists():
            merged = copy_dir_contents(src_libs_variant, dst_libs_dir)
            if merged:
                print_info(f"已复制依赖库({variant}): {merged}")
        else:
            print_warn(f"未找到依赖库目录: {src_libs_variant}")

        # 4) 复制 :godot:lib 模块的 AAR 文件 android/build/godot/lib/build/outputs/aar -> android/out/<variant>/godot_lib
        src_lib_aar_dir = script_base.parent / "lib" / "build" / "outputs" / "aar"
        dst_lib_aar_dir = out_root / variant / "godot_lib"
        if src_lib_aar_dir.exists():
            for aar_file in src_lib_aar_dir.glob("*.aar"):
                # 根据变体过滤 AAR 文件
                if variant == "debug" and "template_debug" in aar_file.name:
                    dst_aar = copy_if_needed(aar_file, dst_lib_aar_dir)
                    if dst_aar:
                        print_info(f"已复制 lib AAR({variant}): {dst_aar}")
                elif variant == "release" and "template_release" in aar_file.name:
                    dst_aar = copy_if_needed(aar_file, dst_lib_aar_dir)
                    if dst_aar:
                        print_info(f"已复制 lib AAR({variant}): {dst_aar}")
        else:
            print_warn(f"未找到 lib AAR 目录: {src_lib_aar_dir}")

    print_header("打包完成!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
