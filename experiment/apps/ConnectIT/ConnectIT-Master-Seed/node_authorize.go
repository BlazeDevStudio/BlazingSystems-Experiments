package main

import (
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Node authorization is issued by the local, OS-privileged Master operator.
// It grants federation access, NOT account/device authentication.
type NodeCertificatePayload struct {
	Format    string `json:"format"`
	NodeID    string `json:"node_id"`
	PublicKey string `json:"public_key"`
	IssuedAt  int64  `json:"issued_at"`
	ExpiresAt int64  `json:"expires_at"`
}
type SignedNodeCertificate struct {
	Payload   NodeCertificatePayload `json:"payload"`
	Signature string                 `json:"signature_b64"`
}

func nodeAuthorize(dir, nodeID, publicPath, out string, ttlHours int) error {
	if !validNodeLabel(nodeID) || publicPath == "" || out == "" || ttlHours < 1 || ttlHours > 168 {
		return errors.New("node-id, node-public-key, node-cert-out and TTL 1..168h required")
	}
	if _, err := os.Stat(out); err == nil {
		return errors.New("node certificate already exists; refusing overwrite")
	} else if !os.IsNotExist(err) {
		return err
	}
	d, err := openDB(dbpath(dir))
	if err != nil {
		return err
	}
	defer d.close()
	ok, err := rotated(d)
	if err != nil {
		return err
	}
	if !ok {
		return errors.New("rotate bootstrap administrator password before issuing nodes")
	}
	raw, err := os.ReadFile(publicPath)
	if err != nil {
		return err
	}
	key, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(raw)))
	if err != nil || len(key) != ed25519.PublicKeySize {
		return errors.New("invalid node Ed25519 public key")
	}
	private, err := readKey(dir, "private.key", ed25519.PrivateKeySize)
	if err != nil {
		return err
	}
	now := time.Now().Unix()
	payload := NodeCertificatePayload{Format: "connectit-seed-cert-v1", NodeID: nodeID, PublicKey: base64.StdEncoding.EncodeToString(key), IssuedAt: now, ExpiresAt: now + int64(ttlHours)*3600}
	packed, _ := json.Marshal(payload)
	sign := ed25519.Sign(ed25519.PrivateKey(private), append([]byte("ConnectIT-seed-cert-v1\n"), packed...))
	if err := recordNodeIssue(d, payload, nodeKeyHash(key)); err != nil {
		return err
	}
	doc, _ := json.MarshalIndent(SignedNodeCertificate{Payload: payload, Signature: base64.RawURLEncoding.EncodeToString(sign)}, "", "  ")
	if err := os.MkdirAll(filepath.Dir(out), 0700); err != nil {
		return err
	}
	f, err := os.OpenFile(out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	_, werr := f.Write(append(doc, '\n'))
	cerr := f.Sync()
	eclose := f.Close()
	if werr != nil || cerr != nil || eclose != nil {
		os.Remove(out)
		return fmt.Errorf("certificate write: %v %v %v", werr, cerr, eclose)
	}
	fmt.Printf("Master authorized node %s until %s. Deliver certificate securely to that Seed.\n", nodeID, time.Unix(payload.ExpiresAt, 0).UTC().Format(time.RFC3339))
	return nil
}
func validNodeLabel(s string) bool {
	if len(s) < 1 || len(s) > 64 {
		return false
	}
	for _, r := range s {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '.' || r == '-' || r == '_' {
			continue
		}
		return false
	}
	return true
}
