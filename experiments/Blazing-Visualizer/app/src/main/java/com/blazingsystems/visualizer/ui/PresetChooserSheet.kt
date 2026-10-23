package com.blazingsystems.visualizer.ui

import android.graphics.Bitmap
import android.graphics.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ContentCopy
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import java.io.File
import java.util.UUID
import kotlin.math.*

@Composable
internal fun PresetChooserSheet(scene: Scene,saved: List<Scene>,onSave: ()->Unit,
    onSelect: (Scene)->Unit,onImport: ()->Unit,onExport: ()->Unit) {
    val assets=File(LocalContext.current.filesDir,"assets")
    val builtins=remember { BuiltinScenes.all() }
    Column(Modifier.fillMaxWidth().height(560.dp).padding(horizontal=16.dp)) {
        Text("Visualizers",fontSize=24.sp,fontWeight=FontWeight.Bold)
        LazyVerticalGrid(columns=GridCells.Adaptive(120.dp),modifier=Modifier.weight(1f).testTag("preset-grid"),
            contentPadding=PaddingValues(vertical=12.dp),horizontalArrangement=Arrangement.spacedBy(10.dp),
            verticalArrangement=Arrangement.spacedBy(10.dp)) {
            items((builtins+saved).distinctBy { it.id },key={it.id}) { preset ->
                val bitmap=remember(preset) {
                    Bitmap.createBitmap(240,240,Bitmap.Config.ARGB_8888).also { image ->
                        val demo=FeatureFrame(700_000,rms=.35f,
                            spectrum=List(1024) { (.08*abs(sin(it*.17))/(1+it*.03)).toFloat() },
                            notes=listOf(60,64,67).map { NoteEvent("demo-$it",it,0,2_000_000) })
                        ScenePainter(assets).use { it.draw(Canvas(image),SceneEvaluator.evaluate(
                            SceneLayouts.fit(preset,1f),demo,demo.sourceTimeUs),240,240) }
                    }.asImageBitmap()
                }
                Card(onClick={onSelect(preset)},modifier=Modifier.fillMaxWidth(),
                    border=if(preset.id==scene.id) androidx.compose.foundation.BorderStroke(2.dp,MaterialTheme.colorScheme.primary) else null) {
                    Image(bitmap,contentDescription=null,modifier=Modifier.fillMaxWidth().aspectRatio(1f))
                    Text(preset.name,modifier=Modifier.padding(8.dp),maxLines=1,overflow=TextOverflow.Ellipsis,
                        style=MaterialTheme.typography.labelLarge)
                }
            }
        }
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween) {
            TextButton(onClick=onSave) { Text("Save current preset") }
            IconButton(onClick={onSelect(scene.copy(id=UUID.randomUUID().toString(),name=scene.name+" copy"))}) {
                Icon(Icons.Rounded.ContentCopy,"Duplicate current visualizer")
            }
        }
        Row(Modifier.padding(bottom=12.dp),horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick=onImport,modifier=Modifier.weight(1f)) { Text("Import preset") }
            Button(onClick=onExport,modifier=Modifier.weight(1f)) { Text("Export pack") }
        }
    }
}
