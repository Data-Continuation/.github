#!/usr/bin/env python3
"""Organization-resident runtime boundary for Data-Continuation.

This file is the organization-local owner of runtime activation records and all
cross-boundary ingress/egress construction. It creates no credential, execution,
routing, receiving, or transition authority.
"""
from __future__ import annotations
import argparse, hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"control/organization-runtime.json"
ACTIVATIONS=ROOT/"runtime/activations"
INGRESS=ROOT/"runtime/ingress"
EGRESS=ROOT/"runtime/egress"

class RuntimeBoundaryError(ValueError): pass
def canon(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def sha(v:Any)->str:return "sha256:"+hashlib.sha256(v if isinstance(v,bytes) else canon(v)).hexdigest()
def now()->str:return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def load_config()->dict[str,Any]:
    value=json.loads(CONFIG.read_text(encoding="utf-8"))
    if value.get("organization")!="Data-Continuation" or value.get("runtime_owner_repo")!="Data-Continuation/.github": raise RuntimeBoundaryError("runtime owner mismatch")
    if value.get("cross_boundary_communication_requires_interlock_intr") is not True: raise RuntimeBoundaryError("Interlock/InTr requirement disabled")
    if value.get("credential_authority")!="TV/TVC" or value.get("github_actions_runtime_authority")!="NONE": raise RuntimeBoundaryError("authority boundary mismatch")
    return value
def safe_id(value:str)->str:
    if not value or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in value): raise RuntimeBoundaryError("invalid id")
    return value
def write_once(path:Path,value:Mapping[str,Any])->Path:
    raw=json.dumps(dict(value),sort_keys=True,indent=2,ensure_ascii=False).encode()+b"\n"; path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()==raw:return path
        raise RuntimeBoundaryError("write-once collision: "+str(path))
    path.write_bytes(raw)
    if path.read_bytes()!=raw: raise RuntimeBoundaryError("write verification failed")
    return path

def register_activation(*,activation_id:str,node_ref:str)->dict[str,Any]:
    load_config(); activation_id=safe_id(activation_id)
    body={"schema":"stegverse.organization-runtime-activation/v1","organization":"Data-Continuation","runtime_owner_repo":"Data-Continuation/.github","activation_id":activation_id,"node_ref":node_ref,"state":"ACTIVATION_REQUESTED_NOT_OBSERVED","requested_at":now(),"credential_authority":"TV/TVC","github_actions_runtime_authority":"NONE","heartbeat_grants_execution_authority":False,"request_grants_execution_authority":False,"authority_effect":"NONE_REQUEST_ONLY"}
    body["activation_hash"]=sha(body); write_once(ACTIVATIONS/(activation_id+".json"),body); return body

def build_egress(*,message_id:str,operation_id:str,destination:Mapping[str,str],payload:bytes,hb_reference:str|None=None)->dict[str,Any]:
    load_config(); message_id=safe_id(message_id)
    intent={"schema":"stegverse.universal-intr-transport/v1","protocol":"InTr","operation_id":operation_id,"packet_id":message_id,"payload_hash":sha(payload),"source":{"boundary":"ORGANIZATION","subsystem":"Data-Continuation:.github"},"destination":dict(destination),"boundary_path":["ORGANIZATION","EXTERNAL_OR_ADJACENT"],"interlock_required":True,"transport_semantics":{"event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,"receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION","exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False},"authority":{"authority_transfer":False,"transport_grants_execution_authority":False,"credential_authority":"TV/TVC"}}
    envelope={"schema":"stegverse.organization-interlock-envelope/v1","organization":"Data-Continuation","direction":"EGRESS","interlock_required":True,"intr_intent":intent,"payload_base64":__import__("base64").b64encode(payload).decode(),"hb_reference":hb_reference,"heartbeat_grants_authority":False,"credential_authority":"TV/TVC","authority_effect":"NONE_TRANSPORT_ONLY"}
    envelope["envelope_hash"]=sha(envelope); write_once(EGRESS/(message_id+".json"),envelope); return envelope

def admit_ingress(envelope:Mapping[str,Any])->dict[str,Any]:
    load_config()
    if envelope.get("schema")!="stegverse.organization-interlock-envelope/v1": raise RuntimeBoundaryError("interlock envelope schema mismatch")
    intent=envelope.get("intr_intent")
    if not isinstance(intent,Mapping) or intent.get("schema")!="stegverse.universal-intr-transport/v1" or intent.get("protocol")!="InTr": raise RuntimeBoundaryError("InTr intent invalid")
    if intent.get("interlock_required") is not True or intent.get("authority",{}).get("transport_grants_execution_authority") is not False: raise RuntimeBoundaryError("transport authority invalid")
    body=dict(envelope); claimed=body.pop("envelope_hash",None)
    if claimed!=sha(body): raise RuntimeBoundaryError("envelope hash mismatch")
    import base64
    try: payload=base64.b64decode(envelope.get("payload_base64",""),validate=True)
    except Exception as exc: raise RuntimeBoundaryError("payload base64 invalid") from exc
    if sha(payload)!=intent.get("payload_hash"): raise RuntimeBoundaryError("payload hash mismatch")
    receipt={"schema":"stegverse.organization-interlock-ingress-receipt/v1","organization":"Data-Continuation","packet_id":intent.get("packet_id"),"payload_hash":intent.get("payload_hash"),"state":"INGRESS_VALIDATED_NOT_EXECUTED","validated_at":now(),"interlock_validated":True,"intr_validated":True,"execution_authorized":False,"credential_authority":"TV/TVC","authority_effect":"NONE"}
    receipt["receipt_hash"]=sha(receipt); write_once(INGRESS/(safe_id(str(intent.get("packet_id")))+".json"),receipt); return receipt

def main()->int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("activate"); a.add_argument("--activation-id",required=True); a.add_argument("--node-ref",required=True)
    e=sub.add_parser("egress"); e.add_argument("--message-id",required=True); e.add_argument("--operation-id",required=True); e.add_argument("--destination-boundary",required=True); e.add_argument("--destination-subsystem",required=True); e.add_argument("--payload",required=True); e.add_argument("--hb-reference")
    i=sub.add_parser("ingress"); i.add_argument("--file",type=Path,required=True)
    args=ap.parse_args()
    if args.cmd=="activate": result=register_activation(activation_id=args.activation_id,node_ref=args.node_ref)
    elif args.cmd=="egress": result=build_egress(message_id=args.message_id,operation_id=args.operation_id,destination={"boundary":args.destination_boundary,"subsystem":args.destination_subsystem},payload=args.payload.encode(),hb_reference=args.hb_reference)
    else: result=admit_ingress(json.loads(args.file.read_text(encoding="utf-8")))
    print(json.dumps(result,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
