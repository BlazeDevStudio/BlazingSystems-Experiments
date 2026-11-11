package com.blazesystems.threadharbor

import android.annotation.SuppressLint
import android.app.DownloadManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.graphics.Bitmap
import android.webkit.WebResourceError
import android.os.Message
import android.webkit.CookieManager
import android.webkit.URLUtil
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import org.json.JSONArray
import java.net.URLEncoder

private class BrowserTab(val view: WebView, val id: Int) {
    var address by mutableStateOf("about:blank")
    var title by mutableStateOf("New tab")
    var error by mutableStateOf<String?>(null)
}

private fun normalizeAddress(value: String): String {
    val input = value.trim()
    return when {
        input.isBlank() -> "about:blank"
        input.startsWith("https://", true) || input.startsWith("http://", true) -> input
        !input.contains(" ") && (input.contains(".") || input.startsWith("localhost")) ->
            "https://$input"
        else -> "https://www.google.com/search?q=" + URLEncoder.encode(input, "UTF-8")
    }
}

private fun readStoredUrls(raw: String?, maximum: Int, allowBlank: Boolean = false): List<String> = try {
    val values = JSONArray(raw ?: "[]")
    (0 until minOf(values.length(), maximum)).mapNotNull { index ->
        values.optString(index).takeIf {
            (it.startsWith("https://") || it.startsWith("http://") || (allowBlank && it == "about:blank")) && it.length <= 4096
        }
    }
} catch (_: Exception) { emptyList() }

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun BrowserScreen(context: Context, visible: Boolean = true) {
    val preferences = remember { context.getSharedPreferences("browser_v2", Context.MODE_PRIVATE) }
    var upload by remember { mutableStateOf<ValueCallback<Array<Uri>>?>(null) }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        upload?.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data))
        upload = null
    }
    val tabs = remember { mutableStateListOf<BrowserTab>() }
    var selected by remember { mutableIntStateOf(preferences.getInt("selected", 0)) }
    var counter by remember { mutableIntStateOf(0) }
    var status by remember { mutableStateOf<String?>(null) }
    var reader by remember { mutableStateOf<ReaderSnapshot?>(null) }
    val bookmarks = remember {
        mutableStateListOf<String>().apply {
            addAll(readStoredUrls(preferences.getString("bookmarks", null), 100))
        }
    }
    val history = remember {
        mutableStateListOf<String>().apply {
            addAll(readStoredUrls(preferences.getString("history", null), 200))
        }
    }
    var bookmarksExpanded by remember { mutableStateOf(false) }
    var historyExpanded by remember { mutableStateOf(false) }
    var toolsExpanded by remember { mutableStateOf(false) }

    fun saveUrls() {
        fun encode(values: List<String>) = JSONArray().apply { values.forEach { put(it) } }.toString()
        preferences.edit().putString("bookmarks", encode(bookmarks))
            .putString("history", encode(history)).apply()
    }

    fun saveSession() {
        val urls = JSONArray().apply {
            tabs.forEach { tab ->
                if (tab.address.startsWith("https://") || tab.address.startsWith("http://")) {
                    put(tab.address)
                } else {
                    put("about:blank")
                }
            }
        }
        preferences.edit().putString("tabs", urls.toString())
            .putInt("selected", selected).apply()
    }

    fun recordHistory(url: String) {
        if (!url.startsWith("https://") && !url.startsWith("http://")) return
        history.remove(url)
        history.add(0, url)
        while (history.size > 200) history.removeAt(history.lastIndex)
        saveUrls()
    }

    fun openExternal(url: String): Boolean = try {
        val parsed = Uri.parse(url)
        val scheme = parsed.scheme?.lowercase()
        if (scheme !in setOf("https", "http", "mailto", "tel", "geo", "market")) {
            status = "Blocked an unsupported external link"
            false
        } else {
            context.startActivity(Intent(Intent.ACTION_VIEW, parsed)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            true
        }
    } catch (_: Exception) {
        status = "No app available to open that link"
        false
    }

    fun enqueueDownload(url: String, agent: String?, disposition: String?, mime: String?) {
        if (!url.startsWith("https://") && !url.startsWith("http://")) {
            status = "Only HTTP(S) downloads are supported"
            return
        }
        try {
            val request = DownloadManager.Request(Uri.parse(url))
                .setTitle(URLUtil.guessFileName(url, disposition, mime))
                .setDescription(Uri.parse(url).host ?: "Website download")
                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            if (!mime.isNullOrBlank()) request.setMimeType(mime)
            // Deliberately do NOT forward WebView cookies to DownloadManager.
            // Its redirect behavior is not enforced by our code: an HTTP redirect
            // could otherwise carry a session cookie to a different host.
            // Authenticated transfers require a future redirect-aware engine.
            agent?.takeIf { it.isNotBlank() }?.let { request.addRequestHeader("User-Agent", it) }
            val id = (context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager).enqueue(request)
            val pref = context.getSharedPreferences("downloads", Context.MODE_PRIVATE)
            val ids = pref.getString("ids", "").orEmpty().split(",")
                .filter { it.toLongOrNull() != null }.takeLast(99)
            pref.edit().putString("ids", (ids + id.toString()).joinToString(",")).apply()
            status = "Download queued — see Downloads"
        } catch (_: Exception) {
            status = "Download could not be started; use External browser"
        }
    }

    fun newTab(initial: String, loadInitial: Boolean = true): BrowserTab {
        val web = WebView(context)
        val tab = BrowserTab(web, counter++)
        tab.address = initial
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.allowFileAccess = false
        web.settings.allowContentAccess = true
        web.settings.setSupportMultipleWindows(true)
        web.settings.javaScriptCanOpenWindowsAutomatically = false
        web.settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW
        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, false)
        web.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView, url: String, favicon: Bitmap?) {
                tab.error = null
                tab.address = url
            }
            override fun onReceivedError(
                view: WebView, request: WebResourceRequest, error: WebResourceError
            ) {
                if (request.isForMainFrame) {
                    tab.error = error.description?.toString()?.take(200) ?: "Network error"
                }
            }
            override fun onPageFinished(view: WebView, url: String) {
                tab.address = url
                if (tab.error == null) recordHistory(url)
                saveSession()
            }
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val scheme = request.url.scheme?.lowercase()
                if (scheme == "http" || scheme == "https" || scheme == "about") return false
                if (request.isForMainFrame) openExternal(request.url.toString())
                return true
            }
        }
        web.webChromeClient = object : WebChromeClient() {
            override fun onReceivedTitle(view: WebView?, title: String?) {
                tab.title = title?.take(25)?.ifBlank { "New tab" } ?: "New tab"
            }
            override fun onShowFileChooser(view: WebView?, cb: ValueCallback<Array<Uri>>,
                                           params: FileChooserParams): Boolean {
                upload?.onReceiveValue(null)
                upload = cb
                return try {
                    picker.launch(params.createIntent())
                    true
                } catch (_: Exception) {
                    upload?.onReceiveValue(null)
                    upload = null
                    false
                }
            }
            override fun onCreateWindow(view: WebView?, isDialog: Boolean,
                                        isUserGesture: Boolean, resultMsg: Message?): Boolean {
                if (!isUserGesture || tabs.size >= 12 || resultMsg == null) return false
                val transport = resultMsg.obj as? WebView.WebViewTransport ?: return false
                val child = newTab("about:blank", loadInitial = false)
                tabs.add(child)
                selected = tabs.lastIndex
                transport.webView = child.view
                resultMsg.sendToTarget()
                saveSession()
                return true
            }
        }
        web.setDownloadListener { url, agent, disposition, mime, _ ->
            enqueueDownload(url, agent, disposition, mime)
        }
        if (loadInitial) web.loadUrl(initial)
        return tab
    }

    if (tabs.isEmpty()) {
        val restored = readStoredUrls(preferences.getString("tabs", null), 12, allowBlank = true)
            .ifEmpty { listOf("about:blank") }
        restored.forEach { tabs.add(newTab(it)) }
        selected = selected.coerceIn(0, tabs.lastIndex)
    }

    val active = tabs.getOrNull(selected) ?: tabs.first()
    var address by remember(active.id) { mutableStateOf(active.address) }
    LaunchedEffect(active.id, active.address) { address = active.address }
    LaunchedEffect(tabs.size, selected) { saveSession() }
    BackHandler(enabled = visible && reader != null) { reader = null }
    BackHandler(enabled = visible && reader == null && active.view.canGoBack()) { active.view.goBack() }

    if (reader != null) {
        NativeReaderScreen(reader!!) { reader = null }
    } else Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        Text("Tabs: ${tabs.size}", style = MaterialTheme.typography.labelSmall,
            modifier = Modifier.padding(horizontal = 8.dp))
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            tabs.forEachIndexed { index, tab ->
                TextButton(onClick = { selected = index }) {
                    Text((if (index == selected) "● " else "") + tab.title, maxLines = 1)
                }
            }
            TextButton(enabled = tabs.size < 12, onClick = {
                tabs.add(newTab("about:blank"))
                selected = tabs.lastIndex
            }) { Text("+ Tab") }
            TextButton(enabled = tabs.size > 1, onClick = {
                // An Android WebView must be detached before destruction.
                (active.view.parent as? android.view.ViewGroup)?.removeView(active.view)
                active.view.stopLoading()
                active.view.destroy()
                tabs.removeAt(selected)
                selected = selected.coerceAtMost(tabs.lastIndex)
                saveSession()
            }) { Text("Close") }
        }
        Row {
            TextField(
                value = address, onValueChange = { address = it }, singleLine = true,
                modifier = Modifier.weight(1f),
                placeholder = { Text("Website or search") }
            )
            Button(onClick = { active.view.loadUrl(normalizeAddress(address)) }) { Text("Go") }
        }
        Row(
            modifier = Modifier.fillMaxWidth().heightIn(min = 44.dp),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            TextButton(onClick = { if (active.view.canGoBack()) active.view.goBack() }) { Text("Back") }
            TextButton(onClick = { if (active.view.canGoForward()) active.view.goForward() }) { Text("Next") }
            TextButton(onClick = { active.view.reload() }) { Text("Reload") }
            Box {
                TextButton(onClick = { toolsExpanded = true }) { Text("More") }
                DropdownMenu(expanded = toolsExpanded, onDismissRequest = { toolsExpanded = false }) {
                    DropdownMenuItem(text = { Text("Home") }, onClick = {
                        toolsExpanded = false
                        active.view.loadUrl("about:blank")
                    })
                    val saved = bookmarks.contains(active.address)
                    DropdownMenuItem(text = {
                        Text(if (saved) "Remove bookmark" else "Bookmark this page")
                    }, onClick = {
                        toolsExpanded = false
                        if (saved) bookmarks.remove(active.address)
                        else if (active.address.startsWith("https://") || active.address.startsWith("http://")) {
                            bookmarks.add(0, active.address)
                            while (bookmarks.size > 100) bookmarks.removeAt(bookmarks.lastIndex)
                        }
                        saveUrls()
                    })
                    DropdownMenuItem(text = { Text("Bookmarks") }, onClick = {
                        toolsExpanded = false
                        bookmarksExpanded = true
                    })
                    DropdownMenuItem(text = { Text("History") }, onClick = {
                        toolsExpanded = false
                        historyExpanded = true
                    })
                    DropdownMenuItem(text = { Text("Native Reader") }, onClick = {
                        toolsExpanded = false
                        if (active.error != null) {
                            status = "Cannot interpret a page that failed to load"
                        } else {
                            interpretVisiblePage(active.view) { snapshot ->
                                if (snapshot == null) status = "This page cannot be interpreted in native reading mode"
                                else reader = snapshot
                            }
                        }
                    })
                    DropdownMenuItem(text = { Text("Open externally") }, onClick = {
                        toolsExpanded = false
                        openExternal(active.address)
                    })
                }
                DropdownMenu(expanded = bookmarksExpanded, onDismissRequest = { bookmarksExpanded = false }) {
                    if (bookmarks.isEmpty()) DropdownMenuItem(
                        text = { Text("No saved bookmarks") },
                        onClick = { bookmarksExpanded = false }
                    )
                    bookmarks.take(40).forEach { url ->
                        DropdownMenuItem(text = { Text(url, maxLines = 1) }, onClick = {
                            active.view.loadUrl(url)
                            bookmarksExpanded = false
                        })
                    }
                }
                DropdownMenu(expanded = historyExpanded, onDismissRequest = { historyExpanded = false }) {
                    if (history.isEmpty()) DropdownMenuItem(
                        text = { Text("History is empty") }, onClick = { historyExpanded = false }
                    )
                    history.take(40).forEach { url ->
                        DropdownMenuItem(text = { Text(url, maxLines = 1) }, onClick = {
                            active.view.loadUrl(url)
                            historyExpanded = false
                        })
                    }
                    DropdownMenuItem(text = { Text("Clear URL history") }, onClick = {
                        history.clear()
                        saveUrls()
                        historyExpanded = false
                    })
                }
            }
        }
        status?.let { Text(it, style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.padding(horizontal = 8.dp)) }
        if (active.address == "about:blank") {
            Column(Modifier.fillMaxWidth().weight(1f).padding(20.dp)) {
                Text("Blaze ThreadHarbor", color = MaterialTheme.colorScheme.onBackground,
                    style = MaterialTheme.typography.headlineMedium)
                Spacer(Modifier.height(8.dp))
                Text("Start browsing", color = MaterialTheme.colorScheme.onBackground,
                    style = MaterialTheme.typography.titleMedium)
                Text("Type a website address or a search above. This start page works without an internet connection.",
                    color = MaterialTheme.colorScheme.onBackground)
                Spacer(Modifier.height(24.dp))
                Text("Saved sites", color = MaterialTheme.colorScheme.onBackground,
                    style = MaterialTheme.typography.titleMedium)
                if (bookmarks.isEmpty()) Text("No bookmarks yet.",
                    color = MaterialTheme.colorScheme.onBackground)
                bookmarks.take(8).forEach { url ->
                    TextButton(onClick = { active.view.loadUrl(url) }) {
                        Text(url, maxLines = 1)
                    }
                }
            }
        } else if (active.error != null) {
            Column(Modifier.fillMaxWidth().weight(1f).padding(20.dp)) {
                Text("Cannot open this webpage", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(8.dp))
                Text(active.address, maxLines = 2)
                Text(active.error ?: "Network error")
                Spacer(Modifier.height(12.dp))
                Row {
                    Button(onClick = { active.view.reload() }) { Text("Retry") }
                    TextButton(onClick = { openExternal(active.address) }) { Text("Open externally") }
                }
                Text("Check your connection or try another address.")
            }
        } else key(active.id) {
            AndroidView(factory = {
                (active.view.parent as? android.view.ViewGroup)?.removeView(active.view)
                active.view
            }, modifier = Modifier.fillMaxWidth().weight(1f))
        }
    }
    DisposableEffect(Unit) {
        onDispose {
            saveSession()
            upload?.onReceiveValue(null)
            tabs.forEach { tab ->
                (tab.view.parent as? android.view.ViewGroup)?.removeView(tab.view)
                tab.view.stopLoading()
                tab.view.destroy()
            }
            tabs.clear()
        }
    }
}
