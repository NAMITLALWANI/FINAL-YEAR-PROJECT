import sys
f="hammer_pilot/metrics_c7.py"; s=open(f).read()
muts={
 "M1 unresolved dropped from denominator": ('return INCORRECT, "unresolved"', 'return UNCERTAIN, "unresolved"'),
 "M2 no-matching-candidate dropped from denominator": ('return INCORRECT, "resolved_no_matching_candidate"', 'return UNCERTAIN, "resolved_no_matching_candidate"'),
 "M3 E1 weight wrongly includes g": ('return w * case.group_count if estimand == "E2" else w', 'return w * case.group_count'),
 "M4 label-free denominator excludes failures": ('Quantity(f"rate_{o}", LABEL_FREE, "proportion", (lambda c, o=o: _flag(c.outcome == o)), lambda c: 1.0)', 'Quantity(f"rate_{o}", LABEL_FREE, "proportion", (lambda c, o=o: _flag(c.outcome == o)), lambda c: _flag(c.outcome != "provider_failed"))'),
 "M5 unmapped counted outside end-to-end denominator": ('(lambda c, k=k: _flag(mapped(c) and first_rank(c) <= k)), lambda c: 1.0))', '(lambda c, k=k: _flag(mapped(c) and first_rank(c) <= k)), lambda c: _flag(mapped(c))))'),
 "M6 bootstrap runs on zero errors": ('if raw_d < settings.sparse_automatic_warn or errors < settings.sparse_error_warn:', 'if False:'),
}
name=sys.argv[1]; old,new=muts[name]; assert old in s, name
open(f,"w").write(s.replace(old,new,1))
