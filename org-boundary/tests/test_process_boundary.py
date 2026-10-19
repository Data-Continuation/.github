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
# content faults: terminal 65, six-field record, no traceback, nothing written
def run_reg(envelope,registry,out):
 return subprocess.run(["python3","org-boundary/runtime/process_boundary.py","--envelope",str(envelope),"--registry",str(registry),"--out",str(out)],capture_output=True,text=True)
def content_fault(p,name,e,predicate,registry="org-boundary/registry/services.json",raw=None):
 f=p/(name+".json"); f.write_text(raw if raw is not None else json.dumps(e)); out=p/("out-"+name+".json")
 r=run_reg(f,registry,out); rec=record(r)
 assert r.returncode==65, (name,r.returncode,r.stderr); assert rec["failure_code"]=="PROCESS_BOUNDARY_INPUT_FAULT"; assert rec["failed_predicate"]==predicate, rec; assert rec["terminal"] is True; assert not out.exists()
 return rec
with tempfile.TemporaryDirectory() as td:
 p=Path(td)
 rec=content_fault(p,"missing",{k:v for k,v in env.items() if k not in ("carrier","payload")},"ENVELOPE_HAS_REQUIRED_FIELDS"); assert "carrier" in rec["required_evidence_or_repair"] and "payload" in rec["required_evidence_or_repair"]
 rec=content_fault(p,"wrong-org",{**env,"destination":{**env["destination"],"org":"Other-Org"}},"DESTINATION_ORG_MATCHES_REGISTRY"); assert "Other-Org" in rec["required_evidence_or_repair"]
 rec=content_fault(p,"unknown-svc",{**env,"destination":{**env["destination"],"service":"no.such.service"}},"SERVICE_REGISTERED"); assert "no.such.service" in rec["required_evidence_or_repair"]
 ctl=next(s["service_id"] for s in reg["services"] if s.get("boundary_role")!="BOUNDARY_LOCAL_DIAGNOSTIC")
 rec=content_fault(p,"no-adapter",{**env,"destination":{**env["destination"],"service":ctl}},"ENDPOINT_ADAPTER_INSTALLED"); assert ctl in rec["required_evidence_or_repair"]
 # wrong-typed fields
 for i,e in enumerate([{**env,"destination":"x"},{**env,"destination":{"org":reg["organization"]}},{**env,"destination":{"org":1,"service":svc}},{**env,"transition":"x"},{**env,"transition":{}}]):
  content_fault(p,"typed-%d"%i,e,"ENVELOPE_HAS_REQUIRED_FIELDS")
 for i,rg in enumerate([{"organization":reg["organization"]},{"organization":1,"services":[]},{"organization":reg["organization"],"services":{}},{"organization":reg["organization"],"services":[1]},{"organization":reg["organization"],"services":[{}]}]):
  (p/("reg-%d.json"%i)).write_text(json.dumps(rg)); content_fault(p,"reg-typed-%d"%i,env,"REGISTRY_HAS_REQUIRED_FIELDS",registry=p/("reg-%d.json"%i))
 # deeply nested --envelope and --registry: RecursionError is a terminal input fault
 deep='{"a":'+'['*200000
 rec=content_fault(p,"deep-env",None,"INPUT_READABLE_JSON_OBJECT",raw=deep); assert "RecursionError" in rec["required_evidence_or_repair"], rec
 (p/"deep-registry.json").write_text(deep); rec=content_fault(p,"deep-reg",env,"INPUT_READABLE_JSON_OBJECT",registry=p/"deep-registry.json"); assert "RecursionError" in rec["required_evidence_or_repair"], rec
print("PASS")
