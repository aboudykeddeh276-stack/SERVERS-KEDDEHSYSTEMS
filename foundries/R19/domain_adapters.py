from __future__ import annotations
from dataclasses import dataclass
from typing import Callable,Dict,Any

@dataclass(frozen=True)
class DomainAdapterContract:
    adapter_id:str
    capabilities:tuple[str,...]
    authority_class:str

class DomainAdapterRegistry:
    def __init__(self):
        self.contracts={}; self.handlers={}
    def register(self,contract,handler=None):
        self.contracts[contract.adapter_id]=contract
        if handler:self.handlers[contract.adapter_id]=handler
    def invoke(self,adapter_id,capability,payload):
        c=self.contracts.get(adapter_id)
        if not c:return {"status":"UNKNOWN_ADAPTER"}
        if capability not in c.capabilities:return {"status":"CAPABILITY_DENIED"}
        h=self.handlers.get(adapter_id)
        if not h:return {"status":"AUTHORITY_UNBOUND","authority_class":c.authority_class}
        return h(capability,payload)

def default_domain_registry():
    r=DomainAdapterRegistry()
    r.register(DomainAdapterContract("adapter://registrar/epp",("DISCOVER","ACQUIRE","RENEW","TRANSFER","READBACK"),"REGISTRAR"))
    r.register(DomainAdapterContract("adapter://dns/authoritative",("ZONE_CREATE","UPSERT","DELETE","PUBLISH","READBACK"),"DNS"))
    r.register(DomainAdapterContract("adapter://tls/acme",("ISSUE","RENEW","REVOKE","READBACK"),"TLS"))
    r.register(DomainAdapterContract("adapter://ingress/http",("BIND","UNBIND","HEALTH","READBACK"),"INGRESS"))
    return r
