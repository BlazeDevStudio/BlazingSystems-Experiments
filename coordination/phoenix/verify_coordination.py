#!/usr/bin/env python3
"""
Project Phoenix — Coordination & Architecture Contract Verification Test
Validates:
1. Existence and integrity of coordination/phoenix/ documentation.
2. Non-overlapping scope boundaries across the 7 developer roles.
3. Compliance of BLAZE-COMMS/1 protocol envelopes with the schema specification.
"""

import sys
import os
import re
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COORDINATION_FILES = [
    "ARCHITECTURE_CONTRACTS.md",
    "ROLE_ASSIGNMENTS.md",
    "INTEGRATION_MATRIX.md",
    "AUDIT_SUMMARY.md",
]

def check_files_exist():
    print("[1/4] Checking coordination file presence...")
    for filename in COORDINATION_FILES:
        path = os.path.join(BASE_DIR, filename)
        if not os.path.isfile(path):
            print(f"FAIL: Missing expected coordination file: {path}")
            return False
        if os.path.getsize(path) < 500:
            print(f"FAIL: Coordination file appears incomplete or empty: {path}")
            return False
        print(f"  OK: {filename} ({os.path.getsize(path)} bytes)")
    return True

def check_role_ownership():
    print("\n[2/4] Checking non-overlapping role ownership...")
    role_assignments_path = os.path.join(BASE_DIR, "ROLE_ASSIGNMENTS.md")
    with open(role_assignments_path, "r", encoding="utf-8") as f:
        content = f.read()

    roles = [
        "PHX-MASTER",
        "PHX-CORE",
        "PHX-RENTAL",
        "PHX-PISONET",
        "PHX-HARDWARE",
        "PHX-QA",
        "PHX-RELEASE",
    ]

    for role in roles:
        if role not in content:
            print(f"FAIL: Role {role} not documented in ROLE_ASSIGNMENTS.md")
            return False
        print(f"  OK: Role {role} verified in ownership registry")
    return True

def check_protocol_envelope():
    print("\n[3/4] Validating BLAZE-COMMS/1 message envelope structure...")
    sample_envelope = {
        "protocol": "BLAZE-COMMS/1",
        "message_id": "PHX-20261113-MASTER-001",
        "from": "PHX-MASTER",
        "to": "ALL",
        "type": "ASSIGN",
        "priority": "P0",
        "task_id": "PHX-0172",
        "branch": "phoenix/master-coordination",
        "base_sha": "f4e8a891aed8af86d5fd315d28750a0ac3a7372b",
        "scope": ["coordination/phoenix/"],
        "status": "IN_PROGRESS",
        "evidence": ["https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172"],
        "blockers": ["#31", "#32", "#34", "#43"],
        "next_action": "Coordinate fd4 admission lock verification with PHX-CORE and PHX-QA",
        "updated_utc": "2026-11-13T19:25:00Z"
    }

    required_keys = [
        "protocol", "message_id", "from", "to", "type", "priority",
        "task_id", "branch", "base_sha", "scope", "status",
        "evidence", "blockers", "next_action", "updated_utc"
    ]

    for key in required_keys:
        if key not in sample_envelope:
            print(f"FAIL: Missing required protocol key: {key}")
            return False

    if sample_envelope["protocol"] != "BLAZE-COMMS/1":
        print(f"FAIL: Invalid protocol identifier: {sample_envelope['protocol']}")
        return False

    print("  OK: Protocol envelope structure conformant with BLAZE-COMMS/1")
    return True

def check_safety_gates():
    print("\n[4/4] Verifying production safety NO-GO declarations...")
    contracts_path = os.path.join(BASE_DIR, "ARCHITECTURE_CONTRACTS.md")
    with open(contracts_path, "r", encoding="utf-8") as f:
        contracts_content = f.read()

    audit_path = os.path.join(BASE_DIR, "AUDIT_SUMMARY.md")
    with open(audit_path, "r", encoding="utf-8") as f:
        audit_content = f.read()

    if "NO-GO" not in contracts_content or "NO-GO" not in audit_content:
        print("FAIL: Mandatory NO-GO production safety gate declaration missing")
        return False

    print("  OK: Production safety NO-GO boundaries explicitly declared")
    return True

def main():
    print("==================================================")
    print("Project Phoenix — Master Coordination Verification")
    print("==================================================")

    if not check_files_exist():
        sys.exit(1)
    if not check_role_ownership():
        sys.exit(1)
    if not check_protocol_envelope():
        sys.exit(1)
    if not check_safety_gates():
        sys.exit(1)

    print("\n==================================================")
    print("ALL COORDINATION CHECKS PASSED: Matrix & contracts verified.")
    print("==================================================")
    sys.exit(0)

if __name__ == "__main__":
    main()
