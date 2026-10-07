export function render(a){const n=Math.min(6,Math.max(2,Number(a.props.level)||2));const e=document.createElement("h"+n);e.className="k-heading";e.textContent=a.props.text||"Heading";return e;}
