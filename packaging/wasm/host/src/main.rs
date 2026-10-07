use anyhow::{bail,Context,Result};
use clap::Parser; use serde::Deserialize; use sha2::{Digest,Sha256};
use std::{fs,path::{Path,PathBuf},process::{Command,Stdio}};
#[derive(Parser)] struct Args { #[arg(long)] package:PathBuf, #[arg(long)] request:PathBuf, #[arg(long)] allow_unpinned:bool }
#[derive(Deserialize)] struct Package { schema_version:String,module_id:String,artifact:String,sha256:Option<String>,abi:String,wit_world:String,entry_protocol:String,preopens:Vec<Preopen>,network:String }
#[derive(Deserialize)] struct Preopen { host:String,guest:String,mode:String }
fn sha256(path:&Path)->Result<String>{ let bytes=fs::read(path).with_context(||format!("read {}",path.display()))?; Ok(format!("{:x}",Sha256::digest(bytes))) }
fn main()->Result<()>{
 let a=Args::parse(); let base=a.package.parent().unwrap_or(Path::new(".")); let p:Package=serde_json::from_slice(&fs::read(&a.package)?)?;
 if p.schema_version!="keddeh.wasm-package/v1"||p.abi!="wasi-preview1-command+wit-contract"||p.entry_protocol!="stdin-request/stdout-receipt-json-v1"||p.wit_world!="keddeh:runtime/keddeh-module@1.0.0"{bail!("package contract mismatch");}
 if p.network!="none"{bail!("network requires a separately reviewed host mediator");}
 let artifact=base.join(&p.artifact).canonicalize().context("canonical artifact")?; let actual=sha256(&artifact)?;
 match p.sha256{Some(ref expected) if expected==&actual=>{},Some(_)=>bail!("artifact sha256 mismatch"),None if !a.allow_unpinned=>bail!("unpinned artifact rejected"),None=>{}}
 let request=fs::File::open(&a.request)?; let mut cmd=Command::new("wasmtime"); cmd.arg("run");
 for mount in &p.preopens{let host=PathBuf::from(&mount.host).canonicalize().with_context(||format!("preopen {}",mount.host))?;if mount.mode!="ro"&&mount.mode!="rw"{bail!("invalid preopen mode");}cmd.arg("--dir").arg(format!("{}::{}",host.display(),mount.guest));}
 let status=cmd.arg(&artifact).env_clear().env("KEDDEH_MODULE_ID",&p.module_id).stdin(Stdio::from(request)).stdout(Stdio::inherit()).stderr(Stdio::inherit()).status().context("start wasmtime")?;
 if !status.success(){bail!("guest exited {}",status);} Ok(())
}
