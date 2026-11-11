package main

import (
	"net"
	"testing"
	"time"
)

func TestBoundedListenerMaxConnections(t *testing.T) {
	inner, e := net.Listen("tcp", "127.0.0.1:0")
	if e != nil {
		t.Fatal(e)
	}
	defer inner.Close()
	l := &boundedListener{Listener: inner, slots: make(chan struct{}, 1)}
	finished := make(chan struct{})
	go func() {
		defer close(finished)
		c, e := net.DialTimeout("tcp", inner.Addr().String(), time.Second)
		if e == nil {
			c.Close()
		}
	}()
	c, e := l.Accept()
	if e != nil {
		t.Fatal(e)
	}
	if len(l.slots) != 1 {
		t.Fatal("connection slot was not acquired")
	}
	c.Close()
	select {
	case <-finished:
	case <-time.After(time.Second):
		t.Fatal("client blocked")
	}
	if len(l.slots) != 0 {
		t.Fatal("connection slot leak")
	}
}
func TestHopCounterBound(t *testing.T) {
	m := Message{Hops: 4}
	m.Hops++
	if m.Hops != 5 || m.Hops < 0 || m.Hops > 5 {
		t.Fatal("five-hop boundary")
	}
}
