#!/usr/bin/env python3
"""Export an iOS-feature PCK, without requiring a signing team or IPA export."""
import shutil
import plistlib
from pathlib import Path
from common import INTEGRATION, edition, main_guard, output_root, parser, project_root, run, variants


def package_aot(root, package, variant):
    """Convert the .NET export's dylib slices to embeddable iOS frameworks."""
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
    # .NET's ICU data is looked up in the application bundle, outside the PCK.
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
    # This integration deliberately builds the standard engine. Silently exporting
    # C# scripts would produce a runnable app with broken game logic.
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
            # A failed export must never be mistaken for a previous successful PCK.
            (resources / "game.pck").unlink(missing_ok=True)
        command = [args.godot, "--headless", "--path", root]
        # Main::start supports combining these switches: debug selects script
        # debug data, pack selects resource-only export (no signed app).
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
