package me.shiki.flutter_godot

import android.util.Log
import org.godotengine.godot.Godot
import org.godotengine.godot.plugin.GodotPlugin
import org.godotengine.godot.plugin.SignalInfo
import org.godotengine.godot.plugin.UsedByGodot

/** 供 Godot 项目的 PlatformEventNode 使用的消息接口。 */
class AndroidEventPlugin(godot: Godot) : GodotPlugin(godot) {
    override fun getPluginName(): String = "PlatformEvent"

    override fun getPluginSignals(): Set<SignalInfo> =
        setOf(SignalInfo("platform_event", String::class.java))

    fun sendPlatformEventMsg(msg: String) {
        // 本项目在独立的消息处理线程中渲染 Godot。
        GodotRenderHandler.getInstance().queueEvent {
            emitSignal("platform_event", msg)
        }
    }

    @UsedByGodot
    fun onGodotEventMsg(msg: String) {
        Log.d("PlatformEvent", "Godot event: $msg")
    }
}
