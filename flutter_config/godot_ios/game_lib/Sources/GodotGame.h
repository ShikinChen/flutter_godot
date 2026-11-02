#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN
/// Native game messages. userInfo[@"json"] is the JSON string sent by Godot.
FOUNDATION_EXPORT NSNotificationName const GodotGameEventNotification;

/// All methods must be called on the main thread. One engine per process.
@interface GodotGame : NSObject
+ (instancetype)shared;
/// Creates the engine once. Retain/reuse this controller; restarting is unsupported.
- (nullable UIViewController *)startWithError:(NSError * _Nullable * _Nullable)error;
- (void)pause;
- (void)resume;
/// Returns NO before the scene bridge is ready, or if json is invalid JSON.
- (BOOL)sendPlatformEvent:(NSString *)json;
@end
NS_ASSUME_NONNULL_END
