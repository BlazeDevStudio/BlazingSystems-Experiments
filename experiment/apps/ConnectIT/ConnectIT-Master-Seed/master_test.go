package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"
)

func testSystem(t *testing.T) (*api, string, string, ed25519.PrivateKey, string) {
	t.Helper()
	dir := t.TempDir()
	if e := initMaster(dir, "Temporary-Admin-Password-987"); e != nil {
		t.Fatal(e)
	}
	d, e := openDB(dbpath(dir))
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(d.close)
	ready, e := rotated(d)
	if e != nil || ready {
		t.Fatal("temporary admin not enforced", e)
	}
	if e := rotateAdmin(dir, "Temporary-Admin-Password-987", "Different-Admin-Password-543"); e != nil {
		t.Fatal(e)
	}
	if e := createAccount(dir, "Test User", "Strong-Account-Password-976"); e != nil {
		t.Fatal(e)
	}
	arow, e := d.run("SELECT id FROM accounts")
	if e != nil || len(arow) != 1 {
		t.Fatal(e)
	}
	id := arow[0]["id"]
	if !validID(id) {
		t.Fatalf("invalid id: %q", id)
	}
	priv, err := readKey(dir, "private.key", 64)
	if err != nil {
		t.Fatal(err)
	}
	key, err := readKey(dir, "install-hmac.key", 32)
	if err != nil {
		t.Fatal(err)
	}
	api := &api{db: d, priv: ed25519.PrivateKey(priv), hmacKey: key, attempts: map[string]rate{}}
	_, device, e := ed25519.GenerateKey(rand.Reader)
	if e != nil {
		t.Fatal(e)
	}
	return api, dir, id, device, "Strong-Account-Password-976"
}
func submit(t *testing.T, a *api, path string, in any, expected int) map[string]any {
	t.Helper()
	b, e := json.Marshal(in)
	if e != nil {
		t.Fatal(e)
	}
	req := httptest.NewRequest("POST", "http://127.0.0.1:7070"+path, bytes.NewReader(b))
	w := httptest.NewRecorder()
	mux := http.NewServeMux()
	a.routes(mux)
	mux.ServeHTTP(w, req)
	if w.Code != expected {
		t.Fatalf("%s code %d != %d: %s", path, w.Code, expected, w.Body.String())
	}
	var out map[string]any
	json.Unmarshal(w.Body.Bytes(), &out)
	return out
}
func signDevice(d ed25519.PrivateKey, s string) string {
	return base64.RawURLEncoding.EncodeToString(ed25519.Sign(d, []byte(s)))
}
func pub64(d ed25519.PrivateKey) string { return b64(d.Public().(ed25519.PublicKey)) }
func TestIdentityAndFirstDevice(t *testing.T) {
	a, dir, id, dev, pw := testSystem(t)
	nonce := rnd(22)
	installation := rnd(24)
	request := map[string]any{"username": id, "password": pw, "device_public_key_b64": pub64(dev), "installation_id": installation, "nonce": nonce, "proof_signature_b64": signDevice(dev, "ConnectIT-enroll-v1\n"+id+"\n"+nonce)}
	resp := submit(t, a, "/v1/enroll", request, 200)
	if resp["device_certificate"] == "" {
		t.Fatal("no certificate")
	}
	request["nonce"] = rnd(22)
	request["proof_signature_b64"] = signDevice(dev, "ConnectIT-enroll-v1\n"+id+"\n"+request["nonce"].(string))
	submit(t, a, "/v1/enroll", request, 200)
	_, second, _ := ed25519.GenerateKey(rand.Reader)
	request["device_public_key_b64"] = pub64(second)
	request["nonce"] = rnd(22)
	request["proof_signature_b64"] = signDevice(second, "ConnectIT-enroll-v1\n"+id+"\n"+request["nonce"].(string))
	submit(t, a, "/v1/enroll", request, 409)
	_, _ = os.Stat(filepath.Join(dir, "connectit.sqlite3"))
}
func signedRequest(t *testing.T, a *api, device ed25519.PrivateKey, cert string, body any, path string, code int) map[string]any {
	t.Helper()
	raw, _ := json.Marshal(body)
	req := httptest.NewRequest("POST", "http://127.0.0.1:7070"+path, bytes.NewReader(raw))
	ts := strconv.FormatInt(time.Now().Unix(), 10)
	nonce := rnd(22)
	sum := sha256.Sum256(raw)
	proof := "POST\n" + req.Host + "\n" + req.URL.RequestURI() + "\n" + ts + "\n" + nonce + "\n" + hex.EncodeToString(sum[:])
	req.Header.Set("Authorization", "Bearer "+cert)
	req.Header.Set("X-Device-Time", ts)
	req.Header.Set("X-Device-Nonce", nonce)
	req.Header.Set("X-Device-Signature", signDevice(device, proof))
	w := httptest.NewRecorder()
	mux := http.NewServeMux()
	a.routes(mux)
	mux.ServeHTTP(w, req)
	if w.Code != code {
		t.Fatalf("decision code %d != %d: %s", w.Code, code, w.Body.String())
	}
	var v map[string]any
	json.Unmarshal(w.Body.Bytes(), &v)
	return v
}
func TestSecureBindReplayAndCountdown(t *testing.T) {
	a, _, id, original, pw := testSystem(t)
	originalInstall := rnd(24)
	nonce := rnd(22)
	entry := map[string]any{"username": id, "password": pw, "device_public_key_b64": pub64(original), "installation_id": originalInstall, "nonce": nonce, "proof_signature_b64": signDevice(original, "ConnectIT-enroll-v1\n"+id+"\n"+nonce)}
	r := submit(t, a, "/v1/enroll", entry, 200)
	cert := r["device_certificate"].(string)
	_, target, _ := ed25519.GenerateKey(rand.Reader)
	nonce = rnd(22)
	bind := map[string]any{"username": id, "password": pw, "device_public_key_b64": pub64(target), "installation_id": rnd(24), "nonce": nonce, "proof_signature_b64": signDevice(target, "ConnectIT-bind-start-v1\n"+id+"\n"+nonce), "confirmed": true}
	started := submit(t, a, "/v1/bind/start", bind, 202)
	bid := started["binding_id"].(string)
	finalNonce := rnd(22)
	fin := map[string]any{"username": id, "password": pw, "binding_id": bid, "nonce": finalNonce, "proof_signature_b64": signDevice(target, "ConnectIT-bind-finalize-v1\n"+bid+"\n"+finalNonce)}
	submit(t, a, "/v1/bind/finalize", fin, 409) // timer alone can never bypass approval
	rows, e := a.db.run("SELECT id FROM devices WHERE account_id=?", id)
	if e != nil || len(rows) != 1 {
		t.Fatal(e)
	}
	trustedID := rows[0]["id"]
	issued := time.Now().Unix()
	approvalID := rnd(22)
	canonical := fmtSecureBind(bid, approvalID, trustedID, pub64(target), started["challenge"].(string), 0, issued, "approve")
	decision := map[string]any{"binding_id": bid, "approval_id": approvalID, "action": "approve", "issued": issued, "interval_index": 0, "signature_b64": signDevice(original, canonical)}
	signedRequest(t, a, original, cert, decision, "/v1/bind/decision", 200)
	signedRequest(t, a, original, cert, decision, "/v1/bind/decision", 409) // same interval/replay rejected
	submit(t, a, "/v1/bind/finalize", fin, 409)                             // approval doesn't bypass the 4-hour-minus-30min delay
	// Test clock evolution by modifying only the TEST database (not the production server clock).
	_, e = a.db.run("UPDATE bindings SET started=? WHERE id=?", time.Now().Unix()-15000, bid)
	if e != nil {
		t.Fatal(e)
	}
	submit(t, a, "/v1/bind/finalize", fin, 200)
	submit(t, a, "/v1/bind/finalize", fin, 409) // duplicate finalize fails
}
func fmtSecureBind(bid, aid, device, key, challenge string, interval int, issued int64, action string) string {
	return strings.Join([]string{"ConnectIT-SecureBind-v1", bid, aid, device, key, challenge, strconv.Itoa(interval), strconv.FormatInt(issued, 10), action}, "\n")
}
func TestRejectInvalidSignatureAndTenDigitFormat(t *testing.T) {
	_, priv, _ := ed25519.GenerateKey(rand.Reader)
	if validID("100") || validID("000000000a") || !validID("0000000001") {
		t.Fatal("ID formatting")
	}
	if signedProof(pub64(priv), "auth", "wrong") {
		t.Fatal("wrong sig accepted")
	}
}
