package main

import (
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"net/http"
	"sort"
	"strconv"
	"time"
)

// A signed snapshot contains no account IDs or raw device keys. It is deliberately
// time bounded: a Seed cannot safely accept an indefinitely stale revocation view.
type RevocationPayload struct {
	Format           string   `json:"format"`
	Generation       int64    `json:"generation"`
	GeneratedAt      int64    `json:"generated_at"`
	ValidUntil       int64    `json:"valid_until"`
	RevokedKeyHashes []string `json:"revoked_key_hashes"`
}
type SignedRevocations struct {
	Payload   RevocationPayload `json:"payload"`
	Signature string            `json:"signature_b64"`
}

func deviceHash(pub64 string) (string, error) {
	b, e := base64.StdEncoding.DecodeString(pub64)
	if e != nil || len(b) != ed25519.PublicKeySize {
		return "", errors.New("bad device public key")
	}
	h := sha256.Sum256(b)
	return base64.RawURLEncoding.EncodeToString(h[:]), nil
}
func bumpRevocations(d *DB) error {
	// MUST be called from inside d.transaction, using d.query (not d.run).
	_, e := d.query("INSERT INTO meta(key,value) VALUES('revocation_generation','1') ON CONFLICT(key) DO UPDATE SET value=CAST(CAST(value AS INTEGER)+1 AS TEXT)")
	return e
}
func (a *api) revocations(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		failure(w, 405, "GET required")
		return
	}
	// Get a coherent DB view without allowing the response to mutate authority.
	var rows []map[string]string
	var generation int64
	e := a.db.transaction(func() error {
		gen, e := a.db.query("SELECT value FROM meta WHERE key='revocation_generation'")
		if e != nil {
			return e
		}
		if len(gen) != 0 {
			generation, e = strconv.ParseInt(gen[0]["value"], 10, 64)
			if e != nil {
				return e
			}
		}
		rows, e = a.db.query("SELECT DISTINCT d.public_key FROM devices d JOIN accounts a ON a.id=d.account_id WHERE d.state!='active' OR a.state!='active' LIMIT 50001")
		return e
	})
	if e != nil || len(rows) > 50000 {
		failure(w, 503, "revocation view unavailable")
		return
	}
	hashes := make([]string, 0, len(rows))
	for _, v := range rows {
		h, e := deviceHash(v["public_key"])
		if e != nil {
			failure(w, 503, "invalid authority device key")
			return
		}
		hashes = append(hashes, h)
	}
	sort.Strings(hashes)
	now := time.Now().Unix()
	p := RevocationPayload{Format: "connectit-revocations-v1", Generation: generation, GeneratedAt: now, ValidUntil: now + 3600, RevokedKeyHashes: hashes}
	raw, _ := json.Marshal(p)
	sig := ed25519.Sign(a.priv, append([]byte("ConnectIT-revocations-v1\n"), raw...))
	reply(w, 200, SignedRevocations{Payload: p, Signature: base64.RawURLEncoding.EncodeToString(sig)})
}

func revokeDevice(dir, id string) error {
	if !validNonce(id) {
		return errors.New("invalid device identifier")
	}
	d, e := openDB(dbpath(dir))
	if e != nil {
		return e
	}
	defer d.close()
	return d.transaction(func() error {
		rows, e := d.query("SELECT state FROM devices WHERE id=?", id)
		if e != nil {
			return e
		}
		if len(rows) != 1 {
			return errors.New("device not found")
		}
		if rows[0]["state"] == "revoked" {
			return nil
		}
		if _, e = d.query("UPDATE devices SET state='revoked' WHERE id=?", id); e != nil {
			return e
		}
		if _, e = d.query("INSERT INTO revocations(device_id,revoked_at,reason) VALUES(?,?,?)", id, time.Now().Unix(), "local admin revocation"); e != nil {
			return e
		}
		return bumpRevocations(d)
	})
}
