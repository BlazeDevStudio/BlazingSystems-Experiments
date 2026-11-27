package com.blazesystems.blazerental;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import org.junit.Test;
import static org.junit.Assert.*;

public class RentalPolicyTest {
    private static Set<String> set(String... values) {
        return new HashSet<String>(Arrays.asList(values));
    }

    @Test public void rentalModeRequiresExplicitAllow() {
        RentalPolicy p = new RentalPolicy(1L, RentalPolicy.MODE_RENTAL,
                set("com.example.game"), set("com.example.hidden"), null);
        assertTrue(p.isPackageAllowed("com.example.game"));
        assertFalse(p.isPackageAllowed("com.example.other"));
        assertFalse(p.isPackageAllowed("com.example.hidden"));
    }

    @Test public void sensitivePackageIsForcedHiddenInRentalMode() {
        RentalPolicy p = new RentalPolicy(1L, RentalPolicy.MODE_RENTAL,
                set("com.android.settings"), null, null);
        assertFalse(p.isPackageAllowed("com.android.settings"));
    }

    @Test public void unrestrictedModeDoesNotLeaseGateApps() {
        RentalPolicy p = new RentalPolicy(2L, RentalPolicy.MODE_UNRESTRICTED,
                null, set("com.example.hidden"), null);
        assertTrue(p.isPackageAllowed("com.example.hidden"));
        assertTrue(p.isPackageAllowed("com.android.settings"));
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsMalformedMode() {
        new RentalPolicy(1L, "broken", null, null, null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsMalformedPackage() {
        new RentalPolicy(1L, RentalPolicy.MODE_RENTAL, set("not valid"), null, null);
    }
}
