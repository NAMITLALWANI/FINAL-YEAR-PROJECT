# T014: reconciliation of the LAGOS-AND publication-year range

**Test ID:** T014 (run 1) | **Date:** 20 November 2026 | **Type:** independent read-only full scan of the archive | **Status:** PASS (discrepancy explained; manuscript value confirmed) | **No provider request; no name, ORCID or DOI printed.**

> T001 to T013 and all their raw outputs are preserved unchanged.

## 1. Question and reason
Two project documents give different publication-year ranges for the dataset: the schema inspection report says 1963 to 2022 and the sampling report and the manuscript say 1870 to 2022. A value must not be chosen by assumption.

## 2. Method
A new script (`RAW_OUTPUTS/T014_run1/scripts/year_range_scan.py`) streams every row of the verified archive through the project's own reader (`hammer_lagos.prep.open_csv_rows`), parses `pub_year` and prints only aggregate counts.

## 3. Environment
Python 3.12, git `6d31cbe`, dirty tree. Archive: `LAGOS-AND-BLOCK-TRIMMED.csv.tar.gz`, SHA-256 `a0ac028b8955fcb4c6797b9fe1f5602fef43b45424f4044d0108c4f7d4bb6840`. Script SHA-256 `a700b8748c65a9497ad8ece389887fa156d78ae3abbf98d827ae9faf642aede4`.

## 4. Results
| Quantity | Value |
|---|---|
| Rows read | 1,476,550 (matches the verified total) |
| Rows with a non-numeric year | 0 |
| Minimum and maximum year | **1870 and 2022** |
| Rows dated before 1963 | 45 (decades 1870: 1, 1890: 1, 1900: 2, 1910: 1, 1930: 2, 1940: 2, and the remainder in 1950 to 1962) |

## 5. Interpretation
The schema inspection report (19 November) read a bounded prefix of the file: 16,710 rows (8,376 + 3,836 + 4,498 by split flag). The 45 pre-1963 rows lie outside that prefix, so that report's 1963 to 2022 describes the prefix and not the archive. The full-archive range is 1870 to 2022, which is the value in the manuscript (Table dataset). The manuscript now states the provenance of the range.

## 6. Limitations
The scan confirms the recorded range; it does not assess whether the early years are correct publication years (a handful of rows before 1963 may be data errors in the benchmark; none is used specially).

## 7. Artifacts
`RAW_OUTPUTS/T014_run1/year_range_scan_output.txt`, `scripts/year_range_scan.py`.
