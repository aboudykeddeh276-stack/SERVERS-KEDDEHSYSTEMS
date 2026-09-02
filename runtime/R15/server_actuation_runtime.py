from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict
import subprocess, sys, time

@dataclass(frozen=True)
class Carrier:
    carrier_id:str
    priority:int
    available:bool
    route_prefix:str

class ToTOrcDispatcher:
    def __init__(self):
        self.carriers=[Carrier("TL2",10,True,"runtime://braink/active-continuation"),Carrier("TL1",20,True,"runtime://braink/active-continuation"),Carrier("VPN-TL",30,True,"runtime://braink/active-continuation")]
        self.handlers:Dict[str,Callable]={}
        self.receipts=[]
    def register_handler(self,carrier_id,fn): self.handlers[carrier_id]=fn
    def set_availability(self,carrier_id,available):
        self.carriers=[Carrier(c.carrier_id,c.priority,available if c.carrier_id==carrier_id else c.available,c.route_prefix) for c in self.carriers]
    def dispatch(self,continuation:Dict[str,Any])->Dict[str,Any]:
        attempts=[]
        for c in sorted(self.carriers,key=lambda x:x.priority):
            if not c.available:
                attempts.append({"carrier":c.carrier_id,"status":"UNAVAILABLE"}); continue
            fn=self.handlers.get(c.carrier_id)
            if not fn:
                attempts.append({"carrier":c.carrier_id,"status":"NO_HANDLER"}); continue
            out=fn(continuation); attempts.append({"carrier":c.carrier_id,"status":out.get("status")})
            if out.get("status") in {"DISPATCHED","ACCEPTED","COMPLETED"}:
                receipt={"status":"DISPATCHED","carrier":c.carrier_id,"route":c.route_prefix,"continuation_id":continuation["continuation_id"],"attempts":attempts,"at_ns":time.time_ns()}; self.receipts.append(receipt); return receipt
        receipt={"status":"FAILOVER_EXHAUSTED","continuation_id":continuation["continuation_id"],"attempts":attempts,"at_ns":time.time_ns()}; self.receipts.append(receipt); return receipt

class ProductionActuatorAdapter:
    adapter_id="adapter://keddeh/production-actuator"
    capabilities=("PROBE","VALIDATE_ORIGIN","AMEND","RELEASE","READBACK")
    def __init__(self,actuator_path:str|None=None): self.actuator_path=Path(actuator_path).resolve() if actuator_path else None
    def probe(self): return {"status":"READY" if self.actuator_path and self.actuator_path.exists() else "UNBOUND_ACTUATOR","path":str(self.actuator_path) if self.actuator_path else None}
    def run(self,args):
        if not self.actuator_path: return {"status":"UNBOUND_ACTUATOR"}
        p=subprocess.run([sys.executable,str(self.actuator_path),*args],capture_output=True,text=True,timeout=30)
        return {"status":"EXECUTED" if p.returncode==0 else "FAILED","returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
    def apply(self,operation,payload=None):
        payload=payload or {}
        if operation=="PROBE": return self.probe()
        origin=payload.get("origin")
        if operation in {"VALIDATE_ORIGIN","AMEND","RELEASE"} and not origin: return {"status":"ORIGIN_UNBOUND","operation":operation}
        if operation=="VALIDATE_ORIGIN": return self.run(["validate-origin","--origin",origin])
        if operation=="AMEND": return self.run(["amend","--origin",origin,"--target",payload["target"],"--patch-id",payload["patch_id"]])
        if operation=="RELEASE": return self.run(["release","--origin",origin,"--release-id",payload["release_id"]])
        if operation=="READBACK":
            if not payload.get("target_url"): return {"status":"TARGET_URL_UNBOUND"}
            return self.run(["readback","--target-url",payload["target_url"]])
        return {"status":"UNSUPPORTED_OPERATION","operation":operation}
