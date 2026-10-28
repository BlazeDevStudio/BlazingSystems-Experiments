package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

const nodeCertPrefix = "ConnectIT-seed-cert-v1\n"
const meshRequestPrefix = "ConnectIT-mesh-request-v1\n"
const meshResponsePrefix = "ConnectIT-mesh-response-v1\n"

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

func checkNodeCertificate(raw string, master ed25519.PublicKey, now int64) (NodeCertificatePayload, ed25519.PublicKey, error) {
	var c SignedNodeCertificate
	if len(raw) > 4096 || json.Unmarshal([]byte(raw), &c) != nil {
		return c.Payload, nil, errors.New("node certificate invalid JSON or too large")
	}
	p := c.Payload
	if p.Format != "connectit-seed-cert-v1" || !validName(p.NodeID) || p.IssuedAt > now+90 || p.ExpiresAt <= now || p.ExpiresAt <= p.IssuedAt || p.ExpiresAt > p.IssuedAt+7*86400 {
		return p, nil, errors.New("node certificate expired or invalid interval")
	}
	key, e := base64.StdEncoding.DecodeString(p.PublicKey)
	if e != nil || len(key) != ed25519.PublicKeySize {
		return p, nil, errors.New("node public key invalid")
	}
	sig, e := base64.RawURLEncoding.DecodeString(c.Signature)
	packed, _ := json.Marshal(p)
	if e != nil || len(sig) != ed25519.SignatureSize || !ed25519.Verify(master, append([]byte(nodeCertPrefix), packed...), sig) {
		return p, nil, errors.New("node Master signature invalid")
	}
	return p, ed25519.PublicKey(key), nil
}
func hashBytes(b []byte) string {
	h := sha256.Sum256(b)
	return base64.RawURLEncoding.EncodeToString(h[:])
}
func reqPayload(method, uri, ts, nonce, target string) []byte {
	return []byte(meshRequestPrefix + method + "\n" + uri + "\n" + ts + "\n" + nonce + "\n" + target + "\n" + hashBytes(nil))
}
func responsePayload(nonce string, status int, body []byte) []byte {
	return []byte(meshResponsePrefix + nonce + "\n" + strconv.Itoa(status) + "\n" + hashBytes(body))
}

type MeshIdentity struct {
	NodeID      string
	Certificate string
	Private     ed25519.PrivateKey
	Master      ed25519.PublicKey
	Allowed     map[string]struct{}
	mu          sync.Mutex
	seen        map[string]int64
}

func (m *MeshIdentity) signRequest(r *http.Request, target string) error {
	if m == nil {
		return errors.New("node identity absent")
	}
	nonce := make([]byte, 24)
	if _, e := rand.Read(nonce); e != nil {
		return e
	}
	n := base64.RawURLEncoding.EncodeToString(nonce)
	ts := strconv.FormatInt(time.Now().Unix(), 10)
	r.Header.Set("X-ConnectIT-Node-Cert", base64.RawURLEncoding.EncodeToString([]byte(m.Certificate)))
	r.Header.Set("X-ConnectIT-Node-Time", ts)
	r.Header.Set("X-ConnectIT-Node-Nonce", n)
	r.Header.Set("X-ConnectIT-Node-Signature", base64.RawURLEncoding.EncodeToString(ed25519.Sign(m.Private, reqPayload(r.Method, r.URL.RequestURI(), ts, n, target))))
	return nil
}
func (m *MeshIdentity) authorizeRequest(r *http.Request) error {
	if m == nil {
		return errors.New("node authentication not provisioned")
	}
	raw, e := base64.RawURLEncoding.DecodeString(r.Header.Get("X-ConnectIT-Node-Cert"))
	if e != nil || len(raw) > 4096 {
		return errors.New("bad node certificate encoding")
	}
	cert, key, e := checkNodeCertificate(string(raw), m.Master, time.Now().Unix())
	if e != nil {
		return e
	}
	if _, ok := m.Allowed[cert.NodeID]; !ok {
		return errors.New("node is not on local allowlist")
	}
	timestamp := r.Header.Get("X-ConnectIT-Node-Time")
	when, e := strconv.ParseInt(timestamp, 10, 64)
	now := time.Now().Unix()
	if e != nil || when < now-90 || when > now+90 {
		return errors.New("node request expired")
	}
	nonce := r.Header.Get("X-ConnectIT-Node-Nonce")
	decoded, e := base64.RawURLEncoding.DecodeString(nonce)
	if e != nil || len(decoded) != 24 {
		return errors.New("invalid node nonce")
	}
	sig, e := base64.RawURLEncoding.DecodeString(r.Header.Get("X-ConnectIT-Node-Signature"))
	if e != nil || len(sig) != ed25519.SignatureSize || !ed25519.Verify(key, reqPayload(r.Method, r.URL.RequestURI(), timestamp, nonce, m.NodeID), sig) {
		return errors.New("invalid node request signature")
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	for k, t := range m.seen {
		if now > t+190 {
			delete(m.seen, k)
		}
	}
	k := cert.NodeID + ":" + nonce
	if _, used := m.seen[k]; used {
		return errors.New("replayed node nonce")
	}
	if len(m.seen) >= 4096 {
		return errors.New("node replay cache full")
	}
	m.seen[k] = now
	return nil
}
func (m *MeshIdentity) signedResponse(nonce string, status int, body []byte) (http.Header, error) {
	if len(nonce) > 64 {
		return nil, errors.New("response nonce oversized")
	}
	h := make(http.Header)
	h.Set("X-ConnectIT-Node-Cert", base64.RawURLEncoding.EncodeToString([]byte(m.Certificate)))
	h.Set("X-ConnectIT-Response-Nonce", nonce)
	h.Set("X-ConnectIT-Response-Signature", base64.RawURLEncoding.EncodeToString(ed25519.Sign(m.Private, responsePayload(nonce, status, body))))
	return h, nil
}
func (m *MeshIdentity) verifyResponse(resp *http.Response, nonce, expectedNode string, body []byte) error {
	if m == nil {
		return errors.New("missing node signing identity")
	}
	raw, e := base64.RawURLEncoding.DecodeString(resp.Header.Get("X-ConnectIT-Node-Cert"))
	if e != nil || len(raw) > 4096 {
		return errors.New("peer response node certificate invalid")
	}
	p, key, e := checkNodeCertificate(string(raw), m.Master, time.Now().Unix())
	if e != nil {
		return e
	}
	if p.NodeID != expectedNode {
		return errors.New("unexpected signed peer identity")
	}
	if resp.Header.Get("X-ConnectIT-Response-Nonce") != nonce {
		return errors.New("response challenge mismatch")
	}
	sig, e := base64.RawURLEncoding.DecodeString(resp.Header.Get("X-ConnectIT-Response-Signature"))
	if e != nil || len(sig) != ed25519.SignatureSize || !ed25519.Verify(key, responsePayload(nonce, resp.StatusCode, body), sig) {
		return errors.New("invalid response signature or contents")
	}
	return nil
}
func newMeshIdentity(dir, nodeID, certFile, keyFile string, master ed25519.PublicKey, allowed []string) (*MeshIdentity, error) {
	raw, e := os.ReadFile(certFile)
	if e != nil {
		return nil, e
	}
	cert := strings.TrimSpace(string(raw))
	p, pub, e := checkNodeCertificate(cert, master, time.Now().Unix())
	if e != nil {
		return nil, e
	}
	if p.NodeID != nodeID {
		return nil, errors.New("local node certificate ID mismatch")
	}
	priv, e := readPrivate(keyFile)
	if e != nil {
		return nil, e
	}
	if !ed25519.PublicKey(priv.Public().(ed25519.PublicKey)).Equal(pub) {
		return nil, errors.New("local node private key mismatches certificate")
	}
	peers := map[string]struct{}{}
	for _, v := range allowed {
		if !validName(v) || v == nodeID {
			return nil, errors.New("invalid or self peer ID")
		}
		if _, dup := peers[v]; dup {
			return nil, errors.New("duplicate trusted peer ID")
		}
		peers[v] = struct{}{}
	}
	return &MeshIdentity{NodeID: nodeID, Certificate: cert, Private: priv, Master: master, Allowed: peers, seen: make(map[string]int64)}, nil
}
func signedExport(w http.ResponseWriter, m *MeshIdentity, nonce string, status int, value any) {
	body, e := json.Marshal(value)
	if e != nil {
		http.Error(w, "internal serialization failure", 500)
		return
	}
	body = append(body, '\n')
	headers, e := m.signedResponse(nonce, status, body)
	if e != nil {
		http.Error(w, "signature failure", 500)
		return
	}
	for k, v := range headers {
		w.Header()[k] = v
	}
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_, _ = w.Write(body)
}

// Reject redirects: responses must be signed by the explicitly configured peer.
func signedDownload(client *http.Client, r *http.Request, m *MeshIdentity, expectedID string) ([]byte, int, error) {
	if err := m.signRequest(r, expectedID); err != nil {
		return nil, 0, err
	}
	nonce := r.Header.Get("X-ConnectIT-Node-Nonce")
	resp, e := client.Do(r)
	if e != nil {
		return nil, 0, e
	}
	defer resp.Body.Close()
	data, e := io.ReadAll(io.LimitReader(resp.Body, 24*1024*1024+1))
	if e != nil {
		return nil, 0, e
	}
	if len(data) > 24*1024*1024 {
		return nil, 0, errors.New("signed peer response oversized")
	}
	if e := m.verifyResponse(resp, nonce, expectedID, data); e != nil {
		return nil, 0, fmt.Errorf("signed peer response: %w", e)
	}
	return data, resp.StatusCode, nil
}
