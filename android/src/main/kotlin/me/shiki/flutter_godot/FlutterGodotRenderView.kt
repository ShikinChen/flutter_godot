package me.shiki.flutter_godot

import android.view.SurfaceView
import org.godotengine.godot.GodotRenderView
import org.godotengine.godot.input.GodotInputHandler

/***
 * 作者： shiki
 * 创建日期： 2025-10-23
 * 说明： 空实现 godot 一定需要 RenderView
 ***/


class FlutterGodotRenderView(val godotInputHandler: GodotInputHandler?) : GodotRenderView {
    override fun getView(): SurfaceView? {
        return null
    }

    override fun startRenderer() {
    }

    override fun queueOnRenderThread(event: Runnable?) {
        event?.also {
            GodotRenderHandler.getInstance().queueEvent(it)
        }
    }

    override fun onActivityPaused() {
    }

    override fun onActivityStopped() {
    }

    override fun onActivityResumed() {
    }

    override fun onActivityStarted() {
    }

    override fun blockingExitRenderer(timeout: Long): Boolean {
        return GodotRenderHandler.getInstance().blockingExitRenderer(timeout)
    }

    override fun getInputHandler(): GodotInputHandler? {
        return godotInputHandler
    }

    override fun configurePointerIcon(
        pointerType: Int,
        imagePath: String?,
        hotSpotX: Float,
        hotSpotY: Float
    ) {
    }

    override fun setPointerIcon(pointerType: Int) {
    }

    fun requestPointerCapture() {
        if (canCapturePointer()) {
            inputHandler?.onPointerCaptureChange(true)
        }
    }

    fun releasePointerCapture() {
        inputHandler?.onPointerCaptureChange(false)
    }

    override fun canCapturePointer(): Boolean {
        return inputHandler?.canCapturePointer() ?: false
    }
}