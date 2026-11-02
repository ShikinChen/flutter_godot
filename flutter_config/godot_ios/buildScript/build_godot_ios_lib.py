#!/usr/bin/env python3
"""编译真机与模拟器静态库，并打包为 CocoaPods 使用的 XCFramework。"""
import os
import shutil
import subprocess
import sys
from common import INTEGRATION, edition, main_guard, output_root, parser, project_root, run, variants


def main():
    cli = parser("编译 Godot iOS 引擎并生成 GodotEngine.xcframework")
    cli.add_argument("--scons", default="scons")
    cli.add_argument("--skip-compile", action="store_true", help="复用现有 .a，仅重新打包 XCFramework")
    cli.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    cli.add_argument("--simulator-archs", nargs="+", choices=("arm64", "x86_64"), default=["arm64"])
    args = cli.parse_args()
    root = project_root(args.project)
    source = root / "godot"
    if not (source / "platform/ios/SCsub").is_file():
        raise ValueError(f"缺少 Godot iOS 源码: {source}，请先运行 init_project.py")
    if args.jobs < 1:
        raise ValueError("--jobs 必须大于 0")
    if sys.platform != "darwin" and not args.dry_run:
        raise ValueError("iOS 构建需要 macOS 和完整 Xcode")
    out = output_root(args, root)
    for variant in variants(args.variant):
        slices = []
        for simulator, arch in [(False, "arm64")] + [(True, a) for a in dict.fromkeys(args.simulator_archs)]:
            command = [args.scons, "platform=ios", f"target=template_{variant}", f"arch={arch}",
                 f"simulator={'yes' if simulator else 'no'}", "generate_bundle=no",
                 f"module_mono_enabled={'yes' if edition(args, root) == 'mono' else 'no'}", "module_camera_enabled=no", "vulkan=no", "metal=no",
                 "opengl3=yes", "sdl=no", "disable_path_overrides=no", "extra_suffix=flutter", f"custom_modules={INTEGRATION / 'modules'}",
                 f"-j{args.jobs}"]
            if not args.skip_compile:
                run(command, cwd=source, dry_run=args.dry_run)
            suffix = ".simulator" if simulator else ""
            library = source / f"bin/libgodot.ios.template_{variant}.{arch}{suffix}.flutter.a"
            if not args.dry_run and not library.is_file():
                raise ValueError(f"编译完成但缺少产物: {library}")
            slices.append(library)
        package = out / variant / "godot_lib"
        framework = package / "GodotEngine.xcframework"
        headers = package / "Headers"
        if not args.dry_run:
            headers.mkdir(parents=True, exist_ok=True)
            (out / ".gdignore").touch()
            for name in ("godot_view_controller.h", "godot_view_apple_embedded.h", "app_delegate_service.h"):
                shutil.copy2(source / "drivers/apple_embedded" / name, headers / name)
            shutil.copy2(source / "LICENSE.txt", package / "LICENSE.txt")
            # 在可分发的引擎产物中保留第三方许可证声明。
            shutil.copy2(source / "COPYRIGHT.txt", package / "COPYRIGHT.txt")
            if framework.exists():
                shutil.rmtree(framework)
        # CocoaPods 根据库文件名生成 -l 链接参数，因此两个切片必须使用
        # 相同的简短名称，而 Godot 的 SCons 产物名包含架构或模拟器信息。
        staging = package / "staging"
        device_lib = staging / "device/libGodotEngine.a"
        simulator_lib = staging / "simulator/libGodotEngine.a"
        if not args.dry_run:
            device_lib.parent.mkdir(parents=True, exist_ok=True)
            simulator_lib.parent.mkdir(parents=True, exist_ok=True)
        normalized = []
        for index, source_lib in enumerate(slices):
            destination = staging / f"slice-{index}/libGodotEngine.a"
            print(f"Copy {source_lib} -> {destination}")
            if not args.dry_run:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_lib, destination)
                # 上游导出归档包含独立 SwiftUI 应用的 @main 入口；
                # 以库集成时，应由宿主提供入口与生命周期。
                members = subprocess.check_output(["xcrun", "ar", "-t", str(destination)], text=True).splitlines()
                entries = [name for name in members if name.startswith("app.ios.") and name.endswith(".o")]
                if len(entries) != 1:
                    raise ValueError(f"无法识别引擎中的 SwiftUI app 入口对象: {entries}")
                run(["xcrun", "ar", "-d", destination, entries[0]])
            normalized.append(destination)
        if not args.dry_run:
            shutil.copy2(normalized[0], device_lib)
        if len(slices) > 2:
            run(["xcrun", "lipo", "-create", *normalized[1:], "-output", simulator_lib], dry_run=args.dry_run)
        else:
            print(f"Copy {slices[1]} -> {simulator_lib}")
            if not args.dry_run:
                shutil.copy2(normalized[1], simulator_lib)
        run(["xcodebuild", "-create-xcframework", "-library", device_lib, "-headers", headers,
             "-library", simulator_lib, "-headers", headers, "-output", framework], dry_run=args.dry_run)
        if not args.dry_run:
            shutil.copy2(INTEGRATION / "lib/GodotEngine.podspec", package / "GodotEngine.podspec")
            shutil.copy2(source / "misc/dist/apple_embedded_xcode/PrivacyInfo.xcprivacy", package / "PrivacyInfo.xcprivacy")
            shutil.rmtree(staging)


if __name__ == "__main__":
    main_guard(main)
