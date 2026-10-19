"""BlazeHackintosh native research workbench (experimental, no installer actions).

Standard-library Tkinter GUI for existing read-only scanner and research evaluator.
No disk/ESP modification, OpenCore installation, network fetch or EFI generation.
Only a user-selected NEW JSON file may be written via Export.
"""
from __future__ import annotations

import json
import os
import queue
import re
import threading
import unicodedata
import ipaddress
from pathlib import Path
from typing import Callable

MAX_JSON_BYTES = 2 * 1024 * 1024
NOTICE = (
    "RESEARCH ONLY — not a bootability verdict, macOS installer, EFI generator, "
    "disk writer, or physical hardware acceptance."
)


# A read-only flag is not a privacy guarantee. Only these scanner fields are
# permitted in the GUI and explicitly exported research report. This prevents
# unexpected upstream keys (serial, UUID, MAC, IP, hostname, raw PnP IDs, etc.)
# from being silently persisted. Free-form device names still require care.
_ALLOWED_HARDWARE = {
    "cpu": ("name", "vendor", "physical_cores"),
    "motherboard": ("manufacturer", "model"),
}
_ALLOWED_DEVICES = {
    "gpus": ("name", "pci_id"),
    "network_adapters": ("name", "pci_id"),
    "storage": ("model", "bytes", "interface"),
}
_ALLOWED_EVALUATION = (
    "tool_version", "cpu_name", "cpu_family", "classification", "reason",
    "can_generate_efi", "boot_verified", "missing_inventory_evidence",
    "checks_required", "next_action",
)


# Device labels are untrusted and can carry identifiers even inside allowed keys.
# This is a conservative best-effort privacy filter, NOT proof of anonymity.
_MAC = re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])")
_UUID = re.compile(r"(?i)\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b")
_IPV4 = re.compile(r"(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])")
_PRIVATE_LABEL = re.compile(r"(?i)\b(?:serial(?:\s+(?:number|no))?|host\s*name|hostname|"
                            r"mac\s*address|user\s*name|username)\s*[:=]\s*\S+")
_HOST_TOKEN = re.compile(r"(?i)\b(?:DESKTOP|LAPTOP)-[A-Z0-9-]{4,}\b")
_USER_PATH = re.compile(r"(?i)(?:[A-Z]:[\\/]Users[\\/]|/home/)[^\s\\/]+")


def _safe_text(value: str) -> str:
    value = value[:240]
    if any(unicodedata.category(char) in ("Cc", "Cf") for char in value):
        return "[redacted: control characters]"
    if _MAC.search(value) or _UUID.search(value) or _PRIVATE_LABEL.search(value) or \
            _HOST_TOKEN.search(value) or _USER_PATH.search(value):
        return "[redacted: sensitive identifier]"
    for match in _IPV4.finditer(value):
        try:
            ipaddress.IPv4Address(match.group(0))
        except ipaddress.AddressValueError:
            continue
        return "[redacted: sensitive identifier]"
    return value


def _scalar(value: object) -> str | int | None:
    if value is None:
        return None
    if isinstance(value, str):
        return _safe_text(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return value if 0 <= value < 2**70 else None
    return None


def privacy_project(report: dict) -> dict:
    """Explicitly project safe scanner schema; never copy arbitrary keys."""
    h = report.get("hardware")
    if not isinstance(h, dict):
        raise ValueError("Hardware inventory is missing")
    safe: dict = {}
    for section, keys in _ALLOWED_HARDWARE.items():
        original = h.get(section)
        if original is not None and not isinstance(original, dict):
            raise ValueError("Malformed hardware section: " + section)
        original = original or {}
        safe[section] = {key: _scalar(original.get(key)) for key in keys}
    for section, keys in _ALLOWED_DEVICES.items():
        original = h.get(section)
        if original is not None and not isinstance(original, list):
            raise ValueError("Malformed hardware device list: " + section)
        if len(original or []) > 256:
            raise ValueError("Hardware device list exceeds safety limit")
        devices = []
        for entry in original or []:
            if not isinstance(entry, dict):
                raise ValueError("Malformed hardware device entry")
            devices.append({key: _scalar(entry.get(key)) for key in keys})
        safe[section] = devices
    safe["firmware"] = _scalar(h.get("firmware"))
    safe["memory_bytes"] = _scalar(h.get("memory_bytes"))
    host = report.get("host_os")
    return {
        "format_version": 2,
        "host_os": host if host in ("Windows", "Linux", "Darwin") else "Unknown",
        "hardware": safe,
        "read_only": True,
        "privacy": "Explicit hardware allowlist; unexpected fields omitted",
    }


def evaluation_project(result: dict) -> dict:
    """Retain only recognized evaluator fields, not arbitrary metadata."""
    projected = {}
    for key in _ALLOWED_EVALUATION:
        value = result.get(key)
        if isinstance(value, list):
            if len(value) > 100 or any(not isinstance(x, str) for x in value):
                raise ValueError("Malformed research evaluation list")
            projected[key] = [_safe_text(x) for x in value]
        elif isinstance(value, bool):
            projected[key] = value
        else:
            projected[key] = _scalar(value)
    return projected


def make_snapshot(scan: Callable[[], dict], load_catalog: Callable[[], dict],
                  evaluate: Callable[[dict, dict], dict]) -> dict:
    """Build an in-memory report; reject any upstream claim of boot readiness."""
    report = scan()
    if not isinstance(report, dict) or report.get("read_only") is not True:
        raise ValueError("Scanner did not provide a valid read-only inventory")
    if not isinstance(report.get("hardware"), dict):
        raise ValueError("Hardware inventory is missing")
    safe_report = privacy_project(report)
    catalog = load_catalog()
    result = evaluate(safe_report, catalog)
    if not isinstance(result, dict):
        raise ValueError("Research evaluation was malformed")
    if result.get("boot_verified") is not False or result.get("can_generate_efi") is not False:
        raise ValueError("Unsafe boot or EFI capability assertion")
    if result.get("classification") not in ("Unknown", "Research Only"):
        raise ValueError("Unsupported compatibility classification")
    result = evaluation_project(result)
    snapshot = {
        "schema_version": 1,
        "status": "Research Only",
        "notice": NOTICE,
        "read_only": True,
        "boot_verified": False,
        "can_generate_efi": False,
        "scan": safe_report,
        "evaluation": result,
    }
    encoded = json.dumps(snapshot, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_JSON_BYTES:
        raise ValueError("Research report exceeds the 2 MiB export limit")
    return snapshot


def export_new_json(destination: str | Path, snapshot: dict) -> Path:
    """Explicit new-file export only: never overwrite an existing file or symlink."""
    target = Path(destination)
    if not target.parent.is_dir():
        raise ValueError("Destination directory does not exist")
    if not isinstance(snapshot, dict) or snapshot.get("boot_verified") is not False or \
            snapshot.get("can_generate_efi") is not False or snapshot.get("read_only") is not True:
        raise ValueError("Refusing unsafe or malformed research report")
    if set(snapshot) != {"schema_version", "status", "notice", "read_only",
                         "boot_verified", "can_generate_efi", "scan", "evaluation"}:
        raise ValueError("Refusing unexpected research report fields")
    if snapshot.get("schema_version") != 1 or snapshot.get("status") != "Research Only" or \
            snapshot.get("notice") != NOTICE:
        raise ValueError("Refusing forged research report classification or notice")
    report, evaluation = snapshot.get("scan"), snapshot.get("evaluation")
    if not isinstance(report, dict) or not isinstance(evaluation, dict):
        raise ValueError("Malformed research report content")
    if report != privacy_project(report) or evaluation != evaluation_project(evaluation):
        raise ValueError("Research report contains unexpected metadata")
    if evaluation.get("classification") not in ("Unknown", "Research Only") or \
            evaluation.get("boot_verified") is not False or \
            evaluation.get("can_generate_efi") is not False:
        raise ValueError("Refusing unsafe research evaluation classification")
    payload = (json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if len(payload) > MAX_JSON_BYTES:
        raise ValueError("Research report exceeds the 2 MiB export limit")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
    except BaseException:
        # If the write fails, do not leave a truncated report masquerading as valid.
        try:
            target.unlink()
        except OSError:
            pass
        raise
    return target


def summary_lines(snapshot: dict) -> list[str]:
    report = snapshot["scan"]
    h = report["hardware"]
    ev = snapshot["evaluation"]
    def display(value: object) -> str:
        return str(value)[:180] if value not in (None, "") else "Unknown / not collected"
    return [
        NOTICE,
        "",
        f"Host OS: {display(report.get('host_os'))}",
        f"CPU: {display((h.get('cpu') or {}).get('name'))}",
        f"Motherboard: {display((h.get('motherboard') or {}).get('model'))}",
        f"Firmware: {display(h.get('firmware'))}",
        f"GPU devices: {len(h.get('gpus') or [])}",
        f"Research family: {display(ev.get('cpu_family'))}",
        f"Classification: {display(ev.get('classification'))}",
        f"Missing evidence: {', '.join(map(str, ev.get('missing_inventory_evidence') or [])) or 'None listed'}",
        "",
        "Boot verified: NO   |   EFI generation available: NO",
        "No drives, ESP partitions, or boot configuration were changed.",
    ]


def launch() -> None:
    # Import GUI toolkit only on launch so automated tests run without a display.
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk
    import blazehackintosh as core
    import release_gates

    root = tk.Tk()
    root.title("BlazeHackintosh — Research Workbench (Experimental)")
    root.geometry("1050x730")
    root.minsize(780, 570)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background="#101c2e")
    style.configure("TLabel", background="#101c2e", foreground="#e7effa", font=("Segoe UI", 10))
    style.configure("Title.TLabel", font=("Segoe UI Semibold", 19), foreground="#ffffff")
    style.configure("Warning.TLabel", foreground="#ffce8a", font=("Segoe UI", 10, "bold"))
    style.configure("TButton", font=("Segoe UI", 10), padding=9)
    style.configure("TNotebook", background="#101c2e", borderwidth=0)
    style.configure("TNotebook.Tab", padding=(18, 10), font=("Segoe UI", 10))

    header = ttk.Frame(root, padding=(22, 16))
    header.pack(fill="x")
    ttk.Label(header, text="BlazeHackintosh", style="Title.TLabel").pack(anchor="w")
    ttk.Label(header, text=NOTICE, style="Warning.TLabel", wraplength=950).pack(anchor="w", pady=(5, 0))

    controls = ttk.Frame(root, padding=(22, 0))
    controls.pack(fill="x")
    status = tk.StringVar(value="Ready. Scanning is optional and read-only.")
    snapshot: dict | None = None
    events: queue.Queue = queue.Queue()
    tabs = ttk.Notebook(root)
    tabs.pack(fill="both", expand=True, padx=22, pady=(12, 5))
    views = {}
    for label in ("Overview", "Hardware JSON", "Research Evaluation", "Release Gates"):
        frame = ttk.Frame(tabs)
        tabs.add(frame, text=label)
        view = scrolledtext.ScrolledText(frame, wrap="word", relief="flat", borderwidth=0,
                                        font=("Consolas", 10), bg="#172840", fg="#e7effa",
                                        insertbackground="#e7effa", padx=18, pady=18)
        view.pack(fill="both", expand=True)
        views[label] = view
    def put(name: str, value: str) -> None:
        view = views[name]
        view.configure(state="normal")
        view.delete("1.0", "end")
        view.insert("end", value)
        view.configure(state="disabled")
    put("Overview", "Click 'Scan this PC' to collect a privacy-filtered, read-only inventory.\n\n" + NOTICE)
    put("Hardware JSON", "No scan performed.")
    put("Research Evaluation", "No research evaluation performed.")

    def refresh_gates() -> None:
        try:
            gate = release_gates.readiness()
            put("Release Gates", json.dumps(gate, indent=2) +
                "\n\nNOTICE: Manifest URLs are not independently authenticated.\n"
                "This is not hardware acceptance or production approval.")
        except Exception as exc:
            put("Release Gates", f"Cannot verify release gate ledger: {exc}\nProduction readiness: NOT ESTABLISHED")

    def scan_worker() -> None:
        try:
            result = make_snapshot(core.scan_hardware, core.load_catalog, core.evaluate)
            events.put(("result", result))
        except Exception as exc:
            events.put(("error", str(exc)))

    def scan_click() -> None:
        scan_button.configure(state="disabled")
        status.set("Scanning read-only hardware inventory…")
        threading.Thread(target=scan_worker, daemon=True).start()

    def export_click() -> None:
        if snapshot is None:
            messagebox.showwarning("No report", "Scan the PC before exporting a report.")
            return
        destination = filedialog.asksaveasfilename(title="Export NEW research report",
                        defaultextension=".json", filetypes=[("JSON report", "*.json")])
        if not destination:
            return
        try:
            path = export_new_json(destination, snapshot)
            status.set(f"Exported research-only JSON: {path.name}")
        except FileExistsError:
            messagebox.showerror("File already exists", "Choose a NEW file name. Existing files are never overwritten.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Export failed", str(exc))

    scan_button = ttk.Button(controls, text="Scan this PC", command=scan_click)
    scan_button.pack(side="left", padx=(0, 10))
    ttk.Button(controls, text="Export NEW JSON…", command=export_click).pack(side="left", padx=(0, 10))
    ttk.Button(controls, text="Refresh release gates", command=refresh_gates).pack(side="left")
    ttk.Label(root, textvariable=status, padding=(22, 10)).pack(anchor="w")

    def poll() -> None:
        nonlocal snapshot
        try:
            while True:
                kind, data = events.get_nowait()
                scan_button.configure(state="normal")
                if kind == "error":
                    status.set("Scan failed safely; no file was written.")
                    messagebox.showerror("Read-only scan failed", data)
                else:
                    snapshot = data
                    put("Overview", "\n".join(summary_lines(snapshot)))
                    put("Hardware JSON", json.dumps(snapshot["scan"], indent=2, ensure_ascii=False))
                    put("Research Evaluation", json.dumps(snapshot["evaluation"], indent=2, ensure_ascii=False))
                    status.set("Read-only scan complete. Nothing was written to disk.")
        except queue.Empty:
            pass
        root.after(100, poll)

    refresh_gates()
    root.after(100, poll)
    root.mainloop()


if __name__ == "__main__":
    launch()
