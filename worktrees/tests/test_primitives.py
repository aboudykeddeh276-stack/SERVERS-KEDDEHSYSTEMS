import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class PrimitiveTests(unittest.TestCase):
 def test_registry_is_complete(self):
  registry=json.loads((ROOT/"worktrees/primitives/registry.json").read_text())
  expected={"link","button","execution","heading","title","photo","container","name","claim","learning"}
  self.assertEqual({x["type"] for x in registry["primitives"]},expected)
  for ref in registry["primitives"]:
   manifest=json.loads((ROOT/ref["index"]).read_text())
   self.assertEqual(manifest["primitive"],ref["type"])
   self.assertTrue((ROOT/ref["module"]).is_file())
   self.assertTrue((ROOT/ref["stylesheet"]).is_file())
   self.assertFalse(manifest["security"]["arbitrary_eval"])
 def test_seed_references_are_closed(self):
  doc=json.loads((ROOT/"worktrees/authoring-surface/document.seed.json").read_text())
  ids={x["artifact_id"] for x in doc["artifacts"]}
  self.assertEqual(len(ids),len(doc["artifacts"]))
  for artifact in doc["artifacts"]:
   self.assertTrue(artifact["parent_id"] is None or artifact["parent_id"] in ids)
 def test_browser_has_no_eval_or_unsafe_html(self):
  app=(ROOT/"worktrees/authoring-surface/app.js").read_text()
  self.assertNotIn("eval(",app)
  self.assertNotIn(".innerHTML",app)
if __name__=="__main__":unittest.main()
