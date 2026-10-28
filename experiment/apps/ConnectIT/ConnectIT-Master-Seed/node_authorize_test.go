package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestNodeAuthorizeRequiresRotationAndSignedCert(t *testing.T) {
	d := t.TempDir()
	if e := initMaster(d, "InitialSecurePassphrase#21"); e != nil {
		t.Fatal(e)
	}
	pub, _, e := ed25519.GenerateKey(rand.Reader)
	if e != nil {
		t.Fatal(e)
	}
	source := filepath.Join(d, "node.public.key")
	out := filepath.Join(d, "node.cert.json")
	if e = os.WriteFile(source, []byte(base64.StdEncoding.EncodeToString(pub)), 0644); e != nil {
		t.Fatal(e)
	}
	if e = nodeAuthorize(d, "seed-a", source, out, 24); e == nil {
		t.Fatal("issued certificate with unrotated admin")
	}
	if e = rotateAdmin(d, "InitialSecurePassphrase#21", "DifferentSecureAdminPassword#22"); e != nil {
		t.Fatal(e)
	}
	if e = nodeAuthorize(d, "seed-a", source, out, 24); e != nil {
		t.Fatal(e)
	}
	certBytes, e := os.ReadFile(out)
	if e != nil {
		t.Fatal(e)
	}
	var c SignedNodeCertificate
	if e = json.Unmarshal(certBytes, &c); e != nil {
		t.Fatal(e)
	}
	master, e := readKey(d, "public.key", 32)
	if e != nil {
		t.Fatal(e)
	}
	raw, _ := json.Marshal(c.Payload)
	sig, _ := base64.RawURLEncoding.DecodeString(c.Signature)
	if !ed25519.Verify(master, append([]byte("ConnectIT-seed-cert-v1\n"), raw...), sig) {
		t.Fatal("Master cert signature invalid")
	}
	if c.Payload.ExpiresAt <= time.Now().Unix() || c.Payload.NodeID != "seed-a" {
		t.Fatal("bad node certificate")
	}
	if e = nodeAuthorize(d, "seed-a", source, out, 24); e == nil {
		t.Fatal("silent certificate overwrite")
	}
	if e = nodeAuthorize(d, "seed-a", source, filepath.Join(d, "bad.cert"), 169); e == nil {
		t.Fatal("overlong certificate TTL")
	}
}
