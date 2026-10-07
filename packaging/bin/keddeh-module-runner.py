#!/usr/bin/env python3
"""Conservative systemd entrypoint for indexed KEDDEH modules."""
from __future__ import annotations
import argparse, hashlib, json, os, signal, subprocess, sys, time
from pathlib import Path
def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def digest(v): return hashlib.sha256(canon(v)).hexdigest()
def atomic(path:Path,value):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(value,sort_keys=True,indent=2)+"\n"); os.replace(tmp,path)
def append(path:Path,value):
    path.parent.mkdir(parents=True,exist_ok=True); line=json.dumps(value,sort_keys=True,separators=(",",":"))+"\n"
    fd=os.open(path,os.O_APPEND|os.O_CREAT|os.O_WRONLY,0o640)
    try: os.write(fd,line.encode()); os.fsync(fd)
    finally: os.close(fd)
def load_module(root:Path,module_id:str):
    runtime=json.loads((root/"packaging/runtime.index.json").read_text()); refs={x["module_id"]:x["index"] for x in runtime["modules"]}
    if module_id not in refs: raise ValueError(f"unknown module: {module_id}")
    m=json.loads((root/refs[module_id]).read_text())
    if m["module_id"]!=module_id: raise ValueError("module identity mismatch")
    for source in m["source_paths"]:
        if not (root/source).exists(): raise ValueError(f"missing source: {source}")
    ev=m["evidence"]
    if ev["state_root_path"]==ev["phase_root_path"]: raise ValueError("state/phase root collision")
    if ev["generator_id"]==ev["verifier_id"]: raise ValueError("generator/verifier collision")
    return m
def receipt(m,event,status,detail=None):
    ev=m["evidence"]; now=time.time_ns()
    state={"module_id":m["module_id"],"event":event,"status":status,"observed_ns":now,"detail":detail or {}}
    state["state_root"]=digest(state)
    phase={"module_id":m["module_id"],"phase":event,"observed_ns":now,"state_root":state["state_root"]}; phase["phase_root"]=digest(phase)
    atomic(Path(ev["state_root_path"]),state); atomic(Path(ev["phase_root_path"]),phase)
    record={**state,"phase_root":phase["phase_root"],"generator_id":ev["generator_id"],"promotion_status":ev["promotion_status"]}
    append(Path(ev["receipt_path"]),record); print(json.dumps(record,sort_keys=True),flush=True)
def require_activation(m):
    if m["execution"]["activation_default"]: return
    if os.environ.get("KEDDEH_ALLOW_ACTIVATION")!="1": raise PermissionError("explicit activation required: set KEDDEH_ALLOW_ACTIVATION=1 in the host-bound unit override")
    missing=[x for x in m["execution"]["required_env"] if not os.environ.get(x)]
    if missing: raise PermissionError("required environment missing: "+",".join(missing))
def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",default=os.environ.get("KEDDEH_INSTALL_ROOT","/opt/keddeh/SERVERS-KEDDEHSYSTEMS")); p.add_argument("--module",required=True); p.add_argument("action",choices=["validate","start","health"]); a=p.parse_args()
    root=Path(a.root).resolve(); m=load_module(root,a.module)
    if a.action=="validate": receipt(m,"VALIDATED","PASS"); return
    if a.action=="health":
        state=Path(m["evidence"]["state_root_path"]); detail={"state_present":state.is_file(),"source_count":len(m["source_paths"])}
        receipt(m,"HEALTH_READBACK","PASS" if state.is_file() else "DEGRADED",detail)
        if not state.is_file(): raise SystemExit(3)
        return
    require_activation(m); cls=m["execution"]["class"]; cmd=m["execution"]["command"]
    if cls in {"data-only","library"}: receipt(m,"REGISTERED_STATIC","PASS"); return
    if cls=="external-interface" and not cmd:
        receipt(m,"EXTERNAL_ACTUATOR_REQUIRED","BLOCKED",{"authority_class":m["authority_class"]}); raise SystemExit(78)
    if not cmd: raise ValueError("executable module has no command")
    receipt(m,"START_REQUESTED","PENDING",{"command":cmd}); proc=subprocess.Popen(cmd,cwd=root,env=os.environ.copy(),start_new_session=True)
    def stop(_signum,_frame):
        if proc.poll() is None: os.killpg(proc.pid,signal.SIGTERM)
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop); code=proc.wait()
    receipt(m,"PROCESS_EXIT","PASS" if code==0 else "FAIL",{"exit_code":code}); raise SystemExit(code)
if __name__=="__main__":
    try: main()
    except PermissionError as exc:
        print(json.dumps({"status":"BLOCKED","error":str(exc)}),file=sys.stderr); raise SystemExit(77)
    except Exception as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)}),file=sys.stderr); raise SystemExit(1)
