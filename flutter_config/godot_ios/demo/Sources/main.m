#import <UIKit/UIKit.h>
#import <GodotGame/GodotGame.h>

@interface DemoController : UIViewController
@property(nonatomic, strong) UIView *container;
@property(nonatomic, strong) UILabel *status;
@property(nonatomic) BOOL paused;
@property(nonatomic) BOOL alternateColor;
@end

@implementation DemoController
- (void)viewDidLoad {
    [super viewDidLoad];
    self.view.backgroundColor = UIColor.systemTealColor;
    self.container = [UIView new];
    self.container.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:self.container];
    self.status = [UILabel new];
    self.status.text = @"准备启动 Godot";
    self.status.textColor = UIColor.labelColor;
    self.status.numberOfLines = 3;
    self.status.accessibilityIdentifier = @"godotStatus";
    UIStackView *controls = [[UIStackView alloc] initWithArrangedSubviews:@[self.status]];
    controls.axis = UILayoutConstraintAxisVertical;
    controls.spacing = 8;
    controls.backgroundColor = UIColor.secondarySystemBackgroundColor;
    controls.layoutMarginsRelativeArrangement = YES;
    controls.layoutMargins = UIEdgeInsetsMake(12, 16, 12, 16);
    controls.translatesAutoresizingMaskIntoConstraints = NO;
    NSArray *titles = @[@"切换 page_a", @"返回 main", @"暂停 / 恢复", @"切换宿主背景颜色"];
    for (NSInteger i = 0; i < titles.count; i++) {
        UIButton *button = [UIButton buttonWithType:UIButtonTypeSystem];
        [button setTitle:titles[i] forState:UIControlStateNormal];
        button.tag = i;
        [button addTarget:self action:@selector(action:) forControlEvents:UIControlEventTouchUpInside];
        [controls addArrangedSubview:button];
    }
    [self.view addSubview:controls];
    [NSLayoutConstraint activateConstraints:@[
        [controls.leadingAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.leadingAnchor],
        [controls.trailingAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.trailingAnchor],
        [controls.bottomAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.bottomAnchor],
        [self.container.topAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.topAnchor],
        [self.container.leadingAnchor constraintEqualToAnchor:self.view.leadingAnchor],
        [self.container.trailingAnchor constraintEqualToAnchor:self.view.trailingAnchor],
        [self.container.bottomAnchor constraintEqualToAnchor:controls.topAnchor]
    ]];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(message:)
        name:GodotGameEventNotification object:nil];
}
- (void)viewDidAppear:(BOOL)animated {
    [super viewDidAppear:animated];
    if (self.childViewControllers.count) return;
    NSError *error;
    UIViewController *game = [GodotGame.shared startWithError:&error];
    if (!game) {
        self.status.text = error.localizedDescription;
        return;
    }
    [self addChildViewController:game];
    game.view.frame = self.container.bounds;
    game.view.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    [self.container addSubview:game.view];
    [game didMoveToParentViewController:self];
    self.status.text = @"引擎已创建，等待场景加载；可测试消息、暂停和背景透明";
}
- (void)action:(UIButton *)sender {
    if (sender.tag < 2) {
        NSString *json = [NSString stringWithFormat:@"{\"type\":\"ToScene\",\"data\":{\"sceneName\":\"%@\"}}", sender.tag == 0 ? @"page_a" : @"main"];
        self.status.text = [GodotGame.shared sendPlatformEvent:json] ? @"消息已入队，查看游戏场景 / Xcode 日志" : @"场景桥接尚未就绪，请稍后重试";
    } else if (sender.tag == 2) {
        self.paused = !self.paused;
        if (self.paused) [GodotGame.shared pause]; else [GodotGame.shared resume];
        self.status.text = self.paused ? @"已暂停渲染" : @"已恢复渲染";
    } else {
        self.alternateColor = !self.alternateColor;
        self.view.backgroundColor = self.alternateColor ? UIColor.systemPinkColor : UIColor.systemTealColor;
    }
}
- (void)message:(NSNotification *)note {
    self.status.text = [@"Godot → iOS: " stringByAppendingString:note.userInfo[@"json"] ?: @""];
}
- (void)dealloc { [[NSNotificationCenter defaultCenter] removeObserver:self]; }
@end

@interface AppDelegate : UIResponder <UIApplicationDelegate>
@property(nonatomic, strong) UIWindow *window;
@end
@implementation AppDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)options {
    self.window = [[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];
    self.window.rootViewController = [DemoController new];
    [self.window makeKeyAndVisible];
    return YES;
}
@end

int main(int argc, char *argv[]) {
    @autoreleasepool { return UIApplicationMain(argc, argv, nil, NSStringFromClass(AppDelegate.class)); }
}
