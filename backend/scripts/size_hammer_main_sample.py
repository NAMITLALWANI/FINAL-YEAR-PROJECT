"""Offline stratified predictive sizing of Decision C9 from a JSON input file. Reads no data, makes no provider request, draws no sample.

The input file must supply every parameter explicitly (no defaults): frame (post-exclusion stratum sizes), floors, pilot counts per stratum, m_prime, beta,
gamma and n_max (optionally m). The output is a planning calculation and freezes nothing. The output file must not already exist."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

from hammer_pilot.sizing_c9 import SizingError, size_sample

REQUIRED = ("frame", "floors", "pilot", "m_prime", "beta", "gamma", "n_max")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="new JSON file; refuses to overwrite")
    args = parser.parse_args()
    spec = json.loads(args.inputs.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if k not in spec]
    if missing:
        print(f"missing required inputs (no defaults are provided): {missing}", file=sys.stderr)
        return 2
    try:
        result = size_sample(spec["frame"], spec["floors"], spec["pilot"], m_prime=spec["m_prime"], beta=spec["beta"], gamma=spec["gamma"],
                             n_max=spec["n_max"], m=spec.get("m"))
    except SizingError as exc:
        print(f"sizing refused: {exc}", file=sys.stderr)
        return 1
    with open(args.out, "x", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=1, sort_keys=True) + "\n")
    for key in ("primary_jeffreys", "sensitivity_uniform_prior", "sensitivity_lower_bound"):
        r = result[key]
        print(f"{key}: {r['status']}" + (f", N = {r['N']}, P = {r['probability_at_N']:.4f}" if r["N"] is not None else f" ({r.get('reason')})"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
