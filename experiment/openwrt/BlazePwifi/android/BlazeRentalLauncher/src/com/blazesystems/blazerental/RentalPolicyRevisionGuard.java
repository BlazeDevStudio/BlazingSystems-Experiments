package com.blazesystems.blazerental;

/**
 * Pure compatibility check for refreshing a signed lease without rewriting an
 * existing launcher policy. This does NOT authenticate the response: callers
 * must validate both the coin-window and policy signatures, and reject stale
 * revisions, before invoking it. This class never writes Android state.
 */
final class RentalPolicyRevisionGuard {
    private RentalPolicyRevisionGuard() {}

    static boolean sameRevisionMayRefresh(RentalPolicy accepted, RentalPolicy proposed,
                                          String acceptedSignedPayload, String deviceId,
                                          String proposedSignedAllowedCsv) {
        // The stored v2/v3 payload records whether the already-accepted
        // policy used a wildcard BEFORE the installed inventory was expanded.
        // A changing installed-app inventory must not cause a same-revision
        // lease refresh to rewrite or widen accepted package restrictions.
        String[] oldFields = acceptedSignedPayload.split("\\|", -1);
        boolean acceptedWildcard = oldFields.length > 8
                && ("v2".equals(oldFields[0]) || "v3".equals(oldFields[0]))
                && deviceId.equals(oldFields[1])
                && Long.toString(proposed.getRevision()).equals(oldFields[5])
                && "*".equals(oldFields[7]);

        boolean allowedMatches = accepted.getAllowedPackages().equals(
                proposed.getAllowedPackages());
        return accepted.getLauncherMode().equals(proposed.getLauncherMode())
                && (allowedMatches || (acceptedWildcard
                        && "*".equals(proposedSignedAllowedCsv)))
                && accepted.getHiddenPackages().equals(proposed.getHiddenPackages());
    }
}
