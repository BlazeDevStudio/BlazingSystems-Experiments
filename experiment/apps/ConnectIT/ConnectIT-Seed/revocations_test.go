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

func testRevBytes(t *testing.T, sk ed25519.PrivateKey, gen, expiry int64, hashes []string) []byte {
	t.Helper()
	now := time.Now().Unix()
	p := RevocationPayload{"connectit-revocations-v1", gen, now, expiry, hashes}
	raw, _ := json.Marshal(p)
	sig := ed25519.Sign(sk, append([]byte("ConnectIT-revocations-v1\n"), raw...))
	data, _ := json.Marshal(SignedRevocations{p, base64.RawURLEncoding.EncodeToString(sig)})
	return data
}
func TestRevocationsSignatureExpiredRollbackAndReload(t *testing.T) {
	pub, sk, _ := ed25519.GenerateKey(rand.Reader)
	dp, _, _ := ed25519.GenerateKey(rand.Reader)
	h := sha256.Sum256(dp)
	hash := base64.RawURLEncoding.EncodeToString(h[:])
	pk := base64.StdEncoding.EncodeToString(dp)
	c := newRevocationCache(pub, filepath.Join(t.TempDir(), "snapshot.json"))
	if c.check(pk) == nil {
		t.Fatal("uninitialized cache accepted")
	}
	now := time.Now().Unix()
	a := testRevBytes(t, sk, 2, now+3500, []string{hash})
	if e := c.accept(a, now); e != nil {
		t.Fatal(e)
	}
	if e := c.check(pk); e == nil {
		t.Fatal("revoked key accepted")
	}
	copyA := append([]byte{}, a...)
	copyA[len(copyA)-3] ^= 1
	if c.accept(copyA, now) == nil {
		t.Fatal("tampered signature accepted")
	}
	if c.accept(testRevBytes(t, sk, 1, now+3500, nil), now) == nil {
		t.Fatal("generation rollback accepted")
	}
	if c.accept(testRevBytes(t, sk, 3, now-1, nil), now) == nil {
		t.Fatal("expired view accepted")
	}
	if e := writeAtomic(c.path, a, 0600); e != nil {
		t.Fatal(e)
	}
	restored := newRevocationCache(pub, c.path)
	if e := restored.load(); e != nil {
		t.Fatal(e)
	}
	if restored.check(pk) == nil {
		t.Fatal("revocation lost on restart")
	}
}
func TestRevocationsFetchAndMasterOutageCache(t *testing.T) {
	pub, sk, _ := ed25519.GenerateKey(rand.Reader)
	p := newRevocationCache(pub, filepath.Join(t.TempDir(), "snapshot.json"))
	snapshot := testRevBytes(t, sk, 9, time.Now().Unix()+3600, nil)
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/revocations", func(w http.ResponseWriter, r *http.Request) { w.Write(snapshot) })
	srv := httptest.NewServer(mux)
	if e := p.refresh(context.Background(), srv.URL+"/v1/revocations"); e != nil {
		t.Fatal(e)
	}
	srv.Close()
	q := newRevocationCache(pub, p.path)
	if e := q.load(); e != nil {
		t.Fatalf("failed offline cached load: %v", e)
	}
	if _, e := os.Stat(p.path); e != nil {
		t.Fatal(e)
	}
	if e := p.refresh(context.Background(), "http://example.com/v1/revocations"); e == nil {
		t.Fatal("cleartext internet refresh allowed")
	}
}
