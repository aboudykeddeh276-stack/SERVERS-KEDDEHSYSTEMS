#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,tempfile,threading,time,uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
STATE=Path(os.environ.get("KEDDEH_AUTHORING_STATE","/var/lib/keddeh/authoring"))
DOC=STATE/"document.json"; AUDIT=STATE/"audit.jsonl"; SEED=Path(__file__).with_name("document.seed.json")
LOCK=threading.RLock()
def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def etag(v):return '"sha256:'+hashlib.sha256(canon(v)).hexdigest()+'"'
def atomic(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(dir=path.parent,prefix=path.name+".",text=True)
 try:
  with os.fdopen(fd,"w") as f:json.dump(value,f,sort_keys=True,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
  os.replace(name,path)
 finally:
  if os.path.exists(name):os.unlink(name)
def read_doc():
 STATE.mkdir(parents=True,exist_ok=True)
 if not DOC.exists():atomic(DOC,json.loads(SEED.read_text()))
 return json.loads(DOC.read_text())
def validate(d):
 if d.get("schema_version")!="keddeh.editable-document/v1" or not isinstance(d.get("artifacts"),list):raise ValueError("invalid document")
 ids=set()
 for a in d["artifacts"]:
  identity=a.get("artifact_id")
  if not isinstance(identity,str) or not identity or identity in ids:raise ValueError("invalid or duplicate artifact_id")
  ids.add(identity)
  if a.get("type") not in {"link","button","execution","heading","title","photo","container","name","claim","learning"}:raise ValueError("unknown artifact type")
  if not isinstance(a.get("revision"),int) or a["revision"]<1:raise ValueError("invalid artifact revision")
  if not isinstance(a.get("props"),dict) or not isinstance(a.get("style"),dict) or not isinstance(a.get("behavior"),dict):raise ValueError("invalid artifact code stack")
 for a in d["artifacts"]:
  if a.get("parent_id") is not None and a["parent_id"] not in ids:raise ValueError("orphan artifact")
 return d
def append_audit(actor,before,after,phase,transaction_id):
 prev="0"*64
 if AUDIT.exists():
  lines=[x for x in AUDIT.read_text().splitlines() if x.strip()]
  if lines:prev=json.loads(lines[-1])["proof_root"]
 event={"observed_ns":time.time_ns(),"transaction_id":transaction_id,"phase":phase,"actor":actor,"before_etag":etag(before),"after_etag":etag(after),"previous_proof_root":prev}
 event["proof_root"]=hashlib.sha256(canon(event)).hexdigest()
 fd=os.open(AUDIT,os.O_APPEND|os.O_CREAT|os.O_WRONLY,0o640)
 try:os.write(fd,(json.dumps(event,sort_keys=True,separators=(",",":"))+"\n").encode());os.fsync(fd)
 finally:os.close(fd)
 return event["proof_root"]
class H(BaseHTTPRequestHandler):
 server_version="KEDDEH-Authoring/1"
 def admin(self):return self.headers.get("X-Keddeh-Auth-Verified")=="1" and bool(self.headers.get("X-Keddeh-Admin"))
 def send_json(self,code,payload,tag=None):
  body=json.dumps(payload,sort_keys=True).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(body)));self.send_header("Cache-Control","no-store")
  if tag:self.send_header("ETag",tag)
  self.end_headers();self.wfile.write(body)
 def do_GET(self):
  if self.path=="/health":self.send_json(200,{"status":"ok","service":"keddeh-authoring"});return
  if self.path!="/api/document":self.send_json(404,{"error":"not found"});return
  if not self.admin():self.send_json(401,{"error":"authenticated admin required"});return
  with LOCK:d=read_doc()
  self.send_json(200,d,etag(d))
 def do_PUT(self):
  if self.path!="/api/document":self.send_json(404,{"error":"not found"});return
  if not self.admin():self.send_json(401,{"error":"authenticated admin required"});return
  try:
   n=int(self.headers.get("Content-Length","0"))
   if n<2 or n>2_000_000:raise ValueError("invalid content length")
   incoming=validate(json.loads(self.rfile.read(n)));actor=self.headers["X-Keddeh-Admin"];tx=str(uuid.uuid4())
   with LOCK:
    current=read_doc()
    if self.headers.get("If-Match")!=etag(current):self.send_json(412,{"error":"revision conflict","current_etag":etag(current)});return
    if incoming.get("revision",0)<=current.get("revision",0):raise ValueError("document revision must advance")
    append_audit(actor,current,incoming,"PREPARED",tx)
    try:atomic(DOC,incoming)
    except Exception:
     append_audit(actor,current,current,"ABORTED",tx);raise
    append_audit(actor,current,incoming,"COMMITTED",tx)
   self.send_json(200,incoming,etag(incoming))
  except Exception as exc:self.send_json(400,{"error":str(exc)})
 def log_message(self,fmt,*args):print(json.dumps({"observed_ns":time.time_ns(),"remote":self.client_address[0],"message":fmt%args}))
if __name__=="__main__":
 STATE.mkdir(parents=True,exist_ok=True)
 ThreadingHTTPServer(("127.0.0.1",8787),H).serve_forever()
