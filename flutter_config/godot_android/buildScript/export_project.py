#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from pathlib import Path
import shutil
import re


# 自动发现 Godot/Godot_mono 可执行文件（mac 优先）
def discover_godot_binary() -> Path:
    """
    尝试在以下位置自动查找 Godot 可执行文件：
    1) PATH 中的命令：godot, godot4, Godot, Godot_mono
    2) 常见安装目录的 .app 包：
       - /Applications/Godot*.app
       - ~/Applications/Godot*.app
    3) 常见目录下的可执行文件名：
       - Godot, Godot_mono, godot, godot_mono
    找到即返回 Path；找不到则抛出 FileNotFoundError。
    """
    import shutil as _shutil

    # 1) PATH 中寻找常见命令名
    cmd_names = ["godot4", "godot", "Godot", "Godot_mono", "godot_mono"]
    for name in cmd_names:
        found = _shutil.which(name)
        if found:
            p = Path(found).resolve()
            if p.exists():
                return p

    # 2) 常见 .app 安装目录
    app_roots = [
        Path("/Applications"),
        Path.home() / "Applications",
    ]
    app_names = [
        "Godot.app",
        "Godot_mono.app",
        "Godot4.app",
        "Godot4_mono.app",
    ]
    mac_inner = ["Contents/MacOS/Godot", "Contents/MacOS/Godot_mono"]

    for root in app_roots:
        for app in app_names:
            app_path = root / app
            for inner in mac_inner:
                cand = app_path / inner
                if cand.exists() and cand.is_file():
                    return cand

    # 3) 常见目录可执行名组合
    common_dirs = [
        Path("/usr/local/bin"),
        Path("/opt/homebrew/bin"),
        Path("/usr/bin"),
        Path("/opt/local/bin"),
        Path.home() / "bin",
    ]
    bin_names = ["Godot", "Godot_mono", "godot", "godot_mono", "godot4"]
    for d in common_dirs:
        for n in bin_names:
            cand = d / n
            if cand.exists() and cand.is_file():
                return cand.resolve()

    raise FileNotFoundError("未设置 GODOT_HOME/GODOT_BIN，且自动搜索未找到 Godot 可执行文件。\n请设置环境变量 GODOT_BIN 指向 Godot 可执行文件路径，例如：\n  export GODOT_BIN=/Applications/Godot_mono.app\n  或\n  export GODOT_BIN=/Applications/Godot_mono.app/Contents/MacOS/Godot_mono")


def resolve_godot_binary(godot_home: str) -> Path:
    """
    根据 GODOT_HOME 定位 Godot 可执行文件。
    兼容 Godot 与 Godot_mono（含 .app 包、目录与直接文件）多种布局：
    - /Applications/Godot.app
    - /Applications/Godot_mono.app
    - /path/to/dir/Godot 或 Godot_mono
    - 直接指向可执行文件
    """
    p = Path(godot_home).expanduser().resolve()
    # 直接给的是可执行文件
    if p.is_file():
        return p

    candidates: list[Path] = []

    # 如果传入的是 .app 包
    if p.suffix == ".app":
        candidates = [
            p / "Contents" / "MacOS" / "Godot",
            p / "Contents" / "MacOS" / "Godot_mono",
        ]
    else:
        # 传入的是目录：尝试常见可执行名
        candidates = [
            p / "Godot",
            p / "Godot_mono",
            p / "godot",
            p / "godot_mono",
        ]
        # 也可能目录里包含 .app
        for app_name in ("Godot.app", "Godot_mono.app"):
            candidates = [
                p / app_name / "Contents" / "MacOS" / "Godot",
                p / app_name / "Contents" / "MacOS" / "Godot_mono",
            ]

    for c in candidates:
        if c.exists() and c.is_file():
            return c

    raise FileNotFoundError(f"无法通过 GODOT_HOME 定位 Godot 可执行文件: {godot_home}")


def project_root_from_here() -> Path:
    """从脚本目录向上查找包含 project.godot 的游戏项目。"""
    start = Path(__file__).resolve().parent
    for candidate in (start, *start.parents):
        if (candidate / "project.godot").is_file():
            return candidate
    raise FileNotFoundError("未找到 project.godot，请用 --project 指定 Godot 游戏项目目录")


def read_script_encryption_key(project_root: Path) -> str:
    """
    读取项目的 godot.gdkey 文件获取脚本加密密钥。
    如果文件不存在，返回空字符串。
    """
    gdkey_path = project_root / "godot.gdkey"
    if not gdkey_path.exists():
        return ""
    
    try:
        with open(gdkey_path, 'r', encoding='utf-8') as f:
            key = f.read().strip()
        return key
    except Exception as e:
        print(f"警告: 读取 godot.gdkey 文件失败: {e}", file=sys.stderr)
        return ""


def update_script_encryption_key(project_root: Path) -> bool:
    """
    更新 .godot/export_credentials.cfg 中的 script_encryption_key。
    根据 godot.gdkey 文件内容设置密钥，如果文件不存在则设置为空字符串。
    返回是否成功更新。
    """
    # 获取加密密钥
    encryption_key = read_script_encryption_key(project_root)
    
    # 目标配置文件路径
    export_credentials_path = project_root / ".godot" / "export_credentials.cfg"
    
    if not export_credentials_path.exists():
        print(f"警告: export_credentials.cfg 文件不存在: {export_credentials_path}", file=sys.stderr)
        return False
    
    try:
        # 读取原文件内容
        with open(export_credentials_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式替换所有 script_encryption_key 的值
        # 匹配 script_encryption_key="..." 的模式
        pattern = r'(script_encryption_key=)"[^"]*"'
        replacement = f'\\1"{encryption_key}"'
        updated_content = re.sub(pattern, replacement, content)
        
        # 检查是否有变更
        if updated_content == content:
            print("script_encryption_key 已经是正确值，无需更新")
            return True
        
        # 写回文件
        with open(export_credentials_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"已更新 script_encryption_key: {encryption_key if encryption_key else '(空字符串)'}")
        return True
        
    except Exception as e:
        print(f"错误: 更新 export_credentials.cfg 失败: {e}", file=sys.stderr)
        return False


def run(cmd: list[str], env: dict[str, str]) -> int:
    """
    以实时输出的方式运行子进程命令，返回退出码。
    """
    print("执行命令:", " ".join(cmd))
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.stdout is not None
    export_failed = False
    errors = []
    for line in proc.stdout:
        sys.stdout.write(line)
        if line.lstrip().startswith('ERROR:'):
            errors.append(line.strip())
        if 'ERROR: Cannot export project' in line or ('ERROR: Project export for preset' in line and 'failed' in line):
            export_failed = True
    proc.wait()
    rc = proc.returncode or (1 if export_failed else 0)
    if rc:
        relevant = [error for error in errors if not any(noise in error for noise in (
            'host fxr folder', 'EditorSettings not instantiated', 'Project export for preset',
        ))]
        for error in dict.fromkeys(relevant):
            print(f"[ERROR] 导出原因: {error.removeprefix('ERROR:').strip()}", file=sys.stderr)
        if any('Could not find release keystore' in error for error in errors):
            print("[ERROR] Android 导出预设未配置有效的 Release 签名证书。请在 Godot 的 Android 导出设置中配置 Keystore/Release、别名和密码。", file=sys.stderr)
            print("[INFO] 开发构建可运行: ./run_android_build.py --export-mode apk-debug（仍会生成 Debug/Release AAR）", file=sys.stderr)
    return rc


def main(argv: list[str]) -> int:
    """
    主入口。支持三种模式：
    - apk-debug: 导出 Debug APK
    - apk-release: 导出 Release APK
    - both: 依次导出 Debug 与 Release
    """
    import argparse

    parser = argparse.ArgumentParser(description="导出 Godot 项目到 Android APK。")
    parser.add_argument("--preset", default="Android", help="export_presets.cfg 中的导出预设名")
    parser.add_argument("--mode", choices=["both", "apk-debug", "apk-release"], default="both",
                        help="导出模式")
    parser.add_argument("--output", default=None, help="输出路径（APK）。默认：android/android.apk")
    parser.add_argument("--project", default=None, help="自定义项目根目录（默认从脚本目录向上查找 project.godot）")
    args = parser.parse_args(argv)

    # 解析 Godot 可执行文件
    # 优先：GODOT_HOME 指定 .app 或目录/文件
    godot_home = os.environ.get("GODOT_HOME")
    if godot_home:
        try:
            godot_bin = resolve_godot_binary(godot_home)
        except Exception as e:
            print(str(e), file=sys.stderr)
            return 2
    else:
        # 其次：GODOT_BIN 指定完整路径
        godot_bin_env = os.environ.get("GODOT_BIN")
        if godot_bin_env:
            godot_bin = Path(godot_bin_env).expanduser().resolve()
            if not godot_bin.exists():
                print(f"GODOT_BIN 指向的文件不存在: {godot_bin}", file=sys.stderr)
                return 2
        else:
            # 最后：自动发现 Godot 可执行文件
            try:
                godot_bin = discover_godot_binary()
            except Exception as e:
                print(str(e), file=sys.stderr)
                return 2

    # 解析项目根目录并校验
    try:
        project_root = Path(args.project).expanduser().resolve() if args.project else project_root_from_here()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not (project_root / "project.godot").exists():
        print(f"未找到 project.godot，项目根目录无效: {project_root}", file=sys.stderr)
        return 2

    # 集成配置及其构建产物不属于游戏资源，避免被扫描和打入 APK。
    integration_dir = Path(__file__).resolve().parents[2]
    if integration_dir != project_root and project_root in integration_dir.parents:
        (integration_dir / ".gdignore").touch(exist_ok=True)

    # 更新 script_encryption_key
    print("正在更新 script_encryption_key...")
    if not update_script_encryption_key(project_root):
        print("警告: script_encryption_key 更新失败，但继续执行导出", file=sys.stderr)

    # 解析输出路径
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        output_path = project_root / "android" / "android.apk"

    # 确保输出目录存在（若是文件，确保其父目录存在）
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 构建基础参数：headless editor，避免加载插件/工具脚本导致卡住
    base = [
        str(godot_bin),
        "-v",
        "--headless",
        "--editor",
        "--no-header",
        "--path", str(project_root),
    ]

    # Godot 官方 CLI 支持在导出时安装缺失的 Android 构建模板。
    if not (project_root / "android" / "build" / "gradlew").is_file():
        base.append("--install-android-build-template")

    env = os.environ.copy()

    def export_apk(command, destination):
        rc = run(command, env)
        if rc != 0:
            print(f"APK 导出失败: {destination}", file=sys.stderr)
            return rc
        if not destination.is_file() or destination.stat().st_size == 0:
            print(f"APK 导出未生成有效文件: {destination}", file=sys.stderr)
            return 1
        print(f"APK 输出: {destination}")
        return 0

    if args.mode == "apk-debug":
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = base + ["--export-debug", args.preset, str(output_path)]
        return export_apk(cmd, output_path)

    elif args.mode == "apk-release":
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = base + ["--export-release", args.preset, str(output_path)]
        return export_apk(cmd, output_path)

    else:
        # both: 依次导出 debug 与 release，避免覆盖输出
        output_path.parent.mkdir(parents=True, exist_ok=True)
        base_out = output_path
        debug_out = base_out.with_name(f"{base_out.stem}-debug{base_out.suffix}")
        release_out = base_out.with_name(f"{base_out.stem}-release{base_out.suffix}")

        # 1) 导出 debug
        cmd_debug = base + ["--export-debug", args.preset, str(debug_out)]
        rc_debug = export_apk(cmd_debug, debug_out)
        if rc_debug != 0:
            return rc_debug

        # 2) 在执行 release 之前，暂存 android/build/libs/debug 以避免被清理/覆盖
        android_build_dir = project_root / "android" / "build"
        libs_debug_dir = android_build_dir / "libs" / "debug"
        backup_dir = android_build_dir / "libs" / "debug__backup_before_release"

        backup_done = False
        try:
            if libs_debug_dir.exists():
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.move(str(libs_debug_dir), str(backup_dir))
                backup_done = True
        except Exception as e:
            print(f"警告: 备份 debug 依赖目录失败: {e}")

        # 3) 导出 release（使用 try/finally 确保还原）
        try:
            cmd_release = base + ["--export-release", args.preset, str(release_out)]
            rc_release = export_apk(cmd_release, release_out)
        finally:
            # 4) 还原先前备份的 debug 依赖目录
            try:
                if backup_done and backup_dir.exists():
                    # 若 release 构建过程中创建了新的 debug 目录，先移除再还原
                    if libs_debug_dir.exists():
                        shutil.rmtree(libs_debug_dir)
                    shutil.move(str(backup_dir), str(libs_debug_dir))
            except Exception as e:
                print(f"警告: 还原 debug 依赖目录失败: {e}")

        return rc_release


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))