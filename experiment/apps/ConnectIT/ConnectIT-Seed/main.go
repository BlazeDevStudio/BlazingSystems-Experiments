// Blaze Messenger Seed: compact, stdlib-only federated signaling / message relay prototype.
// Copyright is intentionally unspecified. See README for security limitations.
package main

import (
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/subtle"
	"crypto/tls"
	"encoding/base64"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"
)

const protocol = "blaze-seed-v1" // Conservative compatibility with v0.2.0 signed device credentials
const tokenHeader = `{"alg":"EdDSA","typ":"JWT"}`

type TokenClaims struct {
	Iss             string `json:"iss"`
	Aud             string `json:"aud"`
	Sub             string `json:"sub"`
	Iat             int64  `json:"iat"`
	Exp             int64  `json:"exp"`
	DevicePublicKey string `json:"device_public_key,omitempty"`
}
type Message struct {
	Seq               uint64 `json:"seq"`
	Hops              int    `json:"hops"`
	ID                string `json:"id"`
	From              string `json:"from"`
	To                string `json:"to"`
	Kind              string `json:"kind"`
	Ciphertext        string `json:"ciphertext_b64"`
	Time              int64  `json:"time"`
	Created           int64  `json:"created"`
	SenderCertificate string `json:"sender_certificate"`
	DeviceSignature   string `json:"device_signature_b64"`
}
type SendRequest struct {
	ID              string `json:"id"`
	To              string `json:"to"`
	Kind            string `json:"kind"`
	Ciphertext      string `json:"ciphertext_b64"`
	Created         int64  `json:"created"`
	DeviceSignature string `json:"device_signature_b64"`
}
type MessageSet struct {
	Messages []Message `json:"messages"`
	Cursor   uint64    `json:"cursor"`
}

func main() {
	log.SetFlags(log.LstdFlags | log.LUTC)
	if len(os.Args) < 2 {
		usage()
		return
	}
	var e error
	switch os.Args[1] {
	case "init":
		e = seedInit(os.Args[2:])
	case "start":
		e = seedStart(os.Args[2:])
	case "status":
		e = seedStatus(os.Args[2:])
	case "test-client-init":
		e = clientInit(os.Args[2:])
	case "test-client-send":
		e = clientSend(os.Args[2:])
	case "test-client-inbox":
		e = clientInbox(os.Args[2:])
	default:
		usage()
		os.Exit(2)
	}
	if e != nil {
		log.Printf("ERROR: %v", e)
		os.Exit(1)
	}
}
func usage() {
	fmt.Println(`ConnectIT Seed v0.1.3 signed federation preview
 connectit-seed init --dir ./seed-data --node-id seed-a --master-public-key ./master/public.key
 connectit-seed start --dir ./seed-data
 connectit-seed status --dir ./seed-data
 The Seed is a separate service; no account authority or private master signing key.
 See README.md for Master-signed node certificate setup and TLS/allowlist limitations.`)
}

func flagDir(args []string, name string) (*flag.FlagSet, *string) {
	fs := flag.NewFlagSet(name, flag.ContinueOnError)
	d := fs.String("dir", "./data", "persistent storage directory")
	return fs, d
}
func writeAtomic(path string, b []byte, perm os.FileMode) error {
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	f, err := os.CreateTemp(filepath.Dir(path), ".temp-*")
	if err != nil {
		return err
	}
	defer os.Remove(f.Name())
	defer f.Close()
	if err = f.Chmod(perm); err != nil {
		return err
	}
	if _, err = f.Write(b); err != nil {
		return err
	}
	if err = f.Sync(); err != nil {
		return err
	}
	if err = f.Close(); err != nil {
		return err
	}
	return os.Rename(f.Name(), path)
}
func validName(s string) bool {
	if len(s) < 1 || len(s) > 64 {
		return false
	}
	for _, r := range s {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '_' || r == '-' || r == '.' {
			continue
		}
		return false
	}
	return true
}
func readPrivate(path string) (ed25519.PrivateKey, error) {
	b, e := os.ReadFile(path)
	if e != nil {
		return nil, e
	}
	v, e := base64.StdEncoding.DecodeString(strings.TrimSpace(string(b)))
	if e != nil || len(v) != ed25519.PrivateKeySize {
		return nil, errors.New("invalid master private key")
	}
	return ed25519.PrivateKey(v), nil
}
func readPublic(path string) (ed25519.PublicKey, error) {
	b, e := os.ReadFile(path)
	if e != nil {
		return nil, e
	}
	v, e := base64.StdEncoding.DecodeString(strings.TrimSpace(string(b)))
	if e != nil || len(v) != ed25519.PublicKeySize {
		return nil, errors.New("invalid master public key")
	}
	return ed25519.PublicKey(v), nil
}
func jwtVerifyClaims(pub ed25519.PublicKey, token string) (TokenClaims, error) {
	var zero TokenClaims
	if len(token) > 4096 {
		return zero, errors.New("token too long")
	}
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return zero, errors.New("invalid token parts")
	}
	hb, e := base64.RawURLEncoding.DecodeString(parts[0])
	if e != nil || string(hb) != tokenHeader {
		return zero, errors.New("invalid token header")
	}
	sig, e := base64.RawURLEncoding.DecodeString(parts[2])
	if e != nil || len(sig) != ed25519.SignatureSize || !ed25519.Verify(pub, []byte(parts[0]+"."+parts[1]), sig) {
		return zero, errors.New("bad signature")
	}
	body, e := base64.RawURLEncoding.DecodeString(parts[1])
	if e != nil || len(body) > 4096 {
		return zero, errors.New("bad payload")
	}
	var c TokenClaims
	if e = json.Unmarshal(body, &c); e != nil {
		return zero, e
	}
	now := time.Now().Unix()
	maxLifetime := int64(7 * 86400)
	if c.DevicePublicKey != "" {
		devicePub, e := base64.StdEncoding.DecodeString(c.DevicePublicKey)
		if e != nil || len(devicePub) != ed25519.PublicKeySize {
			return zero, errors.New("invalid device public key")
		}
		maxLifetime = 366 * 86400
	}
	if c.Iss != protocol || c.Aud != "blaze-relays" || !validName(c.Sub) || c.Exp <= now || c.Iat > now+60 || c.Iat < now-maxLifetime-60 || c.Exp <= c.Iat || c.Exp > c.Iat+maxLifetime {
		return zero, errors.New("token expired or invalid claims")
	}
	return c, nil
}
func jwtVerify(pub ed25519.PublicKey, token string) (string, error) {
	c, e := jwtVerifyClaims(pub, token)
	return c.Sub, e
}

func sendJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
func sendError(w http.ResponseWriter, code int, message string) {
	sendJSON(w, code, map[string]string{"error": message})
}
func decodeBody(w http.ResponseWriter, r *http.Request, v any) bool {
	r.Body = http.MaxBytesReader(w, r.Body, 16384)
	defer r.Body.Close()
	d := json.NewDecoder(r.Body)
	d.DisallowUnknownFields()
	if err := d.Decode(v); err != nil {
		sendError(w, 400, "invalid json or request too large")
		return false
	}
	var extra any
	if err := d.Decode(&extra); err != io.EOF {
		sendError(w, 400, "trailing JSON data")
		return false
	}
	return true
}
func onlyMethod(w http.ResponseWriter, r *http.Request, method string) bool {
	if r.Method != method {
		w.Header().Set("Allow", method)
		sendError(w, 405, "method not allowed")
		return false
	}
	return true
}
func withServer(listen, cert, key string, h http.Handler, maxConnections int) error {
	if cert == "" {
		host, _, e := net.SplitHostPort(listen)
		if e != nil || !isLoopbackURL("http://"+net.JoinHostPort(host, "80")) {
			return errors.New("refusing public plaintext HTTP; use TLS cert/key or listen on 127.0.0.1 behind HTTPS reverse proxy")
		}
	}
	s := &http.Server{Addr: listen, Handler: h, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 15 * time.Second, IdleTimeout: 65 * time.Second, MaxHeaderBytes: 16384}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	go func() {
		<-ctx.Done()
		c, cancel := context.WithTimeout(context.Background(), 4*time.Second)
		defer cancel()
		_ = s.Shutdown(c)
	}()
	log.Printf("listening on %s (TLS=%t)", listen, cert != "")
	if (cert == "") != (key == "") {
		return errors.New("set both --tls-cert and --tls-key")
	}
	listener, e := net.Listen("tcp", listen)
	if e != nil {
		return e
	}
	defer listener.Close()
	lim := &boundedListener{Listener: listener, slots: make(chan struct{}, maxConnections)}
	var serving net.Listener = lim
	if cert != "" {
		pair, e := tls.LoadX509KeyPair(cert, key)
		if e != nil {
			return e
		}
		serving = tls.NewListener(lim, &tls.Config{MinVersion: tls.VersionTLS12, Certificates: []tls.Certificate{pair}})
	}
	e = s.Serve(serving)
	if errors.Is(e, http.ErrServerClosed) {
		return nil
	}
	return e
}

type Store struct {
	mu       sync.Mutex
	items    []Message
	ids      map[string]bool
	next     uint64
	maxItems int
	path     string
	notify   chan struct{}
}

func newStore(dir string, max int) (*Store, error) {
	if e := os.MkdirAll(dir, 0700); e != nil {
		return nil, e
	}
	s := &Store{maxItems: max, path: filepath.Join(dir, "messages.jsonl"), ids: make(map[string]bool), notify: make(chan struct{})}
	f, e := os.Open(s.path)
	if os.IsNotExist(e) {
		return s, nil
	}
	if e != nil {
		return nil, e
	}
	defer f.Close()
	dec := json.NewDecoder(f)
	for {
		var msg Message
		e = dec.Decode(&msg)
		if e == io.EOF {
			break
		}
		if e != nil {
			return nil, fmt.Errorf("corrupt message log: %w", e)
		}
		if msg.Seq <= s.next {
			return nil, errors.New("message log sequence not increasing")
		}
		s.next = msg.Seq
		s.items = append(s.items, msg)
		if len(s.items) > 2*max {
			s.items = append([]Message(nil), s.items[len(s.items)-max:]...)
		}
	}
	if len(s.items) > max {
		s.items = s.items[len(s.items)-max:]
	}
	for _, m := range s.items {
		s.ids[m.ID] = true
	}
	return s, nil
}
func (s *Store) oldest() uint64 {
	if len(s.items) == 0 {
		return 0
	}
	return s.items[0].Seq
}
func (s *Store) append(m Message) (Message, bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.ids[m.ID] {
		for _, existing := range s.items {
			if existing.ID == m.ID {
				if existing.From != m.From || existing.To != m.To || existing.Kind != m.Kind || existing.Ciphertext != m.Ciphertext {
					return existing, false, errors.New("message ID collision")
				}
				return existing, false, nil
			}
		}
		return Message{}, false, errors.New("duplicate id")
	}
	m.Seq = s.next + 1
	m.Time = time.Now().UnixMilli()
	b, e := json.Marshal(m)
	if e != nil {
		return m, false, e
	}
	f, e := os.OpenFile(s.path, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0600)
	if e != nil {
		return m, false, e
	}
	_, e = f.Write(append(b, '\n'))
	if e == nil {
		e = f.Sync()
	}
	closeErr := f.Close()
	if e == nil {
		e = closeErr
	}
	if e != nil {
		return m, false, e
	}
	s.next = m.Seq
	s.items = append(s.items, m)
	s.ids[m.ID] = true
	if len(s.items) > s.maxItems {
		old := s.items[0]
		delete(s.ids, old.ID)
		s.items = s.items[1:]
		if m.Seq%uint64(s.maxItems) == 0 {
			if e = s.compact(); e != nil {
				log.Printf("log compaction failed: %v", e)
			}
		}
	}
	close(s.notify)
	s.notify = make(chan struct{})
	return m, true, nil
}
func (s *Store) compact() error {
	var buf strings.Builder
	for _, m := range s.items {
		b, _ := json.Marshal(m)
		buf.Write(b)
		buf.WriteByte('\n')
	}
	return writeAtomic(s.path, []byte(buf.String()), 0600)
}
func (s *Store) read(since uint64, to string, limit int) (MessageSet, bool, <-chan struct{}) {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := MessageSet{Messages: []Message{}, Cursor: since}
	old := s.oldest()
	if since != 0 && old > 0 && since < old-1 {
		return out, true, s.notify
	}
	for _, m := range s.items {
		if m.Seq <= since {
			continue
		}
		out.Cursor = m.Seq
		if m.Kind == "signal" && time.Now().Unix()-m.Created > 180 {
			continue
		}
		if to == "" || m.To == to || m.From == to {
			out.Messages = append(out.Messages, m)
		}
		if len(out.Messages) >= limit {
			break
		}
	}
	// Cursor advances across filtered messages as well; per-user ordering is relay-local.
	if len(out.Messages) < limit {
		out.Cursor = s.next
	}
	return out, false, s.notify
}
func loadCursor(path string) map[string]uint64 {
	b, e := os.ReadFile(path)
	if e != nil {
		return map[string]uint64{}
	}
	m := map[string]uint64{}
	if json.Unmarshal(b, &m) != nil {
		return map[string]uint64{}
	}
	return m
}
func (s *Store) listSize() int { s.mu.Lock(); defer s.mu.Unlock(); return len(s.items) }
func uniqueID() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	return base64.RawURLEncoding.EncodeToString(b)
}
func validID(s string) bool {
	if len(s) < 16 || len(s) > 96 {
		return false
	}
	for _, r := range s {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '_' || r == '-' || r == '.' || r == ':' {
			continue
		}
		return false
	}
	return true
}
func validateMsg(m Message, maxBytes int) error {
	if !validID(m.ID) || !validName(m.From) || !validName(m.To) || !(m.Kind == "message" || m.Kind == "signal") {
		return errors.New("invalid id, sender, recipient or kind")
	}
	b, e := base64.StdEncoding.DecodeString(m.Ciphertext)
	if e != nil || len(b) == 0 || len(b) > maxBytes {
		return fmt.Errorf("ciphertext_b64 must be base64, 1..%d bytes", maxBytes)
	}
	return nil
}
func relayServe(args []string) error {
	fs, dir := flagDir(args, "relay serve")
	listen := fs.String("listen", "127.0.0.1:8081", "bind address")
	node := fs.String("node-id", "", "unique node identifier")
	pubPath := fs.String("master-public-key", "", "master public.key path")
	peers := fs.String("peers", "", "comma-separated peer URLs (HTTPS recommended)")
	env := fs.String("mesh-secret-env", "BLAZE_MESH_SECRET", "localhost-only legacy mesh secret environment variable")
	nodeCert := fs.String("node-cert", "", "Master-authorized node certificate (JSON)")
	nodeKey := fs.String("node-private-key", "", "Ed25519 node private key path")
	peerIDs := fs.String("peer-ids", "", "comma-separated trusted peer node IDs, in peers URL order")
	maxItems := fs.Int("max-messages", 8000, "number of retained envelopes (100..100000)")
	maxConnections := fs.Int("max-connections", 64, "maximum simultaneously accepted HTTP connections (4..2048)")
	maxBytes := fs.Int("max-payload-bytes", 8192, "max decoded ciphertext bytes (256..65536)")
	cert := fs.String("tls-cert", "", "HTTPS certificate")
	key := fs.String("tls-key", "", "HTTPS private key")
	period := fs.Int("sync-seconds", 3, "replication sync interval (1..60 seconds)")
	revokeURL := fs.String("revocations-url", "", "pinned Master HTTPS /v1/revocations endpoint")
	if e := fs.Parse(args); e != nil {
		return e
	}
	if !validName(*node) || *pubPath == "" || *maxItems < 100 || *maxItems > 100000 || *maxConnections < 4 || *maxConnections > 2048 || *maxBytes < 256 || *maxBytes > 65536 || *period < 1 || *period > 60 {
		return errors.New("invalid node-id, public key path, max-messages, max-payload-bytes or sync-seconds")
	}
	pub, e := readPublic(*pubPath)
	if e != nil {
		return e
	}
	s, e := newStore(*dir, *maxItems)
	if e != nil {
		return e
	}
	secret := os.Getenv(*env)
	var urls []string
	if strings.TrimSpace(*peers) != "" {
		for _, u := range strings.Split(*peers, ",") {
			u = strings.TrimRight(strings.TrimSpace(u), "/")
			if !(strings.HasPrefix(u, "https://") || strings.HasPrefix(u, "http://")) {
				return fmt.Errorf("bad peer url: %s", u)
			}
			if strings.HasPrefix(u, "http://") && !isLoopbackURL(u) {
				return fmt.Errorf("peer %s must use HTTPS (HTTP only for localhost)", u)
			}
			urls = append(urls, u)
		}
	}
	listenHost, _, listenErr := net.SplitHostPort(*listen)
	if listenErr != nil {
		return listenErr
	}
	ip := net.ParseIP(listenHost)
	loopback := (ip != nil && ip.IsLoopback()) || listenHost == "localhost"
	if !loopback && *revokeURL == "" {
		return errors.New("remote Seed requires signed Master revocations URL; refusing to serve unchecked device credentials")
	}
	revocations, e := newConfiguredRevocations(*dir, pub, *revokeURL)
	if e != nil {
		return e
	}
	if revocations == nil {
		log.Printf("WARNING: localhost-only legacy Seed has no revocation feed; not for production")
	}
	// Signed mode is mandatory for any non-loopback listener or federation URL.
	// Legacy shared-secret mode survives only for explicitly local regression clients.
	allLoopback := loopback
	for _, u := range urls {
		if !isLoopbackURL(u) {
			allLoopback = false
		}
	}
	var ids []string
	if *peerIDs != "" {
		for _, v := range strings.Split(*peerIDs, ",") {
			ids = append(ids, strings.TrimSpace(v))
		}
	}
	signedMode := *nodeCert != "" || *nodeKey != "" || *peerIDs != ""
	if !signedMode && !allLoopback {
		return errors.New("remote Seed federation requires Master-authorized signed node identity; no shared-secret fallback")
	}
	var mesh *MeshIdentity
	if signedMode {
		if *nodeCert == "" || *nodeKey == "" || len(ids) != len(urls) {
			return errors.New("signed mode requires node-cert, node-private-key and a peer-id per peer URL")
		}
		mesh, e = newMeshIdentity(*dir, *node, *nodeCert, *nodeKey, pub, ids)
		if e != nil {
			return fmt.Errorf("node identity: %w", e)
		}
	} else if len(urls) > 0 && len(secret) < 32 {
		return errors.New("localhost legacy mesh secret must have at least 32 characters")
	}
	mux := http.NewServeMux()
	internalAuth := func(r *http.Request) bool {
		return len(secret) >= 32 && subtle.ConstantTimeCompare([]byte(r.Header.Get("X-Mesh-Secret")), []byte(secret)) == 1
	}
	proofs := newReplayCache()
	authenticate := func(r *http.Request) (string, error) {
		h := strings.TrimSpace(r.Header.Get("Authorization"))
		if !strings.HasPrefix(h, "Bearer ") {
			return "", errors.New("Bearer token required")
		}
		claims, e := jwtVerifyClaims(pub, strings.TrimSpace(strings.TrimPrefix(h, "Bearer ")))
		if e != nil {
			return "", e
		}
		if claims.DevicePublicKey == "" {
			return "", errors.New("device certificate required")
		}
		if revocations != nil {
			if err := revocations.check(claims.DevicePublicKey); err != nil {
				return "", err
			}
		}
		if err := verifyDeviceProof(r, claims.DevicePublicKey, proofs); err != nil {
			return "", err
		}
		return claims.Sub, nil
	}
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		if !onlyMethod(w, r, "GET") {
			return
		}
		sendJSON(w, 200, map[string]any{"ok": true, "role": "relay", "node": *node, "protocol": protocol})
	})
	mux.HandleFunc("/v1/messages", func(w http.ResponseWriter, r *http.Request) {
		user, e := authenticate(r)
		if e != nil {
			sendError(w, 401, "invalid or expired token")
			return
		}
		if r.Method == "POST" {
			var req SendRequest
			if !decodeBody(w, r, &req) {
				return
			}
			if req.ID == "" {
				req.ID = uniqueID()
			}
			if req.Kind == "" {
				req.Kind = "message"
			}
			id := user + ":" + req.ID
			m := Message{ID: id, From: user, To: req.To, Kind: req.Kind, Ciphertext: req.Ciphertext, Created: req.Created, DeviceSignature: req.DeviceSignature, SenderCertificate: strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")}
			if e = verifyEnvelope(m, pub, *maxBytes); e != nil {
				sendError(w, 400, e.Error())
				return
			}
			saved, _, e := s.append(m)
			if e != nil {
				if strings.Contains(e.Error(), "message ID collision") {
					sendError(w, 409, "duplicate ID with different content")
				} else {
					sendError(w, 500, "cannot persist message")
				}
				return
			}
			sendJSON(w, 202, map[string]any{"id": saved.ID, "seq": saved.Seq, "node": *node})
			return
		}
		if r.Method == "GET" {
			since, e := strconv.ParseUint(r.URL.Query().Get("since"), 10, 64)
			if e != nil {
				sendError(w, 400, "since must be unsigned integer")
				return
			}
			wait := 0
			if p := r.URL.Query().Get("wait"); p != "" {
				wait, e = strconv.Atoi(p)
				if e != nil || wait < 0 || wait > 25 {
					sendError(w, 400, "wait must be 0..25 seconds")
					return
				}
			}
			out, expired, notify := s.read(since, user, 200)
			if expired {
				sendError(w, 410, "cursor fell outside retention; re-fetch with since=0 and reconcile ids")
				return
			}
			if len(out.Messages) == 0 && wait > 0 {
				timer := time.NewTimer(time.Duration(wait) * time.Second)
				defer timer.Stop()
				select {
				case <-notify:
				case <-timer.C:
				case <-r.Context().Done():
					return
				}
				out, expired, _ = s.read(since, user, 200)
				if expired {
					sendError(w, 410, "cursor expired")
					return
				}
			}
			sendJSON(w, 200, out)
			return
		}
		sendError(w, 405, "method not allowed")
	})
	mux.HandleFunc("/internal/export", func(w http.ResponseWriter, r *http.Request) {
		if mesh != nil {
			if e := mesh.authorizeRequest(r); e != nil {
				sendError(w, 403, "signed peer request rejected")
				return
			}
		} else if !internalAuth(r) {
			sendError(w, 403, "forbidden")
			return
		}
		if !onlyMethod(w, r, "GET") {
			return
		}
		since, e := strconv.ParseUint(r.URL.Query().Get("since"), 10, 64)
		if e != nil {
			sendError(w, 400, "invalid since")
			return
		}
		out, expired, _ := s.read(since, "", 200)
		filtered := out.Messages[:0]
		for _, m := range out.Messages {
			if m.Hops < 5 {
				filtered = append(filtered, m)
			}
		}
		out.Messages = filtered
		if expired {
			if mesh != nil {
				signedExport(w, mesh, r.Header.Get("X-ConnectIT-Node-Nonce"), 410, map[string]string{"error": "cursor expired"})
			} else {
				sendError(w, 410, "cursor expired")
			}
			return
		}
		if mesh != nil {
			signedExport(w, mesh, r.Header.Get("X-ConnectIT-Node-Nonce"), 200, out)
		} else {
			sendJSON(w, 200, out)
		}
	})
	mux.HandleFunc("/v1/info", func(w http.ResponseWriter, r *http.Request) {
		if !onlyMethod(w, r, "GET") {
			return
		}
		sendJSON(w, 200, map[string]any{"node": *node, "role": "relay", "retained": s.listSize(), "protocol": protocol, "max_payload_bytes": *maxBytes})
	})
	if len(urls) > 0 {
		ctx, stop := context.WithCancel(context.Background())
		defer stop()
		go syncPeersAuthenticated(ctx, s, urls, ids, mesh, secret, pub, *maxBytes, filepath.Join(*dir, "peer-cursors.json"), time.Duration(*period)*time.Second, revocations)
	}
	if revocations != nil {
		ctx, cancel := context.WithCancel(context.Background())
		defer cancel()
		go revocations.poll(ctx, *revokeURL, 60*time.Second)
	}
	return withServer(*listen, *cert, *key, mux, *maxConnections)
}
func syncPeers(ctx context.Context, s *Store, peers []string, secret string, masterKey ed25519.PublicKey, maxPayload int, path string, interval time.Duration, revocations *RevocationCache) {
	syncPeersAuthenticated(ctx, s, peers, nil, nil, secret, masterKey, maxPayload, path, interval, revocations)
}
func syncPeersAuthenticated(ctx context.Context, s *Store, peers, ids []string, mesh *MeshIdentity, secret string, masterKey ed25519.PublicKey, maxPayload int, path string, interval time.Duration, revocations *RevocationCache) {
	cursors := loadCursor(path)
	client := &http.Client{Timeout: 15 * time.Second, CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return errors.New("mesh redirect forbidden") }}
	t := time.NewTicker(interval)
	defer t.Stop()
	for {
		for _, peer := range peers {
			for p := 0; p < 10; p++ {
				r, e := http.NewRequestWithContext(ctx, "GET", peer+"/internal/export?since="+strconv.FormatUint(cursors[peer], 10), nil)
				if e != nil {
					break
				}
				var data []byte
				var status int
				if mesh != nil {
					if len(ids) != len(peers) {
						log.Printf("peer configuration has mismatched ID count")
						break
					}
					ix := -1
					for j, url := range peers {
						if url == peer {
							ix = j
							break
						}
					}
					if ix < 0 {
						break
					}
					data, status, e = signedDownload(client, r, mesh, ids[ix])
				} else {
					r.Header.Set("X-Mesh-Secret", secret)
					var res *http.Response
					res, e = client.Do(r)
					if e == nil {
						status = res.StatusCode
						data, e = io.ReadAll(io.LimitReader(res.Body, 24*1024*1024+1))
						res.Body.Close()
						if len(data) > 24*1024*1024 {
							e = errors.New("legacy peer response oversized")
						}
					}
				}
				if e != nil {
					log.Printf("peer %s authentication/transport: %v", peer, e)
					break
				}
				if status == 410 {
					cursors[peer] = 0
					continue
				}
				if status != 200 {
					break
				}
				var batch MessageSet
				e = json.Unmarshal(data, &batch)
				if e != nil {
					log.Printf("peer %s: invalid batch: %v", peer, e)
					break
				}
				failed := false
				for _, m := range batch.Messages {
					if m.Hops < 0 || m.Hops >= 5 {
						log.Printf("peer %s: hop limit exceeded", peer)
						failed = true
						break
					}
					if e = verifyEnvelope(m, masterKey, maxPayload); e != nil {
						log.Printf("peer %s: invalid envelope: %v", peer, e)
						failed = true
						break
					}
					if revocations != nil {
						c, err := jwtVerifyClaims(masterKey, m.SenderCertificate)
						if err != nil || revocations.check(c.DevicePublicKey) != nil {
							// Omit a now-revoked, already-stored message while advancing the
							// peer cursor so valid envelopes behind it are not starved.
							log.Printf("peer %s: skipping revoked sender envelope", peer)
							continue
						}
					}
					m.Hops++
					if _, _, e = s.append(m); e != nil {
						log.Printf("peer %s: save failure: %v", peer, e)
						failed = true
						break
					}
				}
				if failed {
					break
				}
				if batch.Cursor < cursors[peer] {
					break
				}
				cursors[peer] = batch.Cursor
				if b, e := json.Marshal(cursors); e == nil {
					if e = writeAtomic(path, b, 0600); e != nil {
						log.Printf("peer cursor persist: %v", e)
					}
				}
				if len(batch.Messages) < 200 {
					break
				}
			}
		}
		select {
		case <-ctx.Done():
			return
		case <-t.C:
		}
	}
}
