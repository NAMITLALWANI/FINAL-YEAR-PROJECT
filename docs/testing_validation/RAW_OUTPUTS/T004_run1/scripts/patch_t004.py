"""T004 patch of backend/hammer_pilot/metrics_c7.py: applies the five director rulings of 20 November 2026 (run from backend/)."""
p = "hammer_pilot/metrics_c7.py"
s = open(p, encoding="utf-8").read()


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:60], s.count(old))
    s = s.replace(old, new)


sub('''Open protocol parameters are never chosen silently:''', '''Rulings applied (director, 20 November 2026; recorded in the Decision C addendum and test record T004):
  - the pool for mapping and retrieval is the captured R2 (name-only) pool; R0 is descriptive only and is not an input here;
  - a ground-truth unresolved case (verified label_state "unresolved") is distinct from a HAMMER abstention (outcome manual, unresolved or no_score);
  - "no matching candidate" is claimed only when every candidate in the pool has a Stage B judgment and all are "different";
  - the audit label error is derived from adjudicated records (impure group, false mapping, missed mapping), never supplied as a flag.

Open protocol parameters are never chosen silently:''')

sub("import json\nimport math\nimport random\n", "import json\nimport math\nimport random\nfrom collections import Counter\n")
sub('AUDIT_SUBSETS = ("automatic", "audit_sample")\n',
    'AUDIT_SUBSETS = ("automatic", "audit_sample")\nPURITY = ("pure", "impure", "cannot_tell")\nAUDIT_REASONS = ("impure_group", "false_mapping", "missed_mapping")\n')

sub('    label_contradicted: bool | None = None    # adjudicated: does the verified label contradict the benchmark label\n',
    '    group_purity: str | None = None           # Stage A group-purity judgment of the benchmark group: pure / impure / cannot_tell\n')
sub('''        if self.selected_judgment is not None and self.selected_judgment not in JUDGMENTS:''',
    '''        if self.group_purity is not None:
            if self.group_purity not in PURITY:
                raise C7Error(f"{self.case_id}: group_purity {self.group_purity!r} is invalid")
            if self.label_state is None:
                raise C7Error(f"{self.case_id}: a group-purity judgment belongs to a verified case")
        if self.selected_judgment is not None and self.selected_judgment not in JUDGMENTS:''')

sub('''    if case.pool_judgments is not None and not any(j == "same" for j in case.pool_judgments.values()):
        return INCORRECT, "resolved_no_matching_candidate"   # definite identity, nobody in the pool is the person: stays in the denominator''',
    '''    if case.pool_judgments is not None and set(case.pool_judgments) == set(case.pool_ids) and all(j == "different" for j in case.pool_judgments.values()):
        return INCORRECT, "resolved_no_matching_candidate"   # every candidate judged, none is the person: stays in the denominator''')

a = s.index("def verified_retrieval(")
b = s.index("# --------------------------------------------------------------------------- top-level report")
new_block = '''def verified_retrieval(primary: Sequence[Case], subset: str, ks: Sequence[int] = (1, 5, 10)) -> dict[str, Any]:
    """Retrieval on verified labels for one subset, unweighted and descriptive. Candidates judged `cannot_tell` give lower and upper bounds.

    A ground-truth unresolved case (verified label_state "unresolved": no unique intended person) is excluded and counted. A HAMMER abstention
    (outcome manual, unresolved or no_score) is NOT a reason to exclude: such a case stays in retrieval evaluation if it is otherwise adjudicable.
    """
    if subset not in AUDIT_SUBSETS:
        raise C7Error(f"subset must be one of {AUDIT_SUBSETS}")
    members = [c for c in primary if c.audit_subset == subset]
    counts = {"in_subset": len(members), "unverified": 0, "uncertain_case": 0, "unverifiable_case": 0, "ground_truth_unresolved": 0, "incomplete_stage_b": 0}
    used: list[tuple[int | None, int | None]] = []          # (rank of first 'same', rank of first 'same' or 'cannot_tell')
    used_outcomes: Counter = Counter()
    for c in members:
        if c.label_state is None:
            counts["unverified"] += 1
        elif c.label_state in ("uncertain", "unverifiable"):
            counts[f"{c.label_state}_case"] += 1
        elif c.label_state == "unresolved":
            counts["ground_truth_unresolved"] += 1           # no intended person: retrieval of that person is undefined
        elif c.pool_ids and (c.pool_judgments is None or set(c.pool_judgments) != set(c.pool_ids)):
            counts["incomplete_stage_b"] += 1                # a miss cannot be claimed unless every candidate was judged
        else:
            j = c.pool_judgments or {}
            same = next((i for i, x in enumerate(c.pool_ids, 1) if j.get(x) == "same"), None)
            either = next((i for i, x in enumerate(c.pool_ids, 1) if j.get(x) in ("same", "cannot_tell")), None)
            used.append((same, either))
            used_outcomes[c.outcome] += 1
    n = len(used)
    counts["hammer_abstentions_included"] = sum(v for o, v in used_outcomes.items() if o in ("manual", "unresolved", "no_score"))
    mapped = [(a, b) for a, b in used if a]                   # M: cases with a verified-same candidate in the pool
    counts["indefinite_mapped_cases"] = sum(1 for a, b in used if not a and b)   # only cannot-tell candidates: outside M, but visible
    nm = len(mapped)
    out: dict[str, Any] = {"subset": subset, "label_basis": VERIFIED, "pool": "captured R2 (name-only) pool",
                           "weighting": "none: subset-specific, descriptive, never pooled with another subset or with benchmark-derived retrieval",
                           "exclusions": "only ground-truth unresolved cases (no unique intended person) and cases not yet verified or not definite; a HAMMER abstention is never an exclusion",
                           "case_counts": counts, "outcomes_of_cases_used": dict(sorted(used_outcomes.items())), "resolved_cases_used": n,
                           "mapping_rate": {"lower": _rate(sum(1 for lo, _ in used if lo), n), "upper": _rate(sum(1 for _, up in used if up), n)}}
    for k in ks:
        lo = sum(1 for a, _ in used if a and a <= k)
        up = sum(1 for _, b in used if b and b <= k)
        out[f"end_to_end_success_at_{k}"] = {"lower": _rate(lo, n), "upper": _rate(up, n), "indefinite_cases": up - lo}
    out["end_to_end_mrr"] = {"lower": (sum(1 / a for a, _ in used if a) / n) if n else None, "upper": (sum(1 / b for _, b in used if b) / n) if n else None, "denominator": n}
    for k in ks:
        out[f"conditional_recall_at_{k}"] = {"lower": _rate(sum(1 for a, _ in mapped if a <= k), nm), "upper": _rate(sum(1 for _, b in mapped if b <= k), nm), "denominator": nm}
    out["conditional_mrr"] = {"lower": (sum(1 / a for a, _ in mapped) / nm) if nm else None, "upper": (sum(1 / b for _, b in mapped) / nm) if nm else None, "denominator": nm}
    return out


def audit_reasons(case: Case) -> list[str]:
    """Reasons for which the adjudicated record contradicts the benchmark label, derived from the record (never supplied as a flag)."""
    reasons = []
    if case.group_purity == "impure":
        reasons.append("impure_group")                       # the benchmark asserts one person; the group holds more than one
    j = case.pool_judgments or {}
    if any(j.get(i) == "different" for i in case.pool_ids if i in case.mapped_ids):
        reasons.append("false_mapping")                      # a benchmark-mapped candidate is judged a different person
    if any(j.get(i) == "same" for i in case.pool_ids if i not in case.mapped_ids):
        reasons.append("missed_mapping")                     # an unmapped candidate is judged the same person
    return reasons


def audit_status(case: Case) -> tuple[str, list[str], str | None]:
    """(status, reasons, indeterminate_reason). Status: contradicted, consistent, indeterminate or unverified.

    An impure group is automatically a contradiction. A ground-truth unresolved case with a pure group is NOT automatically a contradiction.
    A cannot-tell judgment is indeterminate, never an error."""
    if case.label_state is None:
        return "unverified", [], None
    reasons = audit_reasons(case)
    if reasons:
        return "contradicted", reasons, None
    if case.label_state in ("uncertain", "unverifiable"):
        return "indeterminate", [], f"label_{case.label_state}"
    if case.group_purity is None:
        raise C7Error(f"{case.case_id}: an audited case with a definite label needs a Stage A group-purity judgment")
    if case.group_purity == "cannot_tell":
        return "indeterminate", [], "purity_cannot_tell"
    j = case.pool_judgments or {}
    if any(j.get(i) == "cannot_tell" for i in case.pool_ids if i in case.mapped_ids):
        return "indeterminate", [], "mapped_candidate_cannot_tell"
    if case.label_state == "resolved" and case.pool_ids and set(j) != set(case.pool_ids):
        return "indeterminate", [], "incomplete_stage_b"      # consistency cannot be established without every candidate judged
    return "consistent", [], None


def audit_label_error(primary: Sequence[Case]) -> dict[str, Any]:
    """Audit label-error rate over the audited non-automatic sample, derived from adjudicated records. Each affected case counts once in the numerator."""
    audited = [c for c in primary if c.audit_subset == "audit_sample"]
    rows = [(c, *audit_status(c)) for c in audited]
    n = Counter(status for _, status, _, _ in rows)
    reason_counts = Counter(r for _, status, reasons, _ in rows if status == "contradicted" for r in reasons)
    why = Counter(w for _, status, _, w in rows if status == "indeterminate")
    errors, consistent, indeterminate = n["contradicted"], n["consistent"], n["indeterminate"]
    total = errors + consistent + indeterminate
    return {"label_basis": VERIFIED, "population": "the sampled non-automatic frame of the primary pair only; not a correction factor, and not transferable",
            "audited": len(audited), "contradicted": errors, "consistent": consistent, "indeterminate": indeterminate, "unverified": n["unverified"],
            "definite": errors + consistent, "label_errors": errors, "error_rate": _rate(errors, errors + consistent),
            "reason_counts": {r: reason_counts[r] for r in AUDIT_REASONS},
            "reason_counts_note": "a case may have more than one reason, so reason counts can sum to more than label_errors; each case counts once in the numerator",
            "cases_with_more_than_one_reason": sum(1 for _, status, reasons, _ in rows if status == "contradicted" and len(reasons) > 1),
            "indeterminate_reasons": dict(sorted(why.items())),
            "unresolved_not_contradicted": sum(1 for c, status, _, _ in rows if status == "consistent" and c.label_state == "unresolved"),
            "bracket": {"all_right": {"errors": errors, "denominator": total, "value": (errors / total) if total else None},
                        "all_wrong": {"errors": errors + indeterminate, "denominator": total, "value": ((errors + indeterminate) / total) if total else None}}}


'''
s = s[:a] + new_block + s[b:]

sub('''        "scope": {"label_bases":''', '''        "scope": {"pool": "captured R2 (name-only) candidate pool; R0 is descriptive only and is not an input to any C7 metric",
                  "label_bases":''')
open(p, "w", encoding="utf-8").write(s)
print("patched; lines:", s.count("\n"))
