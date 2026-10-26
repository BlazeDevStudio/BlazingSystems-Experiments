package com.blazesystems.threadharbor

import android.app.Activity
import android.app.DownloadManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.WebView
import kotlinx.coroutines.launch
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.documentfile.provider.DocumentFile
import org.json.JSONObject

class MainActivity : ComponentActivity() {
    private lateinit var fixture: FixtureRuntime
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WebView.setWebContentsDebuggingEnabled(false)
        fixture = FixtureRuntime(this)
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = Color(0xFFFF982F),
                    onPrimary = Color(0xFF141820),
                    background = Color(0xFF10151D),
                    onBackground = Color(0xFFF2F5F8),
                    surface = Color(0xFF1A222D),
                    onSurface = Color(0xFFF2F5F8),
                    surfaceVariant = Color(0xFF273440),
                    onSurfaceVariant = Color(0xFFC0CEDA),
                    error = Color(0xFFFF7373)
                )
            ) { HarborShell(this, fixture) }
        }
    }
    override fun onDestroy() { fixture.close(); super.onDestroy() }
}

@Composable
private fun HarborShell(context: Context, fixture: FixtureRuntime) {
    val tabs = listOf("Browser","Chats","Downloads","Files","Gallery","Inspection","Calls","Settings")
    var current by remember { mutableStateOf("Browser") }
    BackHandler(enabled = current != "Browser") { current = "Browser" }
    // Keep message input and Send above the Android software keyboard (IME).
    Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().imePadding()) {
        Text("Blaze ThreadHarbor  •  Development",
            style=MaterialTheme.typography.titleMedium,modifier=Modifier.padding(12.dp))
        ScrollableTabRow(selectedTabIndex=tabs.indexOf(current),edgePadding=0.dp) {
            tabs.forEach {name->Tab(selected=current==name,onClick={current=name},text={Text(name,style=MaterialTheme.typography.labelSmall)})}
        }
        Box(Modifier.weight(1f)) {
            // Browser remains composed at zero size while other tools are open.
            // Its WebViews and in-memory back stacks therefore survive navigation.
            // Unlike a hidden full-screen overlay it cannot steal touches.
            if (current != "Browser") {
                when(current) {
                    "Chats" -> ChatsStatusScreen(openBrowser = { current = "Browser" },
                        openLab = { current = "Developer Lab" })
                    "Developer Lab" -> ChatsScreen(fixture){current="Browser"}
                    "Calls" -> Notice("Calls unavailable","Website calling, voicemail and recording are unsupported until authorized capabilities are demonstrated.")
                    "Gallery" -> GalleryScreen()
                    "Downloads" -> DownloadsScreen(context)
                    "Files" -> FilesScreen(context)
                    "Inspection" -> InspectionScreen(context)
                    "Settings" -> SettingsScreen(context){current="Browser"}
                }
            }
            Box(if (current == "Browser") Modifier.fillMaxSize() else Modifier.size(0.dp)) {
                BrowserScreen(context, visible = current == "Browser")
            }
        }
        // Only mount the privileged app-owned fixture during explicit developer diagnostics.
        // It never shares a WebView or bridge with actual third-party browsing.
        if (current == "Developer Lab") {
            AndroidView(factory={
                (fixture.webView.parent as? android.view.ViewGroup)?.removeView(fixture.webView)
                fixture.webView
            },modifier=Modifier.size(1.dp))
        }
    }
}
@Composable
private fun Notice(title:String,body:String) {
    Column(Modifier.padding(16.dp)){
        Text(title,style=MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(8.dp));Text(body)
    }
}
@Composable
private fun ChatsStatusScreen(openBrowser: () -> Unit, openLab: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("Chats", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(12.dp))
        Text("No compatible messaging site adapter is connected.")
        Spacer(Modifier.height(8.dp))
        Text("ThreadHarbor will not invent conversations or claim website messages were sent. The independent native chat interface stays disconnected until real-site compatibility and permission have been verified.")
        Spacer(Modifier.height(20.dp))
        Button(onClick = openBrowser) { Text("Browse an authentic website") }
        Spacer(Modifier.height(12.dp))
        TextButton(onClick = openLab) { Text("Open controlled adapter diagnostics") }
    }
}

@Composable
private fun ChatsScreen(fixture:FixtureRuntime,openBrowser:()->Unit) {
    var draft by remember { mutableStateOf("") }
    Column(Modifier.fillMaxSize().padding(12.dp)){
        Text("Developer adapter diagnostics",style=MaterialTheme.typography.titleLarge)
        Text("DEMO WEBSITE, NOT FACEBOOK OR REAL INBOX",color=MaterialTheme.colorScheme.error)
        Text(fixture.status,style=MaterialTheme.typography.bodySmall)
        fixture.pending.lastOrNull()?.let { action ->
            Text("Last action: " + action.status, style=MaterialTheme.typography.bodySmall)
        }
        LazyColumn(Modifier.weight(1f)){
            items(fixture.messages,key={"message-" + it.id}){m->
                Card(Modifier.fillMaxWidth().padding(vertical=4.dp)){
                    Column(Modifier.padding(10.dp)){
                        Text(m.sender,style=MaterialTheme.typography.labelLarge)
                        Text(m.text)
                    }
                }
            }
            items(fixture.pending,key={"action-" + it.id}){p->
                Text(p.status + ": " + p.text.take(80),style=MaterialTheme.typography.bodySmall)
            }
        }
        Row {
            OutlinedTextField(value=draft,onValueChange={draft=it.take(4096)},
                modifier=Modifier.weight(1f),maxLines=3,label={Text("Fixture reply")})
            Button(enabled=draft.isNotBlank()&&fixture.supported,onClick={
                fixture.send(draft);draft=""
            }){Text("Send")}
        }
        TextButton(onClick=openBrowser){Text("Open authentic website using Browser")}
    }
}
@Composable
private fun SettingsScreen(context:Context,openBrowser:()->Unit) {
    Column(Modifier.padding(16.dp)){
        Text("Browser and privacy",style=MaterialTheme.typography.titleLarge)
        Text("Meta semantic integration: BLOCKED pending authorization and real-site verification.")
        Spacer(Modifier.height(12.dp))
        Button(onClick=openBrowser){Text("Open full browser")}
        Button(onClick={
            try{context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse("https://www.facebook.com/messages"))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))}catch(_:Exception){}
        }){Text("Facebook Messages (external browser)")}
        Text("Authentication, 2FA and encryption PINs remain entirely website-managed. ThreadHarbor never receives them through the semantic bridge.")
    }
}
private data class DownloadInfo(
    val name: String, val state: Int, val bytes: Long, val total: Long,
    val reason: Int, val url: String
)

@Composable
private fun DownloadsScreen(context: Context) {
    val prefs = remember { context.getSharedPreferences("downloads", Context.MODE_PRIVATE) }
    val manager = remember { context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager }
    var refresh by remember { mutableIntStateOf(0) }
    var feedback by remember { mutableStateOf("") }
    var pendingSaveId by remember { mutableStateOf<Long?>(null) }
    var exporting by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val savePicker = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        val downloadId = pendingSaveId
        pendingSaveId = null
        val destination = result.data?.data
        if (result.resultCode == Activity.RESULT_OK && downloadId != null && destination != null) {
            exporting = true
            feedback = "Copying completed download to your selected document..."
            scope.launch {
                val outcome = exportCompletedDownload(context, manager, downloadId, destination)
                exporting = false
                feedback = outcome.fold(
                    onSuccess = { "Saved successfully: " + it + " bytes" },
                    onFailure = { "Save As failed: " + (it.message ?: "storage error") }
                )
            }
        }
    }
    val ids = remember(refresh) {
        prefs.getString("ids", "").orEmpty().split(",")
            .mapNotNull { it.toLongOrNull() }.distinct().reversed()
    }
    fun untrack(id: Long) {
        val remaining = prefs.getString("ids", "").orEmpty().split(",").filter {
            it.toLongOrNull() != null && it != id.toString()
        }
        prefs.edit().putString("ids", remaining.joinToString(",")).apply()
    }
    Column(Modifier.fillMaxSize().padding(12.dp)) {
        Text("Downloads", style = MaterialTheme.typography.titleLarge)
        Text("System transfers. Save As copies a completed file to your chosen location; network pause/resume remains unsupported.",
            style = MaterialTheme.typography.bodySmall)
        Row {
            TextButton(onClick = { refresh++ }) { Text("Refresh") }
            TextButton(onClick = {
                try { context.startActivity(Intent(DownloadManager.ACTION_VIEW_DOWNLOADS)) }
                catch (_: Exception) { feedback = "System Downloads unavailable" }
            }) { Text("System downloads") }
        }
        if (feedback.isNotEmpty()) Text(feedback, color = MaterialTheme.colorScheme.error)
        if (ids.isEmpty()) Text("No transfers yet. Start a download in Browser.")
        LazyColumn {
            items(ids, key = { it }) { id ->
                val info = remember(id, refresh) {
                    try {
                        manager.query(DownloadManager.Query().setFilterById(id))?.use { cursor ->
                            if (!cursor.moveToFirst()) null else DownloadInfo(
                                name = cursor.getString(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_TITLE)) ?: "Download",
                                state = cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS)),
                                bytes = cursor.getLong(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR)),
                                total = cursor.getLong(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES)),
                                reason = cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_REASON)),
                                url = cursor.getString(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_URI)) ?: ""
                            )
                        }
                    } catch (_: Exception) { null }
                }
                Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Column(Modifier.padding(12.dp)) {
                        Text(info?.name ?: ("Unavailable transfer #" + id),
                            style = MaterialTheme.typography.titleSmall)
                        if (info != null) {
                            val label = when (info.state) {
                                DownloadManager.STATUS_SUCCESSFUL -> "Complete"
                                DownloadManager.STATUS_FAILED -> "Failed, reason " + info.reason
                                DownloadManager.STATUS_PAUSED -> "Paused by Android, reason " + info.reason
                                DownloadManager.STATUS_RUNNING -> "Downloading"
                                else -> "Queued"
                            }
                            Text(label + " • " + info.bytes + " / " +
                                (if (info.total >= 0) info.total.toString() else "unknown") + " bytes")
                            Row {
                                if (info.state == DownloadManager.STATUS_SUCCESSFUL) {
                                    TextButton(onClick = {
                                        try {
                                            val uri = manager.getUriForDownloadedFile(id)
                                            if (uri == null) {
                                                feedback = "File no longer available"
                                            } else context.startActivity(Intent(Intent.ACTION_VIEW).apply {
                                                setDataAndType(uri, context.contentResolver.getType(uri) ?: "*/*")
                                                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
                                            })
                                        } catch (_: Exception) { feedback = "No file viewer available" }
                                    }) { Text("Open") }
                                }
                                if (info.state == DownloadManager.STATUS_SUCCESSFUL) {
                                    TextButton(enabled = !exporting, onClick = {
                                        val suggested = info.name.substringAfterLast('/')
                                            .replace(':', '_').take(140).ifBlank { "download" }
                                        val mime = try {
                                            manager.query(DownloadManager.Query().setFilterById(id))?.use { cursor ->
                                                if (cursor.moveToFirst()) {
                                                    cursor.getString(cursor.getColumnIndexOrThrow(
                                                        DownloadManager.COLUMN_MEDIA_TYPE
                                                    ))
                                                } else null
                                            }
                                        } catch (_: Exception) { null }
                                        try {
                                            pendingSaveId = id
                                            savePicker.launch(Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                                                addCategory(Intent.CATEGORY_OPENABLE)
                                                type = mime?.takeIf { it.contains("/") } ?: "application/octet-stream"
                                                putExtra(Intent.EXTRA_TITLE, suggested)
                                            })
                                        } catch (_: Exception) {
                                            pendingSaveId = null
                                            feedback = "No document provider can create this file"
                                        }
                                    }) { Text("Save As") }
                                }
                                if (info.state == DownloadManager.STATUS_FAILED &&
                                    (info.url.startsWith("https://") || info.url.startsWith("http://"))) {
                                    TextButton(onClick = {
                                        try {
                                            val request = DownloadManager.Request(Uri.parse(info.url))
                                                .setTitle(info.name)
                                                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                                            // Never put session cookies in redirect-uncontrolled retry requests.
                                            val retryId = manager.enqueue(request)
                                            val oldIds = prefs.getString("ids", "").orEmpty()
                                            prefs.edit().putString("ids",
                                                (oldIds + "," + retryId).trim(',')).apply()
                                            refresh++
                                        } catch (_: Exception) { feedback = "Download retry failed" }
                                    }) { Text("Retry") }
                                }
                                if (info.state == DownloadManager.STATUS_RUNNING ||
                                    info.state == DownloadManager.STATUS_PENDING ||
                                    info.state == DownloadManager.STATUS_PAUSED) {
                                    TextButton(onClick = {
                                        try {
                                            manager.remove(id)
                                            untrack(id)
                                            refresh++
                                        } catch (_: Exception) { feedback = "Cancel failed" }
                                    }) { Text("Cancel") }
                                } else {
                                    TextButton(onClick = { untrack(id); refresh++ }) { Text("Hide") }
                                }
                            }
                        } else {
                            TextButton(onClick = { untrack(id); refresh++ }) { Text("Remove entry") }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun FilesScreen(context: Context) {
    val prefs = remember { context.getSharedPreferences("file_tree_v1", Context.MODE_PRIVATE) }
    var rootUri by remember { mutableStateOf(prefs.getString("tree", null)?.let(Uri::parse)) }
    val path = remember { mutableStateListOf<DocumentFile>() }
    var refresh by remember { mutableIntStateOf(0) }
    var feedback by remember { mutableStateOf("") }
    var entryName by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf<DocumentFile?>(null) }
    var confirmDelete by remember { mutableStateOf(false) }
    var importing by remember { mutableStateOf(false) }
    val fileScope = rememberCoroutineScope()

    val choose = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
        if (uri != null) try {
            context.contentResolver.takePersistableUriPermission(
                uri, Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            )
            rootUri = uri
            prefs.edit().putString("tree", uri.toString()).apply()
            feedback = ""
        } catch (_: Exception) { feedback = "The provider did not grant persistent folder access" }
    }
    LaunchedEffect(rootUri) {
        path.clear()
        selected = null
        rootUri?.let { uri ->
            val granted = context.contentResolver.persistedUriPermissions.any {
                it.uri == uri && it.isReadPermission
            }
            if (granted) {
                DocumentFile.fromTreeUri(context, uri)?.let { path.add(it) }
            } else feedback = "Folder access expired. Please choose it again."
        }
    }
    val current = path.lastOrNull()
    val records by produceState<List<DocumentFile>>(emptyList(), current, refresh) {
        value = withContext(Dispatchers.IO) {
            try {
                current?.listFiles()?.sortedWith(
                    compareBy<DocumentFile> { !it.isDirectory }.thenBy { it.name?.lowercase() }
                ) ?: emptyList()
            } catch (_: Exception) { emptyList() }
        }
    }
    val importPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        val destination = path.lastOrNull()
        if (uri != null && destination != null && !importing) {
            importing = true
            feedback = "Importing selected document..."
            fileScope.launch {
                val outcome = importIntoAuthorizedFolder(context, uri, destination)
                importing = false
                feedback = outcome.fold(
                    onSuccess = { "Imported " + it },
                    onFailure = { "Import failed: " + (it.message ?: "storage error") }
                )
                refresh++
            }
        }
    }

    if (confirmDelete && selected != null) {
        AlertDialog(
            onDismissRequest = { confirmDelete = false },
            title = { Text("Delete selected item?") },
            text = { Text("Delete " + selected?.name + "? This may be permanent; no Trash is provided.") },
            confirmButton = { TextButton(onClick = {
                val item = selected
                confirmDelete = false
                if (item?.delete() == true) {
                    selected = null
                    entryName = ""
                    feedback = "Deleted"
                    refresh++
                } else feedback = "Deletion failed or access was revoked"
            }) { Text("Delete") } },
            dismissButton = { TextButton(onClick = { confirmDelete = false }) { Text("Cancel") } }
        )
    }

    Column(Modifier.fillMaxSize().padding(12.dp)) {
        Text("Files • Android folder access", style = MaterialTheme.typography.titleLarge)
        Row {
            Button(onClick = { choose.launch(null) }) { Text("Choose folder") }
            TextButton(onClick = { refresh++ }) { Text("Refresh") }
            if (path.size > 1) TextButton(onClick = {
                path.removeAt(path.lastIndex)
                selected = null
                entryName = ""
            }) { Text("Up") }
        }
        if (feedback.isNotBlank()) Text(feedback, style = MaterialTheme.typography.bodySmall)
        if (current == null) Text("Select a folder to browse, create, import and manage files.")
        else {
            Text(current.name ?: "Selected folder", style = MaterialTheme.typography.titleMedium)
            Row {
                OutlinedTextField(
                    entryName, { entryName = it.take(160) },
                    label = { Text(if (selected == null) "New folder name" else "Rename selected item") },
                    modifier = Modifier.weight(1f), singleLine = true
                )
                TextButton(enabled = entryName.isNotBlank(), onClick = {
                    val name = entryName.trim()
                    if (name.isNotEmpty()) {
                        val target = selected
                        val success = if (target != null) target.renameTo(name)
                                      else current.createDirectory(name) != null
                        feedback = if (success) "Saved successfully" else "Operation failed"
                        if (success) {
                            selected = null
                            entryName = ""
                            refresh++
                        }
                    }
                }) { Text(if (selected == null) "Create" else "Rename") }
            }
            Row {
                Button(enabled = !importing, onClick = { importPicker.launch(arrayOf("*/*")) }) { Text(if (importing) "Importing..." else "Import file") }
                if (selected != null) {
                    TextButton(onClick = { selected = null; entryName = "" }) { Text("Deselect") }
                    TextButton(onClick = { confirmDelete = true }) { Text("Delete") }
                }
            }
            LazyColumn {
                items(records, key = { it.uri.toString() }) { file ->
                    Row {
                        TextButton(modifier = Modifier.weight(1f), onClick = {
                            if (file.isDirectory) {
                                path.add(file)
                                selected = null
                                entryName = ""
                            } else {
                                try {
                                    context.startActivity(Intent(Intent.ACTION_VIEW).apply {
                                        setDataAndType(file.uri, file.type ?: "*/*")
                                        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
                                    })
                                } catch (_: Exception) { feedback = "No app available to open the file" }
                            }
                        }) {
                            Text((if (file.isDirectory) "📁 " else "📄 ") + (file.name ?: "unnamed"),
                                maxLines = 2)
                        }
                        TextButton(onClick = {
                            selected = file
                            entryName = file.name.orEmpty()
                        }) { Text("Edit") }
                    }
                }
            }
        }
    }
}

@Composable
private fun GalleryScreen() {
    var uri by remember{mutableStateOf<Uri?>(null)}
    val choose=rememberLauncherForActivityResult(ActivityResultContracts.GetContent()){uri=it}
    Column(Modifier.fillMaxSize().padding(16.dp)){
        Text("Gallery — image viewer",style=MaterialTheme.typography.titleLarge)
        Button(onClick={choose.launch("image/*")}){Text("Choose image")}
        uri?.let{selected->
            AndroidView(factory={android.widget.ImageView(it).apply{
                scaleType=android.widget.ImageView.ScaleType.FIT_CENTER
            }},update={it.setImageURI(selected)},modifier=Modifier.fillMaxWidth().weight(1f))
        }
        Text("Video, indexing, tagging and duplicate detection are pending.")
    }
}
@Composable
private fun InspectionScreen(context:Context) {
    val prefs=remember{context.getSharedPreferences("inspection",Context.MODE_PRIVATE)}
    var vessel by remember{mutableStateOf(prefs.getString("vessel","").orEmpty())}
    var project by remember{mutableStateOf(prefs.getString("project","").orEmpty())}
    var hatch by remember{mutableStateOf(prefs.getString("hatch","").orEmpty())}
    var notes by remember{mutableStateOf(prefs.getString("notes","").orEmpty())}
    val export=rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")){uri->
        if(uri!=null)try{
            val value=JSONObject().put("vessel",vessel).put("project",project)
                .put("hatch",hatch).put("notes",notes).put("source","manual")
            context.contentResolver.openOutputStream(uri)?.use{
                it.write(value.toString(2).toByteArray(Charsets.UTF_8))
            }
        }catch(_:Exception){}
    }
    Column(Modifier.fillMaxSize().padding(16.dp)){
        Text("Field Inspection Workspace (offline)",style=MaterialTheme.typography.titleLarge)
        OutlinedTextField(vessel,{vessel=it},label={Text("Vessel")})
        OutlinedTextField(project,{project=it},label={Text("Project / inspection no.")})
        OutlinedTextField(hatch,{hatch=it},label={Text("Hatch")})
        OutlinedTextField(notes,{notes=it},label={Text("Notes")},maxLines=4)
        Button(onClick={
            prefs.edit().putString("vessel",vessel).putString("project",project)
                .putString("hatch",hatch).putString("notes",notes).apply()
        }){Text("Save locally")}
        Button(onClick={export.launch("inspection-manifest.json")}){Text("Export JSON")}
        Text("Media tagging and ZIP report packages are planned; no missing metadata is inferred.")
    }
}
