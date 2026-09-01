#!/usr/bin/env python3
import importlib.util
import json
import os
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("resident_boundary_executor",ROOT/"resident-runtime"/"resident_boundary_executor.py")
M=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)

def ingress_fixture():
    reg=json.loads((ROOT/"org-boundary"/"registry"/"services.json").read_text())
    svc=next(s["service_id"] for s in reg["services"] if s.get("boundary_role")=="BOUNDARY_LOCAL_DIAGNOSTIC")
    return {
      "schema_version":"stegverse.intr.org-boundary.v1",
      "packet_id":"resident-test-001",
      "direction":"INGRESS",
      "origin":{"org":"peer","service":"peer.boundary-diagnostic"},
      "destination":{"org":reg["organization"],"service":svc},
      "carrier":{"kind":"HB_DERIVED","reference":"HB-test"},
      "intr_profile":"stegverse.intr.org-boundary.v1",
      "transition":{"reference":"test","authority_effect":"NONE","conditions":[]},
      "payload":{"probe":"ping"},
      "evidence":{"ingress_receipt":None,"dispatch_receipt":None,"consumption_receipt":None,"egress_receipt":None,"reconstruction_reference":None}
    }

def main():
    old_ga=os.environ.get("GITHUB_ACTIONS")
    old_rp=os.environ.get("STEGVERSE_RESIDENT_PROCESS")
    try:
        os.environ["GITHUB_ACTIONS"]="true"
        os.environ["STEGVERSE_RESIDENT_PROCESS"]="1"
        try:
            M.assert_sovereign_runtime()
            raise AssertionError("GitHub Actions must be rejected as resident runtime")
        except RuntimeError as exc:
            assert "validation-only" in str(exc)

        os.environ["GITHUB_ACTIONS"]="false"
        os.environ.pop("STEGVERSE_RESIDENT_PROCESS",None)
        try:
            M.assert_sovereign_runtime()
            raise AssertionError("resident identity must be required")
        except RuntimeError as exc:
            assert "identity-not-asserted" in str(exc)

        os.environ["STEGVERSE_RESIDENT_PROCESS"]="1"
        with tempfile.TemporaryDirectory() as td:
            state=Path(td)/"state"
            layout=M.ensure_layout(state)
            p=layout["ingress"]/"packet.json"
            p.write_text(json.dumps(ingress_fixture()))
            result=M.run_once(state)
            assert result["status"]=="PASS"
            assert result["processed"]==1
            assert not p.exists()
            assert len(list(layout["processed"].glob("*.json")))==1
            assert len(list(layout["egress"].glob("*.json")))==1
            cycle=list(layout["receipts"].glob("*.cycle.json"))
            assert len(cycle)==1
            receipt=json.loads(cycle[0].read_text())
            assert receipt["consumed"] is True
            assert receipt["reconstruction"]=="RECONSTRUCTED"
            assert receipt["authority_effect"]=="NONE"
            assert receipt["github_actions_runtime_authority"]=="NONE"
        print("RESIDENT_BOUNDARY_EXECUTOR_PASS")
        return 0
    finally:
        if old_ga is None: os.environ.pop("GITHUB_ACTIONS",None)
        else: os.environ["GITHUB_ACTIONS"]=old_ga
        if old_rp is None: os.environ.pop("STEGVERSE_RESIDENT_PROCESS",None)
        else: os.environ["STEGVERSE_RESIDENT_PROCESS"]=old_rp

if __name__=="__main__":
    raise SystemExit(main())
