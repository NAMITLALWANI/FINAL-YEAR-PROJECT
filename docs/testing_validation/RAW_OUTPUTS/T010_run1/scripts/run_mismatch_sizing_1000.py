"""Larger run of the realistic-mismatch sizing simulation (1000 replications) to tighten the Monte Carlo error. Run from backend/."""
import json
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "scripts")
sys.path.insert(0, ".")
import validate_methodology_by_simulation as v
print(json.dumps(v.simulate_sizing(1000, 777, "beta_3_20"), indent=1, sort_keys=True))
