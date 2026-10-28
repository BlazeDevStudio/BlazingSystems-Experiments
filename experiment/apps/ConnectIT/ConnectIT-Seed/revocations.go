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
type RevocationCache struct {
	mu          sync.RWMutex
	pub         ed25519.PublicKey
	path        string
	generation  int64
	validUntil  int64
	initialized bool
	revoked     map[string]struct{}
}

func newRevocationCache(pub ed25519.PublicKey, path string) *RevocationCache {
	return &RevocationCache{pub: pub, path: path, revoked: make(map[string]struct{})}
}
func (c *RevocationCache) accept(b []byte, now int64) error {
	if len(b) > 6*1024*1024 {
		return errors.New("revocations oversized")
	}
	var s SignedRevocations
	if e := json.Unmarshal(b, &s); e != nil {
		return e
	}
	p := s.Payload
	if p.Format != "connectit-revocations-v1" || p.Generation < 0 || p.GeneratedAt > now+120 || p.GeneratedAt < now-3600 || p.ValidUntil <= now || p.ValidUntil > p.GeneratedAt+3600 {
		return errors.New("revocations expired or invalid clock window")
	}
	if len(p.RevokedKeyHashes) > 50000 {
		return errors.New("revocation list limit exceeded")
	}
	raw, _ := json.Marshal(p)
	sig, e := base64.RawURLEncoding.DecodeString(s.Signature)
	if e != nil || len(sig) != ed25519.SignatureSize || !ed25519.Verify(c.pub, append([]byte("ConnectIT-revocations-v1\n"), raw...), sig) {
		return errors.New("invalid revocation signature")
	}
	seen := make(map[string]struct{}, len(p.RevokedKeyHashes))
	if !sort.StringsAreSorted(p.RevokedKeyHashes) {
		return errors.New("unsorted revocation list")
	}
	for _, h := range p.RevokedKeyHashes {
		decoded, e := base64.RawURLEncoding.DecodeString(h)
		if e != nil || len(decoded) != sha256.Size {
			return errors.New("invalid revocation hash")
		}
		if _, ok := seen[h]; ok {
			return errors.New("duplicate revocation")
		}
		seen[h] = struct{}{}
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.initialized && p.Generation < c.generation {
		return errors.New("revocation generation rollback")
	}
	// Prevent using an older snapshot from the same generation while already online.
	if c.initialized && p.Generation == c.generation && p.ValidUntil < c.validUntil {
		return errors.New("revocation snapshot rollback")
	}
	c.generation = p.Generation
	c.validUntil = p.ValidUntil
	c.revoked = seen
	c.initialized = true
	return nil
}
func (c *RevocationCache) load() error {
	b, e := os.ReadFile(c.path)
	if e != nil {
		return e
	}
	return c.accept(b, time.Now().Unix())
}
func (c *RevocationCache) check(pub64 string) error {
	c.mu.RLock()
	defer c.mu.RUnlock()
	if !c.initialized || time.Now().Unix() >= c.validUntil {
		return errors.New("revocation state unavailable or expired")
	}
	pub, e := base64.StdEncoding.DecodeString(pub64)
	if e != nil || len(pub) != ed25519.PublicKeySize {
		return errors.New("bad device public key")
	}
	h := sha256.Sum256(pub)
	if _, bad := c.revoked[base64.RawURLEncoding.EncodeToString(h[:])]; bad {
		return errors.New("device revoked")
	}
	return nil
}
func (c *RevocationCache) refresh(ctx context.Context, endpoint string) error {
	u := strings.TrimSpace(endpoint)
	if !strings.HasSuffix(u, "/v1/revocations") {
		return errors.New("revocation URL must end with /v1/revocations")
	}
	if !strings.HasPrefix(u, "https://") && !(strings.HasPrefix(u, "http://") && isLoopbackURL(u)) {
		return errors.New("revocation URL requires HTTPS except localhost")
	}
	req, e := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if e != nil {
		return e
	}
	client := http.Client{Timeout: 8 * time.Second, CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return errors.New("revocation redirects disabled") }}
	res, e := client.Do(req)
	if e != nil {
		return e
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		return fmt.Errorf("master revocations HTTP %d", res.StatusCode)
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
func (c *RevocationCache) poll(ctx context.Context, endpoint string, every time.Duration) {
	t := time.NewTicker(every)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-t.C:
			if err := c.refresh(ctx, endpoint); err != nil {
				fmt.Fprintf(os.Stderr, "ConnectIT revocation refresh: %v (cached view valid only until signed deadline)\n", err)
			}
		}
	}
}
func newConfiguredRevocations(dir string, pub ed25519.PublicKey, endpoint string) (*RevocationCache, error) {
	if endpoint == "" {
		return nil, nil
	} // local-only legacy tests; remote listen requires configuration.
	c := newRevocationCache(pub, filepath.Join(dir, "signed-revocations.json"))
	cached := c.load()
	ctx, cancel := context.WithTimeout(context.Background(), 9*time.Second)
	defer cancel()
	fresh := c.refresh(ctx, endpoint)
	if fresh != nil && cached != nil {
		return nil, fmt.Errorf("no trusted fresh revocation view (cache: %v; master: %v)", cached, fresh)
	}
	return c, nil
}
