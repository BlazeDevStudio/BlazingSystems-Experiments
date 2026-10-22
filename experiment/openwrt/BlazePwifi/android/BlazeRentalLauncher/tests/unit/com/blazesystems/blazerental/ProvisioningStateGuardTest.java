package com.blazesystems.blazerental;

import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class ProvisioningStateGuardTest {
    private static final String SERVER = "https://192.168.1.1";
    private static final String TOKEN = "0123456789ab.0123456789abcdef";
    private static final String PIN =
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

    @Test
    public void freshStateAcceptsFirstProvisioningIdentity() {
        assertTrue(ProvisioningStateGuard.canAccept(
                "", "", "", "", "", "", SERVER, TOKEN, PIN));
    }

    @Test
    public void exactSetupWizardReplayIsIdempotent() {
        assertTrue(ProvisioningStateGuard.canAccept(
                "device_owner_provisioning", SERVER, TOKEN, PIN, "", "",
                SERVER, TOKEN, PIN));
        assertTrue(ProvisioningStateGuard.isExactReplay(
                "device_owner_provisioning", SERVER, TOKEN, PIN,
                SERVER, TOKEN, PIN));
    }

    @Test
    public void changedTokenCannotReplacePendingProvisioningIdentity() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "device_owner_provisioning", SERVER, TOKEN, PIN, "", "",
                SERVER, "fedcba987654.abcdef0123456789", PIN));
    }

    @Test
    public void changedServerCannotReplacePendingProvisioningIdentity() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "device_owner_provisioning", SERVER, TOKEN, PIN, "", "",
                "https://192.168.1.2", TOKEN, PIN));
    }

    @Test
    public void changedCertificatePinCannotReplacePendingProvisioningIdentity() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "device_owner_provisioning", SERVER, TOKEN, PIN, "", "",
                SERVER, TOKEN,
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"));
    }

    @Test
    public void manualPendingEnrollmentCannotBeSilentlyOverwritten() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "standard_manual", SERVER, TOKEN, PIN, "", "",
                SERVER, TOKEN, PIN));
    }

    @Test
    public void partialPermanentIdentityFailsClosed() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "", "", "", "", "00112233445566778899aabb", "",
                SERVER, TOKEN, PIN));
        assertFalse(ProvisioningStateGuard.canAccept(
                "", "", "", "", "", "deadbeef",
                SERVER, TOKEN, PIN));
    }

    @Test
    public void interruptedStateWithOnlyServerCannotChangeOrigin() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "", SERVER, "", "", "", "",
                "https://192.168.1.2", TOKEN, PIN));
    }

    @Test
    public void interruptedStateWithOnlyCertificatePinCannotChangeTrustAnchor() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "", "", "", PIN, "", "",
                SERVER, TOKEN, PIN));
    }

    @Test
    public void interruptedStateWithSourceAndNoTokenFailsClosed() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "device_owner_provisioning", SERVER, "", PIN, "", "",
                SERVER, TOKEN, PIN));
    }

    @Test
    public void interruptedStateWithOnlyOriginAndPinCannotBeReplaced() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "", SERVER, "", PIN, "", "",
                SERVER, TOKEN, PIN));
    }

    @Test
    public void freshStateRejectsIncompleteNewProvisioningIdentity() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "", "", "", "", "", "",
                "", TOKEN, PIN));
        assertFalse(ProvisioningStateGuard.canAccept(
                "", "", "", "", "", "",
                SERVER, "", PIN));
        assertFalse(ProvisioningStateGuard.canAccept(
                "", "", "", "", "", "",
                SERVER, TOKEN, ""));
    }

    @Test
    public void replayWithoutCompleteOriginalIdentityIsNotAccepted() {
        assertFalse(ProvisioningStateGuard.isExactReplay(
                "device_owner_provisioning", SERVER, TOKEN, "",
                SERVER, TOKEN, ""));
        assertFalse(ProvisioningStateGuard.isExactReplay(
                "device_owner_provisioning", "", TOKEN, PIN,
                "", TOKEN, PIN));
    }

    @Test
    public void deviceOwnerCompletionRequiresProvisioningSource() {
        assertTrue(ProvisioningStateGuard.isProvisioningSource("device_owner_provisioning"));
        assertFalse(ProvisioningStateGuard.isProvisioningSource("standard_manual"));
        assertFalse(ProvisioningStateGuard.isProvisioningSource(""));
    }

    @Test
    public void permanentIdentityCannotBeReprovisionedByCallback() {
        assertFalse(ProvisioningStateGuard.canAccept(
                "device_owner_provisioning", SERVER, "", PIN,
                "00112233445566778899aabb",
                "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                SERVER, TOKEN, PIN));
    }
}
