"""共用的路径与子进程处理逻辑，不依赖 shell 展开或当前工作目录。"""
import argparse
import shlex
import subprocess
from pathlib import Path

INTEGRATION = Path(__file__).resolve().parents[1]


def project_root(value=None):
    if value:
        root = Path(value).expanduser().resolve()
        if (root / "project.godot").is_file():
            return root
    else:
        for root in INTEGRATION.parents:
            if (root / "project.godot").is_file():
                return root
    raise ValueError("未找到 project.godot，请通过 --project 指定游戏项目")


def run(command, cwd=None, dry_run=False):
    command = [str(x) for x in command]
    print("+ " + shlex.join(command), flush=True)
    if not dry_run:
        subprocess.run(command, cwd=cwd, check=True)


def parser(description):
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--project", help="Godot 项目，默认从脚本位置定位")
    result.add_argument("--out-dir", help="默认 <项目>/ios/out")
    result.add_argument("--variant", choices=("debug", "release", "both"), default="both")
    result.add_argument("--edition", choices=("auto", "standard", "mono"), default="auto",
                        help="auto: 项目存在 csproj 时使用 mono，否则 standard")
    result.add_argument("--dry-run", action="store_true", help="打印命令，不写入产物、不执行构建")
    return result


def variants(value):
    return ("debug", "release") if value == "both" else (value,)


def output_root(args, project):
    return Path(args.out_dir).expanduser().resolve() if args.out_dir else project / "ios/out"


def edition(args, root):
    return ("mono" if any(root.glob("*.csproj")) else "standard") if args.edition == "auto" else args.edition


def main_guard(action):
    try:
        action()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"[ERROR] {exc}")
