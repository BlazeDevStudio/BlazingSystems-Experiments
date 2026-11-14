package com.blazesystems.blazerental;

import org.junit.Test;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import static org.junit.Assert.*;

/** Host-JVM guards for read-only same-revision lease refresh decisions. */
public final class RentalPolicyRevisionGuardTest {
    private static final String DEVICE = "0123456789abcdef01234567";

    private static Set<String> apps(String... names) {
        Set<String> result = new HashSet<String>();
        Collections.addAll(result, names);
        return result;
    }

    private static RentalPolicy policy(long revision, String mode,
                                       Set<String> allowed, Set<String> hidden) {
        return new RentalPolicy(revision, mode, allowed, hidden,
                Collections.<String>emptySet());
    }

    private static String stored(String allowed, long revision) {
        return "v3|" + DEVICE + "|nonce|100|200|" + revision
                + "|rental|" + allowed + "||||4096||600|overlay|1||1|hold|4000|0";
    }

    @Test public void equalPolicyAllowsSameRevisionLeaseRefresh() {
        RentalPolicy old = policy(7, "rental", apps("com.example.a"), apps("com.example.b"));
        RentalPolicy proposed = policy(7, "rental", apps("com.example.a"), apps("com.example.b"));
        assertTrue(RentalPolicyRevisionGuard.sameRevisionMayRefresh(
                old, proposed, stored("com.example.a", 7), DEVICE, "com.example.a"));
    }

    @Test public void authenticatedWildcardCanRefreshAfterInventoryChanges() {
        RentalPolicy old = policy(7, "rental", apps("com.example.old"), apps());
        RentalPolicy proposed = policy(7, "rental", apps("com.example.new"), apps());
        assertTrue(RentalPolicyRevisionGuard.sameRevisionMayRefresh(
                old, proposed, stored("*", 7), DEVICE, "*"));
    }

    @Test public void explicitPackageRestrictionCannotBecomeWildcard() {
        RentalPolicy old = policy(7, "rental", apps("com.example.old"), apps());
        RentalPolicy proposed = policy(7, "rental", apps("com.example.new"), apps());
        assertFalse(RentalPolicyRevisionGuard.sameRevisionMayRefresh(
                old, proposed, stored("com.example.old", 7), DEVICE, "*"));
    }

    @Test public void wildcardCannotExcuseDifferentExplicitAllowedList() {
        RentalPolicy old = policy(7, "rental", apps("com.example.old"), apps());
        RentalPolicy proposed = policy(7, "rental", apps("com.example.new"), apps());
        assertFalse(RentalPolicyRevisionGuard.sameRevisionMayRefresh(
                old, proposed, stored("*", 7), DEVICE, "com.example.new"));
    }

    @Test public void priorWildcardMustMatchDeviceAndRevision() {
        RentalPolicy old = policy(7, "rental", apps("com.example.old"), apps());
        RentalPolicy proposed = policy(7, "rental", apps("com.example.new"), apps());
        assertFalse(RentalPolicyRevisionGuard.sameRevisionMayRefresh(
                old, proposed, stored("*", 8), DEVICE, "*"));
        assertFalse(RentalPolicyRevisionGuard.sameRevisionMayRefresh(
                old, proposed, stored("*", 7).replace(DEVICE, "wrong-device"), DEVICE, "*"));
    }

    @Test public void modeOrHiddenPackageChangeIsNotLeaseRefresh() {
        RentalPolicy old = policy(7, "rental", apps("com.example.a"), apps());
        assertFalse(RentalPolicyRevisionGuard.sameRevisionMayRefresh(
                old, policy(7, "unrestricted", apps("com.example.a"), apps()),
                stored("*", 7), DEVICE, "*"));
        assertFalse(RentalPolicyRevisionGuard.sameRevisionMayRefresh(
                old, policy(7, "rental", apps("com.example.a"), apps("com.example.b")),
                stored("*", 7), DEVICE, "*"));
    }
}
