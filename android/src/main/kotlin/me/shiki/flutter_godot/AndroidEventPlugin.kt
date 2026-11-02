package me.shiki.flutter_godot

import android.util.Log
import org.godotengine.godot.Godot
import org.godotengine.godot.plugin.GodotPlugin
import org.godotengine.godot.plugin.SignalInfo
import org.godotengine.godot.plugin.UsedByGodot

/** Message interface consumed by PlatformEventNode in the Godot project. */
class AndroidEventPlugin(godot: Godot) : GodotPlugin(godot) {
    override fun getPluginName(): String = "PlatformEvent"

    override fun getPluginSignals(): Set<SignalInfo> =
        setOf(SignalInfo("platform_event", String::class.java))

    fun sendPlatformEventMsg(msg: String) {
        // This project renders Godot on its own handler thread.
        GodotRenderHandler.getInstance().queueEvent {
            emitSignal("platform_event", msg)
        }
    }

    @UsedByGodot
    fun onGodotEventMsg(msg: String) {
        Log.d("PlatformEvent", "Godot event: $msg")
    }
}
