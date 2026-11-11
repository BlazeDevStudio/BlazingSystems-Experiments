-- ConnectIT Master authority schema v1. No seed receives this database.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS admins(username TEXT PRIMARY KEY, salt TEXT NOT NULL, hash TEXT NOT NULL, iterations INTEGER NOT NULL, must_rotate INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY CHECK(length(id)=10 AND id NOT GLOB '*[^0-9]*'), nickname TEXT NOT NULL, salt TEXT NOT NULL, hash TEXT NOT NULL, iterations INTEGER NOT NULL, state TEXT NOT NULL DEFAULT 'active' CHECK(state IN ('active','disabled','retired')), created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS registered_tokens(token_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), released INTEGER NOT NULL DEFAULT 0);
CREATE UNIQUE INDEX IF NOT EXISTS live_token ON registered_tokens(token_hash) WHERE released=0;
CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), public_key TEXT NOT NULL UNIQUE, token_hash TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('active','revoked')), created INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS account_devices ON devices(account_id,state);
CREATE TABLE IF NOT EXISTS bindings(id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), target_key TEXT NOT NULL, target_token TEXT NOT NULL, challenge TEXT NOT NULL, started INTEGER NOT NULL, expires INTEGER NOT NULL, state TEXT NOT NULL CHECK(state IN ('pending','approved','revoked','completed','expired')), approvals INTEGER NOT NULL DEFAULT 0, created_nonce TEXT NOT NULL UNIQUE);
CREATE INDEX IF NOT EXISTS pending_bindings ON bindings(account_id,state);
CREATE TABLE IF NOT EXISTS binding_approvals(id TEXT PRIMARY KEY, binding_id TEXT NOT NULL REFERENCES bindings(id), device_id TEXT NOT NULL REFERENCES devices(id), interval_index INTEGER NOT NULL, issued INTEGER NOT NULL, signature TEXT NOT NULL, UNIQUE(binding_id,interval_index));
CREATE TABLE IF NOT EXISTS revocations(device_id TEXT PRIMARY KEY REFERENCES devices(id), revoked_at INTEGER NOT NULL, reason TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS seeds(id TEXT PRIMARY KEY, public_key TEXT NOT NULL UNIQUE, state TEXT NOT NULL DEFAULT 'pending', created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS recovery_codes(account_id TEXT NOT NULL REFERENCES accounts(id), code_hash TEXT NOT NULL UNIQUE, used_at INTEGER, PRIMARY KEY(account_id,code_hash));
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, created INTEGER NOT NULL, action TEXT NOT NULL, subject TEXT NOT NULL, detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS session_records(id TEXT PRIMARY KEY, account_id TEXT REFERENCES accounts(id), created INTEGER NOT NULL, expires INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS policies(key TEXT PRIMARY KEY, value TEXT NOT NULL);
PRAGMA user_version=1;
