package main

import (
	"net"
	"sync"
)

// Acquires a slot before accept, so excessive new clients remain in the OS backlog
// rather than allocating an unbounded number of application connections.
type boundedListener struct {
	net.Listener
	slots chan struct{}
}
type limitedConn struct {
	net.Conn
	once    sync.Once
	release func()
}

func (l *boundedListener) Accept() (net.Conn, error) {
	l.slots <- struct{}{}
	c, e := l.Listener.Accept()
	if e != nil {
		<-l.slots
		return nil, e
	}
	return &limitedConn{Conn: c, release: func() { <-l.slots }}, nil
}
func (c *limitedConn) Close() error { e := c.Conn.Close(); c.once.Do(c.release); return e }
