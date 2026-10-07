import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("kidx",ROOT/"packaging/bin/keddeh-index.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)
class IndexTests(unittest.TestCase):
 def test_complete_index(self):
  result=MOD.validate(ROOT); self.assertEqual(result["status"],"PASS"); self.assertEqual(result["module_count"],16); self.assertEqual(len(result["aggregate_sha256"]),64)
 def test_every_module_has_wasm_contract(self):
  runtime=json.loads((ROOT/"packaging/runtime.index.json").read_text())
  for ref in runtime["modules"]:
   m=json.loads((ROOT/ref["index"]).read_text()); self.assertEqual(m["wasm"]["world"],"keddeh:runtime/keddeh-module@1.0.0"); self.assertNotEqual(m["evidence"]["state_root_path"],m["evidence"]["phase_root_path"]); self.assertNotEqual(m["evidence"]["generator_id"],m["evidence"]["verifier_id"])
 def test_network_is_explicit(self):
  runtime=json.loads((ROOT/"packaging/runtime.index.json").read_text())
  for ref in runtime["modules"]:
   m=json.loads((ROOT/ref["index"]).read_text())
   if m["network"]["listen"]: self.assertFalse(m["execution"]["activation_default"])
if __name__=="__main__": unittest.main()
