package main

import (
	"context"
	"crypto/ed25519"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	_ "embed"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"math/big"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
)

//go:embed schema.sql
var schema string

const proto = "blaze-seed-v1" // Legacy relay certificate compatibility, not a claim of ConnectIT-v1 feature completeness.
const jwtHead = `{"alg":"EdDSA","typ":"JWT"}`
const rounds = 310000

func b64(b []byte) string { return base64.StdEncoding.EncodeToString(b) }
func rnd(n int) string {
	b := make([]byte, n)
	if _, e := rand.Read(b); e != nil {
		panic(e)
	}
	return base64.RawURLEncoding.EncodeToString(b)
}
func durable(path string, b []byte, mode os.FileMode) error {
	if e := os.MkdirAll(filepath.Dir(path), 0700); e != nil {
		return e
	}
	f, e := os.CreateTemp(filepath.Dir(path), ".pending-")
	if e != nil {
		return e
	}
	defer os.Remove(f.Name())
	defer f.Close()
	if e = f.Chmod(mode); e != nil {
		return e
	}
	if _, e = f.Write(b); e != nil {
		return e
	}
	if e = f.Sync(); e != nil {
		return e
	}
	if e = f.Close(); e != nil {
		return e
	}
	return os.Rename(f.Name(), path)
}
func readKey(dir, n string, sz int) ([]byte, error) {
	b, e := os.ReadFile(filepath.Join(dir, n))
	if e != nil {
		return nil, e
	}
	p, e := base64.StdEncoding.DecodeString(strings.TrimSpace(string(b)))
	if e != nil || len(p) != sz {
		return nil, errors.New("invalid " + n)
	}
	return p, nil
}
func pbkdf2(pw string, salt []byte, iteration int) []byte {
	m := hmac.New(sha256.New, []byte(pw))
	m.Write(salt)
	var block [4]byte
	binary.BigEndian.PutUint32(block[:], 1)
	m.Write(block[:])
	u := m.Sum(nil)
	out := append([]byte(nil), u...)
	for i := 1; i < iteration; i++ {
		m = hmac.New(sha256.New, []byte(pw))
		m.Write(u)
		u = m.Sum(nil)
		for j := range out {
			out[j] ^= u[j]
		}
	}
	return out
}
func salted(pw string) (string, string, error) {
	if len(pw) < 12 || len(pw) > 1024 {
		return "", "", errors.New("password must be 12..1024 characters")
	}
	salt := make([]byte, 16)
	if _, e := rand.Read(salt); e != nil {
		return "", "", e
	}
	return b64(salt), b64(pbkdf2(pw, salt, rounds)), nil
}
func comparePw(pw, salt, hash string, iter int) bool {
	if len(pw) > 1024 || iter < 100000 || iter > 1000000 {
		return false
	}
	s, e := base64.StdEncoding.DecodeString(salt)
	if e != nil || len(s) != 16 {
		return false
	}
	h, e := base64.StdEncoding.DecodeString(hash)
	if e != nil || len(h) != 32 {
		return false
	}
	return subtle.ConstantTimeCompare(h, pbkdf2(pw, s, iter)) == 1
}
func rows1(rows []map[string]string) map[string]string {
	if len(rows) == 0 {
		return nil
	}
	return rows[0]
}
func issue(priv ed25519.PrivateKey, id, pub string, seconds int64) string {
	now := time.Now().Unix()
	claims := struct {
		Iss string `json:"iss"`
		Aud string `json:"aud"`
		Sub string `json:"sub"`
		Iat int64  `json:"iat"`
		Exp int64  `json:"exp"`
		Key string `json:"device_public_key,omitempty"`
	}{proto, "blaze-relays", id, now, now + seconds, pub}
	raw, _ := json.Marshal(claims)
	head := base64.RawURLEncoding.EncodeToString([]byte(jwtHead))
	payload := base64.RawURLEncoding.EncodeToString(raw)
	signed := head + "." + payload
	return signed + "." + base64.RawURLEncoding.EncodeToString(ed25519.Sign(priv, []byte(signed)))
}
func validPub(s string) bool {
	b, e := base64.StdEncoding.DecodeString(s)
	return e == nil && len(b) == 32
}
func validID(s string) bool {
	if len(s) != 10 {
		return false
	}
	for _, c := range s {
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}
func installHash(secret []byte, token string) string {
	mac := hmac.New(sha256.New, secret)
	mac.Write([]byte("connectit.install-id.v1\x00"))
	mac.Write([]byte(token))
	return b64(mac.Sum(nil))
}
func validInstall(token string) bool { return len(token) >= 20 && len(token) <= 256 } // pseudonymous installation token only, cannot guarantee true HWID
func newID() (string, error) {
	i, e := rand.Int(rand.Reader, big.NewInt(10000000000))
	if e != nil {
		return "", e
	}
	return fmt.Sprintf("%010d", i.Int64()), nil
}
func dbpath(d string) string { return filepath.Join(d, "connectit.sqlite3") }
func main() {
	if len(os.Args) < 2 {
		usage()
		return
	}
	fs := flag.NewFlagSet("connectit-master", flag.ExitOnError)
	dir := fs.String("dir", "./master-data", "state directory")
	listen := fs.String("listen", "127.0.0.1:7070", "listener for start")
	tlsCert := fs.String("tls-cert", "", "TLS certificate PEM")
	tlsKey := fs.String("tls-key", "", "TLS key PEM")
	nick := fs.String("nickname", "", "nickname for account creation")
	id := fs.String("id", "", "account ID")
	deviceID := fs.String("device-id", "", "device ID for local revocation")
	nodeID := fs.String("node-id", "", "federation Seed node identifier")
	nodePub := fs.String("node-public-key", "", "federation Seed public key path")
	nodeOut := fs.String("node-cert-out", "", "new signed Seed certificate output path")
	nodeCertToRevoke := fs.String("node-cert", "", "Master-signed node certificate to revoke")
	nodeTTL := fs.Int("node-ttl-hours", 24, "authorized Seed certificate hours (1..168)")
	backupTo := fs.String("backup-to", "", "destination path for an atomic SQLite backup (must not exist)")
	pwEnv := fs.String("password-env", "CONNECTIT_PASSWORD", "environment variable containing account password")
	oldEnv := fs.String("old-password-env", "CONNECTIT_OLD_ADMIN_PASSWORD", "current admin password variable")
	newEnv := fs.String("new-password-env", "CONNECTIT_NEW_ADMIN_PASSWORD", "new admin password variable")
	adminEnv := fs.String("admin-password-env", "CONNECTIT_BOOTSTRAP_PASSWORD", "bootstrap admin password environment variable")
	_ = fs.Parse(os.Args[2:])
	var e error
	switch os.Args[1] {
	case "init":
		e = initMaster(*dir, os.Getenv(*adminEnv))
	case "admin-rotate":
		e = rotateAdmin(*dir, os.Getenv(*oldEnv), os.Getenv(*newEnv))
	case "account-create":
		e = createAccount(*dir, *nick, os.Getenv(*pwEnv))
	case "account-disable":
		e = disableAccount(*dir, *id)
	case "device-revoke":
		e = revokeDevice(*dir, *deviceID)
	case "node-revoke":
		e = nodeRevoke(*dir, *nodeCertToRevoke)
	case "node-authorize":
		e = nodeAuthorize(*dir, *nodeID, *nodePub, *nodeOut, *nodeTTL)
	case "start":
		e = start(*dir, *listen, *tlsCert, *tlsKey)
	case "check":
		e = check(*dir)
	case "backup":
		e = backup(*dir, *backupTo)
	case "status":
		e = status(*dir)
	default:
		usage()
		os.Exit(2)
	}
	if e != nil {
		log.Fatalf("%s: %v", os.Args[1], e)
	}
}
func usage() {
	fmt.Println(`ConnectIT Master Seed v0.1.0 foundation
 connectit-master init --dir ./master-data                 # set CONNECTIT_BOOTSTRAP_PASSWORD
 connectit-master admin-rotate --dir ./master-data         # set CONNECTIT_OLD_ADMIN_PASSWORD and CONNECTIT_NEW_ADMIN_PASSWORD
 connectit-master account-create --nickname Alice         # set CONNECTIT_PASSWORD
 connectit-master account-disable --id 0000000000
 connectit-master device-revoke --device-id <device-id>
 connectit-master node-revoke --dir ./master-data --node-cert compromised-node.cert.json
 connectit-master node-authorize --dir ./master-data --node-id seed-a --node-public-key seed-a/node.public.key --node-cert-out seed-a/node.cert.json --node-ttl-hours 24
 connectit-master start --listen 127.0.0.1:7070
 connectit-master check
 connectit-master backup --backup-to ./backup.sqlite3
 connectit-master status
 All management actions are LOCAL-OS-PRIVILEGED; remote admin API deliberately unavailable.
 No default plaintext password is embedded. See README.`)
}
func initMaster(dir, pw string) error {
	if len(pw) < 12 {
		return errors.New("provide an initial temporary admin password of at least 12 chars using CONNECTIT_BOOTSTRAP_PASSWORD")
	}
	if _, e := os.Stat(filepath.Join(dir, "private.key")); e == nil {
		return errors.New("already initialized; refusing overwrite")
	}
	pub, priv, e := ed25519.GenerateKey(rand.Reader)
	if e != nil {
		return e
	}
	secret := make([]byte, 32)
	if _, e = rand.Read(secret); e != nil {
		return e
	}
	s, h, e := salted(pw)
	if e != nil {
		return e
	}
	d, e := openDB(dbpath(dir))
	if e != nil {
		return e
	}
	defer d.close()
	if e = d.script(schema); e != nil {
		return e
	}
	if _, e = d.run("INSERT INTO admins(username,salt,hash,iterations,must_rotate) VALUES(?,?,?,?,1)", "blaze", s, h, rounds); e != nil {
		return e
	}
	if e = durable(filepath.Join(dir, "private.key"), []byte(b64(priv)), 0600); e != nil {
		return e
	}
	if e = durable(filepath.Join(dir, "public.key"), []byte(b64(pub)), 0644); e != nil {
		return e
	}
	if e = durable(filepath.Join(dir, "install-hmac.key"), []byte(b64(secret)), 0600); e != nil {
		return e
	}
	fmt.Println("Initialized ConnectIT Master. Rotate temporary admin password before start. Never expose private.key or install-hmac.key.")
	return nil
}
func rotated(d *DB) (bool, error) {
	a, e := d.run("SELECT must_rotate FROM admins WHERE username=?", "blaze")
	if e != nil {
		return false, e
	}
	if len(a) == 0 {
		return false, errors.New("missing bootstrap admin")
	}
	return a[0]["must_rotate"] == "0", nil
}
func rotateAdmin(dir, old, new string) error {
	d, e := openDB(dbpath(dir))
	if e != nil {
		return e
	}
	defer d.close()
	a, e := d.run("SELECT salt,hash,iterations FROM admins WHERE username=?", "blaze")
	if e != nil {
		return e
	}
	if len(a) == 0 {
		return errors.New("missing bootstrap admin")
	}
	it, _ := strconv.Atoi(a[0]["iterations"])
	if !comparePw(old, a[0]["salt"], a[0]["hash"], it) {
		return errors.New("incorrect old admin password")
	}
	if old == new {
		return errors.New("new password must differ from previous password")
	}
	s, h, e := salted(new)
	if e != nil {
		return e
	}
	_, e = d.run("UPDATE admins SET salt=?,hash=?,iterations=?,must_rotate=0 WHERE username='blaze'", s, h, rounds)
	if e == nil {
		fmt.Println("Admin password rotated; start is now permitted")
	}
	return e
}
func createAccount(dir, nick, pw string) error {
	if len([]rune(nick)) < 1 || len([]rune(nick)) > 64 {
		return errors.New("nickname required (1..64 characters)")
	}
	d, e := openDB(dbpath(dir))
	if e != nil {
		return e
	}
	defer d.close()
	ready, e := rotated(d)
	if e != nil {
		return e
	}
	if !ready {
		return errors.New("rotate admin password before creating accounts")
	}
	s, h, e := salted(pw)
	if e != nil {
		return e
	}
	for i := 0; i < 12; i++ {
		id, e := newID()
		if e != nil {
			return e
		}
		_, e = d.run("INSERT INTO accounts(id,nickname,salt,hash,iterations,state,created) VALUES(?,?,?,?,?,?,?)", id, nick, s, h, rounds, "active", time.Now().Unix())
		if e == nil {
			d.run("INSERT INTO audit(created,action,subject,detail) VALUES(?,?,?,?)", time.Now().Unix(), "account.create", id, "local-admin-cli")
			fmt.Printf("Account created: %s (nickname %q)\n", id, nick)
			return nil
		}
		if !strings.Contains(e.Error(), "UNIQUE constraint failed: accounts.id") {
			return e
		}
	}
	return errors.New("unable to allocate unique ID")
}
func disableAccount(dir, id string) error {
	if !validID(id) {
		return errors.New("invalid 10-digit ID")
	}
	d, e := openDB(dbpath(dir))
	if e != nil {
		return e
	}
	defer d.close()
	return d.transaction(func() error {
		if _, e := d.query("UPDATE accounts SET state='disabled' WHERE id=?", id); e != nil {
			return e
		}
		_, e = d.query("UPDATE devices SET state='revoked' WHERE account_id=?", id)
		if e != nil {
			return e
		}
		return bumpRevocations(d)
	})
}
func check(dir string) error {
	d, e := openDB(dbpath(dir))
	if e != nil {
		return e
	}
	defer d.close()
	v, e := d.run("PRAGMA integrity_check")
	if e != nil {
		return e
	}
	fmt.Println("SQLite integrity:", v)
	return nil
}
func backup(dir, path string) error {
	if path == "" {
		return errors.New("--backup-to required")
	}
	if _, e := os.Stat(path); e == nil {
		return errors.New("backup destination exists; refusing overwrite")
	}
	if e := os.MkdirAll(filepath.Dir(path), 0700); e != nil {
		return e
	}
	d, e := openDB(dbpath(dir))
	if e != nil {
		return e
	}
	defer d.close()
	if _, e = d.run("VACUUM INTO ?", path); e != nil {
		return e
	}
	verify, e := openDB(path)
	if e != nil {
		return e
	}
	defer verify.close()
	result, e := verify.run("PRAGMA integrity_check")
	if e != nil || len(result) != 1 || result[0]["integrity_check"] != "ok" {
		return errors.New("backup integrity failed")
	}
	fmt.Println("Verified SQLite snapshot at", path)
	return nil
}
func status(dir string) error {
	d, e := openDB(dbpath(dir))
	if e != nil {
		return e
	}
	defer d.close()
	for _, tb := range []string{"accounts", "devices", "bindings", "binding_approvals"} {
		r, e := d.run("SELECT COUNT(*) AS count FROM " + tb)
		if e != nil {
			return e
		}
		fmt.Println(tb, r[0]["count"])
	}
	return nil
}
func reply(w http.ResponseWriter, n int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(n)
	json.NewEncoder(w).Encode(v)
}
func failure(w http.ResponseWriter, n int, s string) { reply(w, n, map[string]string{"error": s}) }
func decode(w http.ResponseWriter, r *http.Request, v any) bool {
	r.Body = http.MaxBytesReader(w, r.Body, 16384)
	defer r.Body.Close()
	de := json.NewDecoder(r.Body)
	de.DisallowUnknownFields()
	if de.Decode(v) != nil {
		failure(w, 400, "invalid JSON")
		return false
	}
	var extra any
	if de.Decode(&extra) != io.EOF {
		failure(w, 400, "extra JSON content")
		return false
	}
	return true
}
func start(dir, listen, cert, key string) error {
	d, e := openDB(dbpath(dir))
	if e != nil {
		return e
	}
	defer d.close()
	ready, e := rotated(d)
	if e != nil {
		return e
	}
	if !ready {
		return errors.New("admin password must be rotated before any network listener starts")
	}
	private, e := readKey(dir, "private.key", 64)
	if e != nil {
		return e
	}
	hmacSecret, e := readKey(dir, "install-hmac.key", 32)
	if e != nil {
		return e
	}
	host, _, e := net.SplitHostPort(listen)
	if e != nil {
		return e
	}
	ip := net.ParseIP(host)
	isLocal := (ip != nil && ip.IsLoopback()) || host == "localhost"
	if !isLocal && (cert == "" || key == "") {
		return errors.New("non-loopback bind requires TLS certificate and key")
	}
	if (cert == "") != (key == "") {
		return errors.New("both TLS cert and key must be provided")
	}
	if e = migrateNodeRevocations(d); e != nil {
		return e
	}
	api := &api{db: d, priv: ed25519.PrivateKey(private), hmacKey: hmacSecret, attempts: map[string]rate{}}
	mux := http.NewServeMux()
	api.routes(mux)
	srv := &http.Server{Addr: listen, Handler: mux, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 12 * time.Second, WriteTimeout: 30 * time.Second, IdleTimeout: 45 * time.Second, MaxHeaderBytes: 8192}
	done := make(chan os.Signal, 1)
	signal.Notify(done, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-done
		ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
		defer cancel()
		srv.Shutdown(ctx)
	}()
	log.Printf("ConnectIT Master listening on %s; admin endpoints intentionally absent", listen)
	if cert != "" {
		e = srv.ListenAndServeTLS(cert, key)
	} else {
		e = srv.ListenAndServe()
	}
	if errors.Is(e, http.ErrServerClosed) {
		return nil
	}
	return e
}
