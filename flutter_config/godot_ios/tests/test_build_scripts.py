"""Contract tests for command generation and artifact packaging; no Xcode needed."""
import contextlib
import importlib
import io
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "buildScript"))
import common
import build_godot_ios_lib
import export_project


class BuildScriptsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="godot ios test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "project.godot").write_text('config_version=5\n')
        (self.root / "godot/platform/ios").mkdir(parents=True)
        (self.root / "godot/platform/ios/SCsub").touch()

    def invoke(self, module, *options):
        args = ["script", "--project", str(self.root), *options]
        with patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()) as output:
            module.main()
        return output.getvalue()

    def test_engine_dry_run_has_distinct_device_and_simulator_slices(self):
        output = self.invoke(build_godot_ios_lib, "--variant", "debug", "--dry-run", "--simulator-archs", "arm64", "x86_64")
        self.assertIn("simulator=no", output)
        self.assertIn("simulator=yes", output)
        self.assertIn("xcrun lipo -create", output)
        self.assertIn("template_debug.arm64.simulator.flutter.a", output)
        self.assertIn("module_mono_enabled=no", output)
        self.assertIn("disable_path_overrides=no", output)
        self.assertIn("sdl=no", output)
        self.assertIn("libGodotEngine.a", output)
        self.assertFalse((self.root / "ios").exists())

    def test_edition_auto_detects_csharp(self):
        (self.root / "Game.csproj").touch()
        self.assertIn("module_mono_enabled=yes", self.invoke(build_godot_ios_lib, "--variant", "release", "--dry-run"))

    def test_debug_pack_uses_debug_flag_without_exporting_app(self):
        output = self.invoke(export_project, "--variant", "debug", "--dry-run")
        self.assertIn("--export-debug iOS --export-pack iOS", output)
        self.assertFalse((self.root / "ios").exists())

    def test_standard_engine_rejects_referenced_csharp(self):
        (self.root / "Main.cs").touch()
        (self.root / "main.tscn").write_text('path="res://Main.cs"')
        with self.assertRaisesRegex(ValueError, "不支持 C#"):
            self.invoke(export_project, "--edition", "standard", "--dry-run")

    def test_aot_requires_successful_export(self):
        with self.assertRaisesRegex(ValueError, "AOT XCFramework"):
            export_project.package_aot(self.root, self.root / "output", "debug")

    def test_aot_conversion_preserves_platform_slices_and_icu(self):
        source = self.root / ".godot/mono/temp/bin/ExportDebug/Game_aot.xcframework"
        source.mkdir(parents=True)
        libraries = []
        for identifier, variant in (("ios-arm64", None), ("ios-arm64-simulator", "simulator")):
            folder = source / identifier
            folder.mkdir()
            (folder / "Game.dylib").write_bytes(b"test dylib")
            item = {"LibraryIdentifier": identifier, "LibraryPath": "Game.dylib", "SupportedPlatform": "ios"}
            if variant:
                item["SupportedPlatformVariant"] = variant
            libraries.append(item)
        (source / "Info.plist").write_bytes(plistlib.dumps({"AvailableLibraries": libraries}))
        icu = self.root / ".godot/mono/temp/bin/godot-publish-dotnet/ExportDebug-ios-arm64/icudt.dat"
        icu.parent.mkdir(parents=True)
        icu.write_bytes(b"icu")
        output = self.root / "output"
        calls = []
        def fake_run(command):
            calls.append(command)
            if command[0] == "xcodebuild":
                for index, token in enumerate(command):
                    if token == "-framework":
                        info = plistlib.loads((command[index + 1] / "Info.plist").read_bytes())
                        self.assertEqual(info["CFBundleExecutable"], "Game")
        with patch.object(export_project, "run", fake_run):
            export_project.package_aot(self.root, output, "debug")
        self.assertEqual(sum(c[0] == "xcrun" for c in calls), 2)
        self.assertEqual((output / "BundleFiles/icudt.dat").read_bytes(), b"icu")
        self.assertFalse((output / "aot-staging").exists())


if __name__ == "__main__":
    unittest.main()
