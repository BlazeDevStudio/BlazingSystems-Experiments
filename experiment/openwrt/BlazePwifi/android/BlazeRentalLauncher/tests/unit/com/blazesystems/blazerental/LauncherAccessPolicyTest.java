package com.blazesystems.blazerental;

import java.util.Arrays;
import java.util.HashSet;
import org.junit.Test;
import static org.junit.Assert.*;

public class LauncherAccessPolicyTest {
    @Test public void hiddenAppStaysBlockedEvenIfAlsoAllowed() {
        RentalPolicy p = new RentalPolicy(9L, RentalPolicy.MODE_RENTAL,
                new HashSet<String>(Arrays.asList("com.example.app")),
                new HashSet<String>(Arrays.asList("com.example.app")), null);
        assertFalse(p.isPackageAllowed("com.example.app"));
    }

    @Test public void unrestrictedModeExposesSettings() {
        RentalPolicy p = new RentalPolicy(10L, RentalPolicy.MODE_UNRESTRICTED,
                null, null, null);
        assertTrue(p.isPackageAllowed("com.android.settings"));
    }
}
