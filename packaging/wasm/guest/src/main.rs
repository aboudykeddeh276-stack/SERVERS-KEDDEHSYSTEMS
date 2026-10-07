use serde::{Deserialize,Serialize};
use sha2::{Digest,Sha256};
use std::io::{self,Read};
#[derive(Deserialize)] struct Request { module_id:String, action:String, #[serde(default)] payload:serde_json::Value, #[serde(default)] state_root:Option<String>, #[serde(default)] phase_root:Option<String> }
#[derive(Serialize)] struct Response { status:&'static str, module_id:String, action:String, next_state_root:String, next_phase_root:String, receipt:serde_json::Value }
fn hash(parts:&[&str])->String { let mut h=Sha256::new(); for p in parts { h.update(p.as_bytes()); h.update([0]); } format!("{:x}",h.finalize()) }
fn main() {
 let mut input=String::new(); io::stdin().read_to_string(&mut input).expect("read request");
 let req:Request=serde_json::from_str(&input).expect("valid request json"); let payload=serde_json::to_string(&req.payload).expect("payload");
 let state=hash(&[&req.module_id,&req.action,&payload,req.state_root.as_deref().unwrap_or("")]);
 let phase=hash(&[&req.module_id,&state,req.phase_root.as_deref().unwrap_or("")]);
 let out=Response{status:"PASS",module_id:req.module_id.clone(),action:req.action.clone(),next_state_root:state.clone(),next_phase_root:phase.clone(),receipt:serde_json::json!({"schema":"keddeh.wasm-receipt/v1","module_id":req.module_id,"action":req.action,"state_root":state,"phase_root":phase,"claim":"deterministic adapter execution only; no deployment claim"})};
 println!("{}",serde_json::to_string(&out).expect("response"));
}
