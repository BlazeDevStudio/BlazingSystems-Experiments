package com.blazesystems.threadharbor

import android.annotation.SuppressLint
import android.app.DownloadManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.webkit.CookieManager
import android.webkit.URLUtil
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import java.net.URLEncoder

private class BrowserTab(val view: WebView, val id: Int) {
    var address by mutableStateOf("https://example.org")
    var title by mutableStateOf("Tab")
}
private fun normalizeAddress(value: String): String {
    val input = value.trim()
    return when {
        input.startsWith("https://") || input.startsWith("http://") -> input
        !input.contains(" ") && input.contains(".") -> "https://" + input
        else -> "https://www.google.com/search?q=" + URLEncoder.encode(input, "UTF-8")
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun BrowserScreen(context: Context) {
    var upload by remember { mutableStateOf<ValueCallback<Array<Uri>>?>(null) }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        upload?.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data))
        upload = null
    }
    val tabs = remember { mutableStateListOf<BrowserTab>() }
    var selected by remember { mutableIntStateOf(0) }
    var counter by remember { mutableIntStateOf(0) }
    fun newTab(): BrowserTab {
        val web = WebView(context)
        val tab = BrowserTab(web, counter++)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.allowFileAccess = false
        web.settings.allowContentAccess = true
        CookieManager.getInstance().setAcceptCookie(true)
        web.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView, url: String) { tab.address = url }
        }
        web.webChromeClient = object : WebChromeClient() {
            override fun onReceivedTitle(view: WebView?, title: String?) {
                tab.title = title?.take(20) ?: "Tab"
            }
            override fun onShowFileChooser(view: WebView?, cb: ValueCallback<Array<Uri>>,
                                           params: FileChooserParams): Boolean {
                upload?.onReceiveValue(null)
                upload = cb
                return try { picker.launch(params.createIntent()); true }
                catch (_: Exception) { upload?.onReceiveValue(null); upload = null; false }
            }
        }
        web.setDownloadListener { url, _, disposition, mime, _ ->
            if (!url.startsWith("https://") && !url.startsWith("http://")) return@setDownloadListener
            try {
                val request = DownloadManager.Request(Uri.parse(url))
                    .setTitle(URLUtil.guessFileName(url, disposition, mime))
                    .setMimeType(mime)
                    .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                val dm = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                val id = dm.enqueue(request)
                val pref = context.getSharedPreferences("downloads",Context.MODE_PRIVATE)
                val previous = pref.getString("ids","").orEmpty().split(",").filter{it.isNotBlank()}.takeLast(99)
                pref.edit().putString("ids",(previous + id.toString()).joinToString(",")).apply()
            } catch (_: Exception) { /* Leave original site download fallback available */ }
        }
        web.loadUrl("https://example.org")
        return tab
    }
    if(tabs.isEmpty()) tabs.add(newTab())
    val active = tabs.getOrNull(selected) ?: tabs.first()
    var address by remember(active.id) { mutableStateOf(active.address) }
    LaunchedEffect(active.address) { address = active.address }
    Column(Modifier.fillMaxSize()) {
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            tabs.forEachIndexed { i, tab ->
                TextButton(onClick={selected=i}){ Text((if(i==selected)"● " else "") + tab.title) }
            }
            TextButton(onClick={tabs.add(newTab());selected=tabs.lastIndex}){Text("+ Tab")}
            TextButton(onClick={
                if(tabs.size>1) { active.view.destroy(); tabs.removeAt(selected); selected=selected.coerceAtMost(tabs.lastIndex) }
            }){Text("Close")}
        }
        Row {
            OutlinedTextField(value=address,onValueChange={address=it},singleLine=true,
                modifier=Modifier.weight(1f),label={Text("Address / search")})
            Button(onClick={active.view.loadUrl(normalizeAddress(address))}){Text("Go")}
        }
        Row {
            TextButton(onClick={if(active.view.canGoBack())active.view.goBack()}){Text("Back")}
            TextButton(onClick={if(active.view.canGoForward())active.view.goForward()}){Text("Next")}
            TextButton(onClick={active.view.reload()}){Text("Reload")}
            TextButton(onClick={
                try {context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(active.address))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))}catch(_:Exception){}
            }){Text("External")}
        }
        key(active.id) {
            AndroidView(factory={
                (active.view.parent as? android.view.ViewGroup)?.removeView(active.view)
                active.view
            },modifier=Modifier.fillMaxWidth().weight(1f))
        }
    }
    DisposableEffect(Unit) {
        onDispose { upload?.onReceiveValue(null); tabs.forEach{it.view.destroy()}; tabs.clear() }
    }
}
