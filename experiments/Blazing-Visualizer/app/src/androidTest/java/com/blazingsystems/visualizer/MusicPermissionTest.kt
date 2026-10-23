package com.blazingsystems.visualizer

import android.Manifest
import android.content.Intent
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

    /** Return false when the OS package installer never exposed a permission dialog. */
    private fun permissionButton(suffix: String): Boolean {
        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        automation.serviceInfo = automation.serviceInfo.apply {
            flags = flags or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        }
        fun find(node: AccessibilityNodeInfo?): AccessibilityNodeInfo? {
            if (node == null) return null
            if (node.viewIdResourceName?.endsWith(":id/$suffix") == true) return node
            val label = (node.text?.toString() ?: node.contentDescription?.toString())
                ?.trim()?.lowercase().orEmpty()
            val deny = suffix == "permission_deny_button" &&
                label in setOf("deny", "don't allow", "do not allow", "not now")
            val allow = suffix == "permission_allow_button" &&
                label in setOf("allow", "allow access", "while using the app")
            if (node.isClickable && (deny || allow)) return node
            for (i in 0 until node.childCount) find(node.getChild(i))?.let { return it }
            return null
        }
        val deadline = SystemClock.uptimeMillis() +
            if (Build.VERSION.SDK_INT <= 27) 5_000 else 15_000
        while (SystemClock.uptimeMillis() < deadline) {
            val roots = listOfNotNull(automation.rootInActiveWindow) +
                automation.windows.mapNotNull { it.root }
            val button = roots.firstNotNullOfOrNull(::find)
            if (button != null && button.performAction(AccessibilityNodeInfo.ACTION_CLICK)) return true
            SystemClock.sleep(100)
        }
        return false
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
        // Launch without ActivityScenario first. The OS permission dialog can
        // leave Android 8 activity STARTED (not RESUMED), which makes
        // ActivityScenario.launch wait/throw before we can click Deny.
        context.startActivity(
            Intent(context, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
        )
        val deniedByDialog = permissionButton("permission_deny_button")
        if (!deniedByDialog) {
                // On CI API26 the system PackageInstaller sometimes crashes before
                // it exposes a dialog. Back dismisses any leftover occluding window.
                // Retain the denied-permission app flow; only the OS-button click is
                // not proven by this emulator in that case.
                assertTrue("Missing real deny button on modern Android", Build.VERSION.SDK_INT <= 27)
                val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
                automation.executeShellCommand("input keyevent 4").use {
                    android.os.ParcelFileDescriptor.AutoCloseInputStream(it).use { stream ->
                        stream.readBytes()
                    }
                }
        }
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(permission))
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
            compose.onNodeWithText("Your library").assertIsDisplayed()
            compose.onNodeWithContentDescription("Import music").assertIsEnabled()
            scenario.recreate()
            compose.onNodeWithText("Your library").assertIsDisplayed()
            compose.onNodeWithContentDescription("Refresh library").performClick()
            val allowedByDialog = permissionButton("permission_allow_button")
            if (!allowedByDialog) {
                assertTrue("Missing real allow button on modern Android", Build.VERSION.SDK_INT <= 27)
                val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
                automation.executeShellCommand("pm grant ${context.packageName} $permission").use {
                    android.os.ParcelFileDescriptor.AutoCloseInputStream(it).use { stream ->
                        stream.readBytes()
                    }
                }
                // Do not recreate ActivityScenario while Android 8's broken
                // system permission overlay has left the app PAUSED.
                // The permission update is system-owned; confirm the real
                // PackageManager state and visible Library without a restart.
            }
            compose.waitUntil(10_000) {
                context.checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED
            }
            if (allowedByDialog) {
                // On a functioning OS dialog the app must return to the
                // foreground with a usable Compose library after granting.
                compose.onNodeWithText("Your library").assertIsDisplayed()
            } else {
                // API26's package installer crashed in CI, leaving our
                // Activity PAUSED and Compose hierarchy unavailable. Still
                // assert the real Android Activity has retained its content
                // and the OS permission changed. Do not claim this fallback
                // verifies foreground Compose behavior.
                scenario.onActivity { activity ->
                    val content = activity.findViewById<android.view.ViewGroup>(
                        android.R.id.content,
                    )
                    assertNotNull("MainActivity has no Android content root", content)
                    assertTrue("MainActivity content was destroyed after grant",
                        content.childCount > 0)
                }
            }
        }
    }
}
