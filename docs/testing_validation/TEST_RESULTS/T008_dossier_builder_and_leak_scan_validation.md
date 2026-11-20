# T008: blinded dossier packet builder and leak scanner (Decision B)

**Test ID:** T008 (run 1) | **Date:** 20 November 2026 | **Type:** unit tests on synthetic fixtures plus an in-memory check against the real smoke payload shape; mutation sanity check | **Status:** PASS (25 tests; 12 of 12 mutants detected) | **No reviewer dossier was generated or saved, and no packet exists outside test memory and temporary test directories.**

> T001 to T007 and all their raw outputs are preserved unchanged.

## 1. Question and reason
Decision B requires allow-list packets, a hash-seeded shuffle, opaque identifiers, a separate crosswalk, identical presentation of automatic and audited cases, and a zero-match leak scan before release. T001 found that the real captured author objects carry the ORCID in `orcid`, `ids.orcid` and `observed_orcids`, plus identifiers and rank fields. Does the builder keep all of that out of reviewer-facing material by construction, and does the scanner catch a leak if the allow-list ever fails?

## 2. Expected behaviour
Stage A packets hold the printed query name and at most *K* group papers (the designated paper always included, others and order by hash), with only allow-listed fields. Stage B packets hold every pool candidate, allow-listed (names and variants, affiliation names with years, topics, works count, yearly counts, capped works list), in a hash-seeded order independent of provider order and rank, under opaque identifiers. The crosswalk and the automatic-versus-audit flags are returned separately and written to a different, non-nested directory. The scanner reports no ORCID-shaped string or orcid.org URL, no OpenAlex author identifier or URL, no key suggesting rank, score, selection, policy, ORCID or the provider profile, and no supplied gold value; a packet is released only on zero findings, and a hand edit after release is detectable.

## 3. Environment
Python 3.12.5, pytest 8.4.2, git `6d31cbe`, dirty tree (untracked files only; nothing staged or committed). SHA-256: `backend/hammer_pilot/dossier.py` `356d96bc5eb6085cd268f03cb56dfe79a1ff1c340a6a2ab0e8c362f5b6f9e618` (201 lines); `backend/tests/test_dossier.py` `b0ae1598fdf6f223197c0092ce3030596466e1b43df40030afe27e4fe9dbc1fe` (239 lines).

## 4. Data
Synthetic papers and OpenAlex-like author objects with an invented ORCID-shaped string injected into every field the real payload uses (`orcid`, `observed_orcids`, `ids.orcid`, works authorships), plus unknown future fields. One test builds Stage B packets **in memory** for all 50 smoke cases from the real captured bodies and checks them against the 50 gold ORCIDs read in memory. No packet was written to disk, no ORCID printed. *K*, the works cap and the seed are required arguments (test values only).

## 5. Procedure and commands
`PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+aiosqlite:///:memory: .venv/bin/python -m pytest tests/test_dossier.py -p no:cacheprovider -v --no-header` (from `backend/`); mutation check `RAW_OUTPUTS/T008_run1/scripts/mutate_t008.py`.

## 6. Results
| Check | Expected | Actual |
|---|---|---|
| `test_dossier.py` | all pass | **25 passed**, 0.76 s |
| Real smoke payloads, in memory | allow-listed packets contain no gold ORCID | raw candidate objects contain the gold ORCID (hit count above zero); the packets contain **0** gold values and **0** scan findings; candidate count equals the recorded R2 pool total (306) |
| Deny-list control | a naive deny-list would still leak | a payload with only `orcid` and `ids` removed still fails the scan; the allow-list passes |
| Scanner positive controls | each leak type found | 10 of 10 (ORCID pattern, orcid.org URL, OpenAlex URL, OpenAlex id, and six forbidden keys) |
| Adversarial display name carrying an ORCID | blocked by the scan although the field is allow-listed | `LeakFound` raised |
| Packet form of automatic and audited cases | identical; queue independent of case origin | identical key sets; queue order is a function of the hash only |
| Release layout | reviewer directory holds packets and scan reports only; crosswalk and flags elsewhere; nested or overwriting use refused; edited packet refused | as expected; no ORCID or provider id in any reviewer file |
| Mutants S1 to S12 | each detected | **12 of 12** |

Mutants: ORCID field copied into the allow-list; designated paper not forced; provider order kept; *K* ignored; forbidden-key scan off; ORCID-pattern scan off; hand-edit check always true; crosswalk written to the reviewer directory; works cap ignored; opaque id built from the provider id; release gate bypassed; gold-value scan off.

## 7. Interpretation
For the real payload shape, the allow-list removes every gold ORCID that the raw objects carry, and the scanner is a second, independent barrier with demonstrated sensitivity. This is evidence that **the builder satisfies B3 on the smoke payloads and on adversarial fixtures**. It does not cover a field the provider might add in a different form that the allow-list copies (an allow-listed display name is scanned, but only for the listed patterns), and it does not address residual leakage through reviewers' own external searches.

## 8. Limitations and points for the director
- The candidate-works capture (B2c) does not exist, so works lists are untested against a real payload (synthetic only).
- The OpenAlex id pattern is deliberately limited to author ids (`A` plus 8 to 11 digits) to avoid false positives on DOIs; other id types are caught only as URLs.
- Stage A fields come from the benchmark row columns; their exact use (for example whether to show author affiliation strings in full) is an open item (B-O9, B-O10).
- Written release does not prove independence of the person who holds the crosswalk; that is a personnel matter (deferred).

## 9. Artifacts
`RAW_OUTPUTS/T008_run1/`: `pytest_test_dossier_verbose.txt`, `mutation_check_t008.txt`, `scripts/mutate_t008.py`. Hashes: `RAW_OUTPUTS/SHA256SUMS.txt`.
