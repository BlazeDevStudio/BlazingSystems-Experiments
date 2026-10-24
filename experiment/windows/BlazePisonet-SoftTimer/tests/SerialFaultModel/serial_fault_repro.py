#!/usr/bin/env python3
"""PHX-L-APPS #164 test-only fault model, derived from actual SerialHardware.cs.

NEVER routes paid credit or touches a device. Counterexamples, not proof of
observed hardware events or a native CLR test. Mirrors observed GetSignal,
IsSignalActive, OnPinChanged and debounce rules for the 2026-10-24 source.
"""
from dataclasses import dataclass
from typing import Optional

DEBOUNCE_MS = 80
MIN_PULSE_MS = 20
MAX_PULSE_MS = 1000

@dataclass
class EmulatedPinChanged:
    active_high: bool = True
    selected_signal: str = 'CTS'
    last_active: bool = False
    pulse_started_ms: Optional[int] = None
    last_accepted_ms: int = -1000000000
    accepted: int = 0

    def connect(self, healthy_raw: bool):
        self.last_active = healthy_raw if self.active_high else not healthy_raw

    def event(self, ms: int, event_type: str, raw_now: Optional[bool]):
        # In the source GetSignal returns false on a read exception or no port.
        if self.selected_signal == 'Ring' and event_type == 'Ring':
            self.accept(ms, max(MIN_PULSE_MS, 1))
            return
        raw = False if raw_now is None else raw_now
        active = raw if self.active_high else not raw
        if active == self.last_active:
            return
        self.last_active = active
        if active:
            self.pulse_started_ms = ms
        elif self.pulse_started_ms is not None:
            width = max(0, ms - self.pulse_started_ms)
            self.pulse_started_ms = None
            self.accept(ms, width)

    def accept(self, ms: int, width: int):
        if ms - self.last_accepted_ms < max(10, DEBOUNCE_MS):
            return
        if width < max(1, MIN_PULSE_MS):
            return
        if MAX_PULSE_MS > 0 and width > MAX_PULSE_MS:
            return
        self.last_accepted_ms = ms
        self.accepted += 1

def check(name: str, actual: int, expected: int) -> None:
    if actual != expected:
        raise AssertionError(f'{name}: expected {expected} accepted, got {actual}')
    print(f'REPRODUCED {name}: {actual} accepted pulse(s)')

def main() -> int:
    good = EmulatedPinChanged(active_high=True)
    good.connect(False)
    good.event(100, 'CtsChanged', True)
    good.event(160, 'CtsChanged', False)
    check('normal active-high 60ms input', good.accepted, 1)

    false_credit = EmulatedPinChanged(active_high=False)
    false_credit.connect(True)
    # No real coin. One read errors while idle, the next read succeeds.
    # The events need not be on the selected CTS line in current source.
    false_credit.event(100, 'DsrChanged', None)
    false_credit.event(210, 'DsrChanged', True)
    check('ACTIVE-LOW false coin after transient serial read failure', false_credit.accepted, 1)

    lost = EmulatedPinChanged(active_high=True)
    lost.connect(False)
    # Physical pin high from 100 to 150ms but callbacks run after release.
    lost.event(180, 'CtsChanged', False)
    lost.event(200, 'CtsChanged', False)
    check('completed 50ms real pulse lost to delayed callback', lost.accepted, 0)

    ring = EmulatedPinChanged(selected_signal='Ring')
    ring.connect(False)
    # An RI notification alone bypasses real pulse width measurement.
    ring.event(100, 'Ring', None)
    ring.event(300, 'Ring', None)
    check('two RI notifications accepted without measuring width', ring.accepted, 2)

    print('MODEL RESULT: 4/4 deterministic traces reproduced. NOT native CLR or physical-device acceptance.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
