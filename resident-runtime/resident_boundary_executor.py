#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

def _load_transport():
    path = ROOT / "org-boundary" / "runtime" / "intr_transport.py"
    spec = importlib.util.spec_from_file_location("intr_transport", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

TRANSPORT = _load_transport()

def _canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()

def _safe_name(packet_id: str) -> str:
    return hashlib.sha256(packet_id.encode()).hexdigest()

def assert_sovereign_runtime() -> None:
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        raise RuntimeError("github-actions-is-validation-only-not-resident-runtime")
    if os.environ.get("STEGVERSE_RESIDENT_PROCESS") != "1":
        raise RuntimeError("resident-process-identity-not-asserted")

def ensure_layout(state_root: Path) -> dict[str, Path]:
    paths = {
        "ingress": state_root / "ingress.d",
        "egress": state_root / "egress.d",
        "processed": state_root / "processed.d",
        "receipts": state_root / "receipts.d",
        "failed": state_root / "failed.d",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths

def process_one(ingress_path: Path, state_root: Path) -> dict[str, Any]:
    assert_sovereign_runtime()
    layout = ensure_layout(state_root)
    ingress = json.loads(ingress_path.read_text(encoding="utf-8"))
    TRANSPORT.validate_org_crossing(ingress, "INGRESS")

    packet_key = _safe_name(str(ingress["packet_id"]))
    execution_path = layout["receipts"] / f"{packet_key}.execution.json"

    process_path = ROOT / "org-boundary" / "runtime" / "process_boundary.py"
    import subprocess
    subprocess.run(
        [sys.executable, str(process_path), "--envelope", str(ingress_path), "--out", str(execution_path)],
        cwd=ROOT,
        check=True,
    )

    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    egress = TRANSPORT.build_egress(ingress, execution)
    TRANSPORT.validate_org_crossing(egress, "EGRESS")

    egress_path = layout["egress"] / f"{packet_key}.json"
    egress_path.write_text(json.dumps(egress, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema": "stegverse.data-continuation.resident-boundary-cycle/v1",
        "packet_id": ingress["packet_id"],
        "ingress_path": str(ingress_path),
        "execution_receipt_path": str(execution_path),
        "egress_path": str(egress_path),
        "consumed": bool(execution.get("consumed")),
        "reconstruction": execution.get("reconstruction", {}).get("status"),
        "authority_effect": execution.get("authority_effect"),
        "github_actions_runtime_authority": "NONE",
        "resident_process_identity_asserted": True,
    }
    receipt_path = layout["receipts"] / f"{packet_key}.cycle.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    processed_path = layout["processed"] / ingress_path.name
    shutil.move(str(ingress_path), processed_path)
    return receipt

def run_once(state_root: Path) -> dict[str, Any]:
    assert_sovereign_runtime()
    layout = ensure_layout(state_root)
    candidates = sorted(layout["ingress"].glob("*.json"))
    if not candidates:
        return {"status": "IDLE", "processed": 0, "authority_effect": "NONE"}
    ingress_path = candidates[0]
    try:
        receipt = process_one(ingress_path, state_root)
        return {"status": "PASS", "processed": 1, "receipt": receipt}
    except Exception as exc:
        failed = layout["failed"] / ingress_path.name
        if ingress_path.exists():
            shutil.move(str(ingress_path), failed)
        failure = {
            "schema": "stegverse.data-continuation.resident-boundary-failure/v1",
            "ingress_file": ingress_path.name,
            "error": str(exc),
            "authority_effect": "NONE",
        }
        failure_path = layout["receipts"] / f"{_safe_name(ingress_path.name)}.failure.json"
        failure_path.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-root", default="resident-runtime/state")
    parser.add_argument("--validate-layout", action="store_true")
    args = parser.parse_args()
    state_root = Path(args.state_root)
    if args.validate_layout:
        layout = ensure_layout(state_root)
        print(json.dumps({"status": "PASS", "paths": sorted(str(p) for p in layout.values()), "authority_effect": "NONE"}))
        return 0
    result = run_once(state_root)
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
