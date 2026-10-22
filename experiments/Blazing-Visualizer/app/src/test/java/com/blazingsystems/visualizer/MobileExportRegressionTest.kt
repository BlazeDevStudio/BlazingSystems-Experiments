package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import org.junit.Assert.*
import org.junit.Test

class MobileExportRegressionTest {
    @Test fun optimizedNoteLayoutUsesTheBottomOfPortraitSquareAndLandscapeFrames() {
        val mode = ExportFrameMode.entries.firstOrNull { it.name == "OPTIMIZE" }
        assertNotNull("Export needs an explicit layout optimization option", mode)
        for (size in listOf(ExportSettings(720,1280), ExportSettings(720,720), ExportSettings(1280,720))) {
            val scene = BuiltinScenes.noteWheel()
            val project = Project(source = SourceRef("content://song"), scene = scene,
                exportFrameMode = mode ?: ExportFrameMode.CONTAIN)
            val resolved = SceneLayouts.forExport(project, size)
            val piano = resolved.layers.single { it.type == ElementType.PIANO_ROLL }.transform
            assertTrue("Keyboard must reach the lower safe margin", piano.y+piano.height/2 >= .95f)
            assertTrue(piano.y+piano.height/2 <= 1f)
            assertEquals("Export must not mutate the saved preview", scene, project.scene)
        }
    }
}
