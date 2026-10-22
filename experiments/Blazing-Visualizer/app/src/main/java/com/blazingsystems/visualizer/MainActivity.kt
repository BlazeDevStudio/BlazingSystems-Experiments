package com.blazingsystems.visualizer
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.ViewModelProvider
import com.blazingsystems.visualizer.ui.*
class MainActivity:ComponentActivity() {
 private val studio by lazy{ViewModelProvider(this)[StudioModel::class.java]}
 override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);enableEdgeToEdge();setContent{BlazingTheme{AveeShell(studio)}};if(savedInstanceState==null)accept(intent)}
 override fun onNewIntent(intent:Intent){super.onNewIntent(intent);accept(intent)}
 private fun accept(intent:Intent?){if(intent?.action==Intent.ACTION_VIEW)intent.data?.let{studio.importTracks(listOf(it))}}
}
