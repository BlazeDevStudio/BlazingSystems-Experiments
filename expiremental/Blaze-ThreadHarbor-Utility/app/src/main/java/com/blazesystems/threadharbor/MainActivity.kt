package com.blazesystems.threadharbor

import android.app.DownloadManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.WebView
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
        setContent { MaterialTheme { HarborShell(this,fixture) } }
    }
    override fun onDestroy() { fixture.close(); super.onDestroy() }
}

@Composable
private fun HarborShell(context: Context, fixture: FixtureRuntime) {
    val tabs = listOf("Browser","Chats (Lab)","Downloads","Files","Gallery","Inspection","Calls","Settings")
    var current by remember { mutableStateOf("Browser") }
    BackHandler(enabled = current != "Browser") { current = "Browser" }
    // Keep message input and Send above the Android software keyboard (IME).
    Column(Modifier.fillMaxSize().imePadding()) {
        Text("Blaze ThreadHarbor  •  Experimental Browser",
            style=MaterialTheme.typography.titleMedium,modifier=Modifier.padding(12.dp))
        ScrollableTabRow(selectedTabIndex=tabs.indexOf(current),edgePadding=0.dp) {
            tabs.forEach {name->Tab(selected=current==name,onClick={current=name},text={Text(name)})}
        }
        Box(Modifier.weight(1f)) {
            // Browser remains composed at zero size while other tools are open.
            // Its WebViews and in-memory back stacks therefore survive navigation.
            // Unlike a hidden full-screen overlay it cannot steal touches.
            if (current != "Browser") {
                when(current) {
                    "Chats (Lab)" -> ChatsScreen(fixture){current="Browser"}
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
        // Stays attached independently of Compose chat UI; no third-party browsing bridge.
        AndroidView(factory={
            (fixture.webView.parent as? android.view.ViewGroup)?.removeView(fixture.webView)
            fixture.webView
        },modifier=Modifier.size(1.dp))
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
private fun ChatsScreen(fixture:FixtureRuntime,openBrowser:()->Unit) {
    var draft by remember { mutableStateOf("") }
    Column(Modifier.fillMaxSize().padding(12.dp)){
        Text("Native messaging — controlled fixture",style=MaterialTheme.typography.titleLarge)
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
@Composable
private fun DownloadsScreen(context:Context) {
    val pref=remember{context.getSharedPreferences("downloads",Context.MODE_PRIVATE)}
    val dm=remember{context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager}
    var refresh by remember{mutableIntStateOf(0)}
    val ids=remember(refresh){pref.getString("ids","").orEmpty().split(",")
        .mapNotNull{it.toLongOrNull()}.reversed()}
    Column(Modifier.padding(16.dp)){
        Text("Download Manager",style=MaterialTheme.typography.titleLarge)
        Text("Android system queue; pause/resume and custom Save As are not yet implemented.")
        TextButton(onClick={refresh++}){Text("Refresh status")}
        LazyColumn{
            items(ids){id->
                val state=try{
                    dm.query(DownloadManager.Query().setFilterById(id))?.use{c->
                        if(!c.moveToFirst())return@use "Unavailable"
                        val status=c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS))
                        val bytes=c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR))
                        val total=c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES))
                        val name=when(status){
                            DownloadManager.STATUS_SUCCESSFUL->"COMPLETE"
                            DownloadManager.STATUS_FAILED->"FAILED"
                            DownloadManager.STATUS_PAUSED->"PAUSED BY SYSTEM"
                            DownloadManager.STATUS_RUNNING->"RUNNING"
                            else->"QUEUED"
                        }
                        name + " — " + bytes + "/" + total + " bytes"
                    }?:"Unavailable"
                }catch(_:Exception){"Query failed"}
                Text("Transfer #" + id + "  " + state,modifier=Modifier.padding(vertical=8.dp))
            }
        }
    }
}
@Composable
private fun FilesScreen(context:Context) {
    var folder by remember{mutableStateOf<Uri?>(null)}
    val choose=rememberLauncherForActivityResult(ActivityResultContracts.OpenDocumentTree()){uri->
        if(uri!=null){
            try{context.contentResolver.takePersistableUriPermission(uri,
                Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)}catch(_:Exception){}
            folder=uri
        }
    }
    val dir=remember(folder){folder?.let{DocumentFile.fromTreeUri(context,it)}}
    val records=remember(dir){try{dir?.listFiles()?.take(200)?.toList()?:emptyList()}
        catch(_:Exception){emptyList()}}
    Column(Modifier.padding(16.dp)){
        Text("Files — user-authorized folder",style=MaterialTheme.typography.titleLarge)
        Button(onClick={choose.launch(null)}){Text("Choose folder")}
        if(dir==null)Text("No folder granted yet.")
        else{
            Text(dir.name?:"Folder")
            LazyColumn{items(records){file->
                TextButton(onClick={
                    if(file.isFile)try{
                        context.startActivity(Intent(Intent.ACTION_VIEW).apply{
                            setDataAndType(file.uri,file.type?:"*/*")
                            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
                        })
                    }catch(_:Exception){}
                }){Text((if(file.isDirectory)"Folder: " else "File: ")+(file.name?:"unnamed"))}
            }}
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
