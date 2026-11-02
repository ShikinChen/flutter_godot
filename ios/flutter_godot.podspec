require 'xcodeproj'

# sync_godot.py 将游戏的 ios/out 同步到 ios/godot。CocoaPods 中的
# 所有文件模式均相对于本插件目录，包括导出的游戏源码。
godot_variant = ENV.fetch('GODOT_VARIANT', 'debug')
raise 'GODOT_VARIANT must be debug or release' unless %w[debug release].include?(godot_variant)
godot_root = "godot/#{godot_variant}"
plugin_root = File.dirname(File.realpath(__FILE__))
engine_info = File.join(plugin_root, godot_root, 'godot_lib/GodotEngine.xcframework/Info.plist')
unless File.file?(engine_info)
  raise "Missing #{engine_info}. Run: python3 ios/sync_godot.py /path/to/game/ios/out"
end
info = Xcodeproj::Plist.read_from_path(engine_info)
simulator_archs = info['AvailableLibraries'].select { |lib|
  lib['SupportedPlatformVariant'] == 'simulator'
}.flat_map { |lib| lib['SupportedArchitectures'] }.uniq
excluded = (['i386'] + (%w[arm64 x86_64] - simulator_archs)).join(' ')

Pod::Spec.new do |s|
  s.name = 'flutter_godot'
  s.version = '0.0.1'
  s.summary = 'Godot rendering, game resources and platform messaging for Flutter.'
  s.description = 'Embeds a local Godot iOS engine and game inside a Flutter platform view.'
  s.homepage = 'http://example.com'
  s.license = { :file => '../LICENSE' }
  s.author = { 'Your Company' => 'email@example.com' }
  s.source = { :path => '.' }
  s.platform = :ios, '15.0'
  s.swift_version = '5.0'
  s.static_framework = true
  s.dependency 'Flutter'

  s.source_files = 'flutter_godot/Sources/flutter_godot/**/*.swift',
                   "#{godot_root}/godot_game_lib/Sources/*.{h,mm}"
  s.public_header_files = "#{godot_root}/godot_game_lib/Sources/GodotGame.h"
  s.vendored_frameworks = "#{godot_root}/godot_lib/GodotEngine.xcframework",
                          "#{godot_root}/godot_game_lib/Frameworks/*.xcframework"
  s.resource_bundles = {
    'GodotGameResources' => ["#{godot_root}/godot_game_lib/Resources/game.pck"],
    'GodotEnginePrivacy' => ["#{godot_root}/godot_lib/PrivacyInfo.xcprivacy"]
  }
  if Dir.glob(File.join(plugin_root, godot_root, 'godot_game_lib/BundleFiles/*.dat')).any?
    s.resources = "#{godot_root}/godot_game_lib/BundleFiles/*.dat"
  end
  s.preserve_paths = "#{godot_root}/godot_lib/LICENSE.txt", "#{godot_root}/godot_lib/COPYRIGHT.txt"
  s.frameworks = 'UIKit', 'Foundation', 'QuartzCore', 'CoreGraphics', 'CoreText',
    'CoreVideo', 'CoreMedia', 'CoreMotion', 'AudioToolbox', 'AVFoundation',
    'GameController', 'OpenGLES', 'Security', 'SystemConfiguration', 'CoreHaptics',
    'Metal', 'IOSurface', 'UniformTypeIdentifiers'
  s.libraries = 'c++', 'z', 'iconv', 'resolv'
  s.requires_arc = true
  s.pod_target_xcconfig = {
    'DEFINES_MODULE' => 'YES',
    'CLANG_CXX_LANGUAGE_STANDARD' => 'c++17',
    'EXCLUDED_ARCHS[sdk=iphonesimulator*]' => excluded
  }
  s.user_target_xcconfig = {
    'OTHER_LDFLAGS' => '$(inherited) -ObjC',
    'ALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES' => 'YES',
    'EXCLUDED_ARCHS[sdk=iphonesimulator*]' => excluded
  }
end
