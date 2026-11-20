p = "tests/test_metrics_c7_rulings.py"
s = open(p, encoding="utf-8").read()


def sub(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


# superseded by T005 clarification 1: group-purity states are pure / impure / unresolved
sub('''    (dict(purity="cannot_tell", judgments={"a": "same", "b": "different"}), "indeterminate", [], "purity_cannot_tell"),''',
    '''    (dict(purity="unresolved", judgments={"a": "same", "b": "different"}), "indeterminate", [], "purity_unresolved"),''')
# superseded by T005 clarification 2: an uncertain case stays outside the definite-label denominator even when its group is impure
sub('''    (dict(purity="impure", state="uncertain", judgments=None), "contradicted", ["impure_group"], None),  # impure group refutes the benchmark even if the case label is uncertain''',
    '''    (dict(purity="impure", state="uncertain", judgments=None), "indeterminate", [], "label_uncertain"),   # T005: outside the definite-label denominator; impurity reported separately''')
sub('''    assert m.audit_status(pure_unresolved) == ("consistent", [], None)                    # no unique intended person, group pure: not automatically a contradiction
    assert m.audit_status(impure_unresolved) == ("contradicted", ["impure_group"], None)
    a = audit([pure_unresolved, impure_unresolved])
    assert (a["label_errors"], a["unresolved_not_contradicted"]) == (1, 1)''',
    '''    assert m.audit_status(pure_unresolved) == ("indeterminate", [], "label_unresolved_pure_group")   # T005: not automatically a contradiction, and no longer consistent
    assert m.audit_status(impure_unresolved) == ("contradicted", ["impure_group"], None)
    a = audit([pure_unresolved, impure_unresolved])
    assert (a["label_errors"], a["indeterminate"]) == (1, 1)''')
open(p, "w", encoding="utf-8").write(s)
print("updated 3 superseded T004 tests")
