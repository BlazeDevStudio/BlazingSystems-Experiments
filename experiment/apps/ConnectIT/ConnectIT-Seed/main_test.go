package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestSignedTokens(t *testing.T) {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	token := jwtIssue(priv, "alice", time.Hour)
	if user, err := jwtVerify(pub, token); err != nil || user != "alice" {
		t.Fatalf("valid JWT: %q %v", user, err)
	}
	if _, err := jwtVerify(pub, token+"x"); err == nil {
		t.Fatal("tampered token accepted")
	}
	pub2, _, _ := ed25519.GenerateKey(rand.Reader)
	if _, err := jwtVerify(pub2, token); err == nil {
		t.Fatal("unrelated key verified token")
	}
	if _, err := jwtVerify(pub, jwtIssue(priv, "alice", -time.Second)); err == nil {
		t.Fatal("expired token accepted")
	}
}
func TestStorePersistenceDedupAndRetention(t *testing.T) {
	dir := t.TempDir()
	store, e := newStore(dir, 100)
	if e != nil {
		t.Fatal(e)
	}
	for i := 0; i < 125; i++ {
		id := strings.Repeat("a", 16) + "-" + strings.Repeat("b", i%5+1) + "-" + strings.Repeat("0", 3) + string(rune('A'+i/5)) // avoid collisions
		if !validID(id) {
			t.Fatal("invalid test id")
		}
		msg := Message{ID: id, From: "alice", To: "bob", Kind: "message", Ciphertext: base64.StdEncoding.EncodeToString([]byte("opaque-encrypted-test"))}
		if _, saved, e := store.append(msg); e != nil || !saved {
			t.Fatalf("append %d: %v %v", i, saved, e)
		}
	}
	if store.listSize() != 100 {
		t.Fatalf("expected capped 100, got %d", store.listSize())
	}
	if _, expired, _ := store.read(1, "bob", 200); !expired {
		t.Fatal("old cursor must expire")
	}
	got, expired, _ := store.read(0, "bob", 200)
	if expired || len(got.Messages) != 100 {
		t.Fatalf("fetch: expired=%t records=%d", expired, len(got.Messages))
	}
	store2, e := newStore(dir, 100)
	if e != nil {
		t.Fatal(e)
	}
	got2, _, _ := store2.read(0, "bob", 200)
	if len(got2.Messages) != 100 || got2.Cursor != 125 {
		t.Fatalf("reopen %d cursor %d", len(got2.Messages), got2.Cursor)
	}
	existing := got2.Messages[0]
	_, saved, e := store2.append(existing)
	if e != nil || saved {
		t.Fatalf("dedupe failed: %t %v", saved, e)
	}
	b, e := os.ReadFile(filepath.Join(dir, "messages.jsonl"))
	if e != nil || len(b) == 0 {
		t.Fatalf("no persistence: %v", e)
	}
}
