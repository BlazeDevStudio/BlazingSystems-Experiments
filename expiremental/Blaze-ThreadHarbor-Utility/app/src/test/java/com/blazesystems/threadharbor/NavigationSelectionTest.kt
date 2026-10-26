package com.blazesystems.threadharbor

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class NavigationSelectionTest {
    private val tabs = listOf(
        "Browser", "Chats", "Downloads", "Files", "Gallery", "Inspection", "Calls", "Settings"
    )

    @Test fun mainTabsAreAlwaysInBounds() {
        tabs.forEachIndexed { index, title ->
            assertEquals(index, selectedHarborTabIndex(title, tabs))
        }
    }

    @Test fun hiddenDiagnosticsRetainChatsParentSelection() {
        assertEquals(1, selectedHarborTabIndex("Developer Lab", tabs))
    }

    @Test fun unknownScreenCanNeverCrashComposeTabRow() {
        assertEquals(0, selectedHarborTabIndex("missing-subpage", tabs))
        assertEquals(0, selectedHarborTabIndex("", tabs))
        assertTrue(selectedHarborTabIndex("missing-subpage", tabs) in tabs.indices)
    }
}
