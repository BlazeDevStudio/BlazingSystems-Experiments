package main

import (
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestSignedRevocationEndpointAndDeviceRevoke(t *testing.T) {
	a, dir, id, dev, pw := testSystem(t)
	nonce := rnd(22)
	install := rnd(24)
	submit(t, a, "/v1/enroll", map[string]any{"username": id, "password": pw, "device_public_key_b64": pub64(dev), "installation_id": install, "nonce": nonce, "proof_signature_b64": signDevice(dev, "ConnectIT-enroll-v1\n"+id+"\n"+nonce)}, 200)
	rows, e := a.db.run("SELECT id FROM devices WHERE account_id=?", id)
	if e != nil || len(rows) != 1 {
		t.Fatal(e, rows)
	}
	get := func() SignedRevocations {
		t.Helper()
		w := httptest.NewRecorder()
		req := httptest.NewRequest(http.MethodGet, "/v1/revocations", nil)
		mux := http.NewServeMux()
		a.routes(mux)
		mux.ServeHTTP(w, req)
		if w.Code != 200 {
			t.Fatalf("revocations HTTP %d: %s", w.Code, w.Body.String())
		}
		var s SignedRevocations
		if e := json.Unmarshal(w.Body.Bytes(), &s); e != nil {
			t.Fatal(e)
		}
		raw, _ := json.Marshal(s.Payload)
		sig, e := base64.RawURLEncoding.DecodeString(s.Signature)
		if e != nil || !ed25519.Verify(a.priv.Public().(ed25519.PublicKey), append([]byte("ConnectIT-revocations-v1\n"), raw...), sig) {
			t.Fatal("invalid signature")
		}
		if s.Payload.ValidUntil <= time.Now().Unix() || s.Payload.ValidUntil > time.Now().Add(61*time.Minute).Unix() {
			t.Fatal("bad validity window")
		}
		return s
	}
	before := get()
	if len(before.Payload.RevokedKeyHashes) != 0 {
		t.Fatal("fresh device revoked")
	}
	if e := revokeDevice(dir, rows[0]["id"]); e != nil {
		t.Fatal(e)
	}
	after := get()
	if after.Payload.Generation <= before.Payload.Generation {
		t.Fatal("generation not incremented")
	}
	h, e := deviceHash(pub64(dev))
	if e != nil || len(after.Payload.RevokedKeyHashes) != 1 || after.Payload.RevokedKeyHashes[0] != h {
		t.Fatalf("missing revoked key fingerprint: %+v", after.Payload)
	}
}
