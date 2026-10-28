package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type SeedConfig struct {
	NodeID          string   `json:"node_id"`
	Listen          string   `json:"listen"`
	MasterPublicKey string   `json:"master_public_key"`
	Peers           []string `json:"peers"`
	MaxMessages     int      `json:"max_messages"`
	MaxConnections  int      `json:"max_connections"`
	MaxPayloadBytes int      `json:"max_payload_bytes"`
	SyncSeconds     int      `json:"sync_seconds"`
	TLSCert         string   `json:"tls_cert"`
	TLSKey          string   `json:"tls_key"`
	MeshSecretEnv   string   `json:"mesh_secret_env"`
	RevocationsURL  string   `json:"revocations_url"`
	PeerIDs         []string `json:"peer_ids,omitempty"`
	NodeCert        string   `json:"node_cert,omitempty"`
	NodePrivateKey  string   `json:"node_private_key,omitempty"`
}

func configRead(dir string) (SeedConfig, error) {
	var c SeedConfig
	b, e := os.ReadFile(filepath.Join(dir, "seed.json"))
	if e != nil {
		return c, e
	}
	e = json.Unmarshal(b, &c)
	return c, e
}
func seedInit(args []string) error {
	fs, dir := flagDir(args, "seed init")
	id := fs.String("node-id", "", "seed name")
	listen := fs.String("listen", "127.0.0.1:8081", "listening address")
	pub := fs.String("master-public-key", "", "Master public key path (must be pinned and provisioned out of band)")
	peers := fs.String("peers", "", "comma-separated peer HTTPS URLs")
	revocationsURL := fs.String("revocations-url", "", "Master HTTPS /v1/revocations URL (required before remote exposure)")
	peerIDs := fs.String("peer-ids", "", "comma-separated expected remote node IDs in peers order")
	if e := fs.Parse(args); e != nil {
		return e
	}
	if !validName(*id) || *pub == "" {
		return errors.New("node-id and Master public key path required")
	}
	if _, e := readPublic(*pub); e != nil {
		return fmt.Errorf("trusted Master public key: %w", e)
	}
	if _, e := os.Stat(filepath.Join(*dir, "seed.json")); e == nil {
		return errors.New("seed configuration exists; refusing overwrite")
	}
	if e := os.MkdirAll(*dir, 0700); e != nil {
		return e
	}
	pubkey, priv, e := ed25519.GenerateKey(rand.Reader)
	if e != nil {
		return e
	}
	if e = writeAtomic(filepath.Join(*dir, "node.private.key"), []byte(base64.StdEncoding.EncodeToString(priv)), 0600); e != nil {
		return e
	}
	if e = writeAtomic(filepath.Join(*dir, "node.public.key"), []byte(base64.StdEncoding.EncodeToString(pubkey)), 0644); e != nil {
		return e
	}
	var urls []string
	if strings.TrimSpace(*peers) != "" {
		for _, p := range strings.Split(*peers, ",") {
			urls = append(urls, strings.TrimSpace(p))
		}
	}
	var trusted []string
	if *peerIDs != "" {
		for _, p := range strings.Split(*peerIDs, ",") {
			trusted = append(trusted, strings.TrimSpace(p))
		}
	}
	if len(trusted) > 0 && len(trusted) != len(urls) {
		return errors.New("peer-ids must correspond to every --peers URL")
	}
	c := SeedConfig{NodeID: *id, Listen: *listen, MasterPublicKey: *pub, Peers: urls, MaxMessages: 8000, MaxConnections: 64, MaxPayloadBytes: 8192, SyncSeconds: 3, MeshSecretEnv: "CONNECTIT_MESH_SECRET", RevocationsURL: *revocationsURL, PeerIDs: trusted, NodeCert: filepath.Join(*dir, "node.cert.json"), NodePrivateKey: filepath.Join(*dir, "node.private.key")}
	b, _ := json.MarshalIndent(c, "", "  ")
	if e = writeAtomic(filepath.Join(*dir, "seed.json"), b, 0600); e != nil {
		return e
	}
	fmt.Println("Seed initialized. Obtain a Master-signed node.cert.json for federation; remote shared-secret fallback is disabled.")
	return nil
}
func seedStart(args []string) error {
	fs, dir := flagDir(args, "seed start")
	if e := fs.Parse(args); e != nil {
		return e
	}
	c, e := configRead(*dir)
	if e != nil {
		return e
	}
	if _, e = readPublic(c.MasterPublicKey); e != nil {
		return fmt.Errorf("Master public key not found: %w", e)
	}
	if c.MaxConnections == 0 {
		c.MaxConnections = 64
	}
	x := []string{"--max-connections", fmt.Sprint(c.MaxConnections), "--dir", *dir, "--node-id", c.NodeID, "--listen", c.Listen, "--master-public-key", c.MasterPublicKey, "--max-messages", fmt.Sprint(c.MaxMessages), "--max-payload-bytes", fmt.Sprint(c.MaxPayloadBytes), "--sync-seconds", fmt.Sprint(c.SyncSeconds), "--mesh-secret-env", c.MeshSecretEnv}
	if c.RevocationsURL != "" {
		x = append(x, "--revocations-url", c.RevocationsURL)
	}
	if len(c.Peers) > 0 {
		x = append(x, "--peers", strings.Join(c.Peers, ","))
	}
	if len(c.PeerIDs) > 0 {
		x = append(x, "--peer-ids", strings.Join(c.PeerIDs, ","))
	}
	if c.NodeCert != "" {
		if _, e := os.Stat(c.NodeCert); e == nil {
			x = append(x, "--node-cert", c.NodeCert, "--node-private-key", c.NodePrivateKey)
		}
	}
	if c.TLSCert != "" {
		x = append(x, "--tls-cert", c.TLSCert, "--tls-key", c.TLSKey)
	}
	return relayServe(x)
}
func seedStatus(args []string) error {
	fs, dir := flagDir(args, "seed status")
	if e := fs.Parse(args); e != nil {
		return e
	}
	c, e := configRead(*dir)
	if e != nil {
		return e
	}
	fmt.Printf("Node %s; address %s; configured peer count %d\n", c.NodeID, c.Listen, len(c.Peers))
	if f, e := os.Stat(filepath.Join(*dir, "messages.jsonl")); e == nil {
		fmt.Printf("Persisted message-log bytes: %d\n", f.Size())
	} else {
		fmt.Println("No message log yet")
	}
	fmt.Println("This is local configuration/status, not a network reachability proof.")
	return nil
}
