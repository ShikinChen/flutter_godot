#!/usr/bin/env python3
"""
build_android_lib.py - Godot Android 动态库编译脚本

专注于编译 libgodot_android.so 动态库

用法: python build_android_lib.py [target] [jobs]
示例: python build_android_lib.py template_release 8
"""

import os
import sys
import subprocess
import time
import argparse
import shutil
from pathlib import Path

# 默认配置
DEFAULT_TARGET = "template_debug"
DEFAULT_JOBS = 16
DEFAULT_ARCH = "arm64"
PLATFORM = "android"

# 支持的目标
VALID_TARGETS = ["template_debug", "template_release", "editor", "dev"]

# 颜色输出类
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # 重置终端颜色
    
    @staticmethod
    def is_supported():
        """检查终端是否支持颜色"""
        return sys.stdout.isatty() and os.name != 'nt'
    
    @classmethod
    def disable_if_unsupported(cls):
        """如果不支持颜色则禁用"""
        if not cls.is_supported():
            cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.NC = ''

Colors.disable_if_unsupported()


def print_header(text):
    """打印标题"""
    print(f"\n{Colors.GREEN}{text}{Colors.NC}")


def print_error(text):
    """打印错误"""
    print(f"{Colors.RED}{text}{Colors.NC}", file=sys.stderr)


def print_warning(text):
    """打印警告"""
    print(f"{Colors.YELLOW}{text}{Colors.NC}")


def print_info(text):
    """打印信息"""
    print(f"{Colors.BLUE}{text}{Colors.NC}")


def check_environment():
    """检查编译环境"""
    print_header("[1/4] 检查编译环境...")
    
    # 检查 ANDROID_HOME
    android_home = os.environ.get('ANDROID_HOME')
    if not android_home:
        print_error("错误: ANDROID_HOME 环境变量未设置")
        print("请设置: export ANDROID_HOME=/path/to/android-sdk")
        return False
    
    if not os.path.isdir(android_home):
        print_error(f"错误: ANDROID_HOME 目录不存在: {android_home}")
        return False
    
    # 检查 SCons
    try:
        result = subprocess.run(['scons', '--version'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        scons_version = result.stdout.split('\n')[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("错误: 未找到 scons 命令")
        print("请安装 SCons: pip install scons")
        return False
    
    print(f"{Colors.GREEN}✓ 环境检查通过{Colors.NC}")
    print(f"  ANDROID_HOME: {android_home}")
    print(f"  SCons 版本: {scons_version}")
    return True


def show_config(target, jobs, arch=DEFAULT_ARCH, mono=False, debug_symbols=True):
    """显示编译配置"""
    print_header("[2/4] 编译配置:")
    print(f"  平台 (platform): {PLATFORM}")
    print(f"  架构 (arch):     {arch}")
    print(f"  目标 (target):   {target}")
    print(f"  并行数 (jobs):   {jobs}")
    print(f"  Mono 支持:       {'是 (C# 支持)' if mono else '否'}")
    print(f"  调试符号:       {'是 (LLDB 调试)' if debug_symbols else '否'}")


def find_godot_root():
    """查找 Godot 源码根目录（包含 SConstruct 文件）"""
    script_dir = Path(__file__).parent
    
    # 优先检查同级的 godot_lib 目录
    godot_lib = script_dir.parent / "godot_lib"
    if (godot_lib / "SConstruct").exists():
        return godot_lib
    
    # 如果没有找到，尝试向上查找
    current = script_dir
    for _ in range(10):
        scons_file = current / "SConstruct"
        if scons_file.exists():
            return current
        
        parent = current.parent
        if parent == current:  # 已经到达根目录
            break
        current = parent
    
    return None


def do_build(target, jobs, arch=DEFAULT_ARCH, mono=False, debug_symbols=True):
    """执行编译 libgodot_android.so"""
    if mono:
        print_header("[3/4] 开始编译 libgodot_android.so (Mono 版本)...")
    else:
        print_header("[3/4] 开始编译 libgodot_android.so...")
    
    # 查找 Godot 根目录
    godot_root = find_godot_root()
    if not godot_root:
        print_error("错误: 找不到 Godot 源码根目录（SConstruct 文件）")
        print_info("请确保脚本在 Godot 源码目录结构中")
        return False
    
    print_info(f"Godot 根目录: {godot_root}")
    if mono:
        print_info("编译模式: Mono (C# 支持)")
    if debug_symbols:
        print_info("调试符号: 启用 (用于 LLDB 调试)")
    
    start_time = time.time()
    
    # 处理 dev 构建类型
    scons_target = target
    dev_build = False
    
    if target == "dev":
        scons_target = "template_debug"
        dev_build = True
    
    # 构建 SCons 命令
    cmd = [
        'scons',
        f'platform={PLATFORM}',
        f'arch={arch}',
        f'target={scons_target}',
        f'-j{jobs}'
    ]
    
    # 添加调试符号支持
    if debug_symbols:
        cmd.append('debug_symbols=yes')
        # 分离调试符号（生成单独的 .so 文件）
        cmd.append('separate_debug_symbols=yes')
    
    # 添加 mono 支持
    if mono:
        cmd.append('module_mono_enabled=yes')
    
    # 添加 dev_build 参数
    if dev_build:
        cmd.append('dev_build=yes')
        cmd.append('dev_mode=yes')
    
    print_warning(f"执行命令: {' '.join(cmd)}")
    print()
    
    # 在 Godot 根目录执行编译
    try:
        subprocess.run(cmd, cwd=str(godot_root), check=True)
        duration = int(time.time() - start_time)
        print()
        print(f"{Colors.GREEN}✓ 编译成功! 耗时: {duration}秒{Colors.NC}")
        return True
    except subprocess.CalledProcessError:
        print()
        print_error("✗ 编译失败!")
        return False
    except KeyboardInterrupt:
        print()
        print_warning("编译被用户中断")
        return False


def copy_to_target_dir(target, arch=DEFAULT_ARCH, mono=True):
    """复制 .so 文件到目标目录 android/build/godot/lib/libs"""
    print_header("[4/5] 复制文件到目标目录...")
    
    # 查找 Godot 根目录
    godot_root = find_godot_root()
    if not godot_root:
        print_error("错误: 找不到 Godot 根目录")
        return False
    
    # 确定库类型目录
    lib_type_map = {
        "template_debug": "debug",
        "template_release": "release",
        "editor": "tools/release",
        "dev": "dev"
    }
    lib_type = lib_type_map.get(target, "release")
    
    # 架构目录映射
    arch_map = {
        "arm32": "armeabi-v7a",
        "arm64": "arm64-v8a",
        "x86_32": "x86",
        "x86_64": "x86_64"
    }
    arch_dir = arch_map.get(arch, "arm64-v8a")
    
    # 源目录（相对于 Godot 根目录）
    source_dir = godot_root / "platform" / "android" / "java" / "lib" / "libs" / lib_type / arch_dir
    
    # 目标目录路径（相对于 buildScript 的上级目录）
    script_dir = Path(__file__).parent
    target_dir = script_dir.parent / "lib" / "libs" / lib_type / arch_dir
    
    # 创建目标目录
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        print_info(f"目标目录: {target_dir}")
    except Exception as e:
        print_error(f"错误: 无法创建目标目录: {e}")
        return False
    
    # 需要复制的文件列表
    files_to_copy = [
        "libgodot_android.so",
        "libc++_shared.so"
    ]
    
    success = True
    copied_count = 0
    
    # 复制所有文件
    for filename in files_to_copy:
        source_file = source_dir / filename
        target_file = target_dir / filename
        
        if not source_file.exists():
            print_warning(f"警告: 源文件不存在: {source_file}")
            continue
        
        try:
            shutil.copy2(source_file, target_file)
            file_size = target_file.stat().st_size / (1024 * 1024)  # MB
            print(f"{Colors.GREEN}✓ 复制成功:{Colors.NC} {filename} ({file_size:.2f} MB)")
            copied_count += 1
        except Exception as e:
            print_error(f"错误: 复制 {filename} 失败: {e}")
            success = False
    
    if copied_count == 0:
        print_error("错误: 没有文件被复制")
        return False
    
    print(f"\n{Colors.GREEN}✓ 总计复制 {copied_count}/{len(files_to_copy)} 个文件{Colors.NC}")
    
    # 复制调试符号文件
    copy_debug_symbols(godot_root, source_dir, target_dir)
    
    # 如果启用 Mono，还需要复制 .NET 程序集
    if mono:
        if not copy_mono_assemblies(godot_root, target_dir):
            print_warning("警告: Mono 程序集复制失败")
    
    return success


def copy_debug_symbols(godot_root, source_dir, target_dir):
    """复制调试符号文件用于 LLDB 调试"""
    print()
    print_info("复制调试符号文件...")
    
    # 查找调试符号文件
    debug_files = []
    
    # 1. 带符号的 .so 文件（未 strip 的）
    unstripped_so = source_dir / "libgodot_android.so.debug"
    if unstripped_so.exists():
        debug_files.append((unstripped_so, "libgodot_android.so.debug"))
    
    # 2. 分离的符号文件
    symbol_file = source_dir / "libgodot_android.so.sym"
    if symbol_file.exists():
        debug_files.append((symbol_file, "libgodot_android.so.sym"))
    
    # 3. dSYM 文件（如果有）
    dsym_dir = source_dir / "libgodot_android.so.dSYM"
    if dsym_dir.exists():
        debug_files.append((dsym_dir, "libgodot_android.so.dSYM"))
    
    if not debug_files:
        print_warning("警告: 未找到调试符号文件")
        print_info("请确保编译时启用了 debug_symbols=yes")
        return False
    
    # 创建 symbols 目录
    symbols_dir = target_dir / "symbols"
    try:
        symbols_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print_error(f"错误: 无法创建 symbols 目录: {e}")
        return False
    
    copied = 0
    for source_file, filename in debug_files:
        target_file = symbols_dir / filename
        try:
            if source_file.is_dir():
                # 复制目录（dSYM）
                shutil.copytree(source_file, target_file, dirs_exist_ok=True)
                print(f"{Colors.GREEN}✓{Colors.NC} {filename} (目录)")
            else:
                # 复制文件
                shutil.copy2(source_file, target_file)
                file_size = target_file.stat().st_size / (1024 * 1024)  # MB
                print(f"{Colors.GREEN}✓{Colors.NC} {filename} ({file_size:.2f} MB)")
            copied += 1
        except Exception as e:
            print_warning(f"警告: 复制 {filename} 失败: {e}")
    
    if copied > 0:
        print(f"\n{Colors.GREEN}✓ 调试符号文件已复制到: {symbols_dir}{Colors.NC}")
        print_info("\nLLDB 调试命令:")
        print(f"  lldb")
        print(f"  (lldb) target create {target_dir / 'libgodot_android.so'}")
        print(f"  (lldb) target symbols add {symbols_dir / 'libgodot_android.so.debug'}")
        return True
    
    return False


def copy_mono_assemblies(godot_root, target_dir):
    """复制 Mono .NET 程序集文件"""
    print()
    print_info("复制 Mono .NET 程序集...")
    
    # TODO: 实现 Mono 程序集复制
    
    return True


def show_output(target, arch=DEFAULT_ARCH):
    """显示输出文件"""
    print_header("[5/5] 输出文件:")
    
    # 查找 Godot 根目录
    godot_root = find_godot_root()
    
    # 确定库类型目录
    lib_type_map = {
        "template_debug": "debug",
        "template_release": "release",
        "editor": "tools/release",
        "dev": "dev"
    }
    lib_type = lib_type_map.get(target, "release")
    
    # 架构目录映射
    arch_map = {
        "arm32": "armeabi-v7a",
        "arm64": "arm64-v8a",
        "x86_32": "x86",
        "x86_64": "x86_64"
    }
    arch_dir = arch_map.get(arch, "arm64-v8a")
    
    # 检查源输出文件（相对于 Godot 根目录）
    if godot_root:
        output_dir = godot_root / "platform" / "android" / "java" / "lib" / "libs" / lib_type / arch_dir
    else:
        output_dir = Path(f"platform/android/java/lib/libs/{lib_type}/{arch_dir}")
    output_file = output_dir / "libgodot_android.so"
    
    if output_file.exists():
        file_size = output_file.stat().st_size / (1024 * 1024)  # MB
        print(f"  {Colors.GREEN}✓{Colors.NC} {output_file} ({file_size:.2f} MB)")
    else:
        print(f"  {Colors.YELLOW}!{Colors.NC} {output_file} (未找到)")
    
    # 检查目标目录的文件（相对于 buildScript 的上级目录）
    script_dir = Path(__file__).parent
    target_dir = script_dir.parent / "lib" / "libs" / lib_type / arch_dir
    
    # 检查 libgodot_android.so
    target_godot = target_dir / "libgodot_android.so"
    if target_godot.exists():
        target_size = target_godot.stat().st_size / (1024 * 1024)  # MB
        print(f"  {Colors.GREEN}✓{Colors.NC} {target_godot} ({target_size:.2f} MB)")
    
    # 检查 libc++_shared.so
    target_cpp = target_dir / "libc++_shared.so"
    if target_cpp.exists():
        cpp_size = target_cpp.stat().st_size / (1024 * 1024)  # MB
        print(f"  {Colors.GREEN}✓{Colors.NC} {target_cpp} ({cpp_size:.2f} MB)")
    
    # 检查 bin 目录
    if godot_root:
        bin_file = godot_root / "bin" / "libgodot_android.so"
    else:
        bin_file = Path("bin/libgodot_android.so")
    
    if bin_file.exists():
        bin_size = bin_file.stat().st_size / (1024 * 1024)  # MB
        print(f"  {Colors.GREEN}✓{Colors.NC} {bin_file} ({bin_size:.2f} MB)")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Godot Android 动态库编译脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
示例:
  %(prog)s                              # 使用默认参数 (template_release, arm64, 16并行)
  %(prog)s template_debug               # 编译 debug 版本
  %(prog)s template_release 8           # 编译 release 版本，8 个并行任务
  %(prog)s dev                          # 编译 dev 版本（开发版本）
  %(prog)s editor 12                    # 编译编辑器版本，12 个并行任务
  %(prog)s -a arm32 template_debug      # 编译 arm32 架构的 debug 版本
  %(prog)s --arch x86_64 -j 4 editor    # 编译 x86_64 架构的编辑器，4 个并行任务
  
  # Mono 支持（默认启用）
  %(prog)s template_debug               # 默认编译 Mono 版本（支持 C#）
  %(prog)s --no-mono template_release   # 编译普通版本（不支持 C#）
  %(prog)s --no-mono -a arm32 dev       # 编译普通 dev 版本，arm32 架构
        """
    )
    
    parser.add_argument(
        'target',
        nargs='?',
        default=DEFAULT_TARGET,
        choices=VALID_TARGETS,
        help=f'编译目标 (默认: {DEFAULT_TARGET})'
    )
    
    parser.add_argument(
        'jobs',
        nargs='?',
        type=int,
        default=DEFAULT_JOBS,
        help=f'并行编译数 (默认: {DEFAULT_JOBS})'
    )
    
    parser.add_argument(
        '-a', '--arch',
        default=DEFAULT_ARCH,
        choices=['arm32', 'arm64', 'x86_32', 'x86_64'],
        help=f'目标架构 (默认: {DEFAULT_ARCH})'
    )
    
    parser.add_argument(
        '-j', '--parallel-jobs',
        type=int,
        dest='jobs_override',
        help='并行编译数（覆盖位置参数）'
    )
    
    parser.add_argument(
        '--no-mono',
        action='store_true',
        help='禁用 Mono 支持（默认启用 C# 支持）'
    )
    
    parser.add_argument(
        '--no-debug-symbols',
        action='store_true',
        help='禁用调试符号（默认启用，用于 LLDB 调试）'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    print()
    print("=" * 50)
    print("  Godot Android 动态库编译脚本")
    print("=" * 50)
    
    # 解析参数
    args = parse_arguments()
    
    # 如果指定了 -j 参数，使用它覆盖位置参数
    jobs = args.jobs_override if args.jobs_override else args.jobs
    
    # 验证 jobs 参数
    if jobs < 1:
        print_error(f"错误: jobs 必须大于 0: {jobs}")
        return 1
    
    # 检查环境
    if not check_environment():
        return 1
    
    # 确定是否启用 Mono（默认启用）
    mono_enabled = not args.no_mono
    
    # 确定是否启用调试符号（默认启用）
    debug_symbols = not args.no_debug_symbols
    
    # 显示配置
    show_config(args.target, jobs, args.arch, mono_enabled, debug_symbols)
    
    # 执行编译
    if do_build(args.target, jobs, args.arch, mono_enabled, debug_symbols):
        # 复制文件到目标目录
        if not copy_to_target_dir(args.target, args.arch, mono_enabled):
            print_warning("警告: 文件复制失败，但编译已完成")
        
        # 显示输出文件
        show_output(args.target, args.arch)
        print()
        print(f"{Colors.GREEN}{'=' * 50}")
        print("  编译完成!")
        print(f"{'=' * 50}{Colors.NC}")
        return 0
    else:
        print()
        print(f"{Colors.RED}{'=' * 50}")
        print("  编译失败!")
        print(f"{'=' * 50}{Colors.NC}")
        return 1


if __name__ == '__main__':
    sys.exit(main())