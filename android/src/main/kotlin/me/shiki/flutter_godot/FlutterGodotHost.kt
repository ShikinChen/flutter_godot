package me.shiki.flutter_godot

import android.app.Activity
import android.os.SystemClock
import android.util.Log
import android.view.MotionEvent
import androidx.lifecycle.LifecycleObserver
import org.godotengine.godot.Godot
import org.godotengine.godot.GodotHost
import org.godotengine.godot.input.GodotInputHandler

/***
 * 作者： shiki
 * 创建日期： 2025-10-20
 * 说明： [文件描述说明]
 ***/


class FlutterGodotHost : GodotHost, LifecycleObserver {

    companion object {

        private const val TAG = "FlutterGodotHost"

        // 单例实例
        @Volatile
        private var instance: FlutterGodotHost? = null

        // 获取单例的方法
        @JvmStatic
        fun getInstance(): FlutterGodotHost {
            return instance ?: synchronized(this) {
                instance ?: FlutterGodotHost().also {
                    instance = it
                }
            }
        }

    }

    private var activity: Activity? = null

    private var usesVulkan: Boolean? = null

    var mainGodot: Godot? = null
        private set

    var isInited = false
        private set

    var godotInputHandler: GodotInputHandler? = null
        private set

    var androidEventPlugin: AndroidEventPlugin? = null
        private set

    fun init(activity: Activity) {
        this.activity = activity
        if (isInited) return
        if (mainGodot == null) {
            mainGodot = Godot.getInstance(activity.applicationContext)
            // 通过反射获取 inputHandler
            godotInputHandler = getInputHandler()
            mainGodot?.renderView = FlutterGodotRenderView(godotInputHandler)
            androidEventPlugin = AndroidEventPlugin(mainGodot!!)
        }
        isInited = true
    }

    override fun getActivity(): Activity? {
        return activity
    }

    override fun getGodot(): Godot? {
        return mainGodot
    }

    fun onActivityCreate() {
        Log.d(TAG, "Activity onCreate")
    }

    fun onActivityStart() {
        Log.d(TAG, "Activity onStart")
    }

    fun onActivityResume() {
        Log.d(TAG, "Activity onResume")
    }

    fun onActivityPause() {
        Log.d(TAG, "Activity onPause")
    }

    fun onActivityStop() {
        Log.d(TAG, "Activity onStop")
    }

    fun onActivityDestroy() {
        Log.d(TAG, "Activity onDestroy")
    }

    private fun getInputHandler(): GodotInputHandler? {
        try {
            if (mainGodot != null) {
                val field = Godot::class.java.getDeclaredField("godotInputHandler")
                field.isAccessible = true
                val handler = field.get(mainGodot)
                Log.d(TAG, "Successfully got inputHandler: ${handler?.javaClass?.simpleName}")
                return handler as GodotInputHandler
            }
            return null
        } catch (e: NoSuchFieldException) {
            Log.e(TAG, "inputHandler field not found, trying alternative names...", e)
            // 尝试其他可能的字段名
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get inputHandler via reflection", e)
        }
        return null
    }

    fun usesVulkan(): Boolean {
        try {
            if (usesVulkan == null) {
                usesVulkan = try {
                    val method = Godot::class.java.getDeclaredMethod("usesVulkan")
                    method.isAccessible = true
                    val isStatic = java.lang.reflect.Modifier.isStatic(method.modifiers)
                    val result: Boolean? = if (isStatic) {
                        method.invoke(null) as? Boolean
                    } else {
                        val target = mainGodot
                        if (target == null) {
                            Log.w(TAG, "usesVulkan called but Godot instance is null")
                            return false
                        }
                        method.invoke(target) as? Boolean
                    }
                    Log.d(TAG, "usesVulkan via reflection: $result")
                    result ?: false
                } catch (e: NoSuchMethodException) {
                    Log.e(TAG, "usesVulkan() method not found on Godot", e)
                    false
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to invoke usesVulkan() via reflection", e)
                    false
                }
            }
        } catch (e: NoSuchFieldException) {
            Log.e(TAG, "inputHandler field not found, trying alternative names...", e)
            // 尝试其他可能的字段名
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get inputHandler via reflection", e)
        }
        return usesVulkan ?: false
    }

    fun sendTap(x: Float, y: Float) {
        Log.d(TAG, "sendTap: $x, $y")
        godotInputHandler?.let {
            val now = SystemClock.uptimeMillis()
            val down = MotionEvent.obtain(now, now, MotionEvent.ACTION_DOWN, x, y, 0)
            val up = MotionEvent.obtain(now, now, MotionEvent.ACTION_UP, x, y, 0)
            try {
                it.onTouchEvent(down)
                it.onTouchEvent(up)
            } finally {
                down.recycle()
                up.recycle()
            }
        }

    }

    fun sendPlatformEventMsg(msg: String) {
        androidEventPlugin?.sendPlatformEventMsg(msg)
    }

    fun onMainResume() {
        godot?.onResume(this)
    }
}