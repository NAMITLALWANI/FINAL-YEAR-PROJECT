"""Generate the Results tables of the paper from a C7 report JSON (and optionally a reviewer-agreement JSON). New files only; never edits the manuscript.

  python paper/HAMMER_IEEE_PAPER/tools/make_result_tables.py --report report.json --out-dir paper/HAMMER_IEEE_PAPER/tables_generated [--agreement agreement.json] [--draft]

Without --draft the script refuses to run while any protocol parameter in the report is still `unspecified`."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
sys.dont_write_bytecode = True

from hammer_pilot.paper_tables import TableError, render_all


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--agreement", type=Path)
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    report = json.loads(a.report.read_text(encoding="utf-8"))
    agreement = json.loads(a.agreement.read_text(encoding="utf-8")) if a.agreement else None
    try:
        tables = render_all(report, draft=a.draft, agreement=agreement)
    except TableError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    a.out_dir.mkdir(parents=True, exist_ok=False)
    for name, text in tables.items():
        with open(a.out_dir / name, "x", encoding="utf-8") as f:
            f.write(text)
    print(f"wrote {len(tables)} tables to {a.out_dir}" + (" (DRAFT)" if a.draft else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
