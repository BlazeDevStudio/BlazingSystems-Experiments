package com.blazesystems.threadharbor

import android.webkit.WebView
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import org.json.JSONArray
import org.json.JSONObject

/** Local-only, user-invoked reading mode. Not a messaging adapter or site impersonation. */
data class ReaderSnapshot(
    val title: String,
    val url: String,
    val sections: List<String>
)

private val readerScript = """(function() {
  'use strict';
  var visible = [];
  var nodes = document.querySelectorAll('article h1, article h2, article h3, article p, main h1, main h2, main h3, main p, h1, h2, p');
  for (var i=0; i<nodes.length && visible.length<60; i++) {
    var element=nodes[i];
    if (element.closest('form, nav, footer, [contenteditable], [aria-hidden="true"], [hidden]')) continue;
    var style=window.getComputedStyle(element);
    if (style.display==='none' || style.visibility==='hidden') continue;
    var value=(element.innerText||'').trim().replace(/\s+/g,' ');
    if (value.length<16) continue;
    visible.push(value.slice(0,800));
  }
  return JSON.stringify({
    title:String(document.title||'Untitled').slice(0,200),
    url:String(location.href).slice(0,4096),
    sections:visible
  });
})()"""

/**
 * Reads only visible H1/H2/H3/P text when the user taps the action.
 * No input values, cookies, tokens, passwords, PINs or background observation.
 * Android's evaluateJavascript result contains an encoded JSON string.
 */
fun interpretVisiblePage(view: WebView, callback: (ReaderSnapshot?) -> Unit) {
    val url = view.url ?: ""
    if (!url.startsWith("https://") && !url.startsWith("http://")) {
        callback(null)
        return
    }
    view.evaluateJavascript(readerScript) { raw ->
        val snapshot = try {
            if (raw.isNullOrBlank() || raw.length > 131072) null else {
                val decoded = JSONArray("[" + raw + "]").optString(0)
                val parsed = JSONObject(decoded)
                val pageUrl = parsed.optString("url", "")
                if (!(pageUrl.startsWith("https://") || pageUrl.startsWith("http://"))) null
                else {
                    val array = parsed.optJSONArray("sections") ?: JSONArray()
                    val sections = (0 until minOf(array.length(), 60))
                        .map { array.optString(it).take(800).trim() }
                        .filter { it.isNotBlank() }
                    ReaderSnapshot(parsed.optString("title", "Untitled").take(200),
                        pageUrl.take(4096), sections)
                }
            }
        } catch (_: Exception) { null }
        callback(snapshot)
    }
}

@Composable
fun NativeReaderScreen(reader: ReaderSnapshot, close: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(12.dp)) {
        Row {
            TextButton(onClick = close) { Text("Back to website") }
            Text("Local reading mode", style = MaterialTheme.typography.labelSmall,
                modifier = Modifier.padding(top = 12.dp))
        }
        Text(reader.title, style = MaterialTheme.typography.titleLarge)
        Text(reader.url, style = MaterialTheme.typography.bodySmall,
            maxLines = 2, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(8.dp))
        if (reader.sections.isEmpty()) {
            Text("No supported visible article text detected. This page may be interactive, encrypted, or not structured as an article.")
        } else LazyColumn {
            items(reader.sections) { section ->
                Text(section, modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp))
                HorizontalDivider()
            }
        }
    }
}
