#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""克隆 Godot 源码，并初始化 Godot 项目根目录下的 .csproj 编译排除目录。"""

import argparse
from pathlib import Path
import re
import sys
import subprocess
import xml.etree.ElementTree as ET


DEFAULT_BRANCH = "4.7.2-stable"
GODOT_REPOSITORY = "https://github.com/godotengine/godot"


EXCLUDED_DIRECTORIES = ("android/**", "flutter/**", "godot/**")


def find_project_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "project.godot").is_file():
            return candidate
    raise FileNotFoundError("未找到 project.godot，请用 --project 指定项目目录或 .csproj 文件")


def update_csproj(path: Path) -> bool:
    # 保留原有 XML 排版、注释、BOM 和换行符，只在 Project 末尾补充配置。
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    root = ET.fromstring(text)
    namespace = root.tag.removesuffix("Project")
    if root.tag != "Project" and not root.tag.endswith("}Project"):
        raise ValueError(f"不是有效的 MSBuild Project: {path}")
    existing = set()
    for group in root.findall(f"{namespace}ItemGroup"):
        if group.get("Condition"):
            continue
        for compile_item in group.findall(f"{namespace}Compile"):
            if not compile_item.get("Condition"):
                existing.update(
                    item.strip().replace("\\", "/")
                    for item in compile_item.get("Remove", "").split(";")
                )
    missing = [directory for directory in EXCLUDED_DIRECTORIES if directory not in existing]
    if not missing:
        return False
    closing = re.search(r"</(?P<prefix>[\w.-]+:)?Project\s*>\s*$", text)
    if closing is None:
        raise ValueError(f"未找到 Project 结束标签: {path}")
    prefix = closing.group("prefix") or ""
    newline = "\r\n" if "\r\n" in text else "\n"
    indent_match = re.search(r"\n([ \t]+)<", text)
    indent = indent_match.group(1) if indent_match else "  "
    lines = [f"{indent}<{prefix}ItemGroup>", f"{indent * 2}<!-- 排除不需要编译的目录 -->"]
    lines.extend(f'{indent * 2}<{prefix}Compile Remove="{directory}" />' for directory in missing)
    lines.append(f"{indent}</{prefix}ItemGroup>")
    before = text[:closing.start()]
    if not before.endswith(("\n", "\r")):
        before += newline
    updated = before + newline.join(lines) + newline + text[closing.start():]
    ET.fromstring(updated)
    encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    path.write_bytes(updated.encode(encoding))
    return True


PROJECT_IGNORE_PATTERNS = (
    ".godot/", "/godot/", "/android/", "bin/", "obj/",
    "/godot.gdkey", "*.keystore", "*.jks", ".DS_Store",
)
CONFIG_IGNORE_PATTERNS = (
    "build/", ".gradle/", ".cxx/", ".externalNativeBuild/",
    "local.properties", "__pycache__/", "*.py[cod]", ".idea/", "*.iml", ".DS_Store",
    "/godot_android/lib/libs/", "*.aar", "*.so", "*.a", "*.dex",
)


def update_gitignore(path: Path, patterns: tuple[str, ...]) -> bool:
    """保留已有规则，仅追加缺少的忽略项。"""
    raw = path.read_bytes() if path.exists() else b""
    text = raw.decode("utf-8-sig")
    existing = {line.strip() for line in text.splitlines()}
    missing = [pattern for pattern in patterns if pattern not in existing]
    if not missing:
        return False
    newline = "\r\n" if "\r\n" in text else "\n"
    if text and not text.endswith(("\n", "\r")):
        text += newline
    if text:
        text += newline
    text += "# Flutter Godot generated files and local configuration" + newline
    text += newline.join(missing) + newline
    encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    path.write_bytes(text.encode(encoding))
    return True


def clone_godot(project_root: Path, branch: str) -> None:
    destination = project_root / "godot"
    if destination.exists():
        if not destination.is_dir() or not (destination / "SConstruct").is_file():
            raise ValueError(f"目标路径已存在，但不是 Godot 源码目录: {destination}")
        print(f"[INFO] Godot 源码已存在，跳过克隆（不切换版本）: {destination}")
        return
    print(f"[INFO] 正在克隆 Godot {branch}: {destination}", flush=True)
    subprocess.run(
        ["git", "clone", "--branch", branch, "--", GODOT_REPOSITORY, str(destination)],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, help="Godot 项目目录或 .csproj 文件；默认从脚本所在的 flutter_config 目录向上查找")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help=f"Godot 源码分支或标签，默认 {DEFAULT_BRANCH}；已有源码时跳过克隆")
    args = parser.parse_args()
    if not args.branch.strip():
        parser.error("--branch 不能为空")
    try:
        if args.project:
            project = args.project.expanduser().resolve()
        else:
            project = find_project_root(Path(__file__).resolve().parent.parent)
        if project.is_file() and project.suffix == ".csproj":
            projects = [project]
        elif project.is_dir():
            projects = sorted(project.glob("*.csproj"))
        else:
            raise FileNotFoundError(f"项目路径不存在或不是 .csproj: {project}")
        if not projects:
            raise FileNotFoundError(f"目录中没有 .csproj 文件: {project}")
        update_gitignore(projects[0].parent / ".gitignore", PROJECT_IGNORE_PATTERNS)
        update_gitignore(Path(__file__).resolve().parent / ".gitignore", CONFIG_IGNORE_PATTERNS)
        clone_godot(projects[0].parent, args.branch)
        for path in projects:
            changed = update_csproj(path)
            print(f"[INFO] {'已更新' if changed else '配置已存在'}: {path}")
        return 0
    except (OSError, ValueError, ET.ParseError, subprocess.CalledProcessError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
