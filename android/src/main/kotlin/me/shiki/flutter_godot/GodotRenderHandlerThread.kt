package me.shiki.flutter_godot

import android.os.HandlerThread

/***
 * CreateBy: shiki
 * CreateDate: 2025-10-15
 * Description: [文件描述说明]
 ***/


class GodotRenderHandlerThread private constructor() : HandlerThread("GodotRenderHandlerThread") {

    companion object {

        private const val TAG = "GodotRenderHandlerThread"

        // 单例实例
        @Volatile
        private var instance: GodotRenderHandlerThread? = null

        // 获取单例的方法
        @JvmStatic
        fun getInstance(): GodotRenderHandlerThread {
            return instance ?: synchronized(this) {
                instance ?: GodotRenderHandlerThread().also {
                    it.start()
                    instance = it
                }
            }
        }
    }
}