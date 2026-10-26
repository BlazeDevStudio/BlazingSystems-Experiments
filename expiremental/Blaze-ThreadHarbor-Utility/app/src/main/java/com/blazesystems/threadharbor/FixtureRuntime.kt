package com.blazesystems.threadharbor

import android.annotation.SuppressLint
import android.content.Context
import android.net.Uri
import android.view.View
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import org.json.JSONObject
import java.util.UUID

data class ObservedMessage(val id: String, val sender: String, val text: String)
data class PendingAction(val id: String, val text: String, val status: String)

/** Dedicated app-owned fixture. The third-party browser NEVER gets a JavaScript bridge. */
class FixtureRuntime(context: Context) {
    private val origin = "https://appassets.androidplatform.net"
    private val fixtureUrl = "$origin/assets/fixture.html"
    private val loader = WebViewAssetLoader.Builder()
        .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(context)).build()
    val messages = mutableStateListOf<ObservedMessage>()
    val pending = mutableStateListOf<PendingAction>()
    var status by mutableStateOf("Starting")
        private set
    var supported by mutableStateOf(false)
        private set

    @SuppressLint("SetJavaScriptEnabled")
    val webView = WebView(context).apply {
        // The diagnostics-only hidden page must not steal IME or accessibility focus.
        isFocusable = false
        isFocusableInTouchMode = false
        importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = false
        settings.allowFileAccess = false
        settings.allowContentAccess = false
        webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? =
                loader.shouldInterceptRequest(request.url)
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean =
                request.url.toString() != fixtureUrl
            override fun onPageFinished(view: WebView, url: String) {
                view.clearFocus()
                status = if (url == fixtureUrl) "Fixture loaded" else "Fixture navigation blocked"
            }
        }
        if (WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
            WebViewCompat.addWebMessageListener(this, "HarborBridge", setOf(origin)) {
                _, message, sourceOrigin, isMainFrame, _ ->
                if (!isMainFrame || sourceOrigin != Uri.parse(origin)) return@addWebMessageListener
                val raw = message.data ?: return@addWebMessageListener
                if (raw.length > 131072) {
                    status = "Rejected oversized bridge payload"
                    return@addWebMessageListener
                }
                try {
                    val data = JSONObject(raw)
                    if (data.optString("type") != "snapshot" || data.optString("adapter") != "fixture-v1") {
                        return@addWebMessageListener
                    }
                    val array = data.optJSONArray("messages") ?: return@addWebMessageListener
                    if (array.length() > 200) {
                        status = "Rejected oversized message list"
                        return@addWebMessageListener
                    }
                    val next = mutableListOf<ObservedMessage>()
                    for (i in 0 until array.length()) {
                        val item = array.getJSONObject(i)
                        val id = item.optString("id").take(100)
                        if (id.isNotBlank()) next.add(ObservedMessage(
                            id, item.optString("sender").take(100), item.optString("text").take(4096)))
                    }
                    messages.clear()
                    messages.addAll(next)
                    for (i in pending.indices) {
                        val action = pending[i]
                        if (next.any { it.id == action.id && it.sender == "You" && it.text == action.text }) {
                            pending[i] = action.copy(status = "OBSERVED_IN_FIXTURE")
                        }
                    }
                    status = "Observed " + next.size + " fixture messages"
                } catch (_: Exception) {
                    status = "Rejected malformed bridge payload"
                }
            }
            supported = true
        } else status = "WebMessageListener unsupported on this device"
        loadUrl(fixtureUrl)
    }

    fun send(text: String) {
        if (!supported || text.isBlank() || text.length > 4096) return
        if (webView.url != fixtureUrl) { status = "Action blocked: wrong page"; return }
        val id = UUID.randomUUID().toString()
        pending.add(PendingAction(id, text, "UNVERIFIED"))
        val action = JSONObject().put("action", "send").put("id", id).put("text", text)
        webView.evaluateJavascript(
            "window.harborAction && window.harborAction(" + JSONObject.quote(action.toString()) + ")", null)
        // Unknown submissions are NOT retried. A click is NOT proof of delivery.
    }
    fun close() { webView.destroy() }
}
