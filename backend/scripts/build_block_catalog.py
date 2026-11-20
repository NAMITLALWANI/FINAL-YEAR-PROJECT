"""Build the block catalog JSON (block -> groups, size, split, case-eligible groups) from the verified LAGOS-AND archive, using the existing streaming
reader (hammer_lagos.prep). Reads the archive only and writes the catalog to a new file. The catalog contains benchmark ORCIDs: treat it as PROTECTED. It makes no provider request."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

from hammer_pilot.selector_c1c import catalog_from_archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="new JSON file; refuses to overwrite")
    args = parser.parse_args()
    catalog = catalog_from_archive(args.archive)            # strict: the recorded size and MD5 of the LAGOS-AND archive must match
    with open(args.out, "x", encoding="utf-8") as f:
        f.write(json.dumps(catalog, sort_keys=True) + "\n")
    print(f"catalog of {len(catalog)} blocks written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
