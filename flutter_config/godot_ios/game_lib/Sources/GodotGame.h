#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN
/// 原生游戏消息；userInfo[@"json"] 为 Godot 发送的 JSON 字符串。
FOUNDATION_EXPORT NSNotificationName const GodotGameEventNotification;

/// 所有方法必须在主线程调用，每个进程仅使用一个引擎实例。
@interface GodotGame : NSObject
+ (instancetype)shared;
/// 仅创建一次引擎；需保留并复用此控制器，不支持重启引擎。
- (nullable UIViewController *)startWithError:(NSError * _Nullable * _Nullable)error;
- (void)pause;
- (void)resume;
/// 场景桥接尚未就绪或 json 不是有效 JSON 时返回 NO。
- (BOOL)sendPlatformEvent:(NSString *)json;
@end
NS_ASSUME_NONNULL_END
