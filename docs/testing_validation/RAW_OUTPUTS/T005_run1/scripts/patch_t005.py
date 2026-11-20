"""T005 patch of backend/hammer_pilot/metrics_c7.py: applies the four director clarifications of 20 November 2026 (run from backend/)."""
p = "hammer_pilot/metrics_c7.py"
s = open(p, encoding="utf-8").read()


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:70], s.count(old))
    s = s.replace(old, new)


sub('''  - the audit label error is derived from adjudicated records (impure group, false mapping, missed mapping), never supplied as a flag.
''', '''  - the audit label error is derived from adjudicated records (impure group, false mapping, missed mapping), never supplied as a flag.
Clarifications applied (director, 20 November 2026; test record T005):
  - group-purity states are pure, impure and unresolved; a pure group whose case label is unresolved is indeterminate, not consistent;
  - benchmark-group validity (Stage A) is kept apart from case-level candidate verification: an uncertain or unverifiable case is outside the
    definite-label audit error-rate denominator even if its group is impure; group impurity is reported separately and the bracket is preserved;
  - overall benchmark-derived retrieval keeps all N primary cases and is never adjusted by any audit or verified result;
  - conditional verified retrieval uses the cases with a verified-same candidate in the R2 pool; every other judgment category is reported separately.
''')

sub('PURITY = ("pure", "impure", "cannot_tell")', 'PURITY = ("pure", "impure", "unresolved")')
sub("# Stage A group-purity judgment of the benchmark group: pure / impure / cannot_tell", "# Stage A group-purity judgment of the benchmark group: pure / impure / unresolved")

# verified retrieval: report every judgment category separately
sub("    used_outcomes: Counter = Counter()\n", "    used_outcomes: Counter = Counter()\n    categories: Counter = Counter()\n")
sub('''            used.append((same, either))
            used_outcomes[c.outcome] += 1
''', '''            used.append((same, either))
            used_outcomes[c.outcome] += 1
            categories["empty_pool" if not c.pool_ids else "verified_same_in_pool" if same else "cannot_tell_only" if either else "verified_no_match"] += 1
            if same and any(x == "cannot_tell" for x in j.values()):
                categories["verified_same_with_cannot_tell_candidates"] += 1
''')
sub('''"case_counts": counts, "outcomes_of_cases_used"''', '''"case_counts": counts,
                           "judgment_categories": {k: categories[k] for k in ("verified_same_in_pool", "cannot_tell_only", "verified_no_match", "empty_pool",
                                                                              "verified_same_with_cannot_tell_candidates")},
                           "judgment_categories_note": "the conditional denominator is verified_same_in_pool; every other category is reported here and is outside it "
                                                       "(verified_same_with_cannot_tell_candidates is a subset of verified_same_in_pool)",
                           "outcomes_of_cases_used"''')

# audit: rewrite audit_status and audit_label_error
a = s.index("def audit_status(")
b = s.index("# --------------------------------------------------------------------------- top-level report")
block = '''def audit_status(case: Case) -> tuple[str, list[str], str | None]:
    """(status, reasons, indeterminate_reason). Status: contradicted, consistent, indeterminate or unverified.

    Benchmark-group validity (Stage A) is kept apart from case-level candidate verification:
      - an uncertain or unverifiable case is outside the definite-label denominator (indeterminate), whatever its group purity; its impurity is
        reported separately by `group_validity`;
      - for a definite case, an impure group is a contradiction; so are a false mapping and a missed mapping;
      - an unresolved group purity, or a pure group whose case label is unresolved, is indeterminate (never consistent);
      - a cannot-tell judgment on a mapped candidate, or a missing judgment for some pool candidate, is indeterminate."""
    if case.label_state is None:
        return "unverified", [], None
    if case.label_state in ("uncertain", "unverifiable"):
        return "indeterminate", [], f"label_{case.label_state}"
    if case.group_purity is None:
        raise C7Error(f"{case.case_id}: an audited case with a definite label needs a Stage A group-purity judgment")
    reasons = audit_reasons(case)
    if reasons:
        return "contradicted", reasons, None
    if case.group_purity == "unresolved":
        return "indeterminate", [], "purity_unresolved"
    if case.label_state == "unresolved":
        return "indeterminate", [], "label_unresolved_pure_group"
    j = case.pool_judgments or {}
    if any(j.get(i) == "cannot_tell" for i in case.pool_ids if i in case.mapped_ids):
        return "indeterminate", [], "mapped_candidate_cannot_tell"
    if case.pool_ids and set(j) != set(case.pool_ids):
        return "indeterminate", [], "incomplete_stage_b"      # consistency cannot be established without every candidate judged
    return "consistent", [], None


def audit_label_error(primary: Sequence[Case]) -> dict[str, Any]:
    """Audit label-error rate over the audited non-automatic sample, derived from adjudicated records. Each affected case counts once in the numerator.

    The rate uses definite-label cases only (contradicted or consistent). Indeterminate cases stay visible and bracketed. Group impurity is reported
    separately under `group_validity`, including impure groups whose case label is uncertain or unverifiable."""
    audited = [c for c in primary if c.audit_subset == "audit_sample"]
    rows = [(c, *audit_status(c)) for c in audited]
    n = Counter(status for _, status, _, _ in rows)
    reason_counts = Counter(r for _, status, reasons, _ in rows if status == "contradicted" for r in reasons)
    why = Counter(w for _, status, _, w in rows if status == "indeterminate")
    errors, consistent, indeterminate = n["contradicted"], n["consistent"], n["indeterminate"]
    total = errors + consistent + indeterminate
    purity = Counter(c.group_purity or "not_recorded" for c in audited)
    impure_by_label = Counter(c.label_state for c in audited if c.group_purity == "impure")
    return {"label_basis": VERIFIED, "population": "the sampled non-automatic frame of the primary pair only; not a correction factor, and not transferable",
            "audited": len(audited), "contradicted": errors, "consistent": consistent, "indeterminate": indeterminate, "unverified": n["unverified"],
            "definite": errors + consistent, "label_errors": errors, "error_rate": _rate(errors, errors + consistent),
            "reason_counts": {r: reason_counts[r] for r in AUDIT_REASONS},
            "reason_counts_note": "a case may have more than one reason, so reason counts can sum to more than label_errors; each case counts once in the numerator",
            "cases_with_more_than_one_reason": sum(1 for _, status, reasons, _ in rows if status == "contradicted" and len(reasons) > 1),
            "indeterminate_reasons": dict(sorted(why.items())),
            "group_validity": {"label_basis": VERIFIED,
                               "scope": "Stage A benchmark-group validity, reported separately from the definite-label audit error rate",
                               "purity_counts": {k: purity[k] for k in (*PURITY, "not_recorded")},
                               "impure_group_rate": _rate(purity["impure"], purity["pure"] + purity["impure"]),
                               "impure_by_label_state": {k: impure_by_label[k] for k in LABEL_STATES},
                               "impure_outside_definite_label_denominator": impure_by_label["uncertain"] + impure_by_label["unverifiable"]},
            "bracket": {"all_right": {"errors": errors, "denominator": total, "value": (errors / total) if total else None},
                        "all_wrong": {"errors": errors + indeterminate, "denominator": total, "value": ((errors + indeterminate) / total) if total else None}}}


'''
s = s[:a] + block + s[b:]

sub('''"Verified and benchmark-derived results are never combined into one figure.",''', '''"Verified and benchmark-derived results are never combined into one figure.",
                            "Overall benchmark-derived retrieval keeps all N primary cases and is never adjusted by any audit or verified result.",
                            "Benchmark-group validity (group impurity) is reported separately from the definite-label audit error rate.",''')
open(p, "w", encoding="utf-8").write(s)
print("patched; lines:", s.count("\n"))
