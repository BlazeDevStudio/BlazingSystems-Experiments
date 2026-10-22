package com.blazingsystems.visualizer.ui
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.unit.*
import androidx.compose.ui.text.font.FontWeight
import com.blazingsystems.visualizer.project.*
import kotlinx.serialization.json.*
@Composable fun ElementEditorSheet(scene:Scene,model:StudioModel){var selected by rememberSaveable{mutableStateOf<String?>(null)};var add by remember{mutableStateOf(false)};var imageLayer by remember{mutableStateOf<Layer?>(null)};val picker=rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()){uri->if(uri!=null)imageLayer?.let{model.attachImage(it,uri)}}
 Column(Modifier.verticalScroll(rememberScrollState()).padding(20.dp)){Text("Composition",fontSize=25.sp,fontWeight=FontWeight.Bold);OutlinedTextField(scene.name,{model.setScene(scene.copy(name=it.take(200)))},label={Text("Visualizer name")},modifier=Modifier.fillMaxWidth());Spacer(Modifier.height(10.dp));scene.layers.forEachIndexed{i,layer->Card(Modifier.fillMaxWidth().padding(vertical=4.dp)){Column(Modifier.padding(12.dp)){Row(verticalAlignment=Alignment.CenterVertically){Checkbox(layer.visible,{model.setLayer(layer.copy(visible=it))});TextButton(onClick={selected=if(selected==layer.id)null else layer.id},modifier=Modifier.weight(1f)){Text(layer.name)};IconButton(onClick={model.moveLayer(layer.id,-1)},enabled=i>0){Icon(Icons.Rounded.ArrowUpward,"Move layer up")};IconButton(onClick={model.removeLayer(layer.id)}){Icon(Icons.Rounded.DeleteOutline,"Delete layer")}}
  if(selected==layer.id){fun prop(key:String,value:String)=model.setLayer(layer.copy(properties=JsonObject(layer.properties+(key to JsonPrimitive(value)))))
   OutlinedTextField(layer.name,{model.setLayer(layer.copy(name=it.take(200)))},label={Text("Layer name")},modifier=Modifier.fillMaxWidth())
   if(layer.type==ElementType.TEXT)OutlinedTextField(layer.properties["text"]?.jsonPrimitive?.content ?: "BLAZING",{prop("text",it.take(500))},label={Text("Text")},modifier=Modifier.fillMaxWidth())
   if(layer.type==ElementType.IMAGE)OutlinedButton(onClick={imageLayer=layer;picker.launch(arrayOf("image/*"))}){Text("Choose image")}
   var color by remember(layer.id){mutableStateOf(layer.properties["color"]?.jsonPrimitive?.content ?: "#FF9C83FF")};OutlinedTextField(color,{color=it;if(it.matches(Regex("#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?")))prop("color",it)},label={Text("Color #RRGGBB or #AARRGGBB")},singleLine=true,modifier=Modifier.fillMaxWidth())
   val t=layer.transform
   PropertySlider("Position X",t.x,-.5f..1.5f){model.setLayer(layer.copy(transform=t.copy(x=it)))};PropertySlider("Position Y",t.y,-.5f..1.5f){model.setLayer(layer.copy(transform=t.copy(y=it)))}
   PropertySlider("Width",t.width,.05f..2f){model.setLayer(layer.copy(transform=t.copy(width=it)))};PropertySlider("Height",t.height,.05f..2f){model.setLayer(layer.copy(transform=t.copy(height=it)))};PropertySlider("Rotation",t.rotation,-180f..180f){model.setLayer(layer.copy(transform=t.copy(rotation=it)))}
   if(layer.type==ElementType.SPECTRUM)Row{listOf("circle","bars").forEach{path->FilterChip(layer.properties["path"]?.jsonPrimitive?.content==path,{prop("path",path)},label={Text(path)},modifier=Modifier.padding(end=8.dp))}}
   Row(verticalAlignment=Alignment.CenterVertically){Switch(layer.bindings.isNotEmpty(),{model.setLayer(layer.copy(bindings=if(it)listOf(Binding("scale",BindingSource.RMS,1f)) else emptyList()))});Text("Pulse scale with music",Modifier.padding(start=10.dp))}
   layer.bindings.firstOrNull()?.let{binding->Row(Modifier.horizontalScroll(rememberScrollState())){BindingSource.entries.forEach{source->FilterChip(binding.source==source,{model.setLayer(layer.copy(bindings=listOf(binding.copy(source=source))))},label={Text(source.name.lowercase().replace('_',' '))},modifier=Modifier.padding(end=8.dp))}};PropertySlider("Response",binding.amount,0f..4f){model.setLayer(layer.copy(bindings=listOf(binding.copy(amount=it))))}}
  }
 }}};Button(onClick={add=true},modifier=Modifier.fillMaxWidth().padding(top=12.dp)){Icon(Icons.Rounded.Add,null);Text("Add element")};Text("Layers draw from top to bottom. Note layers use the track's detected notes.",fontSize=12.sp,color=MaterialTheme.colorScheme.onSurfaceVariant,modifier=Modifier.padding(top=12.dp))}
 if(add)AlertDialog(onDismissRequest={add=false},title={Text("Add element")},text={Column(Modifier.verticalScroll(rememberScrollState())){ElementType.entries.forEach{type->TextButton(onClick={model.addLayer(type);add=false}){Text(type.name.lowercase().replace('_',' '))}}}},confirmButton={TextButton(onClick={add=false}){Text("Close")}})
}
@Composable private fun PropertySlider(label:String,value:Float,range:ClosedFloatingPointRange<Float>,onChange:(Float)->Unit){Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text(label,fontSize=12.sp);Text("%.2f".format(value),fontSize=12.sp,color=MaterialTheme.colorScheme.onSurfaceVariant)};Slider(value.coerceIn(range),onChange,valueRange=range)}
