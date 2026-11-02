plugins {
    id("com.android.application")
    // Flutter Gradle 插件必须在 Android 和 Kotlin Gradle 插件之后应用。
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "me.shiki.flutter_godot_example"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // 待办：设置应用自己的唯一应用 ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "me.shiki.flutter_godot_example"
        // 可按应用需求调整以下配置。
        // 更多信息参见： https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        // 使用 pubspec.yaml 中的版本号；按 ABI 拆分 APK 时，Flutter 会自动加上
        // 1000 * ABI_VERSION。 (https://developer.android.com/studio/build/configure-apk-splits#configure-APK-versions)
        // 构建时指定 -P force-version-code-ignoring-abi=true，
        // 可强制使用 versionCode 的值。
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    androidResources {
        ignoreAssetsPattern = "!.svn:!.git:!.gitignore:!.ds_store:!*.scc:<dir>_*:!CVS:!thumbs.db:!picasa.ini:!*~"
    }

    buildTypes {
        release {
            // 待办：为发布构建配置自己的签名。
            // 当前使用调试密钥签名，以便运行 flutter run --release。
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
