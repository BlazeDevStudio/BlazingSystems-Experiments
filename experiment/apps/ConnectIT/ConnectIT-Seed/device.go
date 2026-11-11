package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Device certificates carry a public key; the private key never leaves the client.
// Proofs are signed per HTTP request, with a short timestamp window and replay cache.
type replayCache struct {
	mu   sync.Mutex
	seen map[string]int64
}

func newReplayCache() *replayCache { return &replayCache{seen: make(map[string]int64)} }
func (c *replayCache) claim(key string, now int64) bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	if until, ok := c.seen[key]; ok && until > now {
		return false
	}
	if len(c.seen) > 50000 {
		for k, v := range c.seen {
			if v <= now {
				delete(c.seen, k)
			}
		}
		if len(c.seen) > 50000 {
			return false
		}
	}
	c.seen[key] = now + 300
	return true
}
func requestProof(method, host, uri, timestamp, nonce string, body []byte) []byte {
	sum := sha256.Sum256(body)
	return []byte(method + "\n" + host + "\n" + uri + "\n" + timestamp + "\n" + nonce + "\n" + hex.EncodeToString(sum[:]))
}
func verifyDeviceProof(r *http.Request, pub64 string, cache *replayCache) error {
	pub, e := base64.StdEncoding.DecodeString(pub64)
	if e != nil || len(pub) != ed25519.PublicKeySize {
		return errors.New("bad enrolled public key")
	}
	ts := r.Header.Get("X-Device-Time")
	nonce := r.Header.Get("X-Device-Nonce")
	sig64 := r.Header.Get("X-Device-Signature")
	timestamp, e := strconv.ParseInt(ts, 10, 64)
	now := time.Now().Unix()
	if e != nil || timestamp < now-120 || timestamp > now+120 {
		return errors.New("stale device proof")
	}
	if len(nonce) < 20 || len(nonce) > 96 {
		return errors.New("bad device nonce")
	}
	if _, e = base64.RawURLEncoding.DecodeString(nonce); e != nil {
		return errors.New("bad nonce encoding")
	}
	sig, e := base64.RawURLEncoding.DecodeString(sig64)
	if e != nil || len(sig) != ed25519.SignatureSize {
		return errors.New("bad device signature")
	}
	body, e := io.ReadAll(io.LimitReader(r.Body, 16385))
	if e != nil || len(body) > 16384 {
		return errors.New("request too large")
	}
	r.Body.Close()
	r.Body = io.NopCloser(bytes.NewReader(body))
	if !ed25519.Verify(ed25519.PublicKey(pub), requestProof(r.Method, r.Host, r.URL.RequestURI(), ts, nonce, body), sig) {
		return errors.New("invalid device signature")
	}
	if !cache.claim(pub64+":"+nonce, now) {
		return errors.New("replayed device proof")
	}
	return nil
}
func envelopeSignedBytes(m Message) []byte {
	// Struct JSON field order makes the signed representation unambiguous.
	b, _ := json.Marshal(struct {
		ID         string `json:"id"`
		From       string `json:"from"`
		To         string `json:"to"`
		Kind       string `json:"kind"`
		Ciphertext string `json:"ciphertext_b64"`
		Created    int64  `json:"created"`
	}{m.ID, m.From, m.To, m.Kind, m.Ciphertext, m.Created})
	return b
}
func verifyEnvelope(m Message, masterKey ed25519.PublicKey, maxBytes int) error {
	if e := validateMsg(m, maxBytes); e != nil {
		return e
	}
	now := time.Now().Unix()
	if m.Created <= 0 || m.Created > now+120 || m.Created < now-7*86400 {
		return errors.New("invalid message creation time")
	}
	if m.Kind == "signal" && m.Created < now-180 {
		return errors.New("expired connection signal")
	}
	if len(m.SenderCertificate) > 4096 {
		return errors.New("certificate too long")
	}
	claims, e := jwtVerifyClaims(masterKey, m.SenderCertificate)
	if e != nil || claims.Sub != m.From || claims.DevicePublicKey == "" {
		return errors.New("invalid sender device certificate")
	}
	pub, e := base64.StdEncoding.DecodeString(claims.DevicePublicKey)
	if e != nil || len(pub) != ed25519.PublicKeySize {
		return errors.New("invalid sender device key")
	}
	sig, e := base64.RawURLEncoding.DecodeString(m.DeviceSignature)
	if e != nil || len(sig) != ed25519.SignatureSize || !ed25519.Verify(ed25519.PublicKey(pub), envelopeSignedBytes(m), sig) {
		return errors.New("invalid envelope signature")
	}
	return nil
}
func tokenUserUnsafe(cert string) (string, error) {
	parts := strings.Split(cert, ".")
	if len(parts) != 3 {
		return "", errors.New("invalid device certificate")
	}
	buf, e := base64.RawURLEncoding.DecodeString(parts[1])
	if e != nil || len(buf) > 4096 {
		return "", errors.New("invalid device certificate")
	}
	var c TokenClaims
	if e = json.Unmarshal(buf, &c); e != nil || !validName(c.Sub) {
		return "", errors.New("invalid device certificate")
	}
	// Not a trust decision: server independently verifies the master signature.
	return c.Sub, nil
}
func isLoopbackURL(s string) bool {
	u, e := url.Parse(s)
	if e != nil {
		return false
	}
	h := u.Hostname()
	if strings.EqualFold(h, "localhost") {
		return true
	}
	ip := net.ParseIP(h)
	return ip != nil && ip.IsLoopback()
}
func requireSafeHTTP(raw string) error {
	u, e := url.Parse(raw)
	if e != nil || u.Host == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || (u.Scheme != "https" && !(u.Scheme == "http" && isLoopbackURL(raw))) {
		return errors.New("server URL must be HTTPS (HTTP allowed only for localhost)")
	}
	return nil
}
func clientInit(args []string) error {
	fs, dir := flagDir(args, "client init")
	if e := fs.Parse(args); e != nil {
		return e
	}
	path := filepath.Join(*dir, "device.key")
	if _, e := os.Stat(path); e == nil {
		return errors.New("device already exists; refusing overwrite")
	}
	pub, priv, e := ed25519.GenerateKey(rand.Reader)
	if e != nil {
		return e
	}
	if e = writeAtomic(path, []byte(base64.StdEncoding.EncodeToString(priv)), 0600); e != nil {
		return e
	}
	if e = writeAtomic(filepath.Join(*dir, "device.pub"), []byte(base64.StdEncoding.EncodeToString(pub)), 0644); e != nil {
		return e
	}
	fmt.Println("Created device identity; keep device.key private and backed up.")
	return nil
}
func loadDevice(dir string) (ed25519.PrivateKey, string, error) {
	k, e := readPrivate(filepath.Join(dir, "device.key"))
	if e != nil {
		return nil, "", e
	}
	b, e := os.ReadFile(filepath.Join(dir, "device.cert"))
	if e != nil {
		return nil, "", e
	}
	return k, strings.TrimSpace(string(b)), nil
}
func clientEnroll(args []string) error {
	fs, dir := flagDir(args, "client enroll")
	master := fs.String("master-url", "", "master HTTPS URL")
	name := fs.String("username", "", "user account name")
	passEnv := fs.String("password-env", "BLAZE_PASSWORD", "password environment variable")
	if e := fs.Parse(args); e != nil {
		return e
	}
	if e := requireSafeHTTP(*master); e != nil {
		return e
	}
	if !validName(*name) {
		return errors.New("invalid username")
	}
	priv, e := readPrivate(filepath.Join(*dir, "device.key"))
	if e != nil {
		return e
	}
	pw := os.Getenv(*passEnv)
	if pw == "" {
		return errors.New("password environment variable not set")
	}
	b, _ := json.Marshal(map[string]string{"username": *name, "password": pw, "device_public_key_b64": base64.StdEncoding.EncodeToString(priv.Public().(ed25519.PublicKey))})
	client := &http.Client{Timeout: 20 * time.Second}
	res, e := client.Post(strings.TrimRight(*master, "/")+"/v1/enroll", "application/json", bytes.NewReader(b))
	if e != nil {
		return e
	}
	defer res.Body.Close()
	if res.StatusCode != 200 {
		return fmt.Errorf("enroll HTTP %d: %s", res.StatusCode, readSmall(res.Body))
	}
	var out struct {
		Certificate string `json:"device_certificate"`
		Expires     int    `json:"expires_in"`
	}
	if e = json.NewDecoder(io.LimitReader(res.Body, 8192)).Decode(&out); e != nil {
		return e
	}
	if out.Certificate == "" {
		return errors.New("missing certificate")
	}
	if e = writeAtomic(filepath.Join(*dir, "device.cert"), []byte(out.Certificate), 0600); e != nil {
		return e
	}
	fmt.Printf("Device enrolled; certificate valid for %d days. Master not needed for message access until renewal.\n", out.Expires/86400)
	return nil
}
func readSmall(r io.Reader) string {
	b, _ := io.ReadAll(io.LimitReader(r, 1024))
	return strings.TrimSpace(string(b))
}
func sendSigned(priv ed25519.PrivateKey, cert, method, target string, body []byte) (*http.Response, error) {
	req, e := http.NewRequest(method, target, bytes.NewReader(body))
	if e != nil {
		return nil, e
	}
	nonce := make([]byte, 24)
	if _, e = rand.Read(nonce); e != nil {
		return nil, e
	}
	ts := strconv.FormatInt(time.Now().Unix(), 10)
	n := base64.RawURLEncoding.EncodeToString(nonce)
	signature := ed25519.Sign(priv, requestProof(req.Method, req.URL.Host, req.URL.RequestURI(), ts, n, body))
	req.Header.Set("Authorization", "Bearer "+cert)
	req.Header.Set("X-Device-Time", ts)
	req.Header.Set("X-Device-Nonce", n)
	req.Header.Set("X-Device-Signature", base64.RawURLEncoding.EncodeToString(signature))
	req.Header.Set("Content-Type", "application/json")
	c := &http.Client{Timeout: 30 * time.Second, CheckRedirect: func(req *http.Request, via []*http.Request) error { return http.ErrUseLastResponse }}
	return c.Do(req)
}

// relayTargets builds an ordered set; the client can try the next seed if one fails.
func relayTargets(primary, csv string) ([]string, error) {
	joined := strings.TrimSpace(csv)
	if joined == "" {
		joined = primary
	}
	if joined == "" {
		return nil, errors.New("--relay-url or --relays required")
	}
	var out []string
	for _, part := range strings.Split(joined, ",") {
		target := strings.TrimRight(strings.TrimSpace(part), "/")
		if e := requireSafeHTTP(target); e != nil {
			return nil, e
		}
		out = append(out, target)
	}
	return out, nil
}
func clientSend(args []string) error {
	fs, dir := flagDir(args, "client send")
	relay := fs.String("relay-url", "", "relay HTTPS URL")
	relays := fs.String("relays", "", "comma-separated relay HTTPS URLs for ordered failover")
	to := fs.String("to", "", "recipient")
	kind := fs.String("kind", "message", "message or signal")
	ciphertext := fs.String("ciphertext-b64", "", "already-encrypted small envelope, base64")
	id := fs.String("id", "", "stable unique ID (for retries)")
	if e := fs.Parse(args); e != nil {
		return e
	}
	targets, e := relayTargets(*relay, *relays)
	if e != nil {
		return e
	}
	if *ciphertext == "" {
		return errors.New("ciphertext-b64 required; server does NOT encrypt plaintext")
	}
	priv, cert, e := loadDevice(*dir)
	if e != nil {
		return e
	}
	if *id == "" {
		*id = uniqueID()
	}
	from, e := tokenUserUnsafe(cert)
	if e != nil {
		return e
	}
	if *kind != "message" && *kind != "signal" {
		return errors.New("kind must be message or signal")
	}
	created := time.Now().Unix()
	m := Message{ID: from + ":" + *id, From: from, To: *to, Kind: *kind, Ciphertext: *ciphertext, Created: created}
	signature := base64.RawURLEncoding.EncodeToString(ed25519.Sign(priv, envelopeSignedBytes(m)))
	b, _ := json.Marshal(SendRequest{ID: *id, To: *to, Kind: *kind, Ciphertext: *ciphertext, Created: created, DeviceSignature: signature})
	var last error
	for _, target := range targets {
		res, e := sendSigned(priv, cert, "POST", target+"/v1/messages", b)
		if e != nil {
			last = e
			continue
		}
		if res.StatusCode == 202 {
			_, e = io.Copy(os.Stdout, io.LimitReader(res.Body, 8192))
			res.Body.Close()
			return e
		}
		last = fmt.Errorf("relay %s HTTP %d: %s", target, res.StatusCode, readSmall(res.Body))
		res.Body.Close()
		if res.StatusCode != 502 && res.StatusCode != 503 && res.StatusCode != 504 {
			return last
		}
	}
	return fmt.Errorf("no available seed: %w", last)
}
func clientInbox(args []string) error {
	fs, dir := flagDir(args, "client inbox")
	relay := fs.String("relay-url", "", "relay HTTPS URL")
	relays := fs.String("relays", "", "comma-separated relay URLs for ordered failover")
	since := fs.Uint64("since", 0, "relay-specific cursor; 0 means fetch retained messages")
	if e := fs.Parse(args); e != nil {
		return e
	}
	targets, e := relayTargets(*relay, *relays)
	if e != nil {
		return e
	}
	priv, cert, e := loadDevice(*dir)
	if e != nil {
		return e
	}
	var last error
	for _, base := range targets {
		target := base + "/v1/messages?since=" + strconv.FormatUint(*since, 10)
		res, e := sendSigned(priv, cert, "GET", target, nil)
		if e != nil {
			last = e
			continue
		}
		if res.StatusCode == 200 {
			_, e = io.Copy(os.Stdout, io.LimitReader(res.Body, 1024*1024))
			res.Body.Close()
			fmt.Println()
			return e
		}
		last = fmt.Errorf("relay %s HTTP %d: %s", base, res.StatusCode, readSmall(res.Body))
		res.Body.Close()
		if res.StatusCode != 502 && res.StatusCode != 503 && res.StatusCode != 504 {
			return last
		}
	}
	return fmt.Errorf("no available seed: %w", last)
}
