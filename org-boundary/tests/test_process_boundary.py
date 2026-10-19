#!/usr/bin/env python3
import json, subprocess, tempfile
from pathlib import Path
reg=json.loads(Path("org-boundary/registry/services.json").read_text())
svc=next(s["service_id"] for s in reg["services"] if s.get("boundary_role")=="BOUNDARY_LOCAL_DIAGNOSTIC")
env={"schema_version":"test","packet_id":"pkt-001","direction":"INGRESS","origin":{"org":"peer","service":"peer.boundary-diagnostic"},"destination":{"org":reg["organization"],"service":svc},"carrier":{"kind":"HB_DERIVED","reference":"HB-test"},"intr_profile":"stegverse.intr.org-boundary.v1","transition":{"reference":"test","authority_effect":"NONE"},"payload":{"probe":"ping"},"evidence":{"ingress_receipt":None,"dispatch_receipt":None,"consumption_receipt":None,"egress_receipt":None,"reconstruction_reference":None}}
with tempfile.TemporaryDirectory() as td:
 p=Path(td); (p/"in.json").write_text(json.dumps(env)); subprocess.run(["python3","org-boundary/runtime/process_boundary.py","--envelope",str(p/"in.json"),"--out",str(p/"out.json")],check=True)
 out=json.loads((p/"out.json").read_text()); assert out["consumed"] is True; assert out["reconstruction"]["status"]=="RECONSTRUCTED"; assert out["authority_effect"]=="NONE"
FIELDS={"failure_code","failed_predicate","required_evidence_or_repair","retry_entrypoint","owning_existing_goal","next_attempt","terminal"}
def run(td,envelope,out):
 return subprocess.run(["python3","org-boundary/runtime/process_boundary.py","--envelope",str(envelope),"--out",str(out)],capture_output=True,text=True)
def record(r):
 assert "Traceback" not in r.stderr, r.stderr
 rec=json.loads(r.stderr); assert set(rec)==FIELDS, rec; return rec
with tempfile.TemporaryDirectory() as td:
 p=Path(td); (p/"in.json").write_text(json.dumps(env)); (p/"blocker").write_text("x")
 # unwritable --out: parent is a regular file
 r=run(td,p/"in.json",p/"blocker"/"sub"/"out.json"); rec=record(r)
 assert r.returncode==75; assert rec["failure_code"]=="PROCESS_BOUNDARY_WRITE_FAULT"; assert rec["failed_predicate"]=="OUT_PATH_WRITABLE"; assert rec["terminal"] is False
 # unwritable --out: target is a directory, so os.replace fails after the temp file is written
 (p/"outdir").mkdir(); before=sorted(x.name for x in p.iterdir())
 r=run(td,p/"in.json",p/"outdir"); rec=record(r)
 assert r.returncode==75; assert rec["failure_code"]=="PROCESS_BOUNDARY_WRITE_FAULT"; assert rec["terminal"] is False
 assert sorted(x.name for x in p.iterdir())==before; assert list((p/"outdir").iterdir())==[]
 # missing and unparsable inputs: terminal, nothing written
 (p/"bad.json").write_text("not json"); (p/"list.json").write_text("[]"); (p/"bin.json").write_bytes(b"\xff\xfe")
 for bad in [p/"missing.json",p/"bad.json",p/"list.json",p/"bin.json",p/"outdir"]:
  out=p/("out-"+bad.name); r=run(td,bad,out); rec=record(r)
  assert r.returncode not in (0,75), r.returncode; assert rec["failure_code"]=="PROCESS_BOUNDARY_INPUT_FAULT"; assert rec["terminal"] is True; assert not out.exists()
print("PASS")
