#!/usr/bin/env python3
import base64, http.server, json, os, socketserver, threading, time, urllib.parse, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1] / "openwrt" / "rootfs" / "www" / "blazepwifi"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "browser-v04-audit").resolve()
OUT.mkdir(parents=True, exist_ok=True)

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

os.chdir(str(ROOT))
server = socketserver.TCPServer(("127.0.0.1", 0), Quiet)
port = server.server_address[1]
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

mock_member_state={
    "revision":7,
    "members":[
        {"username":"alice","label":"Alice Existing","enabled":1,"banked_seconds":600,
         "revision":6,"updated":int(time.time()),"source":"admin:seed"}
    ],
    "preview_token":"browser-member-import-token"
}

def member_text_b64(value):
    return base64.b64encode(("v1:"+value).encode("utf-8")).decode("ascii")

def member_export_text():
    lines=["BLAZE_MEMBER_METADATA_V1",
           "exported_at\t"+str(int(time.time())),
           "global_revision\t"+str(mock_member_state["revision"])]
    for m in mock_member_state["members"]:
        lines.append("\t".join([
            "member",m["username"],str(int(bool(m["enabled"]))),str(m["banked_seconds"]),
            str(m["updated"]),member_text_b64(m.get("label","")),member_text_b64(m.get("source",""))
        ]))
    return "\n".join(lines)+"\n"

member_import_file=OUT/"browser-member-import.blazemembers"
member_import_file.write_text("\n".join([
    "BLAZE_MEMBER_METADATA_V1",
    "exported_at\t"+str(int(time.time())),
    "global_revision\t7",
    "\t".join(["member","alice","0","120",str(int(time.time())),member_text_b64("Imported Alice"),member_text_b64("legacy-local")]),
    "\t".join(["member","carol","1","900",str(int(time.time())),member_text_b64("Carol Imported"),member_text_b64("legacy-local")]),
])+"\n")

mock_console_state={
    "terminal_enabled":False,
    "terminal_open":False,
    "remote_runtime":{
        "activation_state":"staged","transport":"none","apply_supported":True,"public_key":"",
        "applied_at":0,"last_handshake":0,"last_error":"",
        "zerotier":{"active":0,"network_id":"","node_id":"","interface":"","address":"","status":"staged"}
    },
    "remote_config":{
        "mode":"disabled","monitoring":1,"management":0,"terminal":0,
        "node_name":"BlazePwifi","site_label":"","source_allowlist":"",
        "heartbeat_seconds":30,"offline_seconds":120,
        "wg_endpoint":"","wg_port":51820,"wg_address":"","wg_peer_public_key":"",
        "wg_allowed_ips":"","wg_keepalive":25,"wg_dns":"","wg_mtu":1420,
        "zt_network_id":""
    }
}

def mock_admin(action, params=None):
    params=params or {}
    if action == "status":
        return {"ok": True, "active_sessions": 3, "online_vendos": 1,
                "mem_available_kb": 131072, "load1": "0.11",
                "uptime_seconds": 7200, "must_change": 0}
    if action in ("rental_device_list", "rental_list"):
        return {"ok": True, "devices": [{
            "device_id": "0123456789abcdef01234567",
            "label": "Demo rental phone",
            "lease_until": int(time.time()) + 3600,
            "last_seen": int(time.time()),
            "policy_revision": 4,
            "launcher_mode": "rental",
            "allowed_packages": "com.android.camera,com.android.calculator2",
            "hidden_packages": "com.android.settings",
            "preferred_vendo": "vendo-01",
            "timer_user_toggle": 1,
            "notifications_enabled": 1,
            "admin_password_set": True,
            "inventory": "com.android.camera,com.android.calculator2,com.android.settings"
        }]}
    if action == "member_list":
        return {"ok":True,"revision":mock_member_state["revision"],"members":[dict(x) for x in mock_member_state["members"]]}
    if action == "member_events":
        return {"ok":True,"events":[]}
    if action == "member_export":
        payload=base64.b64encode(member_export_text().encode("utf-8")).decode("ascii")
        return {"ok":True,"format":"BLAZE_MEMBER_METADATA_V1",
                "filename":"BlazePwifi-members-browser-audit.blazemembers",
                "revision":mock_member_state["revision"],"payload_b64":payload}
    if action == "member_import_preview":
        return {"ok":True,"preview_token":mock_member_state["preview_token"],"count":2,
                "creates":1,"collisions":1,"requested_enabled":1,"export_revision":7,
                "expires":int(time.time())+600,"items":[
                    {"username":"alice","label":"Imported Alice","requested_enabled":0,
                     "banked_seconds":120,"updated":int(time.time()),"source":"legacy-local","status":"collision"},
                    {"username":"carol","label":"Carol Imported","requested_enabled":1,
                     "banked_seconds":900,"updated":int(time.time()),"source":"legacy-local","status":"create"}
                ]}
    if action == "member_import_apply":
        if params.get("preview_token",[""])[0] != mock_member_state["preview_token"]:
            return {"ok":False,"error":"invalid preview token"}
        policy=params.get("collision_policy",["abort"])[0]
        if policy=="abort":
            return {"ok":False,"error":"member import has username collisions; choose skip or metadata-only update"}
        if policy=="update":
            mock_member_state["members"][0].update({"label":"Imported Alice","enabled":0,"banked_seconds":120,
                                                    "revision":8,"updated":int(time.time()),"source":"import:admin"})
            updated=1
        else:
            updated=0
        if not any(x["username"]=="carol" for x in mock_member_state["members"]):
            mock_member_state["members"].append(
                {"username":"carol","label":"Carol Imported","enabled":0,"banked_seconds":900,
                 "revision":9,"updated":int(time.time()),"source":"import:admin"})
        mock_member_state["revision"]=9
        return {"ok":True,"created":1,"updated":updated,"skipped":1 if policy=="skip" else 0,
                "revision":mock_member_state["revision"],"new_members_require_password_reset":True}
    if action in ("member_create","member_update","member_balance","member_transfer","member_password","member_delete"):
        return {"ok":True,"revision":mock_member_state["revision"]}
    if action == "controller_list":
        return {"ok": True, "controllers": [{
            "id": "vendo-01", "last_seen": int(time.time()), "ip": "192.168.1.50",
            "coin_pin": 4, "relay_pin": 5, "coin_debounce_ms": 40, "pulse_group_ms": 400
        }]}
    if action == "config_get":
        return {"ok": True, "value": "600"}
    if action == "config_set":
        return {"ok": True}
    if action == "remote_status":
        cfg=mock_console_state["remote_config"]
        return {"ok":True,"recommended":"wireguard","remote":{
            "mode":cfg["mode"],"ready":cfg["mode"]!="disabled",
            "monitoring":cfg["monitoring"],"management":cfg["management"],"terminal":cfg["terminal"],
            "node_name":cfg["node_name"],"site_label":cfg["site_label"],
            "wireguard":"installed","zerotier":"unavailable",
            "runtime":dict(mock_console_state["remote_runtime"])
        }}
    if action == "remote_config_get":
        return {"ok":True,"config":dict(mock_console_state["remote_config"])}
    if action == "remote_config_set":
        cfg=mock_console_state["remote_config"]
        for key in list(cfg):
            if key in params:
                raw=params[key][0]
                if key in ("monitoring","management","terminal","heartbeat_seconds","offline_seconds",
                           "wg_port","wg_keepalive","wg_mtu"):
                    try: cfg[key]=int(raw)
                    except Exception: cfg[key]=raw
                else:
                    cfg[key]=raw
        rt=mock_console_state["remote_runtime"]
        if rt["activation_state"]=="active":
            rt["activation_state"]="active_staged_changes"
        return {"ok":True,"remote":{
            "mode":cfg["mode"],"ready":cfg["mode"]!="disabled",
            "monitoring":cfg["monitoring"],"management":cfg["management"],"terminal":cfg["terminal"],
            "node_name":cfg["node_name"],"site_label":cfg["site_label"],
            "wireguard":"installed","zerotier":"unavailable","runtime":dict(rt)
        }}
    if action == "remote_wireguard_key":
        rt=mock_console_state["remote_runtime"]
        rt["public_key"]="CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC="
        return {"ok":True,"public_key":rt["public_key"]}
    if action == "remote_wireguard_apply":
        rt=mock_console_state["remote_runtime"]
        rt.update({"activation_state":"active","transport":"wireguard","apply_supported":True,
                   "public_key":rt["public_key"] or "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC=",
                   "applied_at":int(time.time()),"last_handshake":int(time.time()),"last_error":""})
        cfg=mock_console_state["remote_config"]
        return {"ok":True,"remote":{
            "mode":cfg["mode"],"ready":True,"monitoring":cfg["monitoring"],
            "management":cfg["management"],"terminal":cfg["terminal"],
            "node_name":cfg["node_name"],"site_label":cfg["site_label"],
            "wireguard":"online:blazewg:last_handshake_age=0","zerotier":"unavailable","runtime":dict(rt)
        }}
    if action == "remote_wireguard_disable":
        rt=mock_console_state["remote_runtime"]
        rt.update({"activation_state":"staged","transport":"none","applied_at":int(time.time()),"last_handshake":0,"last_error":""})
        cfg=mock_console_state["remote_config"]
        return {"ok":True,"remote":{
            "mode":cfg["mode"],"ready":True,"monitoring":cfg["monitoring"],
            "management":cfg["management"],"terminal":cfg["terminal"],
            "node_name":cfg["node_name"],"site_label":cfg["site_label"],
            "wireguard":"installed","zerotier":"unavailable","runtime":dict(rt)
        }}
    if action == "remote_zerotier_identity":
        rt=mock_console_state["remote_runtime"]
        zt=rt["zerotier"]
        zt.update({"node_id":"abcdef1234","status":"staged"})
        cfg=mock_console_state["remote_config"]
        return {"ok":True,"node_id":"abcdef1234","remote":{
            "mode":cfg["mode"],"ready":True,"monitoring":cfg["monitoring"],
            "management":cfg["management"],"terminal":cfg["terminal"],
            "node_name":cfg["node_name"],"site_label":cfg["site_label"],
            "wireguard":"installed","zerotier":"200 info abcdef1234 1.14.2 ONLINE","runtime":dict(rt)
        }}
    if action == "remote_zerotier_apply":
        rt=mock_console_state["remote_runtime"]
        cfg=mock_console_state["remote_config"]
        zt=rt["zerotier"]
        zt.update({"active":1,"network_id":cfg["zt_network_id"],"node_id":"abcdef1234",
                   "interface":"ztblaze123","address":"10.77.0.2/24","status":"OK"})
        rt.update({"activation_state":"active","transport":"zerotier","apply_supported":True,
                   "applied_at":int(time.time()),"last_handshake":0,"last_error":""})
        return {"ok":True,"remote":{
            "mode":cfg["mode"],"ready":True,"monitoring":cfg["monitoring"],
            "management":cfg["management"],"terminal":cfg["terminal"],
            "node_name":cfg["node_name"],"site_label":cfg["site_label"],
            "wireguard":"installed","zerotier":"200 info abcdef1234 1.14.2 ONLINE","runtime":dict(rt)
        }}
    if action == "remote_zerotier_disable":
        rt=mock_console_state["remote_runtime"]
        zt=rt["zerotier"]
        zt.update({"active":0,"interface":"","address":"","status":"staged"})
        rt.update({"activation_state":"staged","transport":"none","apply_supported":True,
                   "applied_at":int(time.time()),"last_handshake":0,"last_error":""})
        cfg=mock_console_state["remote_config"]
        return {"ok":True,"remote":{
            "mode":cfg["mode"],"ready":True,"monitoring":cfg["monitoring"],
            "management":cfg["management"],"terminal":cfg["terminal"],
            "node_name":cfg["node_name"],"site_label":cfg["site_label"],
            "wireguard":"installed","zerotier":"200 info abcdef1234 1.14.2 ONLINE","runtime":dict(rt)
        }}
    if action == "terminal_status":
        return {"ok":True,"enabled":mock_console_state["terminal_enabled"],
                "active_sessions":1 if mock_console_state["terminal_open"] else 0,
                "ttl_seconds":300,"idle_seconds":60,"command_timeout_seconds":12,
                "output_max_bytes":16000}
    if action == "terminal_set_enabled":
        enabled=params.get("enabled",["0"])[0]=="1"
        mock_console_state["terminal_enabled"]=enabled
        if not enabled: mock_console_state["terminal_open"]=False
        return {"ok":True,"enabled":enabled}
    if action == "terminal_open":
        if not mock_console_state["terminal_enabled"]:
            return {"ok":False,"error":"Advanced Terminal is disabled"}
        mock_console_state["terminal_open"]=True
        return {"ok":True,"terminal_token":"audit-terminal-token","ttl_seconds":300,"idle_seconds":60}
    if action == "terminal_exec":
        if not mock_console_state["terminal_open"] or params.get("terminal_token",[""])[0]!="audit-terminal-token":
            return {"ok":False,"error":"terminal session expired or invalid"}
        return {"ok":True,"exit_code":0,"output":"console-ok"}
    if action == "terminal_close":
        mock_console_state["terminal_open"]=False
        return {"ok":True}
    if action == "tool_run":
        return {"ok":True,"tool":params.get("tool",["ping"])[0],"exit_code":0,"output":"safe-tool-ok"}
    if action in ("rental_device_qr", "rental_binding_qr"):
        return {"ok": True, "qr_type": "binding",
                "enrollment_token": "0123456789abcdef.abcdef0123456789",
                "expires_seconds": 600,
                "server_url": "https://192.168.1.1:8443", "device_name": "Rental phone",
                "qr_payload": json.dumps({
                    "server_url":"https://192.168.1.1:8443",
                    "enrollment_token":"0123456789abcdef.abcdef0123456789",
                    "device_name":"Rental phone"
                })}
    if action == "rental_provisioning_qr":
        payload = {
            "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME":
                "com.blazesystems.blazerental/.BlazeDeviceAdminReceiver",
            "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION":
                "https://updates.example.test/BlazeRental.apk",
            "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM":
                "0K0gvtAOowTbm_9FkoVC_tV0Bw1BbtZbT789i6I9cQI",
            "android.app.extra.PROVISIONING_DEVICE_ADMIN_MINIMUM_VERSION_CODE": 50200,
            "android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE": {
                "server_url": "https://192.168.1.1:8443",
                "enrollment_token": "fedcba9876543210.0123456789abcdef",
                "device_name": "Rental phone"
            }
        }
        return {"ok": True, "qr_type": "device_owner",
                "enrollment_token": "fedcba9876543210.0123456789abcdef",
                "expires_seconds": 600,
                "server_url": "https://192.168.1.1:8443", "device_name": "Rental phone",
                "apk_version": "0.5.2", "apk_version_code": 50200,
                "apk_url": "https://updates.example.test/BlazeRental.apk",
                "apk_checksum": "0K0gvtAOowTbm_9FkoVC_tV0Bw1BbtZbT789i6I9cQI",
                "qr_payload": json.dumps(payload)}
    if action == "voucher_create":
        return {"ok": True, "code": "BLAZE-DEMO", "cents": 100}
    if action in ("rental_policy_set","rental_lease_add","rental_lease_expire",
                  "rental_device_rename","rental_device_revoke"):
        return {"ok": True, "policy_revision": 5}
    return {"ok": True}

errors=[]
admin_mutations=[]
portal_state={"coin_expires":0, "coin_vendo":"", "credit":0, "remaining":65}

def mock_portal(action):
    now=int(time.time())
    if action == "portal_config":
        return {"ok":True,"portal":{}}
    if action == "rates":
        return {"ok":True,"rates":[{"cents":100,"label":"10 minutes"}]}
    if action == "vendos":
        return {"ok":True,"vendos":[{"id":"vendo-01"}]}
    if action == "me":
        return {"ok":True,"device":"demo","mac":"02:11:22:33:44:55","ip":"192.168.13.25",
                "credit_cents":portal_state["credit"],"remaining_seconds":portal_state["remaining"],
                "paused":0,"time_synchronized":True,"server_time":now,
                "coin_expires":portal_state["coin_expires"],"coin_vendo":portal_state["coin_vendo"],
                "hotspot_vlan":13,"speed_limit_kbps":10000,"mem_available_kb":98304,
                "load1":"0.18","uptime_seconds":187200}
    if action == "coin_start":
        portal_state["coin_expires"]=now+120
        portal_state["coin_vendo"]="vendo-01"
        return {"ok":True,"vendo":"vendo-01","target_nonce":"audit-nonce",
                "server_time":now,"expires":now+120}
    if action == "coin_stop":
        portal_state["coin_expires"]=0
        portal_state["coin_vendo"]=""
        return {"ok":True,"server_time":now}
    if action in ("pause","resume","disconnect","redeem","connect"):
        return {"ok":True}
    return {"ok":True}

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={"width": 1440, "height": 1000})
    page.on("console", lambda msg: errors.append("console:"+msg.text) if msg.type=="error" else None)
    page.on("pageerror", lambda exc: errors.append("pageerror:"+str(exc)))

    def route_handler(route):
        req=route.request
        url=req.url
        if url.endswith("/cgi-bin/admin-session"):
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"ok":True,"username":"admin","role":"admin",
                                           "csrf":"browser-audit-csrf","must_change":0}))
            return
        if url.endswith("/cgi-bin/admin"):
            body=req.post_data or ""
            params=urllib.parse.parse_qs(body, keep_blank_values=True)
            action=params.get("action",[""])[0]
            if action:
                admin_mutations.append({
                    "action": action,
                    "csrf_body": params.get("csrf",[""])[0],
                    "csrf_header": req.headers.get("x-blaze-csrf","")
                })
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps(mock_admin(action, params)))
            return
        if url.endswith("/cgi-bin/api"):
            body=req.post_data or ""
            params=urllib.parse.parse_qs(body, keep_blank_values=True)
            action=params.get("action",[""])[0]
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps(mock_portal(action)))
            return
        route.continue_()

    page.route("**/*", route_handler)
    page.goto(f"http://127.0.0.1:{port}/admin.html", wait_until="networkidle")
    page.wait_for_selector("#appView:not(.hidden)")
    assert page.locator("#page-dashboard").is_visible()
    assert "BlazePwifi" in page.locator("body").inner_text()

    page.click('[data-page="rentals"]')
    page.wait_for_selector("#page-rentals.active")
    page.wait_for_selector('[data-device="0123456789abcdef01234567"]')
    assert "Demo rental phone" in page.locator("#rentalCards").inner_text()

    page.click('button:has-text("+ Add device")')
    page.wait_for_selector("#addRentalModal:not(.hidden)")

    page.click('button:has-text("Bind existing BlazeRental")')
    page.wait_for_selector("#qrResult:not(.hidden)")
    page.wait_for_selector("#qrBox svg")
    assert "Standard binding" in page.locator("#qrNotice").inner_text()
    assert "0123456789abcdef" in page.locator("#qrToken").inner_text()

    page.click('button:has-text("Provision factory-reset phone")')
    page.wait_for_function(
        "document.getElementById('qrNotice').textContent.includes('Device Owner provisioning')")
    page.wait_for_function(
        "document.getElementById('qrMeta').textContent.includes('APK 0.5.2 (50200)')")
    page.wait_for_function(
        "document.getElementById('qrToken').textContent.includes('fedcba9876543210')")
    page.wait_for_selector("#qrBox svg")
    assert "Device Owner provisioning" in page.locator("#qrNotice").inner_text()
    assert "APK 0.5.2 (50200)" in page.locator("#qrMeta").inner_text()
    assert "fedcba9876543210" in page.locator("#qrToken").inner_text()
    page.click('#addRentalModal button:has-text("✕")')

    assert admin_mutations
    assert all(x["csrf_body"] == "browser-audit-csrf" for x in admin_mutations)
    assert all(x["csrf_header"] == "browser-audit-csrf" for x in admin_mutations)

    page.click('[data-page="controllers"]')
    page.wait_for_selector("#page-controllers.active")
    page.wait_for_selector("text=vendo-01")

    page.click('[data-page="system"]')
    page.wait_for_selector("#page-system.active")
    system_text = page.locator("#page-system").inner_text()
    assert ("TailAdmin" in system_text
            or ("System & Security" in system_text and "Security posture" in system_text))

    # dev.3 Remote Access control plane: authenticated staging plus guarded WireGuard activation.
    page.click('[data-page="remote"]')
    page.wait_for_selector("#page-remote.active")
    page.wait_for_function("document.getElementById('remoteConfigState').textContent.includes('disabled/staged')")
    page.select_option("#remoteMode","wireguard")
    page.fill("#remoteNodeName","AuditNode")
    page.fill("#remoteSiteLabel","Audit Site")
    page.fill("#wgEndpoint","vpn.example.test")
    page.fill("#wgAddress","10.20.0.2/32")
    page.fill("#wgPeerKey","AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    page.fill("#wgAllowedIps","10.20.0.0/24")
    page.fill("#remoteAllowlist","10.20.0.0/24")
    page.check("#remoteManagement")
    page.fill("#remotePassword","browser-password")
    page.click('button:has-text("Validate & save profile")')
    for _ in range(50):
        page.wait_for_timeout(100)
        if any(x["action"]=="remote_config_set" for x in admin_mutations):
            break
    assert any(x["action"]=="remote_config_set" for x in admin_mutations), admin_mutations
    assert mock_console_state["remote_config"]["mode"]=="wireguard", mock_console_state["remote_config"]
    page.wait_for_function("document.getElementById('remoteModeState').textContent === 'wireguard'")

    # dev.3 live WireGuard: explicit key generation, transactional apply, staged edits, safe disable.
    page.fill("#remotePassword","browser-password")
    page.click('button:has-text("Generate / show key")')
    page.wait_for_function("document.getElementById('wgLocalPublicKey').value.includes('CCCCCCCC')")
    page.fill("#remotePassword","browser-password")
    page.once("dialog", lambda dialog: dialog.accept())
    page.click('button:has-text("Test & Apply WireGuard")')
    page.wait_for_function("document.getElementById('wgActivationState').textContent === 'active'")
    assert "Handshake" in page.locator("#wgHandshakeState").inner_text()

    page.fill("#remoteSiteLabel","Audit Site staged edit")
    page.fill("#remotePassword","browser-password")
    page.click('button:has-text("Validate & save profile")')
    page.wait_for_function("document.getElementById('wgActivationState').textContent === 'active_staged_changes'")
    assert "staged changes" in page.locator("#remoteReadyState").inner_text().lower()

    page.fill("#remotePassword","browser-password")
    page.once("dialog", lambda dialog: dialog.accept())
    page.click('button:has-text("Disable live WireGuard")')
    page.wait_for_function("document.getElementById('wgActivationState').textContent === 'staged'")

    # dev.5 live ZeroTier: stable identity -> authorization-ready node -> transactional apply -> safe disable.
    page.select_option("#remoteMode","zerotier")
    page.fill("#remoteAllowlist","10.77.0.0/24")
    page.fill("#ztNetworkId","0123456789abcdef")
    page.fill("#remotePassword","browser-password")
    page.click('button:has-text("Validate & save profile")')
    page.wait_for_function("document.getElementById('remoteModeState').textContent === 'zerotier'")

    page.fill("#remotePassword","browser-password")
    page.click('button:has-text("Prepare / show node ID")')
    page.wait_for_function("document.getElementById('ztNodeId').value === 'abcdef1234'")
    assert "authorize this node" in page.locator("#ztLiveState").inner_text().lower()

    page.fill("#remotePassword","browser-password")
    page.once("dialog", lambda dialog: dialog.accept())
    page.click('button:has-text("Test & Apply ZeroTier")')
    page.wait_for_function("document.getElementById('wgActivationState').textContent === 'active'")
    page.wait_for_function("document.getElementById('ztLiveState').textContent.includes('10.77.0.2/24')")
    assert "Live ZeroTier active" in page.locator("#remoteReadyState").inner_text()
    assert "OK" in page.locator("#ztLiveState").inner_text()

    page.fill("#remotePassword","browser-password")
    page.once("dialog", lambda dialog: dialog.accept())
    page.click('button:has-text("Disable live ZeroTier")')
    page.wait_for_function("document.getElementById('wgActivationState').textContent === 'staged'")
    assert "Identity ready" in page.locator("#ztLiveState").inner_text()

    # dev.2 Advanced Terminal: enable -> fresh re-auth -> in-memory session -> bounded command -> close.
    page.click('[data-page="tools"]')
    page.wait_for_selector("#page-tools.active")
    page.wait_for_function("document.getElementById('terminalState').textContent.includes('Disabled')")
    page.fill("#terminalPassword","browser-password")
    page.once("dialog", lambda dialog: dialog.accept())
    page.click('button:has-text("Enable")')
    page.wait_for_function("document.getElementById('terminalState').textContent.includes('Enabled')")
    page.fill("#terminalPassword","browser-password")
    page.click('button:has-text("Open session")')
    page.wait_for_function("document.getElementById('terminalOutput').textContent.includes('session opened')")
    page.fill("#terminalCommand","printf console-ok")
    page.click('button:has-text("Run bounded command")')
    page.wait_for_function("document.getElementById('terminalOutput').textContent.includes('console-ok')")
    page.click('button:has-text("Close session")')
    page.wait_for_function("document.getElementById('terminalOutput').textContent.includes('closed')")

    sensitive_actions={"remote_config_set","remote_wireguard_key","remote_wireguard_apply","remote_wireguard_disable",
                       "remote_zerotier_identity","remote_zerotier_apply","remote_zerotier_disable",
                       "terminal_set_enabled","terminal_open","terminal_exec","terminal_close"}
    sensitive=[x for x in admin_mutations if x["action"] in sensitive_actions]
    assert sensitive_actions.issubset({x["action"] for x in sensitive})
    assert all(x["csrf_body"]=="browser-audit-csrf" and x["csrf_header"]=="browser-audit-csrf" for x in sensitive)

    # dev.4 centralized-member metadata migration: verifier-free export -> reviewed preview -> re-authenticated apply.
    page.click('[data-page="members"]')
    page.wait_for_selector("#page-members.active")
    page.wait_for_selector('[data-member="alice"]')
    with page.expect_download() as download_info:
        page.click('button:has-text("Export metadata")')
    export_download=download_info.value
    export_path=OUT/"browser-member-export.blazemembers"
    export_download.save_as(str(export_path))
    export_text=export_path.read_text()
    assert export_text.startswith("BLAZE_MEMBER_METADATA_V1\n")
    assert "sha256i" not in export_text
    assert "password" not in export_text.lower()
    assert "hash" not in export_text.lower()

    page.set_input_files("#memberImportFile",str(member_import_file))
    page.click('button:has-text("Preview import")')
    page.wait_for_function("document.getElementById('memberImportSummary').textContent.includes('1 new')")
    assert "1 collisions" in page.locator("#memberImportSummary").inner_text()
    preview_text=page.locator("#memberImportPreview").inner_text()
    assert "COLLISION  alice" in preview_text
    assert "CREATE  carol" in preview_text
    page.select_option("#memberImportPolicy","skip")
    page.fill("#memberImportPassword","browser-password")
    page.once("dialog", lambda dialog: dialog.accept())
    page.click('button:has-text("Apply reviewed import")')
    page.wait_for_function("document.getElementById('memberImportSummary').textContent.includes('Import applied')")
    page.wait_for_selector('[data-member="carol"]')
    assert "Carol Imported" in page.locator('[data-member="carol"]').inner_text()
    assert "DISABLED" in page.locator('[data-member="carol"]').inner_text()

    member_sensitive={"member_import_preview","member_import_apply"}
    member_calls=[x for x in admin_mutations if x["action"] in member_sensitive]
    assert member_sensitive.issubset({x["action"] for x in member_calls})
    assert all(x["csrf_body"]=="browser-audit-csrf" and x["csrf_header"]=="browser-audit-csrf" for x in member_calls)

    # v0.5 moved voucher creation into its dedicated console module.
    page.click('[data-page="vouchers"]')
    page.wait_for_selector("#page-vouchers.active")
    page.click("#voucherBtn")
    page.wait_for_selector("text=BLAZE-DEMO")

    page.screenshot(path=str(OUT/"admin-dashboard.png"), full_page=True)

    # Captive portal: session countdown and coin reservation must be visibly live.
    page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="networkidle")
    page.wait_for_function("document.getElementById('time').textContent !== '—'")
    first_time=page.locator("#time").inner_text()
    page.wait_for_function(
        "(start) => document.getElementById('time').textContent !== start",
        arg=first_time, timeout=3500)
    second_time=page.locator("#time").inner_text()
    assert first_time != second_time, (first_time, second_time)

    page.click('button:has-text("Open coin slot")')
    page.wait_for_selector("#coinWindow:not(.hide)")
    countdown=page.locator("#coinCountdown").inner_text()
    assert countdown not in ("00:00",""), countdown
    assert "Ready on vendo-01" in page.locator("#coinmsg").inner_text()

    portal_state["credit"]=100
    page.evaluate("refresh()")
    page.wait_for_function("document.getElementById('coinValue').textContent.includes('₱1.00 inserted')")
    assert "vendo-01" in page.locator("#coinValue").inner_text()

    page.click('button:has-text("Done inserting coins")')
    page.wait_for_function("document.getElementById('coinWindow').classList.contains('hide')")
    assert "Coin window closed" in page.locator("#coinmsg").inner_text()
    page.screenshot(path=str(OUT/"portal-coin-window.png"), full_page=True)

    browser.close()

server.shutdown()
if errors:
    (OUT/"browser-errors.txt").write_text("\n".join(errors))
    raise SystemExit("browser console/page errors: "+repr(errors))

result={
    "target":"browser-admin",
    "release":"post-v0.5.2",
    "validation_level":"headless-browser-with-mocked-cgi",
    "checks":{
        "dashboard_loaded":True,
        "rental_navigation":True,
        "device_policy_editor_rendered":True,
        "binding_qr_generated":True,
        "device_owner_qr_generated":True,
        "dual_csrf_transport":True,
        "portal_session_countdown_live":True,
        "portal_coin_window_countdown_live":True,
        "portal_coin_credit_visible":True,
        "controller_page_rendered":True,
        "system_page_rendered":True,
        "voucher_action_rendered":True,
        "remote_profile_saved":True,
        "wireguard_live_apply":True,
        "wireguard_staged_edit":True,
        "wireguard_safe_disable":True,
        "zerotier_identity_prepared":True,
        "zerotier_live_apply":True,
        "zerotier_safe_disable":True,
        "advanced_terminal_session":True,
        "member_metadata_export":True,
        "member_import_preview":True,
        "member_import_apply":True,
        "console_errors":False
    }
}
(OUT/"audit.json").write_text(json.dumps(result,indent=2))
print("BlazePwifi post-v0.5.2 browser audit passed")
