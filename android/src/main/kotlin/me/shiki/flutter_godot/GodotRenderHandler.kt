package me.shiki.flutter_godot

import android.content.Context
import android.os.Handler
import android.os.Message
import android.util.Log
import org.godotengine.godot.BuildConfig
import org.godotengine.godot.GodotLib
import org.godotengine.godot.plugin.GodotPlugin
import org.godotengine.godot.plugin.GodotPluginRegistry

/***
 * CreateBy: shiki
 * CreateDate: 2025-10-15
 * Description: [文件描述说明]
 ***/


class GodotRenderHandler private constructor() :
    Handler(GodotRenderHandlerThread.getInstance().looper) {
    companion object {
        private const val TAG = "GodotRenderHandler"

        private const val INIT = 0

        private const val START = 1

        private const val SURFACE_CHANGED = 2

        private const val ON_DRAW_FRAME = 3

        private const val DESTROY = 10

        const val DEFAULT_FRAME_INTERVAL = 32L

        // 单例实例
        @Volatile
        private var instance: GodotRenderHandler? = null


        // 获取单例的方法
        @JvmStatic
        fun getInstance(): GodotRenderHandler {
            return instance ?: synchronized(this) {
                instance ?: GodotRenderHandler().also {
                    instance = it
                }
            }
        }
    }

    private var activityJustResumed = true

    private var isInited = false
    private var isStarted = false

    private var pluginRegistry: GodotPluginRegistry? = null

    private var eglManager: EGLManager? = null
    private var fboManager: FBOManager? = null

    fun sendInitMsg(context: Context) {
        val msg = Message.obtain()
        msg.what = INIT
        msg.obj = context
        sendMessage(msg)
    }

    fun sendStartMsg(player: FlutterGodotPlayer) {
        val msg = Message.obtain()
        msg.what = START
        msg.obj = player
        sendMessage(msg)
    }

    fun sendTapMsg(player: FlutterGodotPlayer) {
        val msg = Message.obtain()
        msg.what = START
        msg.obj = player
        sendMessage(msg)
    }

    fun sendSurfaceChangedMsg(width: Int, height: Int) {
        val msg = Message.obtain()
        msg.what = SURFACE_CHANGED
        msg.obj = Pair(width, height)
        sendMessage(msg)
    }

    fun sendDestroyMsg(player: FlutterGodotPlayer) {
        val msg = Message.obtain()
        msg.what = DESTROY
        msg.obj = player
        sendMessage(msg)
    }

    fun queueEvent(event: Runnable) {
        post(event)
    }

    fun blockingExitRenderer(timeout: Long): Boolean {
        val cleanup = Runnable {
            isStarted = false
            removeMessages(ON_DRAW_FRAME)
            fboManager?.release()
            fboManager = null
            eglManager?.release()
            eglManager = null
        }
        if (android.os.Looper.myLooper() == looper) {
            cleanup.run()
            return true
        }
        val completed = java.util.concurrent.CountDownLatch(1)
        if (!post {
            try {
                cleanup.run()
            } finally {
                completed.countDown()
            }
        }) return false
        return try {
            completed.await(timeout.coerceAtLeast(0), java.util.concurrent.TimeUnit.MILLISECONDS)
        } catch (_: InterruptedException) {
            Thread.currentThread().interrupt()
            false
        }
    }

    override fun handleMessage(msg: Message) {
        when (msg.what) {
            INIT -> {
                if (!isInited && FlutterGodotHost.getInstance().isInited) {
                    val context = msg.obj as Context
                    val hots = FlutterGodotHost.getInstance()
                    val godot = hots.mainGodot
                    val assetsCommandLine = try {
                        GodotCommandLineFileParser.parseCommandLine(context.assets.open("_cl_"))
                    } catch (ignored: Exception) {
                        mutableListOf()
                    }
                    ///强制godot使用opengl3
                    assetsCommandLine.add("--rendering-driver")
                    assetsCommandLine.add("opengl3")
                    assetsCommandLine.add("--rendering-method")
                    assetsCommandLine.add("gl_compatibility")

                    if (BuildConfig.DEBUG) {
                        assetsCommandLine.add("--verbose")
                    }
                    val hostPlugins = mutableSetOf<GodotPlugin>()
                    hots.androidEventPlugin?.also {
                        hostPlugins.add(it)
                    }
                    isInited =
                        godot?.initEngine(hots, assetsCommandLine, hostPlugins) == true
                }
                Log.d(TAG, "INIT:${isInited}")
            }

            START -> {
                if (!isInited) {
                    return
                }
                pluginRegistry = GodotPluginRegistry.getPluginRegistry()
                if (!isStarted) {
                    val player = msg.obj as FlutterGodotPlayer
                    val surface = player.surface


                    // 初始化 EGL
                    eglManager = EGLManager(surface)
                    if (!eglManager!!.init()) {
                        Log.e(TAG, "Failed to initialize EGL")
                        return
                    }
                    val width = player.width
                    val height = player.height
                    // 初始化 FBO
                    fboManager = FBOManager(width, height)
                    if (!fboManager!!.init()) {
                        Log.e(TAG, "Failed to initialize FBO")
                        return
                    }
                    GodotLib.newcontext(null)

                    GodotLib.resize(null, width, height)
                    if (pluginRegistry != null) {
                        for (plugin in pluginRegistry!!.allPlugins) {
                            plugin.onRegisterPluginWithGodotNative()
                        }
                        for (plugin in pluginRegistry!!.allPlugins) {
                            plugin.onGLSurfaceCreated(null, null)
                        }
                        for (plugin in pluginRegistry!!.allPlugins) {
                            plugin.onGLSurfaceChanged(null, width, height)
                        }
                    }
                    //godot的第一步先启动初始化
                    GodotLib.step()
                    if (!player.isShowLogo) {
                        //godot的第二步是显示logo,后面就是启动主线程进行渲染
                        GodotLib.step()
                    }
                    sendEmptyMessage(ON_DRAW_FRAME)
                    isStarted = true
                }
                Log.d(TAG, "START")
            }

            SURFACE_CHANGED -> {
                if (!isInited) {
                    return
                }
                val obj = msg.obj as Pair<Int, Int>
                val width = obj.first
                val height = obj.second
                GodotLib.resize(null, width, height)
                if (pluginRegistry != null) {
                    for (plugin in pluginRegistry!!.allPlugins) {
                        plugin.onGLSurfaceChanged(null, width, height)
                    }
                }
            }

            ON_DRAW_FRAME -> {
                if (!isInited || !isStarted) {
                    return
                }

                eglManager?.makeCurrent()
                // Render into the EGL window surface consumed by Flutter Texture.
                // An offscreen FBO without a blit would never reach that surface.

                if (activityJustResumed) {
                    GodotLib.onRendererResumed()
                    GodotLib.focusin()
                    activityJustResumed = false
//                    Log.d(TAG, "onRendererResumed")
                }
//                Log.d(TAG, "ON_DRAW_FRAME_step")
                val swapBuffers = GodotLib.step()

                fboManager?.unbind()
                eglManager?.swapBuffers()

                pluginRegistry?.also {
                    for (plugin in it.allPlugins) {
                        plugin.onGLDrawFrame(null)
                    }
                }
//                Log.d(TAG, "ON_DRAW_FRAME_swapBuffers:${swapBuffers}")
                if (swapBuffers) {
                    sendEmptyMessageDelayed(ON_DRAW_FRAME, DEFAULT_FRAME_INTERVAL)
                }
            }

            DESTROY -> {
                val player = msg.obj as FlutterGodotPlayer
                isStarted = false
                removeMessages(ON_DRAW_FRAME)
                if (isInited) GodotLib.ondestroy()
                fboManager?.release()
                fboManager = null
                eglManager?.release()
                eglManager = null
                isInited = false
                player.destroy()
            }

            else -> {}
        }
    }
}