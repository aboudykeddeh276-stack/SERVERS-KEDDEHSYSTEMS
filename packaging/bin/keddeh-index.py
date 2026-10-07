#!/usr/bin/env python3
"""Validate the KEDDEH aggregate/module indexes and emit a deterministic digest."""
from __future__ import annotations
import argparse, hashlib, json, os, sys, time
from pathlib import Path
REQUIRED_TOP={"schema_version","module_id","display_name","version","authority_class","source_paths","execution","dependencies","systemd","wasm","vfs","network","lifecycle","evidence"}
CLASSES={"native","wasi-adapter","data-only","library","external-interface"}
def canonical(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def fail(message): raise ValueError(message)
def validate(root:Path):
    runtime=json.loads((root/"packaging/runtime.index.json").read_text())
    if runtime.get("schema_version")!="keddeh.runtime-index/v1": fail("runtime schema_version mismatch")
    seen=set(); validated=[]
    for ref in runtime.get("modules",[]):
        module_id=ref.get("module_id")
        if not module_id or module_id in seen: fail(f"duplicate or missing module_id: {module_id!r}")
        seen.add(module_id); index_path=root/ref["index"]
        if not index_path.is_file(): fail(f"module index missing: {index_path}")
        module=json.loads(index_path.read_text()); missing=sorted(REQUIRED_TOP-set(module))
        if missing: fail(f"{module_id}: missing {missing}")
        if module["module_id"]!=module_id: fail(f"{module_id}: identity mismatch")
        if module["execution"]["class"] not in CLASSES: fail(f"{module_id}: invalid execution class")
        if module["systemd"]["unit"]!="keddeh-module@.service": fail(f"{module_id}: unit mismatch")
        if module["systemd"]["health_unit"]!="keddeh-module-health@.service": fail(f"{module_id}: health unit mismatch")
        ev=module["evidence"]
        if ev["state_root_path"]==ev["phase_root_path"]: fail(f"{module_id}: state and phase roots collide")
        if ev["generator_id"]==ev["verifier_id"]: fail(f"{module_id}: generator and verifier collide")
        if ev["promotion_status"]!="SOURCE_DEFINED_PENDING_BUILD_AND_RUNTIME_READBACK": fail(f"{module_id}: invalid source-only promotion status")
        for source in module["source_paths"]:
            if not (root/source).exists(): fail(f"{module_id}: missing source {source}")
        declared={f'{x["protocol"]}:{x["port"]}' for x in module["network"]["listen"]}
        if module["network"]["mode"]=="none" and declared: fail(f"{module_id}: listeners declared with network mode none")
        if module["execution"]["class"] in {"data-only","library"} and module["execution"]["command"]: fail(f"{module_id}: non-executable module has command")
        validated.append({"module_id":module_id,"index":ref["index"],"index_sha256":hashlib.sha256(canonical(module)).hexdigest()})
    expected={x["module_id"] for x in runtime["modules"]}
    for profile,ids in runtime.get("activation_profiles",{}).items():
        unknown=set(ids)-expected
        if unknown: fail(f"profile {profile}: unknown modules {sorted(unknown)}")
    digest=hashlib.sha256(canonical({"runtime":runtime,"modules":validated})).hexdigest()
    return {"status":"PASS","module_count":len(validated),"aggregate_sha256":digest,"modules":validated}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--receipt"); args=p.parse_args()
    root=Path(args.root).resolve(); result=validate(root)
    result.update({"verified_at_ns":time.time_ns(),"root":str(root),"verifier_id":"keddeh-index-verifier"})
    if args.receipt:
        out=Path(args.receipt); out.parent.mkdir(parents=True,exist_ok=True); tmp=out.with_suffix(out.suffix+".tmp")
        tmp.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n"); os.replace(tmp,out)
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    try: main()
    except Exception as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)}),file=sys.stderr); raise SystemExit(1)
