#!/usr/bin/env ruby
# Optional regeneration; the generated project is committed. Requires xcodeproj.
require 'xcodeproj'
require 'fileutils'
Dir.chdir(__dir__) do
  project = Xcodeproj::Project.new('GodotIOSDemo.xcodeproj')
  target = project.new_target(:application, 'GodotIOSDemo', :ios, '15.0')
  target.add_file_references([project.main_group.new_file('Sources/main.m')])
  target.build_configurations.each do |config|
    config.build_settings.merge!({
      'PRODUCT_BUNDLE_IDENTIFIER' => 'org.example.godot.iosdemo',
      'PRODUCT_NAME' => '$(TARGET_NAME)',
      'GENERATE_INFOPLIST_FILE' => 'YES',
      'INFOPLIST_KEY_UILaunchScreen_Generation' => 'YES',
      'INFOPLIST_KEY_UIRequiresFullScreen' => 'YES',
      'INFOPLIST_KEY_UISupportedInterfaceOrientations' => 'UIInterfaceOrientationPortrait',
      'TARGETED_DEVICE_FAMILY' => '1,2',
      'CLANG_ENABLE_MODULES' => 'YES',
      'CLANG_ENABLE_OBJC_ARC' => 'YES',
      'SWIFT_VERSION' => '5.0',
      'LD_RUNPATH_SEARCH_PATHS' => '$(inherited) @executable_path/Frameworks',
      'IPHONEOS_DEPLOYMENT_TARGET' => '15.0'
    })
  end
  tests = project.new_target(:ui_test_bundle, 'GodotIOSDemoUITests', :ios, '15.0')
  tests.add_file_references([project.main_group.new_file('UITests/DemoUITests.m')])
  tests.add_dependency(target)
  project.root_object.attributes['TargetAttributes'] ||= {}
  project.root_object.attributes['TargetAttributes'][tests.uuid] = { 'TestTargetID' => target.uuid }
  tests.build_configurations.each do |config|
    config.build_settings.merge!({
      'PRODUCT_BUNDLE_IDENTIFIER' => 'org.example.godot.iosdemo.uitests',
      'GENERATE_INFOPLIST_FILE' => 'YES',
      'TEST_TARGET_NAME' => 'GodotIOSDemo',
      'CLANG_ENABLE_MODULES' => 'YES',
      'CLANG_ENABLE_OBJC_ARC' => 'YES',
      'IPHONEOS_DEPLOYMENT_TARGET' => '15.0'
    })
  end
  project.save
  scheme = Xcodeproj::XCScheme.new
  scheme.add_build_target(target)
  scheme.set_launch_target(target)
  scheme.add_test_target(tests)
  scheme.save_as(project.path, 'GodotIOSDemo', true)
end
