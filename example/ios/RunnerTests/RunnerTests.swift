import Flutter
import UIKit
import XCTest

// 若插件在 Package.swift 中显式设置为 type: .dynamic，
// 需要在 Xcode 中将插件添加为 RunnerTests 的依赖。

@testable import flutter_godot

// 此测试用于验证插件 Swift 实现的基本行为。
//
// XCTest 使用说明参见 https://developer.apple.com/documentation/xctest。

class RunnerTests: XCTestCase {

  func testGetPlatformVersion() {
    let plugin = FlutterGodotPlugin()

    let call = FlutterMethodCall(methodName: "getPlatformVersion", arguments: [])

    let resultExpectation = expectation(description: "result block must be called.")
    plugin.handle(call) { result in
      XCTAssertEqual(result as! String, "iOS " + UIDevice.current.systemVersion)
      resultExpectation.fulfill()
    }
    waitForExpectations(timeout: 1)
  }

}
