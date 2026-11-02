package me.shiki.flutter_godot

import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import org.mockito.Mockito
import kotlin.test.Test

/*
 * 此测试用于验证插件 Kotlin 实现的基本行为。
 *
 * 构建插件示例后，可在 example/android/ 目录执行
 * ./gradlew testDebugUnitTest，
 * 也可在 Android Studio 等支持 JUnit 的开发工具中直接运行。
 */

internal class FlutterGodotPluginTest {
    @Test
    fun onMethodCall_getPlatformVersion_returnsExpectedValue() {
        val plugin = FlutterGodotPlugin()

        val call = MethodCall("getPlatformVersion", null)
        val mockResult: MethodChannel.Result = Mockito.mock(MethodChannel.Result::class.java)
        plugin.onMethodCall(call, mockResult)

        Mockito.verify(mockResult).success("Android " + android.os.Build.VERSION.RELEASE)
    }
}
