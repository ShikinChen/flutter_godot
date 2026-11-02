package org.godotengine.godot.game.lib

import android.util.Log
import org.godotengine.godot.Godot
import org.godotengine.godot.plugin.GodotPlugin
import org.godotengine.godot.plugin.SignalInfo
import org.godotengine.godot.plugin.UsedByGodot
import java.util.Collections


/***
 * CreateBy: shiki
 * CreateDate: 2025-10-27
 * Description: [文件描述说明]
 ***/


class AndroidEventPlugin(godot: Godot) : GodotPlugin(godot) {

    companion object {
        private const val TAG = "AndroidEventPlugin"
        private const val SIGNAL_PLATFORM_EVENT = "platform_event"
    }

    // 用于存储回调的线程安全集合
    private val callbacks by lazy {
        Collections.synchronizedSet(mutableSetOf<GodotEventMsgCallback>())
    }

    override fun getPluginName(): String {
        return "PlatformEvent"
    }

    override fun getPluginSignals(): MutableSet<SignalInfo?> {
        return HashSet(
            listOf(
                SignalInfo(SIGNAL_PLATFORM_EVENT, String::class.java)
            )
        )
    }

    fun sendPlatformEventMsg(msg: String) {
        emitSignal(SIGNAL_PLATFORM_EVENT, msg)
    }

    @UsedByGodot
    fun onGodotEventMsg(msg: String) {
        Log.d(TAG, msg)
        callbacks.forEach {
            it.onGodotEventMsg(msg)
        }
    }

    fun addGodotEventMsgCallback(callback: GodotEventMsgCallback) {
        callbacks.add(callback)
    }

    fun removeGodotEventMsgCallback(callback: GodotEventMsgCallback) {
        callbacks.remove(callback)
    }

    fun clearGodotEventMsgCallback() {
        callbacks.clear()
    }

    override fun onMainDestroy() {
        clearGodotEventMsgCallback()
    }
}