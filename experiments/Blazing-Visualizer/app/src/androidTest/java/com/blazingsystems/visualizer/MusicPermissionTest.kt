package com.blazingsystems.visualizer

import android.Manifest
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.pm.PackageManager
import android.os.Build
import android.os.SystemClock
import android.view.accessibility.AccessibilityNodeInfo
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith

/** Run alone on a fresh install before general tests grant media access. */
@RunWith(AndroidJUnit4::class)
class MusicPermissionTest {
    @get:Rule val compose = createEmptyComposeRule()

    private fun permissionButton(suffix: String) {
        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        automation.serviceInfo = automation.serviceInfo.apply {
            flags = flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
        }
        fun find(node: AccessibilityNodeInfo?): AccessibilityNodeInfo? {
            if (node == null) return null
            if (node.viewIdResourceName?.endsWith(":id/$suffix") == true) return node
            for (i in 0 until node.childCount) find(node.getChild(i))?.let { return it }
            return null
        }
        val deadline = SystemClock.uptimeMillis() + 15_000
        while (SystemClock.uptimeMillis() < deadline) {
            val button = find(automation.rootInActiveWindow)
            if (button != null && button.performAction(AccessibilityNodeInfo.ACTION_CLICK)) return
            SystemClock.sleep(100)
        }
        fail("Runtime permission button $suffix was not displayed")
    }

    @Test fun denialKeepsLibraryUsableAndRefreshCanGrantAccess() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val permission = if (Build.VERSION.SDK_INT >= 33) Manifest.permission.READ_MEDIA_AUDIO
            else Manifest.permission.READ_EXTERNAL_STORAGE
        val fresh = context.checkSelfPermission(permission) == PackageManager.PERMISSION_DENIED
        if (InstrumentationRegistry.getArguments().getString("freshAudioPermission") == "true")
            assertTrue("CI permission smoke test requires a fresh install", fresh)
        else Assume.assumeTrue("Run permission smoke separately on a fresh install", fresh)
        context.getSharedPreferences("music-access", 0).edit().clear().commit()
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            permissionButton("permission_deny_button")
            compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
            compose.onNodeWithText("Your library").assertIsDisplayed()
            compose.onNodeWithContentDescription("Import music").assertIsEnabled()
            scenario.recreate()
            compose.onNodeWithText("Your library").assertIsDisplayed()
            compose.onNodeWithContentDescription("Refresh library").performClick()
            permissionButton("permission_allow_button")
            compose.waitUntil(10_000) {
                context.checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED
            }
            compose.onNodeWithText("Your library").assertIsDisplayed()
        }
    }
}
