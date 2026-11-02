package me.shiki.flutter_godot

import android.os.Handler
import android.os.Looper
import android.view.Surface

/***
 * 作者： shiki
 * 创建日期： 2025-10-15
 * 说明： [文件描述说明]
 ***/


class FlutterGodotPlayer(
    private val textureId: Long = -1L,
    val surface: Surface,
    val width: Int,
    val height: Int,
    val isShowLogo: Boolean = false,
) {
    private val godotHandler by lazy {
        GodotRenderHandler.getInstance()
    }

    private val mainHandler by lazy {
        Handler(Looper.getMainLooper())
    }

    fun start() {
        godotHandler.sendStartMsg(this)
    }

    fun stop() {
//        handler.sendStopMsg(this)
    }

    fun pause() {
//        handler.sendPauseMsg(this)
    }

    fun destroy() {
        surface.release()
    }

    fun sendTap(x: Float, y: Float) {
        mainHandler.post {
            FlutterGodotHost.getInstance().sendTap(x, y)
        }
    }
}