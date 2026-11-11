package main

import (
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"time"
)

// Test-only fixture issuer. The standalone Seed binary contains NO Master certificate issuer.
func jwtIssue(private ed25519.PrivateKey, user string, expires time.Duration) string {
	now := time.Now().Unix()
	data, _ := json.Marshal(TokenClaims{Iss: protocol, Aud: "blaze-relays", Sub: user, Iat: now, Exp: now + int64(expires.Seconds())})
	head := base64.RawURLEncoding.EncodeToString([]byte(tokenHeader))
	body := base64.RawURLEncoding.EncodeToString(data)
	signed := head + "." + body
	return signed + "." + base64.RawURLEncoding.EncodeToString(ed25519.Sign(private, []byte(signed)))
}
func jwtIssueDevice(private ed25519.PrivateKey, user string, device ed25519.PublicKey, expires time.Duration) string {
	now := time.Now().Unix()
	data, _ := json.Marshal(TokenClaims{Iss: protocol, Aud: "blaze-relays", Sub: user, Iat: now, Exp: now + int64(expires.Seconds()), DevicePublicKey: base64.StdEncoding.EncodeToString(device)})
	head := base64.RawURLEncoding.EncodeToString([]byte(tokenHeader))
	body := base64.RawURLEncoding.EncodeToString(data)
	signed := head + "." + body
	return signed + "." + base64.RawURLEncoding.EncodeToString(ed25519.Sign(private, []byte(signed)))
}
