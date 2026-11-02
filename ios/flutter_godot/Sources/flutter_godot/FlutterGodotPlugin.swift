import Flutter
import UIKit

public class FlutterGodotPlugin: NSObject, FlutterPlugin {
  private weak var activeView: GodotPlatformView?
  private weak var lastCreatedView: GodotPlatformView?

  public static func register(with registrar: FlutterPluginRegistrar) {
    let channel = FlutterMethodChannel(name: "flutter_godot", binaryMessenger: registrar.messenger())
    let instance = FlutterGodotPlugin()
    registrar.addMethodCallDelegate(instance, channel: channel)
    registrar.register(GodotViewFactory(registrar: registrar, plugin: instance),
                       withId: "flutter_godot/ios_view")
  }

  fileprivate func registerView(_ view: GodotPlatformView) -> Bool {
    lastCreatedView = view
    guard activeView == nil else { return false }
    activeView = view
    return true
  }

  public func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    switch call.method {
    case "getPlatformVersion":
      result("iOS " + UIDevice.current.systemVersion)
    case "initGodot":
      guard let view = lastCreatedView else {
        result(FlutterError(code: "godot_view_missing", message: "Create GodotView before initializing iOS Godot.", details: nil))
        return
      }
      do {
        try view.start()
        // 此 ID 在 iOS 上标识原生视图，并非 Flutter 纹理。
        result(["textureId": view.viewId])
      } catch {
        result(FlutterError(code: "godot_init_failed", message: error.localizedDescription, details: nil))
      }
    case "sendPlatformEventMsg":
      guard activeView != nil,
            let args = call.arguments as? [String: Any],
            let message = args["platformEventMsg"] as? String else {
        result(false)
        return
      }
      result(GodotGame.shared().sendPlatformEvent(message))
    case "release":
      let args = call.arguments as? [String: Any]
      if let id = args?["textureId"] as? NSNumber, id.int64Value == activeView?.viewId {
        activeView?.stop()
        activeView = nil
      }
      result(nil)
    case "sendTap":
      result(FlutterError(code: "unsupported_input", message: "iOS GodotView receives native touch events; sendTap is Android-only.", details: nil))
    default:
      result(FlutterMethodNotImplemented)
    }
  }
}

fileprivate class GodotViewFactory: NSObject, FlutterPlatformViewFactory {
  private let registrar: FlutterPluginRegistrar
  private let plugin: FlutterGodotPlugin

  init(registrar: FlutterPluginRegistrar, plugin: FlutterGodotPlugin) {
    self.registrar = registrar
    self.plugin = plugin
    super.init()
  }

  func createArgsCodec() -> FlutterMessageCodec & NSObjectProtocol {
    FlutterStandardMessageCodec.sharedInstance()
  }

  func create(withFrame frame: CGRect, viewIdentifier viewId: Int64,
              arguments args: Any?) -> FlutterPlatformView {
    let view = GodotPlatformView(frame: frame, viewId: viewId,
                                 parent: registrar.viewController)
    if !plugin.registerView(view) {
      view.failure = "Only one GodotView can be displayed at a time."
    }
    return view
  }
}

fileprivate class GodotPlatformView: NSObject, FlutterPlatformView {
  let viewId: Int64
  var failure: String?
  private let container: UIView
  private weak var parent: UIViewController?
  private var controller: UIViewController?

  init(frame: CGRect, viewId: Int64, parent: UIViewController?) {
    self.viewId = viewId
    self.parent = parent
    container = UIView(frame: frame)
    container.backgroundColor = .clear
    container.isOpaque = false
    super.init()
  }

  func view() -> UIView { container }

  func start() throws {
    if controller != nil { return }
    guard failure == nil, let parent = parent else {
      throw NSError(domain: "flutter_godot", code: 1,
                    userInfo: [NSLocalizedDescriptionKey: failure ?? "Flutter view controller is unavailable."])
    }
    let game = try GodotGame.shared().start()
    guard game.parent == nil else {
      throw NSError(domain: "flutter_godot", code: 2,
                    userInfo: [NSLocalizedDescriptionKey: "Godot is already attached to another view."])
    }
    parent.addChild(game)
    game.beginAppearanceTransition(true, animated: false)
    game.view.frame = container.bounds
    game.view.autoresizingMask = [.flexibleWidth, .flexibleHeight]
    container.addSubview(game.view)
    game.didMove(toParent: parent)
    game.endAppearanceTransition()
    controller = game
    GodotGame.shared().resume()
  }

  func stop() {
    guard let game = controller else { return }
    GodotGame.shared().pause()
    game.beginAppearanceTransition(false, animated: false)
    game.willMove(toParent: nil)
    game.view.removeFromSuperview()
    game.removeFromParent()
    game.endAppearanceTransition()
    controller = nil
  }

  deinit { stop() }
}
