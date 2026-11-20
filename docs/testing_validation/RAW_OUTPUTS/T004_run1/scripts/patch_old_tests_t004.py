p = "tests/test_metrics_c7.py"
s = open(p, encoding="utf-8").read()
# 1. replace the audit test wholesale (semantics changed: derived from adjudicated records)
a = s.index("def test_audit_label_error_rate_and_bracket")
b = s.index("# ---------------------------------------------------------------- whole report")
new_audit = '''def test_audit_label_error_rate_and_bracket():
    judged = lambda **kw: mk(kw.pop("cid"), label_state=kw.pop("state", "resolved"), audit_subset="audit_sample", mapped={"a"}, **kw)
    cases = [judged(cid="1", group_purity="pure", pool_judgments={"a": "same", "b": "different"}),         # consistent
             judged(cid="2", group_purity="impure", pool_judgments={"a": "same", "b": "different"}),       # impure group
             judged(cid="3", group_purity="pure", pool_judgments={"a": "different", "b": "different"}),    # false mapping
             judged(cid="4", group_purity="pure", pool_judgments={"a": "same", "b": "same"}),              # missed mapping
             judged(cid="5", state="uncertain")]                                                            # indeterminate
    a = m.evaluate_primary(cases, {"S": 100})["audit_label_error"]
    assert (a["definite"], a["label_errors"], a["indeterminate"]) == (4, 3, 1)
    assert a["error_rate"]["value"] == 0.75
    assert a["bracket"]["all_right"]["value"] == pytest.approx(3 / 5) and a["bracket"]["all_wrong"]["value"] == pytest.approx(4 / 5)
    assert "not a correction factor" in a["population"]
    with pytest.raises(C7Error, match="group-purity"):
        m.evaluate_primary([mk("9", label_state="resolved", audit_subset="audit_sample")], {"S": 100})


'''
s = s[:a] + new_audit + s[b:]
# 2. fixtures that carried the removed flag
s = s.replace('label_contradicted=False', 'group_purity="pure"')
s = s.replace('audit_subset="audit_sample", label_contradicted=False if i == 0 else None', 'audit_subset="audit_sample"')
s = s.replace('label_contradicted=False if i == 0 else None', 'group_purity="pure" if i == 0 else None')
s = s.replace('["unresolved_no_unique_person"]', '["ground_truth_unresolved"]')
open(p, "w", encoding="utf-8").write(s)
print("label_contradicted left:", s.count("label_contradicted"))
