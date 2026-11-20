# T020: compilation of the manuscript and page-by-page visual check

**Test ID:** T020 (run 1) | **Date:** 20 November 2026 | **Type:** LaTeX compile (tectonic 0.17.0) and visual inspection of all 22 pages | **Status:** PASS with documented warnings | **Network use: download of the official tectonic release and its TeX support files only.**

> T001 to T019 and all their raw outputs are preserved unchanged.

## 1. Question and reason
The manuscript had never been compiled. Does it compile, with every citation and reference resolved, and does every page render without clipping, overlap or placeholder artefacts?

## 2. Method
Tectonic 0.17.0 (official Apple-silicon release, archive SHA-256 `a3f1cac7c5678f01661a92212f58480ae3b0634115d880dbc59e2953ded45667`, installed in a scratch directory with the user's consent) compiled `main.tex` from an unzipped copy of `paper/HAMMER_IEEE_PAPER.zip` (IEEEtran conference class, A4, BibTeX). All 22 pages were rendered to images and read.

## 3. Results
| Check | Result |
|---|---|
| Compile | succeeds; 22 pages (two-column) |
| Undefined citations or references | **0** |
| Overfull boxes | one of 3.8 pt in a table header (imperceptible) after the fixes below; two larger ones (11.6 pt and 31 pt) were fixed |
| Visual defects found by the check | (1) the full-protocol retrieval table (single column) overlapped the right column: now a full-width float; (2) `K=\tbd{...}` inside math mode printed as italic "tobeconfirmedinthepilot": replaced by `K=10` with its status stated; (3) cramped Table VI header: shortened; (4) an inaccurate freeze-history sentence in Section V corrected |
| Static checker | PASS (optional protocol result tables are warnings) |
| Remaining visible placeholders | red items for values that depend on people or on a confirmatory run (reviewer arrangements, audit size, $m'$) and the four pending protocol-result tables: intended |

## 4. Known rendering limitation
Tectonic substitutes fonts and lacks bold and bold-italic shapes for the Times text font, so run-in bold headings (for example in the Discussion) print in regular weight and the compiler logs font-shape warnings. This is an artefact of this engine, not of the source; Overleaf's pdfLaTeX with IEEEtran will render them bold. Page breaks may also differ slightly there.

## 5. Interpretation and limitations
The source compiles cleanly and every page was inspected. The compiled PDF is a proof of compilation and a visual check, not a camera-ready file. No venue is selected, so no venue-specific formatting rules were checked. At 22 pages the paper is longer than typical conference limits; shortening (for example moving Sections V-D to V-K detail to an appendix) is a venue decision.

## 6. Artifacts
`RAW_OUTPUTS/T020_run1/`: `main.log`, `tectonic_install.txt`, `check_manuscript.txt`. Compiled PDF: `paper/HAMMER_IEEE_PAPER.pdf`.
