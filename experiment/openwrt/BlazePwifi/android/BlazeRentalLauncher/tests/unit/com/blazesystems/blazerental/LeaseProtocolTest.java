package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;

public class LeaseProtocolTest {
    @Test public void statusAuthenticationCanonicalizationIsStable() throws Exception {
        assertEquals(
                "d3da368b0cd5d70736d1070bf9c1e3e3bc630f576f357c87780bd336bef89aae",
                Hmac.sha256Hex("secret", "status|nonce123|secret"));
    }

    @Test public void enrollmentAuthenticationCanonicalizationIsStable() throws Exception {
        assertEquals(
                "e6b45dafdfbcd5bd2e0ad684e7758a133e652e7c05026dce8df2293c382a0ca7",
                Hmac.sha256Hex("enroll.secret", "enroll|abc|enroll.secret"));
    }

    @Test public void noncesAreUniqueAndHexEncoded() {
        String first = Hmac.nonce();
        String second = Hmac.nonce();
        assertEquals(32, first.length());
        assertTrue(first.matches("[0-9a-f]{32}"));
        assertNotEquals(first, second);
    }
}
