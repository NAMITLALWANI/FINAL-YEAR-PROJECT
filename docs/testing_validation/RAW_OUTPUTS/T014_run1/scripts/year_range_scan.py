"""T014: independent full-archive scan of pub_year (read-only; prints aggregate counts only, no names, ORCIDs or DOIs)."""
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "backend"))
from hammer_lagos import prep

ARCHIVE = Path(sys.argv[1])
cols = prep.SOURCE_COLUMNS
iy = cols.index("pub_year")
n = 0; invalid = 0; lo, hi = 10**9, -1
decade = Counter()
below_1963 = 0
for rownum, row in prep.open_csv_rows(ARCHIVE):
    n += 1
    v = row[iy]
    if v.isdigit():
        y = int(v); lo = min(lo, y); hi = max(hi, y); decade[y // 10 * 10] += 1
        if y < 1963: below_1963 += 1
    else:
        invalid += 1
print(f"rows={n} invalid_year_rows={invalid} min_year={lo} max_year={hi} rows_before_1963={below_1963}")
for d in sorted(decade)[:6]: print(f"decade {d}: {decade[d]}")
