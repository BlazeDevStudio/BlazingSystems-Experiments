package main

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func nodeRevSnapshot(t *testing.T, priv ed25519.PrivateKey, gen, validUntil int64, keys []string) []byte {
	t.Helper()
	now := time.Now().Unix()
	p := NodeRevocationPayload{Format: "connectit-node-revocations-v1", Generation: gen, GeneratedAt: now, ValidUntil: validUntil, RevokedNodeKeyHashes: keys}
	raw, _ := json.Marshal(p)
	doc, _ := json.Marshal(SignedNodeRevocations{Payload: p, Signature: base64.RawURLEncoding.EncodeToString(ed25519.Sign(priv, append([]byte(nodeRevocationPrefix), raw...)))})
	return doc
}
func TestNodeRevocationFailClosedAndPersistence(t *testing.T) {
	pub, priv, _ := ed25519.GenerateKey(rand.Reader)
	key, _, _ := ed25519.GenerateKey(rand.Reader)
	hash := sha256.Sum256(key)
	h := base64.RawURLEncoding.EncodeToString(hash[:])
	now := time.Now().Unix()
	path := filepath.Join(t.TempDir(), "node-cache.json")
	c := newNodeRevocationCache(pub, path)
	if c.check(key) == nil {
		t.Fatal("missing node list accepted")
	}
	fresh := nodeRevSnapshot(t, priv, 9, now+3500, []string{h})
	if e := c.accept(fresh, now); e != nil {
		t.Fatal(e)
	}
	if c.check(key) == nil {
		t.Fatal("revoked node accepted")
	}
	tampered := append([]byte{}, fresh...)
	tampered[len(tampered)-2] ^= 3
	if c.accept(tampered, now) == nil {
		t.Fatal("tampered node view accepted")
	}
	if c.accept(nodeRevSnapshot(t, priv, 8, now+3600, nil), now) == nil {
		t.Fatal("rollback node view accepted")
	}
	if c.accept(nodeRevSnapshot(t, priv, 10, now-1, nil), now) == nil {
		t.Fatal("expired node view accepted")
	}
	os.WriteFile(path, fresh, 0600)
	restored := newNodeRevocationCache(pub, path)
	if e := restored.load(); e != nil {
		t.Fatal(e)
	}
	if restored.check(key) == nil {
		t.Fatal("revoked node accepted after offline cache load")
	}
	good, _, _ := ed25519.GenerateKey(rand.Reader)
	if e := restored.check(good); e != nil {
		t.Fatal("valid unrevoked key denied", e)
	}
}
func TestNodeRevocationNetworkRefresh(t *testing.T) {
	pub, priv, _ := ed25519.GenerateKey(rand.Reader)
	c := newNodeRevocationCache(pub, filepath.Join(t.TempDir(), "snap"))
	payload := nodeRevSnapshot(t, priv, 1, time.Now().Unix()+3600, nil)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.Write(payload) }))
	if e := c.refresh(context.Background(), srv.URL+"/v1/node-revocations"); e != nil {
		t.Fatal(e)
	}
	srv.Close()
	offline := newNodeRevocationCache(pub, c.path)
	if e := offline.load(); e != nil {
		t.Fatal("offline cache", e)
	}
	if e := offline.refresh(context.Background(), "http://example.org/v1/node-revocations"); e == nil {
		t.Fatal("permitted cleartext public Master URL")
	}
}
func TestNodeRevocationRejectsRealSignedHTTPRequests(t *testing.T) {
	_, master, _ := ed25519.GenerateKey(rand.Reader)
	a := testNodeIdentity(t, master, "seed-a", []string{"seed-b"})
	b := testNodeIdentity(t, master, "seed-b", []string{"seed-a"})
	// The receiver obtains a signed Master snapshot revoking the sender key.
	h := sha256.Sum256(a.Private.Public().(ed25519.PublicKey))
	c := newNodeRevocationCache(master.Public().(ed25519.PublicKey), filepath.Join(t.TempDir(), "revoked.json"))
	if e := c.accept(nodeRevSnapshot(t, master, 3, time.Now().Unix()+3600, []string{base64.RawURLEncoding.EncodeToString(h[:])}), time.Now().Unix()); e != nil {
		t.Fatal(e)
	}
	b.Revocations = c
	r := httptest.NewRequest("GET", "http://example.org/internal/export?since=0", nil)
	if e := a.signRequest(r, "seed-b"); e != nil {
		t.Fatal(e)
	}
	if e := b.authorizeRequest(r); e == nil {
		t.Fatal("validly signed but revoked node accepted")
	}
	a.Revocations = c
	if e := a.signRequest(httptest.NewRequest("GET", "http://example.org/internal/export", nil), "seed-b"); e == nil {
		t.Fatal("local node signed using revoked key")
	}
}
func TestNodeCertificateRenewalHotRead(t *testing.T) {
	_, master, _ := ed25519.GenerateKey(rand.Reader)
	a := testNodeIdentity(t, master, "seed-a", []string{"seed-b"})
	path := a.CertFile
	// Valid same-key renewal without restarting the MeshIdentity object.
	p, _, e := checkNodeCertificate(a.Certificate, master.Public().(ed25519.PublicKey), time.Now().Unix())
	if e != nil {
		t.Fatal(e)
	}
	p.ExpiresAt += 3600
	signed, _ := json.Marshal(p)
	renewed, _ := json.Marshal(SignedNodeCertificate{Payload: p, Signature: base64.RawURLEncoding.EncodeToString(ed25519.Sign(master, append([]byte(nodeCertPrefix), signed...)))})
	if e := writeAtomic(path, renewed, 0600); e != nil {
		t.Fatal(e)
	}
	req := httptest.NewRequest("GET", "http://example.org/internal/export?since=0", nil)
	if e := a.signRequest(req, "seed-b"); e != nil {
		t.Fatal(e)
	}
	b, err := base64.RawURLEncoding.DecodeString(req.Header.Get("X-ConnectIT-Node-Cert"))
	if err != nil {
		t.Fatal(err)
	}
	var got SignedNodeCertificate
	if e := json.Unmarshal(b, &got); e != nil {
		t.Fatal(e)
	}
	if got.Payload.ExpiresAt != p.ExpiresAt {
		t.Fatal("used stale cert rather than hot-read renewal")
	}
	// Changing the cert to an unrelated node/key must fail closed.
	got.Payload.NodeID = "malicious"
	fake, _ := json.Marshal(got)
	writeAtomic(path, fake, 0600)
	if e := a.signRequest(httptest.NewRequest("GET", "http://example.org/internal/export", nil), "seed-b"); e == nil {
		t.Fatal("accepted unauthorized hot-swap")
	}
}
