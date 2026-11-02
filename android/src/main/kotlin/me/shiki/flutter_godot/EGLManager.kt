package me.shiki.flutter_godot

import android.opengl.EGLContext
import android.opengl.EGLDisplay
import android.opengl.EGLSurface
import android.opengl.EGL14
import android.opengl.EGLConfig
import android.opengl.EGLExt
import android.view.Surface
import android.util.Log

/***
 * CreateBy: shiki
 * CreateDate: 2025-10-23
 * Description: [文件描述说明]
 ***/
class EGLManager(private val surface: Surface) {
    private var eglDisplay: EGLDisplay = EGL14.EGL_NO_DISPLAY
    var eglContext: EGLContext = EGL14.EGL_NO_CONTEXT
        private set
    private var eglSurface: EGLSurface = EGL14.EGL_NO_SURFACE

    var eglConfig: EGLConfig? = null
        private set

    companion object {
        private const val TAG = "EGLManager"
    }

    fun init(): Boolean {
        try {
            // 获取 EGL Display
            eglDisplay = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY)
            if (eglDisplay == EGL14.EGL_NO_DISPLAY) {
                Log.e(TAG, "Failed to get EGL display")
                return false
            }

            // 初始化 EGL
            val version = IntArray(2)
            if (!EGL14.eglInitialize(eglDisplay, version, 0, version, 1)) {
                Log.e(TAG, "Failed to initialize EGL")
                return false
            }

            // 选择 EGL 配置
            val configAttribs = intArrayOf(
                EGL14.EGL_RENDERABLE_TYPE, EGLExt.EGL_OPENGL_ES3_BIT_KHR, // 0x00000040
                EGL14.EGL_SURFACE_TYPE, EGL14.EGL_WINDOW_BIT,
                EGL14.EGL_RED_SIZE, 8,
                EGL14.EGL_GREEN_SIZE, 8,
                EGL14.EGL_BLUE_SIZE, 8,
                EGL14.EGL_ALPHA_SIZE, 8,
                EGL14.EGL_DEPTH_SIZE, 24,                 // 与官方选择器一致
                // 可选: EGL14.EGL_STENCIL_SIZE, 8,
                EGL14.EGL_NONE
            )
            val configs = arrayOfNulls<android.opengl.EGLConfig>(1)
            val numConfigs = IntArray(1)
            if (!EGL14.eglChooseConfig(
                    eglDisplay,
                    configAttribs,
                    0,
                    configs,
                    0,
                    1,
                    numConfigs,
                    0
                )
            ) {
                Log.e(TAG, "Failed to choose EGL config")
                return false
            }
            eglConfig = configs[0]
            // 创建 EGL Context
            val contextAttribs = intArrayOf(
                EGL14.EGL_CONTEXT_CLIENT_VERSION, 3,
                EGL14.EGL_NONE
            )
            eglContext = EGL14.eglCreateContext(
                eglDisplay,
                configs[0],
                EGL14.EGL_NO_CONTEXT,
                contextAttribs,
                0
            )
            if (eglContext == EGL14.EGL_NO_CONTEXT) {
                Log.e(TAG, "Failed to create EGL context")
                return false
            }

            // 创建 EGL Surface
            val surfaceAttribs = intArrayOf(EGL14.EGL_NONE)
            eglSurface =
                EGL14.eglCreateWindowSurface(eglDisplay, configs[0], surface, surfaceAttribs, 0)
            if (eglSurface == EGL14.EGL_NO_SURFACE) {
                Log.e(TAG, "Failed to create EGL surface")
                return false
            }

            // 绑定 EGL Context
            if (!EGL14.eglMakeCurrent(eglDisplay, eglSurface, eglSurface, eglContext)) {
                Log.e(TAG, "Failed to make EGL context current")
                return false
            }

            Log.d(TAG, "EGL initialized successfully")
            return true
        } catch (e: Exception) {
            Log.e(TAG, "EGL init error: ${e.message}")
            return false
        }
    }

    fun makeCurrent(): Boolean {
        return EGL14.eglMakeCurrent(eglDisplay, eglSurface, eglSurface, eglContext)
    }

    fun swapBuffers(): Boolean {
        return EGL14.eglSwapBuffers(eglDisplay, eglSurface)
    }

    fun release() {
        if (eglDisplay != EGL14.EGL_NO_DISPLAY) {
            EGL14.eglMakeCurrent(
                eglDisplay,
                EGL14.EGL_NO_SURFACE,
                EGL14.EGL_NO_SURFACE,
                EGL14.EGL_NO_CONTEXT
            )
            if (eglSurface != EGL14.EGL_NO_SURFACE) {
                EGL14.eglDestroySurface(eglDisplay, eglSurface)
            }
            if (eglContext != EGL14.EGL_NO_CONTEXT) {
                EGL14.eglDestroyContext(eglDisplay, eglContext)
            }
            EGL14.eglTerminate(eglDisplay)
        }
    }
}