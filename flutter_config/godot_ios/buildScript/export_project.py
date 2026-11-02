#!/usr/bin/env python3
"""导出包含 iOS 平台特性的 PCK，无需配置签名团队或导出 IPA。"""
import shutil
import plistlib
from pathlib import Path
from common import INTEGRATION, edition, main_guard, output_root, parser, project_root, run, variants


def package_aot(root, package, variant):
    """将 .NET 导出的 dylib 切片转换为可嵌入的 iOS 框架。"""
    config = "ExportDebug" if variant == "debug" else "ExportRelease"
    candidates = list((root / ".godot/mono/temp/bin" / config).glob("*_aot.xcframework"))
    if len(candidates) != 1:
        raise ValueError(f"需要唯一的 C# AOT XCFramework，实际找到 {len(candidates)} 个: {config}")
    source = candidates[0]
    metadata = plistlib.loads((source / "Info.plist").read_bytes())
    frameworks = package / "Frameworks"
    frameworks.mkdir(parents=True, exist_ok=True)
    name = source.name.removesuffix("_aot.xcframework")
    command = ["xcodebuild", "-create-xcframework"]
    work = package / "aot-staging"
    if work.exists():
        shutil.rmtree(work)
    for item in metadata["AvailableLibraries"]:
        framework = work / item["LibraryIdentifier"] / f"{name}.framework"
        framework.mkdir(parents=True)
        binary = source / item["LibraryIdentifier"] / item["LibraryPath"]
        if binary.suffix == ".framework":
            shutil.copytree(binary, framework, dirs_exist_ok=True)
        else:
            shutil.copy2(binary, framework / name)
            run(["xcrun", "install_name_tool", "-id", f"@rpath/{name}.framework/{name}", framework / name])
            info = {"CFBundleExecutable": name, "CFBundleIdentifier": f"org.godot.aot.{name.replace('_', '-')}",
                    "CFBundleName": name, "CFBundlePackageType": "FMWK", "CFBundleVersion": "1",
                    "CFBundleShortVersionString": "1.0", "MinimumOSVersion": "15.0",
                    "CFBundleSupportedPlatforms": ["iPhoneSimulator" if item.get("SupportedPlatformVariant") == "simulator" else "iPhoneOS"]}
            (framework / "Info.plist").write_bytes(plistlib.dumps(info))
        command.extend(["-framework", framework])
    dest = frameworks / f"{name}.xcframework"
    if dest.exists():
        shutil.rmtree(dest)
    run([*command, "-output", dest])
    shutil.rmtree(work)
    # .NET 在应用包中查找 ICU 数据，而不是在 PCK 内部查找。
    data = root / ".godot/mono/temp/bin/godot-publish-dotnet" / f"{config}-ios-arm64"
    dat_files = list(data.glob("*.dat"))
    for path in dat_files:
        destination = package / "BundleFiles" / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def main():
    cli = parser("导出 iOS 游戏 PCK 并准备 GodotGame 本地 Pod")
    cli.add_argument("--godot", default="/Applications/Godot_mono.app/Contents/MacOS/Godot")
    cli.add_argument("--preset", default="iOS", help="export_presets.cfg 中的 iOS 预设名")
    args = cli.parse_args()
    root = project_root(args.project)
    # 此集成明确构建标准版引擎；若仍悄悄导出 C# 脚本，
    # 会导致应用虽然能运行，游戏逻辑却无法执行。
    scripts = [p for p in root.rglob("*.cs")
               if not set(p.relative_to(root).parts).intersection({"godot", "android", "ios", "flutter_config", ".godot", "bin", "obj"})]
    referenced = []
    for pattern in ("*.tscn", "*.tres", "project.godot"):
        for resource in root.rglob(pattern):
            if set(resource.relative_to(root).parts).intersection({"godot", "android", "ios", "flutter_config", ".godot", "bin", "obj"}):
                continue
            content = resource.read_text(encoding="utf-8")
            referenced.extend(p for p in scripts if "res://" + p.relative_to(root).as_posix() in content)
    if referenced and edition(args, root) == "standard":
        raise ValueError("当前标准引擎不支持 C#，发现资源引用: " + ", ".join(str(p) for p in set(referenced)))
    out = output_root(args, root)
    if not args.dry_run:
        out.mkdir(parents=True, exist_ok=True)
        (out / ".gdignore").touch()
    for variant in variants(args.variant):
        package = out / variant / "godot_game_lib"
        resources = package / "Resources"
        if not args.dry_run:
            resources.mkdir(parents=True, exist_ok=True)
            # 导出失败时，不得将上一次成功生成的 PCK 误认为本次产物。
            (resources / "game.pck").unlink(missing_ok=True)
        command = [args.godot, "--headless", "--path", root]
        # Main::start 支持组合这些参数：debug 选择脚本调试数据，
        # pack 选择仅导出资源包，不生成签名应用。
        if variant == "debug":
            command += ["--export-debug", args.preset]
        command += ["--export-pack", args.preset, resources / "game.pck"]
        run(command, dry_run=args.dry_run)
        if not args.dry_run:
            if not (resources / "game.pck").is_file():
                raise ValueError("Godot 未生成 game.pck")
            shutil.copytree(INTEGRATION / "game_lib/Sources", package / "Sources", dirs_exist_ok=True)
            shutil.copy2(INTEGRATION / "game_lib/GodotGame.podspec", package / "GodotGame.podspec")
            if edition(args, root) == "mono":
                package_aot(root, package, variant)
                spec = package / "GodotGame.podspec"
                extra = "  s.vendored_frameworks = 'Frameworks/*.xcframework'\n"
                if (package / "BundleFiles").exists():
                    extra += "  s.resources = 'BundleFiles/*.dat'\n"
                spec.write_text(spec.read_text().replace("  s.requires_arc", extra + "  s.requires_arc"))


if __name__ == "__main__":
    main_guard(main)
