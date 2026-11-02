package me.shiki.flutter_godot

import java.io.InputStream
import java.nio.charset.StandardCharsets
import java.util.ArrayList

/***
 * 作者： shiki
 * 创建日期： 2025-10-20
 * 说明： [文件描述说明]
 ***/


object GodotCommandLineFileParser {
    fun parseCommandLine(inputStream: InputStream): MutableList<String> {
        return try {
            val headerBytes = ByteArray(4)
            var argBytes = inputStream.read(headerBytes)
            if (argBytes < 4) {
                return mutableListOf()
            }
            val argc = decodeHeaderIntValue(headerBytes)

            val cmdline = ArrayList<String>(argc)
            for (i in 0 until argc) {
                argBytes = inputStream.read(headerBytes)
                if (argBytes < 4) {
                    return mutableListOf()
                }
                val strlen = decodeHeaderIntValue(headerBytes)

                if (strlen > 65535) {
                    return mutableListOf()
                }

                val arg = ByteArray(strlen)
                argBytes = inputStream.read(arg)
                if (argBytes == strlen) {
                    cmdline.add(String(arg, StandardCharsets.UTF_8))
                }
            }
            cmdline
        } catch (e: Exception) {
            // 允许缺少 _cl_ 命令行参数文件，不影响默认启动。
            mutableListOf()
        }
    }

    private fun decodeHeaderIntValue(headerBytes: ByteArray): Int =
        (headerBytes[3].toInt() and 0xFF) shl 24 or
                ((headerBytes[2].toInt() and 0xFF) shl 16) or
                ((headerBytes[1].toInt() and 0xFF) shl 8) or
                (headerBytes[0].toInt() and 0xFF)
}