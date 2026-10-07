const SAFE=new Set(["http:","https:","mailto:","tel:"]);
function href(value){try{const u=new URL(value,location.origin);return (u.origin===location.origin||SAFE.has(u.protocol))?u.href:"#";}catch{return "#";}}
export function render(a){const e=document.createElement("a");e.className="k-link";e.textContent=a.props.text||"Link";e.href=href(a.props.href||"#");e.target=a.props.target==="_blank"?"_blank":"_self";if(e.target==="_blank")e.rel="noopener noreferrer";return e;}
