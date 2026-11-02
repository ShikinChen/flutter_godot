Pod::Spec.new do |s|
  s.name = 'GodotGame'
  s.version = '0.1.0'
  s.summary = 'Godot game resources and native iOS host API.'
  s.homepage = 'https://godotengine.org'
  s.license = { :type => 'MIT' }
  s.author = 'Flutter Godot integration'
  s.source = { :git => 'https://github.com/godotengine/godot.git' }
  s.ios.deployment_target = '15.0'
  s.dependency 'GodotEngine', '= 0.1.0'
  s.source_files = 'Sources/*.{h,mm}'
  s.public_header_files = 'Sources/GodotGame.h'
  s.resource_bundles = { 'GodotGameResources' => ['Resources/game.pck'] }
  s.requires_arc = true
  s.pod_target_xcconfig = { 'CLANG_CXX_LANGUAGE_STANDARD' => 'c++17' }
end
