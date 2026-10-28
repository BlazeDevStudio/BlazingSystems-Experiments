package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"
)

type rate struct {
	start time.Time
	count int
}
type api struct {
	db       *DB
	priv     ed25519.PrivateKey
	hmacKey  []byte
	mu       sync.Mutex
	attempts map[string]rate
	nonces   map[string]int64
}

func (a *api) limit(r *http.Request) bool {
	host, _, _ := net.SplitHostPort(r.RemoteAddr)
	a.mu.Lock()
	defer a.mu.Unlock()
	v := a.attempts[host]
	if time.Since(v.start) > time.Minute {
		v = rate{start: time.Now()}
	}
	v.count++
	a.attempts[host] = v
	if len(a.attempts) > 20000 {
		for key, item := range a.attempts {
			if time.Since(item.start) > 2*time.Minute {
				delete(a.attempts, key)
			}
		}
	}
	return v.count <= 12
}
func (a *api) guard(w http.ResponseWriter, r *http.Request) bool {
	if r.Method != "POST" {
		failure(w, 405, "POST required")
		return false
	}
	if !a.limit(r) {
		failure(w, 429, "rate limited")
		return false
	}
	return true
}
func (a *api) routes(mux *http.ServeMux) {
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			failure(w, 405, "GET required")
			return
		}
		reply(w, 200, map[string]any{"ok": true, "role": "master", "protocol": "connectit-v1-foundation"})
	})
	mux.HandleFunc("/v1/revocations", a.revocations)
	mux.HandleFunc("/v1/node-revocations", a.nodeRevocations)
	mux.HandleFunc("/v1/public-key", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			failure(w, 405, "GET required")
			return
		}
		reply(w, 200, map[string]string{"ed25519_b64": b64(a.priv.Public().(ed25519.PublicKey))})
	})
	mux.HandleFunc("/v1/enroll", a.enroll)
	mux.HandleFunc("/v1/bind/start", a.bindStart)
	mux.HandleFunc("/v1/bind/pending", a.pending)
	mux.HandleFunc("/v1/bind/decision", a.decision)
	mux.HandleFunc("/v1/bind/finalize", a.finalize)
}
func validNonce(s string) bool {
	if len(s) < 20 || len(s) > 96 {
		return false
	}
	b, e := base64.RawURLEncoding.DecodeString(s)
	return e == nil && len(b) >= 16
}
func signedProof(pub64, text, sig64 string) bool {
	pub, e := base64.StdEncoding.DecodeString(pub64)
	if e != nil || len(pub) != ed25519.PublicKeySize {
		return false
	}
	sig, e := base64.RawURLEncoding.DecodeString(sig64)
	return e == nil && len(sig) == ed25519.SignatureSize && ed25519.Verify(ed25519.PublicKey(pub), []byte(text), sig)
}
func (a *api) account(id, pw string) (map[string]string, bool) {
	if !validID(id) || len(pw) == 0 || len(pw) > 1024 {
		return nil, false
	}
	v, e := a.db.run("SELECT id,salt,hash,iterations,state FROM accounts WHERE id=?", id)
	if e != nil || len(v) != 1 {
		return nil, false
	}
	it, _ := strconv.Atoi(v[0]["iterations"])
	return v[0], v[0]["state"] == "active" && comparePw(pw, v[0]["salt"], v[0]["hash"], it)
}
func (a *api) tokenAvailable(hash, account string) bool {
	rows, e := a.db.query("SELECT account_id FROM registered_tokens WHERE token_hash=? AND released=0", hash)
	return e == nil && (len(rows) == 0 || rows[0]["account_id"] == account)
}
func (a *api) enroll(w http.ResponseWriter, r *http.Request) {
	if !a.guard(w, r) {
		return
	}
	var in struct {
		Username        string `json:"username"`
		Password        string `json:"password"`
		DevicePublicKey string `json:"device_public_key_b64"`
		InstallationID  string `json:"installation_id"`
		Nonce           string `json:"nonce"`
		Pop             string `json:"proof_signature_b64"`
	}
	if !decode(w, r, &in) {
		return
	}
	if !validPub(in.DevicePublicKey) || !validInstall(in.InstallationID) || !validNonce(in.Nonce) || !signedProof(in.DevicePublicKey, "ConnectIT-enroll-v1\n"+in.Username+"\n"+in.Nonce, in.Pop) {
		failure(w, 400, "device proof, installation token or nonce invalid")
		return
	}
	if _, ok := a.account(in.Username, in.Password); !ok {
		failure(w, 401, "invalid credentials")
		return
	}
	hash := installHash(a.hmacKey, in.InstallationID)
	now := time.Now().Unix()
	allow := false
	reason := "additional device requires SecureBind"
	e := a.db.transaction(func() error {
		if !a.tokenAvailable(hash, in.Username) {
			reason = "installation already associated with another account"
			return errors.New("blocked")
		}
		rows, e := a.db.query("SELECT public_key,token_hash,state FROM devices WHERE account_id=?", in.Username)
		if e != nil {
			return e
		}
		if len(rows) == 0 {
			dev := rnd(18)
			if _, e = a.db.query("INSERT INTO devices(id,account_id,public_key,token_hash,state,created) VALUES(?,?,?,?,?,?)", dev, in.Username, in.DevicePublicKey, hash, "active", now); e != nil {
				return e
			}
			if _, e = a.db.query("INSERT OR IGNORE INTO registered_tokens(token_hash,account_id,released) VALUES(?,?,0)", hash, in.Username); e != nil {
				return e
			}
			allow = true
			return nil
		}
		for _, row := range rows {
			if row["public_key"] == in.DevicePublicKey && row["token_hash"] == hash && row["state"] == "active" {
				allow = true
				return nil
			}
		}
		return errors.New("blocked")
	})
	if e != nil && !allow {
		failure(w, 409, reason)
		return
	}
	if e != nil {
		failure(w, 500, "enrollment database error")
		return
	}
	reply(w, 200, map[string]any{"device_certificate": issue(a.priv, in.Username, in.DevicePublicKey, 7*86400), "expires_in": 7 * 86400, "protocol": "blaze-seed-v1-compatible"})
}
func (a *api) bindStart(w http.ResponseWriter, r *http.Request) {
	if !a.guard(w, r) {
		return
	}
	var in struct {
		Username        string `json:"username"`
		Password        string `json:"password"`
		DevicePublicKey string `json:"device_public_key_b64"`
		InstallationID  string `json:"installation_id"`
		Nonce           string `json:"nonce"`
		Pop             string `json:"proof_signature_b64"`
		Confirmed       bool   `json:"confirmed"`
	}
	if !decode(w, r, &in) {
		return
	}
	if !in.Confirmed {
		failure(w, 400, "explicit device association consent required")
		return
	}
	if !validPub(in.DevicePublicKey) || !validInstall(in.InstallationID) || !validNonce(in.Nonce) || !signedProof(in.DevicePublicKey, "ConnectIT-bind-start-v1\n"+in.Username+"\n"+in.Nonce, in.Pop) {
		failure(w, 400, "invalid target device proof")
		return
	}
	if _, ok := a.account(in.Username, in.Password); !ok {
		failure(w, 401, "invalid credentials")
		return
	}
	hash := installHash(a.hmacKey, in.InstallationID)
	now := time.Now().Unix()
	bindingID := rnd(24)
	challenge := rnd(32)
	e := a.db.transaction(func() error {
		if !a.tokenAvailable(hash, in.Username) {
			return errors.New("device already associated with another account")
		}
		live, e := a.db.query("SELECT COUNT(*) AS n FROM devices WHERE account_id=? AND state='active'", in.Username)
		if e != nil {
			return e
		}
		if live[0]["n"] == "0" {
			return errors.New("first device must use /v1/enroll")
		}
		_, e = a.db.query("INSERT INTO bindings(id,account_id,target_key,target_token,challenge,started,expires,state,approvals,created_nonce) VALUES(?,?,?,?,?,?,?,?,?,?)", bindingID, in.Username, in.DevicePublicKey, hash, challenge, now, now+86400, "pending", 0, in.Nonce)
		return e
	})
	if e != nil {
		failure(w, 409, "binding denied: "+e.Error())
		return
	}
	reply(w, 202, map[string]any{"binding_id": bindingID, "challenge": challenge, "started_at": now, "expires_at": now + 86400, "not_before": now + 14400, "interval_seconds": 1200, "status": "pending", "server_time": now})
}

// Verify both the master-signed certificate and the Ed25519 proof bound to this precise HTTP request.
func (a *api) trusted(w http.ResponseWriter, r *http.Request) (string, string, bool) {
	h := r.Header.Get("Authorization")
	if !strings.HasPrefix(h, "Bearer ") {
		failure(w, 401, "signed device certificate required")
		return "", "", false
	}
	p := strings.Split(strings.TrimPrefix(h, "Bearer "), ".")
	if len(p) != 3 {
		failure(w, 401, "invalid cert")
		return "", "", false
	}
	sig, e := base64.RawURLEncoding.DecodeString(p[2])
	if e != nil || !ed25519.Verify(a.priv.Public().(ed25519.PublicKey), []byte(p[0]+"."+p[1]), sig) {
		failure(w, 401, "invalid cert signature")
		return "", "", false
	}
	header, e := base64.RawURLEncoding.DecodeString(p[0])
	if e != nil || string(header) != jwtHead {
		failure(w, 401, "bad certificate header")
		return "", "", false
	}
	payload, e := base64.RawURLEncoding.DecodeString(p[1])
	if e != nil || len(payload) > 4096 {
		failure(w, 401, "bad certificate payload")
		return "", "", false
	}
	var claims struct {
		Iss string `json:"iss"`
		Aud string `json:"aud"`
		Sub string `json:"sub"`
		Iat int64  `json:"iat"`
		Exp int64  `json:"exp"`
		Key string `json:"device_public_key"`
	}
	if json.Unmarshal(payload, &claims) != nil || claims.Iss != proto || claims.Aud != "blaze-relays" || !validID(claims.Sub) || !validPub(claims.Key) || claims.Exp <= time.Now().Unix() || claims.Iat > time.Now().Unix()+60 || claims.Exp > claims.Iat+366*86400 {
		failure(w, 401, "expired or invalid certificate")
		return "", "", false
	}
	ts := r.Header.Get("X-Device-Time")
	nonce := r.Header.Get("X-Device-Nonce")
	dsig := r.Header.Get("X-Device-Signature")
	n, e := strconv.ParseInt(ts, 10, 64)
	now := time.Now().Unix()
	if e != nil || n < now-120 || n > now+120 || !validNonce(nonce) {
		failure(w, 401, "stale device proof")
		return "", "", false
	}
	body, e := io.ReadAll(io.LimitReader(r.Body, 16385))
	if e != nil || len(body) > 16384 {
		failure(w, 413, "request too large")
		return "", "", false
	}
	r.Body.Close()
	r.Body = io.NopCloser(bytes.NewReader(body))
	sum := sha256.Sum256(body)
	text := r.Method + "\n" + r.Host + "\n" + r.URL.RequestURI() + "\n" + ts + "\n" + nonce + "\n" + hex.EncodeToString(sum[:])
	if !signedProof(claims.Key, text, dsig) {
		failure(w, 401, "invalid device request signature")
		return "", "", false
	}
	a.mu.Lock()
	if a.nonces == nil {
		a.nonces = map[string]int64{}
	}
	nk := claims.Key + ":" + nonce
	if a.nonces[nk] > now {
		a.mu.Unlock()
		failure(w, 409, "replayed request")
		return "", "", false
	}
	if len(a.nonces) > 10000 {
		for k, t := range a.nonces {
			if t < now {
				delete(a.nonces, k)
			}
		}
	}
	if len(a.nonces) > 50000 {
		a.mu.Unlock()
		failure(w, 503, "replay cache full")
		return "", "", false
	}
	a.nonces[nk] = now + 300
	a.mu.Unlock()
	var drows []map[string]string
	drows, e = a.db.run("SELECT id,state FROM devices WHERE account_id=? AND public_key=?", claims.Sub, claims.Key)
	if e != nil || len(drows) != 1 || drows[0]["state"] != "active" {
		failure(w, 403, "device not currently trusted")
		return "", "", false
	}
	return claims.Sub, drows[0]["id"], true
}
func (a *api) pending(w http.ResponseWriter, r *http.Request) {
	if r.Method != "GET" {
		failure(w, 405, "GET required")
		return
	}
	account, _, ok := a.trusted(w, r)
	if !ok {
		return
	}
	list, e := a.db.run("SELECT id,target_key,challenge,started,expires,approvals,state FROM bindings WHERE account_id=? AND state IN ('pending','approved') ORDER BY started DESC LIMIT 50", account)
	if e != nil {
		failure(w, 500, "database read error")
		return
	}
	reply(w, 200, map[string]any{"requests": list, "server_time": time.Now().Unix()})
}
func (a *api) decision(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		failure(w, 405, "POST required")
		return
	}
	account, device, ok := a.trusted(w, r)
	if !ok {
		return
	}
	var in struct {
		BindingID  string `json:"binding_id"`
		ApprovalID string `json:"approval_id"`
		Action     string `json:"action"`
		Issued     int64  `json:"issued"`
		Interval   int    `json:"interval_index"`
		Signature  string `json:"signature_b64"`
	}
	if !decode(w, r, &in) {
		return
	}
	if len(in.ApprovalID) < 20 || len(in.ApprovalID) > 96 || !(in.Action == "approve" || in.Action == "revoke" || in.Action == "not_me") {
		failure(w, 400, "invalid decision")
		return
	}
	now := time.Now().Unix()
	if in.Issued < now-120 || in.Issued > now+60 {
		failure(w, 401, "expired decision")
		return
	}
	var approveCount int
	var state string
	e := a.db.transaction(func() error {
		rows, e := a.db.query("SELECT * FROM bindings WHERE id=? AND account_id=?", in.BindingID, account)
		if e != nil {
			return e
		}
		if len(rows) != 1 {
			return errors.New("binding not found")
		}
		b := rows[0]
		if b["state"] != "pending" && b["state"] != "approved" {
			return errors.New("binding not pending")
		}
		started, _ := strconv.ParseInt(b["started"], 10, 64)
		exp, _ := strconv.ParseInt(b["expires"], 10, 64)
		if now >= exp {
			return errors.New("binding expired")
		}
		interval := int((now - started) / 1200)
		if interval < 0 || interval != in.Interval {
			return errors.New("incorrect scheduled interval")
		}
		dev, e := a.db.query("SELECT public_key FROM devices WHERE id=? AND account_id=? AND state='active'", device, account)
		if e != nil || len(dev) != 1 {
			return errors.New("trusted device revoked")
		}
		canonical := fmt.Sprintf("ConnectIT-SecureBind-v1\n%s\n%s\n%s\n%s\n%s\n%d\n%d\n%s", in.BindingID, in.ApprovalID, device, b["target_key"], b["challenge"], in.Interval, in.Issued, in.Action)
		if !signedProof(dev[0]["public_key"], canonical, in.Signature) {
			return errors.New("invalid approval signature")
		}
		if in.Action != "approve" {
			state = "revoked"
			_, e = a.db.query("UPDATE bindings SET state='revoked' WHERE id=?", in.BindingID)
			if e != nil {
				return e
			}
			if in.Action == "not_me" {
				_, e = a.db.query("UPDATE session_records SET revoked=1 WHERE account_id=?", account)
			}
			return e
		}
		if _, e = a.db.query("INSERT INTO binding_approvals(id,binding_id,device_id,interval_index,issued,signature) VALUES(?,?,?,?,?,?)", in.ApprovalID, in.BindingID, device, in.Interval, in.Issued, in.Signature); e != nil {
			return e
		}
		approveCount, _ = strconv.Atoi(b["approvals"])
		approveCount++
		state = "approved"
		_, e = a.db.query("UPDATE bindings SET approvals=?,state='approved' WHERE id=?", approveCount, in.BindingID)
		return e
	})
	if e != nil {
		failure(w, 409, "decision rejected: "+e.Error())
		return
	}
	reply(w, 200, map[string]any{"status": state, "approvals": approveCount, "server_time": now})
}
func (a *api) finalize(w http.ResponseWriter, r *http.Request) {
	if !a.guard(w, r) {
		return
	}
	var in struct {
		BindingID string `json:"binding_id"`
		Username  string `json:"username"`
		Password  string `json:"password"`
		Nonce     string `json:"nonce"`
		Proof     string `json:"proof_signature_b64"`
	}
	if !decode(w, r, &in) {
		return
	}
	if !validNonce(in.Nonce) {
		failure(w, 400, "valid target nonce required")
		return
	}
	if _, ok := a.account(in.Username, in.Password); !ok {
		failure(w, 401, "invalid credentials")
		return
	}
	now := time.Now().Unix()
	var target string
	e := a.db.transaction(func() error {
		rows, e := a.db.query("SELECT * FROM bindings WHERE id=? AND account_id=?", in.BindingID, in.Username)
		if e != nil {
			return e
		}
		if len(rows) != 1 {
			return errors.New("binding not found")
		}
		b := rows[0]
		if b["state"] != "approved" {
			return errors.New("at least one authenticated approval required")
		}
		if !signedProof(b["target_key"], "ConnectIT-bind-finalize-v1\n"+in.BindingID+"\n"+in.Nonce, in.Proof) {
			return errors.New("invalid target device proof")
		}
		started, _ := strconv.ParseInt(b["started"], 10, 64)
		expires, _ := strconv.ParseInt(b["expires"], 10, 64)
		approvals, _ := strconv.Atoi(b["approvals"])
		if approvals < 1 || now >= expires || now < started+14400-int64(approvals)*1800 {
			return errors.New("countdown or expiration requirement not satisfied")
		}
		if !a.tokenAvailable(b["target_token"], in.Username) {
			return errors.New("device token belongs to a different account")
		}
		if _, e = a.db.query("INSERT INTO devices(id,account_id,public_key,token_hash,state,created) VALUES(?,?,?,?,?,?)", rnd(18), in.Username, b["target_key"], b["target_token"], "active", now); e != nil {
			return e
		}
		if _, e = a.db.query("INSERT OR IGNORE INTO registered_tokens(token_hash,account_id,released) VALUES(?,?,0)", b["target_token"], in.Username); e != nil {
			return e
		}
		if _, e = a.db.query("UPDATE bindings SET state='completed' WHERE id=?", in.BindingID); e != nil {
			return e
		}
		target = b["target_key"]
		return nil
	})
	if e != nil {
		failure(w, 409, "cannot finalize: "+e.Error())
		return
	}
	reply(w, 200, map[string]any{"status": "completed", "device_certificate": issue(a.priv, in.Username, target, 7*86400), "expires_in": 604800})
}

// Signature and replay validity are covered by master server time, per-device nonce, and SQLite unique keys.
// Binding notification delivery is NOT implemented in this foundation; see gap list.
var _ = subtle.ConstantTimeCompare
var _ = rand.Reader
