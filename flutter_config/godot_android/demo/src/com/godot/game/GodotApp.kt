package com.godot.game

import android.graphics.Color
import android.os.Bundle
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import androidx.activity.enableEdgeToEdge
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.google.gson.Gson
import org.godotengine.godot.BuildConfig
import org.godotengine.godot.Godot
import org.godotengine.godot.GodotActivity
import org.godotengine.godot.game.lib.AndroidEventPlugin
import org.godotengine.godot.plugin.GodotPlugin

/***
 * 作者： shiki
 * 创建日期： 2025-10-27
 * 说明： [文件描述说明]
 ***/


class GodotApp : GodotActivity() {
    private lateinit var androidEventPlugin: AndroidEventPlugin

    private val gson by lazy { Gson() }

    private val updateWindowAppearance = Runnable {
        val godot = getGodot()
        if (godot != null) {
            godot.enableImmersiveMode(godot.isInImmersiveMode(), true)
            godot.enableEdgeToEdge(godot.isInEdgeToEdgeMode(), true)
            godot.setSystemBarsAppearance()
        }
    }

    public override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        this.enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        val contentView = findViewById<FrameLayout>(android.R.id.content)

        contentView.setBackgroundColor(Color.WHITE)

        val inflater = LayoutInflater.from(this)
        val buttonsLayout =
            inflater.inflate(R.layout.buttons_layout, contentView, false) as LinearLayout


        val params = FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT
        )
        params.gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
        params.bottomMargin = 32
        contentView.addView(buttonsLayout, params)

        val initBtn = buttonsLayout.findViewById<Button>(R.id.btn_init)
        initBtn.setOnClickListener {
            val msg = GodotTestEventMsg(type = "ToScene", data = mapOf("sceneName" to "page_a"))
            androidEventPlugin.sendPlatformEventMsg(gson.toJson(msg))
        }
    }

    public override fun onResume() {
        super.onResume()
        updateWindowAppearance.run()
    }

    override fun onGodotMainLoopStarted() {
        super.onGodotMainLoopStarted()
        runOnUiThread(updateWindowAppearance)
    }

    override fun getHostPlugins(engine: Godot): MutableSet<GodotPlugin> {
        val set = mutableSetOf<GodotPlugin>()
        androidEventPlugin = AndroidEventPlugin(engine)
        set.add(androidEventPlugin)
        return set
    }

    companion object {
        init {
            // .NET 运行时库。
            if (BuildConfig.FLAVOR == "mono") {
                try {
                    Log.v("GODOT", "Loading System.Security.Cryptography.Native.Android library")
                    System.loadLibrary("System.Security.Cryptography.Native.Android")
                } catch (e: UnsatisfiedLinkError) {
                    Log.e(
                        "GODOT",
                        "Unable to load System.Security.Cryptography.Native.Android library"
                    )
                }
            }
        }
    }
}
