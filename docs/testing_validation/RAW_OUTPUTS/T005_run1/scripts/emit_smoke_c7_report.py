"""Emit the C7 report for the smoke capture as a TOOLING CHECK (census stand-in frame; not a probability sample; not performance)."""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, ".")
sys.path.insert(0, "tests")
import test_metrics_c7_smoke as t
from hammer_pilot import metrics_c7 as m
fx = t.smoke
get = getattr(fx, "_get_wrapped_function", None) or getattr(fx, "__wrapped__")
smoke = get()()
cases = t.build(smoke)                      # every case treated as primary with its own block id (arithmetic check only)
report = m.evaluate_primary(cases, t.census_frame(cases), seed=1)
sys.stdout.write(m.to_json(report))
