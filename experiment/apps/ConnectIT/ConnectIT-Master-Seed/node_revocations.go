package main

import (
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"
)

const nodeRevocationPrefix = "ConnectIT-node-revocations-v1\n"
const nodeRevocationDDL = `CREATE TABLE IF NOT EXISTS revoked_node_keys (
 key_hash TEXT PRIMARY KEY, node_id TEXT NOT NULL, revoked_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS node_cert_issues (
 node_id TEXT NOT NULL, key_hash TEXT NOT NULL, issued_at INTEGER NOT NULL,
 expires_at INTEGER NOT NULL, PRIMARY KEY(node_id,key_hash,issued_at));`

type NodeRevocationPayload struct {
	Format               string   `json:"format"`
	Generation           int64    `json:"generation"`
	GeneratedAt          int64    `json:"generated_at"`
	ValidUntil           int64    `json:"valid_until"`
	RevokedNodeKeyHashes []string `json:"revoked_node_key_hashes"`
}
type SignedNodeRevocations struct {
	Payload   NodeRevocationPayload `json:"payload"`
	Signature string                `json:"signature_b64"`
}

func nodeKeyHash(pub ed25519.PublicKey) string {
	h := sha256.Sum256(pub)
	return base64.RawURLEncoding.EncodeToString(h[:])
}
func migrateNodeRevocations(db *DB) error { return db.script(nodeRevocationDDL) }
func (a *api) nodeRevocations(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		failure(w, 405, "GET required")
		return
	}
	var gen int64
	var rows []map[string]string
	err := a.db.transaction(func() error {
		v, e := a.db.query("SELECT value FROM meta WHERE key='node_revocation_generation'")
		if e != nil {
			return e
		}
		if len(v) > 0 {
			gen, e = strconv.ParseInt(v[0]["value"], 10, 64)
			if e != nil {
				return e
			}
		}
		rows, e = a.db.query("SELECT key_hash FROM revoked_node_keys ORDER BY key_hash LIMIT 50001")
		return e
	})
	if err != nil || len(rows) > 50000 {
		failure(w, 503, "node revocations unavailable")
		return
	}
	hashes := make([]string, 0, len(rows))
	for _, v := range rows {
		hashes = append(hashes, v["key_hash"])
	}
	sort.Strings(hashes)
	now := time.Now().Unix()
	p := NodeRevocationPayload{Format: "connectit-node-revocations-v1", Generation: gen, GeneratedAt: now, ValidUntil: now + 3600, RevokedNodeKeyHashes: hashes}
	data, _ := json.Marshal(p)
	sig := ed25519.Sign(a.priv, append([]byte(nodeRevocationPrefix), data...))
	reply(w, 200, SignedNodeRevocations{Payload: p, Signature: base64.RawURLEncoding.EncodeToString(sig)})
}
func nodeRevoke(dir, certPath string) error {
	if certPath == "" {
		return errors.New("--node-cert required: exact Master-signed certificate to revoke")
	}
	raw, err := os.ReadFile(certPath)
	if err != nil {
		return err
	}
	if len(raw) > 4096 {
		return errors.New("node certificate oversized")
	}
	var c SignedNodeCertificate
	if err = json.Unmarshal(raw, &c); err != nil {
		return err
	}
	p := c.Payload
	if p.Format != "connectit-seed-cert-v1" || !validNodeLabel(p.NodeID) || p.ExpiresAt <= p.IssuedAt || p.ExpiresAt > p.IssuedAt+7*86400 {
		return errors.New("invalid node certificate")
	}
	pub, e := base64.StdEncoding.DecodeString(p.PublicKey)
	if e != nil || len(pub) != ed25519.PublicKeySize {
		return errors.New("bad node public key")
	}
	sig, e := base64.RawURLEncoding.DecodeString(c.Signature)
	if e != nil || len(sig) != ed25519.SignatureSize {
		return errors.New("bad node signature")
	}
	master, e := readKey(dir, "public.key", ed25519.PublicKeySize)
	if e != nil {
		return e
	}
	signed, _ := json.Marshal(p)
	if !ed25519.Verify(ed25519.PublicKey(master), append([]byte("ConnectIT-seed-cert-v1\n"), signed...), sig) {
		return errors.New("certificate not authorized by this Master")
	}
	db, e := openDB(dbpath(dir))
	if e != nil {
		return e
	}
	defer db.close()
	if e = migrateNodeRevocations(db); e != nil {
		return e
	}
	hash := nodeKeyHash(pub)
	return db.transaction(func() error {
		rows, e := db.query("SELECT key_hash FROM revoked_node_keys WHERE key_hash=?", hash)
		if e != nil {
			return e
		}
		if len(rows) > 0 {
			return nil
		} // idempotent: no generation bump for repeats
		if _, e = db.query("INSERT INTO revoked_node_keys(key_hash,node_id,revoked_at) VALUES(?,?,?)", hash, p.NodeID, time.Now().Unix()); e != nil {
			return e
		}
		if _, e = db.query("INSERT INTO meta(key,value) VALUES('node_revocation_generation','1') ON CONFLICT(key) DO UPDATE SET value=CAST(CAST(value AS INTEGER)+1 AS TEXT)"); e != nil {
			return e
		}
		_, e = db.query("INSERT INTO audit(created,action,subject,detail) VALUES(?,?,?,?)", time.Now().Unix(), "node.revoke", p.NodeID, hash)
		return e
	})
}
func recordNodeIssue(db *DB, p NodeCertificatePayload, keyHash string) error {
	if e := migrateNodeRevocations(db); e != nil {
		return e
	}
	return db.transaction(func() error {
		rows, e := db.query("SELECT key_hash FROM revoked_node_keys WHERE key_hash=?", keyHash)
		if e != nil {
			return e
		}
		if len(rows) > 0 {
			return errors.New("node signing key has been revoked; generate a new keypair")
		}
		existing, e := db.query("SELECT DISTINCT node_id FROM node_cert_issues WHERE key_hash=? LIMIT 2", keyHash)
		if e != nil {
			return e
		}
		for _, row := range existing {
			if row["node_id"] != p.NodeID {
				return errors.New("node signing key already belongs to a different node ID")
			}
		}
		if _, e = db.query("INSERT INTO node_cert_issues(node_id,key_hash,issued_at,expires_at) VALUES(?,?,?,?)", p.NodeID, keyHash, p.IssuedAt, p.ExpiresAt); e != nil {
			return e
		}
		_, e = db.query("INSERT INTO audit(created,action,subject,detail) VALUES(?,?,?,?)", time.Now().Unix(), "node.authorize", p.NodeID, keyHash)
		return e
	})
}
func nodeRevocationURL(endpoint string) string {
	return strings.TrimSuffix(endpoint, "/v1/revocations") + "/v1/node-revocations"
}
