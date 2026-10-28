package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"
	"time"
)

func TestDeviceEnvelopeOfflineValidation(t *testing.T) {
	masterPub, masterPriv, _ := ed25519.GenerateKey(rand.Reader)
	devPub, devPriv, _ := ed25519.GenerateKey(rand.Reader)
	cert := jwtIssueDevice(masterPriv, "alice", devPub, 24*time.Hour)
	m := Message{ID: "alice:example-id-123456", From: "alice", To: "bob", Kind: "message", Ciphertext: base64.StdEncoding.EncodeToString([]byte("opaque payload")), Created: time.Now().Unix(), SenderCertificate: cert}
	m.DeviceSignature = base64.RawURLEncoding.EncodeToString(ed25519.Sign(devPriv, envelopeSignedBytes(m)))
	if e := verifyEnvelope(m, masterPub, 8192); e != nil {
		t.Fatalf("valid envelope rejected: %v", e)
	}
	original := m
	m.To = "charlie"
	if e := verifyEnvelope(m, masterPub, 8192); e == nil {
		t.Fatal("recipient tampering accepted")
	}
	m = original
	m.Ciphertext = base64.StdEncoding.EncodeToString([]byte("changed"))
	if e := verifyEnvelope(m, masterPub, 8192); e == nil {
		t.Fatal("ciphertext tampering accepted")
	}
	m = original
	m.Created = time.Now().Add(-4 * time.Minute).Unix()
	m.Kind = "signal"
	m.DeviceSignature = base64.RawURLEncoding.EncodeToString(ed25519.Sign(devPriv, envelopeSignedBytes(m)))
	if e := verifyEnvelope(m, masterPub, 8192); e == nil {
		t.Fatal("expired call signal accepted")
	}
	otherPub, _, _ := ed25519.GenerateKey(rand.Reader)
	if e := verifyEnvelope(original, otherPub, 8192); e == nil {
		t.Fatal("untrusted master accepted")
	}
}
func TestDeviceRequestProofAndReplay(t *testing.T) {
	pub, priv, _ := ed25519.GenerateKey(rand.Reader)
	target := "http://example.org/v1/messages?since=0"
	body := []byte("test-request-body")
	req := httptest.NewRequest(http.MethodPost, target, bytes.NewReader(body))
	ts := strconv.FormatInt(time.Now().Unix(), 10)
	nonce := base64.RawURLEncoding.EncodeToString([]byte(strings.Repeat("a", 24)))
	sig := ed25519.Sign(priv, requestProof(req.Method, req.Host, req.URL.RequestURI(), ts, nonce, body))
	req.Header.Set("X-Device-Time", ts)
	req.Header.Set("X-Device-Nonce", nonce)
	req.Header.Set("X-Device-Signature", base64.RawURLEncoding.EncodeToString(sig))
	cache := newReplayCache()
	if e := verifyDeviceProof(req, base64.StdEncoding.EncodeToString(pub), cache); e != nil {
		t.Fatalf("valid proof rejected: %v", e)
	}
	req2 := httptest.NewRequest(http.MethodPost, target, bytes.NewReader(body))
	req2.Header = req.Header.Clone()
	if e := verifyDeviceProof(req2, base64.StdEncoding.EncodeToString(pub), cache); e == nil {
		t.Fatal("replay accepted")
	}
	req3 := httptest.NewRequest(http.MethodPost, target, bytes.NewReader([]byte("tampered body")))
	req3.Header = req.Header.Clone()
	req3.Header.Set("X-Device-Nonce", base64.RawURLEncoding.EncodeToString([]byte(strings.Repeat("b", 24))))
	if e := verifyDeviceProof(req3, base64.StdEncoding.EncodeToString(pub), cache); e == nil {
		t.Fatal("body tamper accepted")
	}
}
func TestDisallowRemotePlainHTTP(t *testing.T) {
	if e := requireSafeHTTP("http://203.0.113.9:8080"); e == nil {
		t.Fatal("remote plaintext HTTP accepted")
	}
	if e := requireSafeHTTP("http://127.0.0.1:8080"); e != nil {
		t.Fatal(e)
	}
	if e := requireSafeHTTP("https://seed.example.org"); e != nil {
		t.Fatal(e)
	}
}
