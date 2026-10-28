package main

import (
	"context"
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

const nodeRevocationPrefix = "ConnectIT-node-revocations-v1\n"

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
type NodeRevocationCache struct {
	mu          sync.RWMutex
	pub         ed25519.PublicKey
	path        string
	initialized bool
	generation  int64
	validUntil  int64
	revoked     map[string]struct{}
}

func newNodeRevocationCache(pub ed25519.PublicKey, path string) *NodeRevocationCache {
	return &NodeRevocationCache{pub: pub, path: path, revoked: make(map[string]struct{})}
}
func (c *NodeRevocationCache) accept(b []byte, now int64) error {
	if len(b) > 6*1024*1024 {
		return errors.New("node revocation view oversized")
	}
	var doc SignedNodeRevocations
	if e := json.Unmarshal(b, &doc); e != nil {
		return e
	}
	p := doc.Payload
	if p.Format != "connectit-node-revocations-v1" || p.Generation < 0 || p.GeneratedAt > now+120 || p.GeneratedAt < now-3600 || p.ValidUntil <= now || p.ValidUntil > p.GeneratedAt+3600 {
		return errors.New("node revocation clock or generation invalid")
	}
	if len(p.RevokedNodeKeyHashes) > 50000 || !sort.StringsAreSorted(p.RevokedNodeKeyHashes) {
		return errors.New("invalid node revocation ordering or size")
	}
	raw, _ := json.Marshal(p)
	sig, e := base64.RawURLEncoding.DecodeString(doc.Signature)
	if e != nil || len(sig) != ed25519.SignatureSize || !ed25519.Verify(c.pub, append([]byte(nodeRevocationPrefix), raw...), sig) {
		return errors.New("invalid Master node revocation signature")
	}
	keys := make(map[string]struct{}, len(p.RevokedNodeKeyHashes))
	for _, h := range p.RevokedNodeKeyHashes {
		k, e := base64.RawURLEncoding.DecodeString(h)
		if e != nil || len(k) != sha256.Size {
			return errors.New("bad revoked node fingerprint")
		}
		if _, found := keys[h]; found {
			return errors.New("duplicate node revocation")
		}
		keys[h] = struct{}{}
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.initialized && (p.Generation < c.generation || (p.Generation == c.generation && p.ValidUntil < c.validUntil)) {
		return errors.New("node revocation rollback")
	}
	c.initialized = true
	c.generation = p.Generation
	c.validUntil = p.ValidUntil
	c.revoked = keys
	return nil
}
func (c *NodeRevocationCache) check(pub ed25519.PublicKey) error {
	if c == nil {
		return errors.New("no node revocation cache")
	}
	c.mu.RLock()
	defer c.mu.RUnlock()
	if !c.initialized || time.Now().Unix() >= c.validUntil {
		return errors.New("node revocations stale or unavailable")
	}
	if len(pub) != ed25519.PublicKeySize {
		return errors.New("invalid node public key")
	}
	sum := sha256.Sum256(pub)
	if _, banned := c.revoked[base64.RawURLEncoding.EncodeToString(sum[:])]; banned {
		return errors.New("revoked node signing key")
	}
	return nil
}
func (c *NodeRevocationCache) load() error {
	b, e := os.ReadFile(c.path)
	if e != nil {
		return e
	}
	return c.accept(b, time.Now().Unix())
}
func (c *NodeRevocationCache) refresh(ctx context.Context, endpoint string) error {
	u := strings.TrimSpace(endpoint)
	if !strings.HasSuffix(u, "/v1/node-revocations") {
		return errors.New("bad node revocations URL")
	}
	if !strings.HasPrefix(u, "https://") && !(strings.HasPrefix(u, "http://") && isLoopbackURL(u)) {
		return errors.New("node revocation URL requires HTTPS except localhost")
	}
	req, e := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if e != nil {
		return e
	}
	client := http.Client{Timeout: 8 * time.Second, CheckRedirect: func(_ *http.Request, _ []*http.Request) error {
		return errors.New("node revocation redirect forbidden")
	}}
	res, e := client.Do(req)
	if e != nil {
		return e
	}
	defer res.Body.Close()
	if res.StatusCode != 200 {
		return fmt.Errorf("node revocation HTTP %d", res.StatusCode)
	}
	b, e := io.ReadAll(io.LimitReader(res.Body, 6*1024*1024+1))
	if e != nil {
		return e
	}
	if e = c.accept(b, time.Now().Unix()); e != nil {
		return e
	}
	return writeAtomic(c.path, b, 0600)
}
func (c *NodeRevocationCache) poll(ctx context.Context, u string, every time.Duration) {
	t := time.NewTicker(every)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-t.C:
			if e := c.refresh(ctx, u); e != nil {
				fmt.Fprintf(os.Stderr, "ConnectIT node revocations refresh: %v (fail closed after signed expiry)\n", e)
			}
		}
	}
}
func configuredNodeRevocations(dir string, master ed25519.PublicKey, deviceURL string) (*NodeRevocationCache, error) {
	if deviceURL == "" {
		return nil, errors.New("signed mesh requires Master node revocations URL")
	}
	u := strings.TrimSuffix(deviceURL, "/v1/revocations") + "/v1/node-revocations"
	c := newNodeRevocationCache(master, filepath.Join(dir, "signed-node-revocations.json"))
	cached := c.load()
	ctx, cancel := context.WithTimeout(context.Background(), 9*time.Second)
	defer cancel()
	fresh := c.refresh(ctx, u)
	if cached != nil && fresh != nil {
		return nil, fmt.Errorf("node revocations unavailable (cache %v; Master %v)", cached, fresh)
	}
	return c, nil
}
