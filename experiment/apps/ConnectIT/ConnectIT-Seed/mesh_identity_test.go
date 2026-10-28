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
	"strings"
	"testing"
	"time"
)

func testNodeIdentity(t *testing.T, masterPriv ed25519.PrivateKey, id string, allowed []string) *MeshIdentity {
	t.Helper()
	pub, private, e := ed25519.GenerateKey(rand.Reader)
	if e != nil {
		t.Fatal(e)
	}
	now := time.Now().Unix()
	p := NodeCertificatePayload{Format: "connectit-seed-cert-v1", NodeID: id, PublicKey: base64.StdEncoding.EncodeToString(pub), IssuedAt: now - 2, ExpiresAt: now + 3600}
	raw, _ := json.Marshal(p)
	cert, _ := json.Marshal(SignedNodeCertificate{Payload: p, Signature: base64.RawURLEncoding.EncodeToString(ed25519.Sign(masterPriv, append([]byte(nodeCertPrefix), raw...)))})
	dir := t.TempDir()
	key := filepath.Join(dir, "node.private.key")
	certificate := filepath.Join(dir, "node.cert.json")
	if e = os.WriteFile(key, []byte(base64.StdEncoding.EncodeToString(private)), 0600); e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(certificate, cert, 0600); e != nil {
		t.Fatal(e)
	}
	out, e := newMeshIdentity(dir, id, certificate, key, masterPriv.Public().(ed25519.PublicKey), allowed)
	if e != nil {
		t.Fatal(e)
	}
	return out
}
func TestSignedMeshRequestReplayWrongTargetAndTamper(t *testing.T) {
	_, master, e := ed25519.GenerateKey(rand.Reader)
	if e != nil {
		t.Fatal(e)
	}
	a := testNodeIdentity(t, master, "seed-a", []string{"seed-b"})
	b := testNodeIdentity(t, master, "seed-b", []string{"seed-a"})
	r := httptest.NewRequest(http.MethodGet, "http://example.com/internal/export?since=31", nil)
	if e = a.signRequest(r, "seed-b"); e != nil {
		t.Fatal(e)
	}
	if e = b.authorizeRequest(r); e != nil {
		t.Fatalf("good signed request rejected: %v", e)
	}
	if e = b.authorizeRequest(r); e == nil {
		t.Fatal("replay accepted")
	}
	r2 := httptest.NewRequest(http.MethodGet, "http://example.com/internal/export?since=32", nil)
	r2.Header = r.Header.Clone()
	if e = b.authorizeRequest(r2); e == nil {
		t.Fatal("query changed but signature accepted")
	}
	r3 := httptest.NewRequest(http.MethodGet, "http://example.com/internal/export?since=1", nil)
	if e = a.signRequest(r3, "seed-mallory"); e != nil {
		t.Fatal(e)
	}
	if e = b.authorizeRequest(r3); e == nil {
		t.Fatal("wrong audience accepted")
	}
	mallory := testNodeIdentity(t, master, "seed-mallory", []string{"seed-b"})
	r4 := httptest.NewRequest(http.MethodGet, "http://example.com/internal/export?since=1", nil)
	if e = mallory.signRequest(r4, "seed-b"); e != nil {
		t.Fatal(e)
	}
	if e = b.authorizeRequest(r4); e == nil {
		t.Fatal("unallowlisted peer accepted")
	}
	r5 := httptest.NewRequest(http.MethodGet, "http://example.com/internal/export?since=1", nil)
	if e = a.signRequest(r5, "seed-b"); e != nil {
		t.Fatal(e)
	}
	r5.Header.Set("X-ConnectIT-Node-Time", "1")
	if e = b.authorizeRequest(r5); e == nil {
		t.Fatal("expired timestamp accepted")
	}
}
func TestSignedMeshResponseVerification(t *testing.T) {
	_, master, _ := ed25519.GenerateKey(rand.Reader)
	a := testNodeIdentity(t, master, "seed-a", []string{"seed-b"})
	b := testNodeIdentity(t, master, "seed-b", []string{"seed-a"})
	nonce := "0123456789abcdefghij"
	data := []byte(`{"messages":[],"cursor":0}`)
	h, e := b.signedResponse(nonce, 200, data)
	if e != nil {
		t.Fatal(e)
	}
	resp := &http.Response{StatusCode: 200, Header: h}
	if e = a.verifyResponse(resp, nonce, "seed-b", data); e != nil {
		t.Fatal(e)
	}
	if e = a.verifyResponse(resp, nonce, "seed-b", append(data, 'x')); e == nil {
		t.Fatal("tampered response body accepted")
	}
	if e = a.verifyResponse(resp, nonce, "seed-other", data); e == nil {
		t.Fatal("peer identity substitute accepted")
	}
	if e = a.verifyResponse(resp, nonce+"changed", "seed-b", data); e == nil {
		t.Fatal("incorrect request nonce accepted")
	}
	resp.StatusCode = 410
	if e = a.verifyResponse(resp, nonce, "seed-b", data); e == nil {
		t.Fatal("status code tampered")
	}
}
func TestNodeCertTamperingExpiryAndLocalKeyMismatch(t *testing.T) {
	_, master, _ := ed25519.GenerateKey(rand.Reader)
	a := testNodeIdentity(t, master, "seed-a", []string{"seed-b"})
	_, _, e := checkNodeCertificate(a.Certificate, master.Public().(ed25519.PublicKey), time.Now().Unix())
	if e != nil {
		t.Fatal(e)
	}
	if _, _, e = checkNodeCertificate(strings.Replace(a.Certificate, "seed-a", "seed-c", 1), master.Public().(ed25519.PublicKey), time.Now().Unix()); e == nil {
		t.Fatal("tampered certificate accepted")
	}
	_, alien, _ := ed25519.GenerateKey(rand.Reader)
	if _, _, e = checkNodeCertificate(a.Certificate, alien.Public().(ed25519.PublicKey), time.Now().Unix()); e == nil {
		t.Fatal("wrong Master accepted")
	}
	if _, _, e = checkNodeCertificate(a.Certificate, master.Public().(ed25519.PublicKey), time.Now().Add(2*time.Hour).Unix()); e == nil {
		t.Fatal("expired certificate accepted")
	}
	b := testNodeIdentity(t, master, "seed-b", []string{"seed-a"})
	dir := t.TempDir()
	c := filepath.Join(dir, "cert")
	k := filepath.Join(dir, "key")
	os.WriteFile(c, []byte(a.Certificate), 0600)
	os.WriteFile(k, []byte(base64.StdEncoding.EncodeToString(b.Private)), 0600)
	if _, e = newMeshIdentity(dir, "seed-a", c, k, master.Public().(ed25519.PublicKey), nil); e == nil {
		t.Fatal("private key/certificate mismatch accepted")
	}
}
func TestSignedExportRealSocket(t *testing.T) {
	_, master, _ := ed25519.GenerateKey(rand.Reader)
	a := testNodeIdentity(t, master, "seed-a", []string{"seed-b"})
	b := testNodeIdentity(t, master, "seed-b", []string{"seed-a"})
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if e := b.authorizeRequest(r); e != nil {
			http.Error(w, "not allowed", 403)
			return
		}
		signedExport(w, b, r.Header.Get("X-ConnectIT-Node-Nonce"), 200, MessageSet{Messages: []Message{}, Cursor: 4})
	}))
	defer server.Close()
	req, e := http.NewRequest("GET", server.URL+"/internal/export?since=0", nil)
	if e != nil {
		t.Fatal(e)
	}
	data, status, e := signedDownload(server.Client(), req, a, "seed-b")
	if e != nil || status != 200 || !strings.Contains(string(data), `"cursor":4`) {
		t.Fatalf("real signed HTTP %d %v %s", status, e, data)
	}
}
