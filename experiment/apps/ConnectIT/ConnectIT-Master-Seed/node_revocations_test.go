package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestNodeRevokeOldCertificateAndSameKeyRenewalDenied(t *testing.T) {
	dir := t.TempDir()
	if e := initMaster(dir, "initial-master-password-0123456789"); e != nil {
		t.Fatal(e)
	}
	if e := rotateAdmin(dir, "initial-master-password-0123456789", "rotated-master-password-0123456789"); e != nil {
		t.Fatal(e)
	}
	pub, _, _ := ed25519.GenerateKey(rand.Reader)
	input := filepath.Join(dir, "node.pub")
	os.WriteFile(input, []byte(base64.StdEncoding.EncodeToString(pub)), 0600)
	legacy := filepath.Join(dir, "legacy.cert.json")
	if e := nodeAuthorize(dir, "seed-a", input, legacy, 24); e != nil {
		t.Fatal(e)
	}
	if e := nodeAuthorize(dir, "seed-impostor", input, filepath.Join(dir, "alien-id.cert"), 24); e == nil {
		t.Fatal("node key reused under another node ID")
	}
	if e := nodeRevoke(dir, legacy); e != nil {
		t.Fatal(e)
	}
	if e := nodeRevoke(dir, legacy); e != nil {
		t.Fatal("idempotent revoke:", e)
	}
	if e := nodeAuthorize(dir, "seed-a", input, filepath.Join(dir, "renew.cert"), 24); e == nil {
		t.Fatal("revoked signing key renewed")
	}
	priv, e := readKey(dir, "private.key", 64)
	if e != nil {
		t.Fatal(e)
	}
	d, e := openDB(dbpath(dir))
	if e != nil {
		t.Fatal(e)
	}
	defer d.close()
	a := &api{db: d, priv: priv}
	w := httptest.NewRecorder()
	a.nodeRevocations(w, httptest.NewRequest(http.MethodGet, "/v1/node-revocations", nil))
	if w.Code != 200 {
		t.Fatal(w.Code, w.Body)
	}
	var signed SignedNodeRevocations
	if e = json.Unmarshal(w.Body.Bytes(), &signed); e != nil {
		t.Fatal(e)
	}
	if len(signed.Payload.RevokedNodeKeyHashes) != 1 || signed.Payload.Generation != 1 {
		t.Fatalf("bad signed node revocation: %+v", signed.Payload)
	}
	ePub, _, _ := ed25519.GenerateKey(rand.Reader)
	source2 := filepath.Join(dir, "node2.pub")
	os.WriteFile(source2, []byte(base64.StdEncoding.EncodeToString(ePub)), 0600)
	if e := nodeAuthorize(dir, "seed-a", source2, filepath.Join(dir, "new-key.cert"), 24); e != nil {
		t.Fatal("new key needed for recovery:", e)
	}
	w = httptest.NewRecorder()
	a.nodeRevocations(w, httptest.NewRequest(http.MethodGet, "/v1/node-revocations", nil))
	if w.Code != 200 {
		t.Fatal(w.Code)
	}
	if e = json.Unmarshal(w.Body.Bytes(), &signed); e != nil {
		t.Fatal(e)
	}
	if signed.Payload.Generation != 1 {
		t.Fatal("issuance must not reset or advance revoked keys")
	}
}
func TestNodeRevokeRejectsForgeryFromAnotherMaster(t *testing.T) {
	d := t.TempDir()
	if e := initMaster(d, "temporary-admin-password-1234"); e != nil {
		t.Fatal(e)
	}
	other := t.TempDir()
	if e := initMaster(other, "another-admin-password-5678"); e != nil {
		t.Fatal(e)
	}
	if e := rotateAdmin(other, "another-admin-password-5678", "other-rotated-password-5678"); e != nil {
		t.Fatal(e)
	}
	pub, _, _ := ed25519.GenerateKey(rand.Reader)
	file := filepath.Join(other, "pub")
	os.WriteFile(file, []byte(base64.StdEncoding.EncodeToString(pub)), 0600)
	cert := filepath.Join(other, "issued.json")
	if e := nodeAuthorize(other, "seed-foreign", file, cert, 1); e != nil {
		t.Fatal(e)
	}
	if e := nodeRevoke(d, cert); e == nil {
		t.Fatal("accepted foreign Master-signed node cert")
	}
	// Long-lived old cert expiry must NOT prevent revoking its key.
	p, _ := readKey(other, "private.key", 64)
	now := time.Now().Unix()
	pc := NodeCertificatePayload{Format: "connectit-seed-cert-v1", NodeID: "seed-foreign", PublicKey: base64.StdEncoding.EncodeToString(pub), IssuedAt: now - 48*3600, ExpiresAt: now - 24*3600}
	raw, _ := json.Marshal(pc)
	signed := SignedNodeCertificate{Payload: pc, Signature: base64.RawURLEncoding.EncodeToString(ed25519.Sign(p, append([]byte("ConnectIT-seed-cert-v1\n"), raw...)))}
	old, _ := json.Marshal(signed)
	os.WriteFile(cert, old, 0600)
	if e := nodeRevoke(other, cert); e != nil {
		t.Fatal("expired genuine cert should remain revocable: ", e)
	}
}
