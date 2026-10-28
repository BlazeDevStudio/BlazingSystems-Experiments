package main

/*
#cgo LDFLAGS: -lsqlite3
#include <sqlite3.h>
#include <stdlib.h>
static int bind_text(sqlite3_stmt *s, int n, const char *value, int len) { return sqlite3_bind_text(s,n,value,len,SQLITE_TRANSIENT); }
*/
import "C"

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"unsafe"
)

// DB wraps the system SQLite library (CGO_ENABLED=1, libsqlite3-dev on Linux).
// All transactions share one SQLite connection, serialized in-process.
type DB struct {
	p  *C.sqlite3
	mu sync.Mutex
}

func openDB(path string) (*DB, error) {
	if e := os.MkdirAll(filepath.Dir(path), 0700); e != nil {
		return nil, e
	}
	c := C.CString(path)
	defer C.free(unsafe.Pointer(c))
	var p *C.sqlite3
	if C.sqlite3_open_v2(c, &p, C.SQLITE_OPEN_READWRITE|C.SQLITE_OPEN_CREATE|C.SQLITE_OPEN_FULLMUTEX, nil) != C.SQLITE_OK {
		s := "sqlite open failed"
		if p != nil {
			s = C.GoString(C.sqlite3_errmsg(p))
			C.sqlite3_close(p)
		}
		return nil, errors.New(s)
	}
	d := &DB{p: p}
	for _, q := range []string{"PRAGMA journal_mode=WAL", "PRAGMA synchronous=FULL", "PRAGMA foreign_keys=ON", "PRAGMA busy_timeout=5000"} {
		if _, e := d.run(q); e != nil {
			d.close()
			return nil, e
		}
	}
	return d, nil
}
func (d *DB) close() {
	if d.p != nil {
		C.sqlite3_close(d.p)
		d.p = nil
	}
}
func (d *DB) run(q string, args ...any) ([]map[string]string, error) {
	d.mu.Lock()
	defer d.mu.Unlock()
	return d.query(q, args...)
}
func (d *DB) transaction(fn func() error) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	if _, e := d.query("BEGIN IMMEDIATE"); e != nil {
		return e
	}
	e := fn()
	if e != nil {
		d.query("ROLLBACK")
		return e
	}
	if _, e = d.query("COMMIT"); e != nil {
		d.query("ROLLBACK")
		return e
	}
	return nil
}

// query may be used under transaction lock; do NOT call run in a transaction.
func (d *DB) query(q string, args ...any) ([]map[string]string, error) {
	cq := C.CString(q)
	defer C.free(unsafe.Pointer(cq))
	var st *C.sqlite3_stmt
	if C.sqlite3_prepare_v2(d.p, cq, -1, &st, nil) != C.SQLITE_OK {
		return nil, fmt.Errorf("prepare: %s", C.GoString(C.sqlite3_errmsg(d.p)))
	}
	defer C.sqlite3_finalize(st)
	for i, v := range args {
		var rc C.int
		switch x := v.(type) {
		case string:
			c := C.CString(x)
			rc = C.bind_text(st, C.int(i+1), c, C.int(len(x)))
			C.free(unsafe.Pointer(c))
		case int:
			rc = C.sqlite3_bind_int64(st, C.int(i+1), C.sqlite3_int64(x))
		case int64:
			rc = C.sqlite3_bind_int64(st, C.int(i+1), C.sqlite3_int64(x))
		case nil:
			rc = C.sqlite3_bind_null(st, C.int(i+1))
		default:
			return nil, fmt.Errorf("unsupported sqlite bind %T", v)
		}
		if rc != C.SQLITE_OK {
			return nil, fmt.Errorf("bind error: %s", C.GoString(C.sqlite3_errmsg(d.p)))
		}
	}
	var out []map[string]string
	for {
		rc := C.sqlite3_step(st)
		if rc == C.SQLITE_DONE {
			return out, nil
		}
		if rc != C.SQLITE_ROW {
			return nil, fmt.Errorf("sqlite step: %s", C.GoString(C.sqlite3_errmsg(d.p)))
		}
		row := make(map[string]string)
		for i := C.int(0); i < C.sqlite3_column_count(st); i++ {
			name := C.GoString(C.sqlite3_column_name(st, i))
			if C.sqlite3_column_type(st, i) == C.SQLITE_NULL {
				row[name] = ""
			} else {
				row[name] = C.GoString((*C.char)(unsafe.Pointer(C.sqlite3_column_text(st, i))))
			}
		}
		out = append(out, row)
	}
}
func (d *DB) script(sql string) error {
	d.mu.Lock()
	defer d.mu.Unlock()
	c := C.CString(sql)
	defer C.free(unsafe.Pointer(c))
	var msg *C.char
	rc := C.sqlite3_exec(d.p, c, nil, nil, &msg)
	if rc != C.SQLITE_OK {
		v := C.GoString(msg)
		C.sqlite3_free(unsafe.Pointer(msg))
		return errors.New(v)
	}
	return nil
}
