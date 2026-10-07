#!/usr/bin/env python3
import argparse,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument("--output",required=True);a=p.parse_args();out=Path(a.output).resolve()
if out==ROOT or ROOT in out.parents: raise SystemExit("output must be outside the source repository")
if out.exists(): shutil.rmtree(out)
(out/"workspace").mkdir(parents=True);(out/"primitives").mkdir()
for name in ("index.html","app.js","styles.css","document.seed.json","model.schema.json"):
 shutil.copy2(ROOT/"worktrees/authoring-surface"/name,out/"workspace"/name)
for src in (ROOT/"worktrees/primitives").iterdir():
 if src.name=="registry.json":shutil.copy2(src,out/"primitives"/src.name)
 elif src.is_dir():shutil.copytree(src,out/"primitives"/src.name)
print(out)
