package com.blazesystems.blazerental;

/**
 * Holds only a previously signature-verified policy. Storage is abstracted so
 * pure JVM tests do not depend on Android SharedPreferences.
 */
public final class RentalPolicyStore {
    public interface Storage {
        StoredPolicy load();
        void save(StoredPolicy storedPolicy);
    }

    public static final class StoredPolicy {
        public final RentalPolicy policy;
        public final String signedPayload;
        public final String signature;

        public StoredPolicy(RentalPolicy policy, String signedPayload, String signature) {
            if (policy == null) {
                throw new IllegalArgumentException("policy is required");
            }
            if (signedPayload == null || signedPayload.length() == 0) {
                throw new IllegalArgumentException("signedPayload is required");
            }
            if (signature == null || signature.length() == 0) {
                throw new IllegalArgumentException("signature is required");
            }
            this.policy = policy;
            this.signedPayload = signedPayload;
            this.signature = signature;
        }
    }

    private final Storage storage;
    private StoredPolicy current;

    public RentalPolicyStore(Storage storage) {
        if (storage == null) {
            throw new IllegalArgumentException("storage is required");
        }
        this.storage = storage;
        this.current = storage.load();
    }

    public StoredPolicy getCurrent() {
        return current;
    }

    /**
     * Accept a policy only after the caller has verified its server signature.
     * Equal/older revisions never replace the current policy.
     */
    public boolean applyVerified(StoredPolicy candidate, boolean signatureVerified) {
        if (!signatureVerified) {
            return false;
        }
        if (candidate == null) {
            throw new IllegalArgumentException("candidate is required");
        }
        if (current != null && candidate.policy.getRevision() <= current.policy.getRevision()) {
            return false;
        }
        storage.save(candidate);
        current = candidate;
        return true;
    }
}
