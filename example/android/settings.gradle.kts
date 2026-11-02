pluginManagement {
    val flutterSdkPath =
        run {
            val properties = java.util.Properties()
            file("local.properties").inputStream().use { properties.load(it) }
            val flutterSdkPath = properties.getProperty("flutter.sdk")
            require(flutterSdkPath != null) { "flutter.sdk not set in local.properties" }
            flutterSdkPath
        }

    includeBuild("$flutterSdkPath/packages/flutter_tools/gradle")

    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

plugins {
    id("dev.flutter.flutter-plugin-loader") version "1.0.0"
    id("com.android.application") version "9.1.0" apply false
    id("org.jetbrains.kotlin.android") version "2.4.0" apply false
}

include(":app")

// Per-variant Godot game and engine AAR modules.
val godotRoot = file("../../android/godot")
include(":godot_game_lib_debug", ":godot_game_lib_release", ":godot_lib_debug", ":godot_lib_release")
project(":godot_game_lib_debug").projectDir = File(godotRoot, "debug/godot_game_lib")
project(":godot_game_lib_release").projectDir = File(godotRoot, "release/godot_game_lib")
project(":godot_lib_debug").projectDir = File(godotRoot, "debug/godot_lib")
project(":godot_lib_release").projectDir = File(godotRoot, "release/godot_lib")

// Use the shared wrapper even when exported directories have no build.gradle.
listOf(":godot_game_lib_debug", ":godot_game_lib_release", ":godot_lib_debug", ":godot_lib_release").forEach {
    project(it).buildFileName = "../../../godot_aar.gradle"
}
