package com.blazingsystems.visualizer.ui
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.graphics.Color
private val colors=darkColorScheme(primary=Color(0xFFB5A0FF),onPrimary=Color(0xFF241447),secondary=Color(0xFF70DFD4),background=Color(0xFF090A12),surface=Color(0xFF10111D),surfaceContainer=Color(0xFF1A1B2A),onSurface=Color(0xFFECEAF7),onSurfaceVariant=Color(0xFFABA8BF),outline=Color(0xFF454155))
@Composable fun BlazingTheme(content:@Composable ()->Unit){MaterialTheme(colorScheme=colors){CompositionLocalProvider(LocalContentColor provides MaterialTheme.colorScheme.onSurface){content()}}}
