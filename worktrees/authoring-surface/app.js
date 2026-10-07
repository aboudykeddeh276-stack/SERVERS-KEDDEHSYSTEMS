const ROOT="../primitives/";
const els={canvas:document.querySelector("#canvas"),add:document.querySelector("#add-artifact"),palette:document.querySelector("#palette"),paletteGrid:document.querySelector("#palette-grid"),inspector:document.querySelector("#inspector"),editor:document.querySelector("#code-editor"),title:document.querySelector("#inspector-title"),meta:document.querySelector("#artifact-meta"),mode:document.querySelector("#mode-label"),toast:document.querySelector("#toast")};
let registry,doc,selected=null,admin=false,remote=false,etag=null;
const modules=new Map();
const SAFE_STYLE=new Set(["background-color","color","padding","margin","border","border-radius","max-width","min-height","text-align","gap","grid-template-columns"]);
function applyStyle(node,style){for(const [key,value] of Object.entries(style||{})){if(SAFE_STYLE.has(key)&&typeof value==="string"&&!/url\\s*\\(/i.test(value))node.style.setProperty(key,value);}}
const clone=v=>structuredClone(v);
const uid=t=>t+"-"+crypto.randomUUID();
function toast(m){els.toast.textContent=m;els.toast.classList.add("show");setTimeout(()=>els.toast.classList.remove("show"),1800);}
function audit(op,id,before,after){doc.audit??=[];doc.audit.push({event_id:crypto.randomUUID(),observed_at:new Date().toISOString(),actor:remote?"authenticated-admin":"local-draft",operation:op,artifact_id:id,before_revision:before?.revision??null,after_revision:after?.revision??null});}
async function loadModule(type){
 if(modules.has(type))return modules.get(type);
 const def=registry.primitives.find(x=>x.type===type);if(!def)throw new Error("Unknown primitive "+type);
 if(!document.querySelector('link[data-primitive="'+type+'"]')){const css=document.createElement("link");css.rel="stylesheet";css.href=ROOT+type+"/style.css";css.dataset.primitive=type;document.head.append(css);}
 const mod=await import(ROOT+type+"/render.js");modules.set(type,mod);return mod;
}
function childrenOf(id){return doc.artifacts.filter(x=>x.parent_id===id).sort((a,b)=>a.order-b.order);}
async function shellFor(a){
 const mod=await loadModule(a.type);const shell=document.createElement("div");shell.className="artifact-shell";shell.dataset.artifactId=a.artifact_id;
 applyStyle(shell,a.style);const badge=document.createElement("span");badge.className="artifact-badge";badge.textContent=a.type+" · r"+a.revision;
 const rendered=mod.render(a);shell.append(rendered,badge);
 shell.addEventListener("click",e=>{if(!admin)return;e.stopPropagation();select(a.artifact_id);});
 const slot=rendered.querySelector("[data-child-slot]");
 if(slot)for(const child of childrenOf(a.artifact_id))slot.append(await shellFor(child));
 return shell;
}
async function render(){
 els.canvas.replaceChildren();document.body.classList.toggle("admin",admin);els.add.hidden=!admin;els.mode.textContent=admin?(remote?"Authenticated admin":"Local draft"):"Read only";
 const roots=childrenOf(null);if(!roots.length){const e=document.createElement("div");e.className="empty";e.textContent="No artifacts yet.";els.canvas.append(e);}
 for(const a of roots)els.canvas.append(await shellFor(a));
 if(selected)document.querySelector('[data-artifact-id="'+CSS.escape(selected)+'"]')?.classList.add("selected");
 localStorage.setItem("keddeh.editable-document",JSON.stringify(doc));
}
function editable(a){return {artifact_id:a.artifact_id,type:a.type,parent_id:a.parent_id,order:a.order,revision:a.revision,props:a.props,style:a.style??{},behavior:a.behavior??{}};}
function select(id){
 selected=id;const a=doc.artifacts.find(x=>x.artifact_id===id);if(!a)return;
 els.title.textContent=a.type+" / "+a.artifact_id;els.editor.value=JSON.stringify(editable(a),null,2);
 els.meta.replaceChildren();const rows=[["Identity",a.artifact_id],["Revision",String(a.revision)],["Child artifacts",String(childrenOf(id).length)]];for(const [k,v] of rows){const dt=document.createElement("dt");dt.textContent=k;const dd=document.createElement("dd");dd.textContent=v;els.meta.append(dt,dd);}const dt=document.createElement("dt");dt.textContent="Raw stack";const dd=document.createElement("dd");for(const file of ["primitive.index.json","render.js","style.css"]){const link=document.createElement("a");link.href=ROOT+a.type+"/"+file;link.target="_blank";link.rel="noopener";link.textContent=file;dd.append(link,document.createTextNode(" "));}els.meta.append(dt,dd);
 els.inspector.hidden=false;render();
}
function validateArtifact(a){
 if(!a||typeof a!=="object")throw Error("Artifact must be an object");
 if(!registry.primitives.some(x=>x.type===a.type))throw Error("Unknown type");
 if(typeof a.artifact_id!=="string"||!a.artifact_id)throw Error("Missing artifact_id");
 if(!Number.isInteger(a.revision)||a.revision<1)throw Error("Invalid revision");
 if(typeof a.props!=="object"||Array.isArray(a.props))throw Error("props must be an object");
 return a;
}
function defaultArtifact(type,parent_id=null){
 const base={artifact_id:uid(type),type,parent_id,order:Date.now(),revision:1,props:{},style:{},behavior:{}};
 const props={link:{text:"New link",href:"/",target:"_self"},button:{label:"New button",action_id:"none"},execution:{label:"Run action",action_id:"none",input:{}},heading:{text:"New heading",level:2},title:{text:"New title",eyebrow:"KEDDEH"},photo:{src:"",alt:"Describe this image",caption:""},container:{label:"New container",layout:"stack"},name:{name:"New name",description:""},claim:{claim:"New claim",basis:"Attach evidence.",status:"draft"},learning:{learning:"New learning",source:"",confidence:0}};base.props=props[type];return base;
}
async function connectAdmin(){
 try{const r=await fetch("/api/document",{credentials:"same-origin",headers:{"Accept":"application/json"}});if(!r.ok)throw Error(String(r.status));doc=await r.json();etag=r.headers.get("ETag");remote=true;admin=true;toast("Authenticated admin connected");await render();}
 catch{toast("Admin API unavailable; use local draft for non-production editing");}
}
async function saveRemote(){
 if(!remote)return;const r=await fetch("/api/document",{method:"PUT",credentials:"same-origin",headers:{"Content-Type":"application/json","If-Match":etag||""},body:JSON.stringify(doc)});
 if(r.status===412)throw Error("Revision conflict: reload before saving");if(!r.ok)throw Error("Production save rejected: "+r.status);etag=r.headers.get("ETag");doc=await r.json();
}
function exportDoc(){const b=new Blob([JSON.stringify(doc,null,2)+"\n"],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=doc.document_id+"-r"+doc.revision+".json";a.click();URL.revokeObjectURL(a.href);}
document.querySelector("#admin-control").onclick=connectAdmin;
document.querySelector("#local-draft").onclick=async()=>{admin=true;remote=false;toast("Local draft enabled");await render();};
els.add.onclick=()=>els.palette.hidden=false;
for(const def of (registry=await fetch(ROOT+"registry.json").then(r=>r.json())).primitives){const b=document.createElement("button");b.textContent=def.type;b.onclick=()=>{const parent=selected&&doc.artifacts.find(x=>x.artifact_id===selected)?.type==="container"?selected:null;const a=defaultArtifact(def.type,parent);doc.artifacts.push(a);audit("create",a.artifact_id,null,a);selected=a.artifact_id;els.palette.hidden=true;render().then(()=>select(a.artifact_id));};els.paletteGrid.append(b);}
document.querySelectorAll("[data-close]").forEach(b=>b.onclick=()=>document.querySelector("#"+b.dataset.close).hidden=true);
document.querySelector("#apply-code").onclick=async()=>{try{const next=validateArtifact(JSON.parse(els.editor.value));const i=doc.artifacts.findIndex(x=>x.artifact_id===selected);if(i<0)throw Error("Artifact missing");const before=clone(doc.artifacts[i]);next.artifact_id=before.artifact_id;next.revision=before.revision+1;doc.artifacts[i]=next;doc.revision++;audit("update",selected,before,next);await saveRemote();toast("Revision applied");await render();select(selected);}catch(e){toast(e.message);}};
document.querySelector("#duplicate-artifact").onclick=async()=>{const a=doc.artifacts.find(x=>x.artifact_id===selected);if(!a)return;const n=clone(a);n.artifact_id=uid(a.type);n.revision=1;n.order=Date.now();doc.artifacts.push(n);doc.revision++;audit("duplicate",n.artifact_id,null,n);selected=n.artifact_id;await saveRemote();await render();select(selected);};
document.querySelector("#delete-artifact").onclick=async()=>{const ids=new Set([selected]);let changed=true;while(changed){changed=false;for(const a of doc.artifacts)if(ids.has(a.parent_id)&&!ids.has(a.artifact_id)){ids.add(a.artifact_id);changed=true;}}const before=doc.artifacts.filter(x=>ids.has(x.artifact_id));doc.artifacts=doc.artifacts.filter(x=>!ids.has(x.artifact_id));doc.revision++;audit("delete-tree",selected,before,null);selected=null;els.inspector.hidden=true;await saveRemote();await render();};
document.querySelector("#export-document").onclick=exportDoc;
document.addEventListener("keddeh-action",e=>{const a=e.detail;if(a.action_id==="export-document")exportDoc();else toast("Execution request: "+a.action_id);});
document.querySelector("#import-document").onclick=()=>document.querySelector("#import-file").click();
document.querySelector("#import-file").onchange=async e=>{try{const next=JSON.parse(await e.target.files[0].text());if(next.schema_version!=="keddeh.editable-document/v1"||!Array.isArray(next.artifacts))throw Error("Invalid document schema");next.artifacts.forEach(validateArtifact);doc=next;admin=true;remote=false;toast("Imported into local draft");await render();}catch(err){toast(err.message);}};
const saved=localStorage.getItem("keddeh.editable-document");doc=saved?JSON.parse(saved):await fetch("./document.seed.json").then(r=>r.json());await render();
