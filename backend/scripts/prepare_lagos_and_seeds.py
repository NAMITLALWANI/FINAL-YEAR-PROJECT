"""Verify the LAGOS-AND v2.0 BLOCK-TRIMMED archive, sample complete blocks reproducibly and write the benchmark seed files.

Reads the archive by streaming; nothing is extracted into the repository; no network, no OpenAlex.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

from hammer_lagos.prep import prepare


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True, help="must not exist yet")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--target-cases", type=int, default=50)
    args = p.parse_args()
    if args.out_dir.exists():
        print("refusing to write into an existing directory")
        return 2
    manifest = prepare(args.archive, args.out_dir, seed=args.seed, target_cases=args.target_cases)
    print({"selected_cases": manifest["counts"]["selected_cases"], "selected_blocks": manifest["counts"]["selected_blocks"], "rows": manifest["counts"]["rows_total"]})
    return 0


if __name__ == "__main__":
    sys.exit(main())
