"""Write the evaluation freeze manifest (new file only) or verify an existing one.

  python scripts/freeze_evaluation.py write --freeze-id F1 --parameters params.json --out freeze.json
  python scripts/freeze_evaluation.py verify --freeze freeze.json
Run from backend/. Refuses if any AUTHOR_*, ENABLE_AUTHOR_* or DEDUP_* environment variable is set."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from hammer_pilot import freeze as fz

FROZEN_FILES = [
    "backend/config.py", "backend/author_resolution/candidates.py", "backend/author_resolution/context.py", "backend/author_resolution/enrichment.py",
    "backend/author_resolution/enrichment_types.py", "backend/author_resolution/evidence.py", "backend/author_resolution/policy.py",
    "backend/author_resolution/resolver.py", "backend/author_resolution/scoring.py", "backend/author_resolution/schemas.py",
    "backend/hammer_pilot/capture.py", "backend/hammer_pilot/replay.py", "backend/hammer_pilot/pipeline.py", "backend/hammer_pilot/common.py",
    "backend/hammer_pilot/context_rules.py", "backend/hammer_pilot/selector_c1c.py", "backend/hammer_pilot/seeds_from_manifest.py",
    "backend/hammer_pilot/freeze.py", "backend/hammer_pilot/guarded_transport.py", "backend/scripts/capture_hammer_pilot.py", "backend/scripts/replay_hammer_pilot.py",
]


def effective_config():
    import config as c
    keys = ["AUTHOR_AUTO_SCORE_THRESHOLD", "AUTHOR_AUTO_MARGIN_THRESHOLD", "AUTHOR_AUTO_DOMINANCE_THRESHOLD", "AUTHOR_MANUAL_SCORE_THRESHOLD",
            "AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO", "AUTHOR_RESOLVER_VERSION", "AUTHOR_SCORING_VERSION", "AUTHOR_THRESHOLD_VERSION",
            "AUTHOR_SCORE_WEIGHTS", "ENABLE_AUTHOR_ENRICHMENT", "AUTHOR_ENRICHMENT_WORKS_PER_PAGE", "AUTHOR_ENRICHMENT_MAX_PAGES"]
    return {k: getattr(c, k) for k in keys}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write")
    w.add_argument("--freeze-id", required=True)
    w.add_argument("--parameters", type=Path, required=True)
    w.add_argument("--out", type=Path, required=True)
    v = sub.add_parser("verify")
    v.add_argument("--freeze", type=Path, required=True)
    a = ap.parse_args()
    repo = BACKEND.parent
    try:
        if a.cmd == "write":
            params = json.loads(a.parameters.read_text(encoding="utf-8"))
            m = fz.build_freeze(repo, a.freeze_id, FROZEN_FILES, effective_config(), params, os.environ)
            with open(a.out, "x", encoding="utf-8") as f:
                f.write(json.dumps(m, indent=1, sort_keys=True) + "\n")
            print(f"freeze {a.freeze_id}: wrote {a.out}; manifest sha256 {m['manifest_sha256']}; seeds {m['seeds']}")
            return 0
        problems = fz.verify_freeze(json.loads(a.freeze.read_text(encoding="utf-8")), repo)
        print("FREEZE VERIFIED: no differences" if not problems else "FREEZE BROKEN:\n  " + "\n  ".join(problems))
        return 0 if not problems else 2
    except (fz.FreezeError, FileExistsError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
