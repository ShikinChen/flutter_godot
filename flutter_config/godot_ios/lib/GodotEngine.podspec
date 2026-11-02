Pod::Spec.new do |s|
  s.name = 'GodotEngine'
  s.version = '0.1.0'
  s.summary = 'Locally built Godot iOS static engine with IOSGameBridge.'
  s.homepage = 'https://godotengine.org'
  s.license = { :type => 'MIT', :file => 'LICENSE.txt' }
  s.author = 'Godot contributors'
  s.source = { :git => 'https://github.com/godotengine/godot.git' }
  s.ios.deployment_target = '15.0'
  s.vendored_frameworks = 'GodotEngine.xcframework'
  s.preserve_paths = 'COPYRIGHT.txt'
  s.resource_bundles = { 'GodotEnginePrivacy' => ['PrivacyInfo.xcprivacy'] }
  s.frameworks = 'UIKit', 'Foundation', 'QuartzCore', 'CoreGraphics', 'CoreText',
    'CoreVideo', 'CoreMedia', 'CoreMotion', 'AudioToolbox', 'AVFoundation',
    'GameController', 'OpenGLES', 'Security', 'SystemConfiguration', 'CoreHaptics',
    'Metal', 'IOSurface', 'UniformTypeIdentifiers'
  s.libraries = 'c++', 'z', 'iconv', 'resolv'
  s.pod_target_xcconfig = { 'CLANG_CXX_LANGUAGE_STANDARD' => 'c++17' }
  s.user_target_xcconfig = { 'OTHER_LDFLAGS' => '$(inherited) -ObjC',
    'ALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES' => 'YES' }
end
