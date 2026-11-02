#include "register_types.h"
#include "core/config/engine.h"
#include "core/object/class_db.h"
#import <Foundation/Foundation.h>

class IOSGameBridge : public Object {
    GDCLASS(IOSGameBridge, Object);
protected:
    static void _bind_methods() {
        ClassDB::bind_method(D_METHOD("send_event", "json"), &IOSGameBridge::send_event);
        ClassDB::bind_method(D_METHOD("onGodotEventMsg", "json"), &IOSGameBridge::send_event);
        ADD_SIGNAL(MethodInfo("platform_event", PropertyInfo(Variant::STRING, "json")));
    }
public:
    void send_event(const String &json) {
        NSString *message = [NSString stringWithUTF8String:json.utf8().get_data()];
        dispatch_async(dispatch_get_main_queue(), ^{
            [[NSNotificationCenter defaultCenter] postNotificationName:@"GodotGameEvent"
                object:nil userInfo:@{@"json": message ?: @""}];
        });
    }
};

static IOSGameBridge *bridge = nullptr;

extern "C" bool FGSendPlatformEvent(const char *json) {
    if (!bridge || !json || !bridge->has_connections("platform_event")) return false;
    bridge->call_deferred("emit_signal", StringName("platform_event"), String::utf8(json));
    return true;
}

void initialize_ios_game_bridge_module(ModuleInitializationLevel level) {
    if (level != MODULE_INITIALIZATION_LEVEL_SCENE) return;
    // The shipped GodotSharp assembly has no generated IOSGameBridge wrapper.
    // Internal registration lets C# use its known Object base via GetSingleton.
    GDREGISTER_INTERNAL_CLASS(IOSGameBridge);
    bridge = memnew(IOSGameBridge);
    Engine::get_singleton()->add_singleton(Engine::Singleton("PlatformEvent", bridge));
}

void uninitialize_ios_game_bridge_module(ModuleInitializationLevel level) {
    if (level != MODULE_INITIALIZATION_LEVEL_SCENE || !bridge) return;
    Engine::get_singleton()->remove_singleton("PlatformEvent");
    memdelete(bridge);
    bridge = nullptr;
}
