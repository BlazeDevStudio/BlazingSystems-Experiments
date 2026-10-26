# BlazeNetMonitor — Evidence-driven dot status design

Updated: 2026-10-26 | version 0.2.4 preview | developer: Blaze Systems

## Principles
The two status dots are independently measured for their specific user-configured endpoint. Neither is the total throughput indicator, and a successful probe of one provider does not prove other services are reachable. Do not infer browsing/streaming quality solely from an ICMP response or an idle link.

## Candidate thresholds implemented in QualityTracker
- Probe cadence: user-selected 3–120 s; default 5 s, bounded timeout ~3 s.
- Records: max 24 latest per-target persisted observations, last 12 for latency trend and last 6 for loss/jitter. Missing gaps exceeding max(15 s, 3×cadence) reset continuity.
- RED: 2 consecutive probe failures.
- ORANGE: latest probe fails, recent loss >=25% (4 or more records), average or latest latency >=350 ms, jitter >=110 ms over at least four successes, or latest latency > max(250 ms, learned baseline × 5).
- YELLOW: recent loss >=8% (4 or more records), average/latest RTT >=180 ms, recent jitter >=60 ms (4+ successful probes), or RTT > max(140 ms, baseline × 3).
- GREEN: none of the above, and at least 3 healthy results before returning to green after a non-green state.
- BLUE: persistent GREEN without interruption for >=24h crossing a local calendar day. Any red/orange/yellow or missed-probe gap revokes this until re-earned.
- Unknown (grey): before a completed probe.
- Baseline: slow exponentially weighted healthy RTT (97% prior, 3% current), updating only on successful clean low-jitter probes, avoiding one spike overwriting normal.
- Results are intentionally labeled estimates. VPNs, firewalls, packet shaping, IP changes and ICMP restrictions can affect data. HTTP 4xx may indicate reachability rather than site usability. Never claim measured streaming capacity.

## Suggested future research
- Rolling 5/15-minute EWMA measurements and provider-specific normalized thresholds after at least 10–20 probes.
- Configurable “strict”, “balanced” and “lenient” quality modes, with explicit hysteresis.
- Quantile (p95) latency trends, probe protocol fallback only with user consent, local clock changes and network-switch invalidation.
- Multi-target aggregate badge (different from per-endpoint dot) to avoid treating one server as the whole Internet.
- Small synthetic HTTPS page load / optional download test to distinguish browsing latency from measurable bandwidth. This should be opt-in and rate-limited, never inferred without testing.
- 24h physical soak validation through sleep/wake and network changes. Automated tests only establish deterministic decision rules, not field validity.
