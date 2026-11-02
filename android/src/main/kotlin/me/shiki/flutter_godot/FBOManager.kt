package me.shiki.flutter_godot

import android.opengl.GLES30
import android.util.Log

/***
 * CreateBy: shiki
 * CreateDate: 2025-10-23
 * Description: [文件描述说明]
 ***/


class FBOManager(private val width: Int, private val height: Int) {
    private var fboId = 0
    private var colorTextureId = 0
    private var depthRenderBufferId = 0

    companion object {
        private const val TAG = "FBOManager"
    }

    fun init(): Boolean {
        try {
            // 创建纹理
            val textures = IntArray(1)
            GLES30.glGenTextures(1, textures, 0)
            colorTextureId = textures[0]

            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, colorTextureId)
            GLES30.glTexImage2D(
                GLES30.GL_TEXTURE_2D, 0, GLES30.GL_RGBA,
                width, height, 0,
                GLES30.GL_RGBA, GLES30.GL_UNSIGNED_BYTE, null
            )
            GLES30.glTexParameteri(
                GLES30.GL_TEXTURE_2D,
                GLES30.GL_TEXTURE_MIN_FILTER,
                GLES30.GL_LINEAR
            )
            GLES30.glTexParameteri(
                GLES30.GL_TEXTURE_2D,
                GLES30.GL_TEXTURE_MAG_FILTER,
                GLES30.GL_LINEAR
            )
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)

            // 创建 Depth Render Buffer
            val renderBuffers = IntArray(1)
            GLES30.glGenRenderbuffers(1, renderBuffers, 0)
            depthRenderBufferId = renderBuffers[0]

            GLES30.glBindRenderbuffer(GLES30.GL_RENDERBUFFER, depthRenderBufferId)
            GLES30.glRenderbufferStorage(
                GLES30.GL_RENDERBUFFER,
                GLES30.GL_DEPTH_COMPONENT16,
                width, height
            )
            GLES30.glBindRenderbuffer(GLES30.GL_RENDERBUFFER, 0)

            // 创建 FBO
            val fbos = IntArray(1)
            GLES30.glGenFramebuffers(1, fbos, 0)
            fboId = fbos[0]

            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, fboId)
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D,
                colorTextureId, 0
            )
            GLES30.glFramebufferRenderbuffer(
                GLES30.GL_FRAMEBUFFER,
                GLES30.GL_DEPTH_ATTACHMENT,
                GLES30.GL_RENDERBUFFER,
                depthRenderBufferId
            )

            val status = GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER)
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)

            if (status != GLES30.GL_FRAMEBUFFER_COMPLETE) {
                Log.e(TAG, "Framebuffer not complete: $status")
                return false
            }

            Log.d(TAG, "FBO created successfully: $fboId, texture: $colorTextureId")
            return true
        } catch (e: Exception) {
            Log.e(TAG, "FBO init error: ${e.message}")
            return false
        }
    }

    fun bind() {
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, fboId)
        GLES30.glViewport(0, 0, width, height)
    }

    fun unbind() {
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
    }

    fun getColorTextureId(): Int = colorTextureId

    fun release() {
        if (colorTextureId != 0) {
            GLES30.glDeleteTextures(1, intArrayOf(colorTextureId), 0)
        }
        if (depthRenderBufferId != 0) {
            GLES30.glDeleteRenderbuffers(1, intArrayOf(depthRenderBufferId), 0)
        }
        if (fboId != 0) {
            GLES30.glDeleteFramebuffers(1, intArrayOf(fboId), 0)
        }
    }
}