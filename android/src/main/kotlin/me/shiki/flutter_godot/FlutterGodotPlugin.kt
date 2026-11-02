package me.shiki.flutter_godot

import android.app.Activity
import android.app.Application
import android.content.Context
import android.os.Build
import android.os.Bundle
import android.view.PointerIcon
import android.view.View
import io.flutter.Log
import io.flutter.embedding.engine.plugins.FlutterPlugin
import io.flutter.embedding.engine.plugins.activity.ActivityAware
import io.flutter.embedding.engine.plugins.activity.ActivityPluginBinding
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.MethodChannel.MethodCallHandler
import io.flutter.plugin.common.MethodChannel.Result
import io.flutter.view.TextureRegistry
import io.flutter.view.TextureRegistry.SurfaceProducer

/** FlutterGodotPlugin */
class FlutterGodotPlugin :
    FlutterPlugin,
    MethodCallHandler, ActivityAware, Application.ActivityLifecycleCallbacks {
    private lateinit var channel: MethodChannel

    private lateinit var context: Context

    private lateinit var textureRegistry: TextureRegistry

    private val surfaceProducerMap by lazy {
        HashMap<String, TextureRegistry.SurfaceProducer>()
    }

    private val playerMap by lazy {
        HashMap<String, FlutterGodotPlayer>()
    }

    companion object {

        private const val TAG = "FlutterGodotPlugin"

        ///方法名
        private const val nativeInit: String = "initGodot"

        private const val nativeStart: String = "start"

        private const val nativeStop: String = "stop"

        private const val nativePause: String = "pause"

        private const val nativeRelease: String = "release"

        private const val nativeSendTap: String = "sendTap"

        private const val nativeSendPlatformEventMsg: String = "sendPlatformEventMsg"

        ///参数名
        private const val argumentTextureId: String = "textureId"
        private const val argumentGameWidth: String = "gameWidth"
        private const val argumentGameHeight: String = "gameHeight"

        private const val argumentPlatformEventMsg: String = "platformEventMsg"

        private const val argumentX: String = "x"

        private const val argumentY: String = "y"
    }

    private var currentActivity: Activity? = null

    override fun onAttachedToEngine(flutterPluginBinding: FlutterPlugin.FlutterPluginBinding) {
        channel = MethodChannel(flutterPluginBinding.binaryMessenger, "flutter_godot")
        channel.setMethodCallHandler(this)
        context = flutterPluginBinding.applicationContext
        textureRegistry = flutterPluginBinding.textureRegistry
    }

    override fun onMethodCall(
        call: MethodCall,
        result: Result
    ) {
        when (call.method) {
            "getPlatformVersion" -> result.success("Android ${Build.VERSION.RELEASE}")
            nativeInit -> {
                initGodot(call, result)
            }

            nativeStart -> {
                result.success(true)
            }

            nativeStop -> {
                result.success(true)
            }

            nativePause -> {
                result.success(true)
            }

            nativeRelease -> {
                val id = call.argument<Number>(argumentTextureId)?.toLong()?.toString()
                if (id != null && playerMap.containsKey(id)) onDestroy()
                result.success(null)
            }

            nativeSendPlatformEventMsg -> {
                sendPlatformEventMsg(call, result)
            }

            nativeSendTap -> {
                val arguments = call.arguments<Map<String, Any>>()
                val x = (arguments?.get(argumentX) as? Number)?.toFloat()
                val y = (arguments?.get(argumentY) as? Number)?.toFloat()
                val textureId = (arguments?.get(argumentTextureId) as? Number)?.toLong()
                if (x == null || y == null || textureId == null ||
                    !x.isFinite() || !y.isFinite()) {
                    result.error("invalid_arguments", "sendTap requires numeric x, y and textureId", null)
                    return
                }
                if (playerMap.containsKey(textureId.toString())) {
                    val player = playerMap[textureId.toString()]
                    player?.sendTap(x, y)
                }
                result.success(playerMap.containsKey(textureId.toString()))
            }

            else -> result.notImplemented()
        }
    }

    private fun sendPlatformEventMsg(call: MethodCall, result: Result) {
        val msg = call.argument<String>(argumentPlatformEventMsg)
        if (msg == null) {
            result.error("invalid_arguments", "platformEventMsg must be a string", null)
            return
        }
        if (playerMap.isEmpty()) {
            result.success(false)
            return
        }
        FlutterGodotHost.getInstance().sendPlatformEventMsg(msg)
        result.success(true)
    }


    override fun onDetachedFromEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        onDestroy()
        channel.setMethodCallHandler(null)
    }

    private fun initGodot(call: MethodCall, result: Result) {
        val width = call.argument<Number>(argumentGameWidth)?.toInt()
        val height = call.argument<Number>(argumentGameHeight)?.toInt()
        if (width == null || height == null || width <= 0 || height <= 0) {
            result.error("invalid_arguments", "Positive gameWidth and gameHeight are required", null)
            return
        }
        if (currentActivity == null) {
            result.error("no_activity", "Godot requires an attached Activity", null)
            return
        }
        if (playerMap.isNotEmpty() || sessionReleased) {
            result.error("godot_session", "Only one Godot session per process is supported", null)
            return
        }
        var producer: SurfaceProducer? = null
        try {
            producer = textureRegistry.createSurfaceProducer()
            producer.setSize(width, height)
            val textureId = producer.id()
            val player = FlutterGodotPlayer(textureId, producer.surface, width, height)
            surfaceProducerMap[textureId.toString()] = producer
            playerMap[textureId.toString()] = player
            player.start()
            result.success(mapOf(argumentTextureId to textureId))
        } catch (e: Exception) {
            producer?.release()
            surfaceProducerMap.clear()
            playerMap.clear()
            result.error("godot_init_failed", e.message, null)
        }
    }

    private var sessionReleased = false

    private fun onDestroy() {
        if (playerMap.isEmpty()) return
        sessionReleased = true
        // Stop drawing and destroy EGL on the render thread before releasing the producer.
        val producers = surfaceProducerMap.values.toList()
        val players = playerMap.values.toList()
        surfaceProducerMap.clear()
        playerMap.clear()
        players.forEach { GodotRenderHandler.getInstance().sendDestroyMsg(it) }
        GodotRenderHandler.getInstance().queueEvent {
            android.os.Handler(android.os.Looper.getMainLooper()).post {
                producers.forEach { it.release() }
            }
        }
    }

    override fun onAttachedToActivity(binding: ActivityPluginBinding) {
        val activity = binding.activity
        currentActivity = activity

        val rootView = currentActivity?.window?.decorView?.findViewById<View>(android.R.id.content)
        // 设置光标
        rootView?.pointerIcon = PointerIcon.getSystemIcon(context, PointerIcon.TYPE_DEFAULT)

        // 注册生命周期监听
        activity.application.registerActivityLifecycleCallbacks(this)
        FlutterGodotHost.getInstance().init(activity)
        GodotRenderHandler.getInstance().sendInitMsg(context)
        Log.d(TAG, "onAttachedToActivity")
    }

    override fun onDetachedFromActivityForConfigChanges() {
        currentActivity?.application?.unregisterActivityLifecycleCallbacks(this)
        currentActivity = null
        Log.d(TAG, "onDetachedFromActivityForConfigChanges")
    }

    override fun onReattachedToActivityForConfigChanges(binding: ActivityPluginBinding) {
        onAttachedToActivity(binding)
        Log.d(TAG, "onReattachedToActivityForConfigChanges")
    }

    override fun onDetachedFromActivity() {
        onDestroy()
        currentActivity?.application?.unregisterActivityLifecycleCallbacks(this)
        currentActivity = null
        Log.d(TAG, "onDetachedFromActivity")
    }

    // Activity 生命周期回调
    override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) {
        if (activity == currentActivity) {
            Log.d(TAG, "Activity onActivityCreated")
            FlutterGodotHost.getInstance().onActivityCreate()
        }
    }

    override fun onActivityStarted(activity: Activity) {
        if (activity == currentActivity) {
            Log.d(TAG, "Activity onActivityStarted")
            FlutterGodotHost.getInstance().onActivityStart()
        }
    }

    override fun onActivityResumed(activity: Activity) {
        if (activity == currentActivity) {
            Log.d(TAG, "Activity onActivityResumed")
            FlutterGodotHost.getInstance().onActivityResume()
        }
    }

    override fun onActivityPaused(activity: Activity) {
        if (activity == currentActivity) {
            Log.d(TAG, "Activity onActivityPaused")
            FlutterGodotHost.getInstance().onActivityPause()
        }
    }

    override fun onActivityStopped(activity: Activity) {
        if (activity == currentActivity) {
            Log.d(TAG, "Activity onActivityStopped")
            FlutterGodotHost.getInstance().onActivityStop()
        }
    }

    override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) {
        // 不需要处理
    }

    override fun onActivityDestroyed(activity: Activity) {
        if (activity == currentActivity) {
            Log.d(TAG, "Activity onActivityDestroyed")
            FlutterGodotHost.getInstance().onActivityDestroy()
        }
    }
}
