#import <XCTest/XCTest.h>

@interface DemoUITests : XCTestCase
@end

@implementation DemoUITests
- (void)testEmbeddedEngineAndControls {
    self.continueAfterFailure = NO;
    XCUIApplication *app = [XCUIApplication new];
    [app launch];
    XCUIElement *status = app.staticTexts[@"godotStatus"];
    XCTAssertTrue([status waitForExistenceWithTimeout:30]);
    NSPredicate *started = [NSPredicate predicateWithFormat:@"label CONTAINS %@", @"引擎已创建"];
    [self expectationForPredicate:started evaluatedWithObject:status handler:nil];
    [self waitForExpectationsWithTimeout:30 handler:nil];
    // Startup is staged over several display frames; retry until the scene
    // bridge exists, rather than relying on a fixed sleep.
    NSDate *deadline = [NSDate dateWithTimeIntervalSinceNow:30];
    do {
        [app.buttons[@"切换 page_a"] tap];
        if ([status.label containsString:@"消息已入队"]) break;
    } while (deadline.timeIntervalSinceNow > 0);
    XCTAssertTrue([status.label containsString:@"消息已入队"]);
    [app.buttons[@"返回 main"] tap];
    XCTAssertTrue([status.label containsString:@"消息已入队"]);
    [app.buttons[@"暂停 / 恢复"] tap];
    XCTAssertEqualObjects(status.label, @"已暂停渲染");
    [app.buttons[@"暂停 / 恢复"] tap];
    XCTAssertEqualObjects(status.label, @"已恢复渲染");
    [app.buttons[@"切换宿主背景颜色"] tap];
    XCTAttachment *capture = [XCTAttachment attachmentWithScreenshot:app.screenshot];
    capture.name = @"Godot embedded view after host background change";
    capture.lifetime = XCTAttachmentLifetimeKeepAlways;
    [self addAttachment:capture];
}
@end
