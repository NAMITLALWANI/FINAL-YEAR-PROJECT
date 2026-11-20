# HAMMER IEEE paper (Overleaf project)

Canonical manuscript. One source only; do not maintain a parallel Word copy.

## Use in Overleaf
Upload `../HAMMER_IEEE_PAPER.zip` (New Project -> Upload Project), or copy this folder's contents. `main.tex` is the root file. Overleaf's TeX Live provides `IEEEtran.cls` and `IEEEtran.bst`, so no class file is vendored. Compiler: pdfLaTeX. Bibliography: BibTeX (the default Overleaf recipe runs it).

## Layout
`main.tex` · `references.bib` · `sections/01..09_*.tex` · `tables/` · `figures/` (`*.pdf` plus `make_figures.py`, the source that regenerates them; needs Python with matplotlib) · `REFERENCE_VERIFICATION.md` · `STAGE2_VERIFICATION_NOTES.md`.

## Status
| Part | State |
|---|---|
| Introduction, Related Work, Table I | Draft 1 (needs full-text confirmation, see REFERENCE_VERIFICATION.md) |
| Sections III-V | Draft 1 (Stage 2); three vector figures; TODO markers listed in STAGE2_VERIFICATION_NOTES.md |
| Abstract, Results, Discussion, Conclusion | Intentionally empty until the label audit and main evaluation exist |

## Deliberately absent
Conference name, dates, copyright block, ISBN, IEEE logo, funding or acknowledgement text, supervisor details.

## Checks that exist today
`python3 ../check_manuscript.py` verifies citation keys, labels, `\input` files, brace and environment balance. It is not a compile. **A real compile has not been run on this machine** (no LaTeX engine is installed); compile once in Overleaf and fix any warnings.
