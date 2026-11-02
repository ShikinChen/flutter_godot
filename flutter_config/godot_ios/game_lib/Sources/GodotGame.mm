#import "GodotGame.h"
#import "godot_view_controller.h"
#import "godot_view_apple_embedded.h"
#import "app_delegate_service.h"
#include <vector>
#include <string>

extern int apple_embedded_main(int argc, char **argv);
extern "C" bool FGSendPlatformEvent(const char *json);

// 标准 iOS 导出通常会生成这些函数；本包使用自定义
// 引擎模块，不包含外部 .gdip 插件。
void godot_apple_embedded_plugins_initialize() {}
void godot_apple_embedded_plugins_deinitialize() {}

NSNotificationName const GodotGameEventNotification = @"GodotGameEvent";

@interface GodotGame ()
@property(nonatomic, strong) GDTViewController *controller;
@property(nonatomic, strong) GDTAppDelegateService *lifecycle;
@property(nonatomic) BOOL attempted;
@property(nonatomic) BOOL manuallyPaused;
@end

@interface GDTViewController (FGSetupDeclaration)
- (BOOL)godotViewFinishedSetup:(GDTView *)view;
@end

@interface FGGameController : GDTViewController <GDTViewDelegate>
@property(nonatomic) BOOL gameReady;
@end
@implementation FGGameController
- (BOOL)godotViewFinishedSetup:(GDTView *)view {
    BOOL ready = [super godotViewFinishedSetup:view];
    // 即使 viewport 已透明，Godot 的 iOS GLES 图层默认仍为不透明。
    view.opaque = NO;
    view.layer.opaque = NO;
    view.renderingLayer.opaque = NO;
    view.backgroundColor = UIColor.clearColor;
    self.gameReady = ready;
    return ready;
}
@end

@implementation GodotGame
+ (instancetype)shared {
    static GodotGame *instance;
    static dispatch_once_t once;
    dispatch_once(&once, ^{ instance = [GodotGame new]; });
    return instance;
}

- (UIViewController *)startWithError:(NSError **)error {
    NSAssert(NSThread.isMainThread, @"GodotGame requires the main thread");
    if (self.controller) return self.controller;
    NSString *failure = nil;
    NSBundle *bundle = [NSBundle bundleWithPath:[[NSBundle mainBundle] pathForResource:@"GodotGameResources" ofType:@"bundle"]];
    NSString *pack = [bundle pathForResource:@"game" ofType:@"pck"];
    if (self.attempted) failure = @"Godot startup previously failed; relaunch the app to retry.";
    else if (!pack) failure = @"Missing GodotGameResources.bundle/game.pck. Run the export script and pod install.";
    else if ([[NSBundle mainBundle] objectForInfoDictionaryKey:@"godot_cmdline"]) failure = @"Remove godot_cmdline from the host Info.plist; arguments are managed by GodotGame.";
    if (!failure) {
        self.attempted = YES;
        // main_ios 的参数缓冲区最多容纳 64 项，此固定列表应保持精简。
        std::vector<std::string> args = { NSBundle.mainBundle.executablePath.UTF8String,
            "--main-pack", pack.UTF8String, "--rendering-method", "gl_compatibility",
            "--rendering-driver", "opengl3" };
        std::vector<char *> argv;
        for (auto &arg : args) argv.push_back(arg.data());
        argv.push_back(nullptr);
        if (apple_embedded_main((int)args.size(), argv.data()) != 0) {
            failure = @"Godot setup failed. See the Xcode console.";
        } else {
            self.lifecycle = [GDTAppDelegateService new];
            self.controller = [FGGameController new];
            GDTAppDelegateService.viewController = self.controller;
            self.controller.view.opaque = NO;
            self.controller.view.backgroundColor = UIColor.clearColor;
            NSNotificationCenter *center = NSNotificationCenter.defaultCenter;
            [center addObserver:self selector:@selector(inactive:) name:UIApplicationWillResignActiveNotification object:nil];
            [center addObserver:self selector:@selector(active:) name:UIApplicationDidBecomeActiveNotification object:nil];
            [center addObserver:self selector:@selector(background:) name:UIApplicationDidEnterBackgroundNotification object:nil];
            [center addObserver:self selector:@selector(foreground:) name:UIApplicationWillEnterForegroundNotification object:nil];
        }
    }
    if (failure) {
        if (error) *error = [NSError errorWithDomain:@"GodotGame" code:1 userInfo:@{NSLocalizedDescriptionKey: failure}];
        return nil;
    }
    return self.controller;
}
- (void)pause {
    NSAssert(NSThread.isMainThread, @"GodotGame requires the main thread");
    self.manuallyPaused = YES;
    [self.controller.godotView stopRendering];
}
- (void)resume {
    NSAssert(NSThread.isMainThread, @"GodotGame requires the main thread");
    self.manuallyPaused = NO;
    if (UIApplication.sharedApplication.applicationState == UIApplicationStateActive)
        [self.controller.godotView startRendering];
}
- (void)inactive:(NSNotification *)note {
    [self.controller.godotView stopRendering];
    [self.lifecycle applicationWillResignActive:UIApplication.sharedApplication];
}
- (void)active:(NSNotification *)note {
    [self.lifecycle applicationDidBecomeActive:UIApplication.sharedApplication];
    if (self.manuallyPaused) [self.controller.godotView stopRendering];
    else [self.controller.godotView startRendering];
}
- (void)background:(NSNotification *)note {
    [self.lifecycle applicationDidEnterBackground:UIApplication.sharedApplication];
}
- (void)foreground:(NSNotification *)note {
    [self.lifecycle applicationWillEnterForeground:UIApplication.sharedApplication];
    if (self.manuallyPaused) [self.controller.godotView stopRendering];
}
- (BOOL)sendPlatformEvent:(NSString *)json {
    NSAssert(NSThread.isMainThread, @"GodotGame requires the main thread");
    if (!self.controller || ![(FGGameController *)self.controller gameReady] ||
        ![NSJSONSerialization JSONObjectWithData:[json dataUsingEncoding:NSUTF8StringEncoding] options:NSJSONReadingFragmentsAllowed error:nil]) return NO;
    return FGSendPlatformEvent(json.UTF8String);
}
@end
