# T018: claim-level check of five key references and the manuscript update

**Test ID:** T018 (run 1) | **Date:** 20 November 2026 | **Type:** literature verification (fetched text) and manuscript edit; static manuscript check | **Status:** PARTIAL: four sources supported, LAGOS-AND partly supported (its journal paper could not be read) | **The manuscript was edited; nothing was compiled.**

> T001 to T017 and all their raw outputs are preserved unchanged.

## 1. Question and reason
Whether the cited sources support the statements made about them (S2AND, WhoIsWho, CONNA, HUMO and r-HUMO, LAGOS-AND), and whether the manuscript reflects the final protocol and the work actually completed.

## 2. Method
A fetch agent read the arXiv abstract and HTML text (and the Zenodo record) and answered fixed questions; answers it marked as model summaries were not treated as verified. Results are in `paper/HAMMER_IEEE_PAPER/REFERENCE_VERIFICATION.md` (section "Claim-level check"). The manuscript edits were then applied and `check_manuscript.py` re-run.

## 3. Results
| Source | Verdict | Manuscript change |
|---|---|---|
| S2AND | supported | "often transfer poorly" became "may generalize poorly" (the paper says "may") |
| WhoIsWho | supported | Table I evidence and measures corrected to what the text shows |
| CONNA | supported with a caveat | joint training stated as joint fine-tuning by reinforcement learning after separate training |
| HUMO, r-HUMO | supported | none; evaluated on entity-resolution, not author-disambiguation, data (the text already says so) |
| LAGOS-AND | partly supported | block subset qualified; undocumented ORCID attribution method stated as unknown; the Wiley paper returned HTTP 403 and was not read |
Manuscript: Sections 1, 2, 5, 7 and 9 and the literature table updated; search procedure stated honestly (not systematic; not Scopus, Web of Science, Google Scholar, dblp or Semantic Scholar); year-range provenance added (T014); freeze, adopted parameters and pilot-draw counts added; Discussion and Conclusion written from supported content only; the Abstract remains a pending item by design. Static check: PASS (optional result tables are warnings).

## 4. Limitations
Only five sources were checked at claim level; the other entries remain at metadata or abstract level (see `REFERENCE_VERIFICATION.md`). The agent could not read some PDFs. LaTeX has not been compiled (no TeX installation).

## 5. Artifacts
`paper/HAMMER_IEEE_PAPER/REFERENCE_VERIFICATION.md`; the pre-edit sections are preserved outside the repository in the scratch directory and, for the earlier protocol edit, in `paper/HAMMER_IEEE_PAPER/_backup_before_final_protocol/`.
