package com.blazesystems.blazerental;

import java.util.Arrays;
import java.util.HashSet;
import org.junit.Test;
import static org.junit.Assert.*;

public class AppPolicySelectionTest {
    private static HashSet<String> set(String... values) {
        return new HashSet<String>(Arrays.asList(values));
    }

    @Test public void explicitHiddenPackageIsRemovedFromAllowlist() {
        AppPolicySelection selection = AppPolicySelection.of(
                set("com.example.game", "com.example.camera"),
                set("com.example.game"));
        assertFalse(selection.getAllowed().contains("com.example.game"));
        assertTrue(selection.getHidden().contains("com.example.game"));
        assertTrue(selection.getAllowed().contains("com.example.camera"));
    }

    @Test public void outputCsvIsStableForPolicyPatch() {
        AppPolicySelection selection = AppPolicySelection.of(
                set("com.z.app", "com.a.app"), set("com.m.hidden"));
        assertEquals("com.a.app,com.z.app", selection.allowedCsv());
        assertEquals("com.m.hidden", selection.hiddenCsv());
    }
}
