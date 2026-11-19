# Metric Definitions and Denominators

**Status:** Proposed definitions for the independent RQ2 study
**Rule:** Publish counts and denominators beside every rate. Never combine retrieval, ranking, and decision quality into one accuracy number.

## Pilot boundary

For the approved pilot, report descriptive workflow measures only: counts of evidence packets completed, status counts, reviewer agreement/disagreement, adjudications, candidate-pool size distribution, mapping outcomes, source failures, and workload. Include exact denominators and suitable uncertainty intervals. Do not compute author-resolution accuracy or use pilot outcomes as a performance evaluation.

## Population and labels

Let Q be the preregistered primary query for each independently reviewed test identity group with final resolved/Confirmed or unresolved labels. Exclude uncertain labels from primary rates and report their number separately. The statuses are resolved, unresolved, and uncertain. Resolved requires external evidence for one intended person; unresolved means the query/context does not establish a unique target, not nonexistence; uncertain means reviewers cannot settle identity. V3 Probable must not be encoded as resolved. A separate grade is optional and not recommended unless a sensitivity question justifies added complexity. Unresolved controls mean no uniquely supported target is established from the supplied query/context; this does not assert that the named person does not exist. Additional query variants are secondary and reported with identity-grouped denominators.

For each Confirmed identity group, the post-freeze source-coverage audit determines whether one or more OpenAlex profiles can be externally mapped to that gold person. Let M be Confirmed primary queries with at least one such mapped profile. Source mapping does not change the gold identity.

## Candidate retrieval

For one retrieval strategy and rank cutoff k:

- **Catalog coverage** = Confirmed identity groups with at least one externally mapped OpenAlex profile / all Confirmed identity groups.
- **Recall@k** = queries in M with a mapped profile among the first k returned candidates / |M|.
- **MRR** = mean over M of the reciprocal rank of the first mapped profile; a miss contributes zero.
- **Candidate-pool size** = unique source-author IDs returned; report mean, median, and empty-pool rate.
- **Source failure rate** = failed requests / all retrieval attempts, separately from successful empty results.

Report Recall@1, Recall@5, Recall@10, and MRR. If fewer than k candidates are returned, use all returned candidates; do not pad. If a person maps to multiple independently verified OpenAlex profiles due to source fragmentation, any mapped profile is a hit; also report profile multiplicity.

Source coverage is separate because a provider omission is not a retrieval miss within that provider's catalog. For end-to-end resolution, a Confirmed person with no candidate-source representation remains in the denominator and cannot count as a correct automatic assignment.

## Automatic resolution

Primary decision analysis includes adjudicated resolved/Confirmed and unresolved primary queries. Uncertain rows are excluded. Any separately graded Probable rows require a reviewed companion field and are reported apart from primary metrics.

- **Correct automatic assignment:** the auto-selected candidate is independently mapped to the query's Confirmed gold_person_id.
- **Wrong automatic assignment:** an auto selection maps to another person, has insufficient mapping evidence, or occurs on an unresolved/no-supported-match query.
- **Auto precision:** correct automatic assignments / all automatic assignments. Also report Confirmed-only auto precision and unresolved-control false-accept count separately.
- **Selective risk:** wrong automatic assignments / all automatic assignments = 1 − auto precision.
- **Automatic coverage:** automatic assignments / all eligible adjudicated queries, including source failures and successful empty pools.
- **Correct-resolution coverage:** correct automatic assignments / all Confirmed queries.
- **Manual-review rate:** manual-review outcomes / all eligible adjudicated queries.
- **Unresolved rate:** resolver-unresolved outcomes / all eligible adjudicated queries.
- **Candidate-source failure rate** and **successful-empty rate:** their respective query counts / all eligible adjudicated queries; do not hide them inside resolver-unresolved.
- **Top-1 correctness** for forced-choice policies: correct top-1 selections / all eligible adjudicated queries. A failed or empty source is not a correct selection and remains in the end-to-end denominator.

Also provide a conditional decision table for candidate-available queries. It can explain gate behavior but cannot replace the end-to-end denominator.

An auto decision on an unresolved query is a false acceptance even if the selected profile belongs to a real person with a similar name. A Confirmed person with no OpenAlex profile cannot be correctly resolved by an OpenAlex-only pool; any auto assignment for that row is wrong and the source omission is reported.

## Paired comparisons and uncertainty

For auto precision with n automatic decisions, report a two-sided exact binomial 95% interval and n. It assumes independent Bernoulli outcomes; selective assignment and a curated cohort limit population interpretation. With zero errors, the one-sided exact 95% upper risk bound is 1 − 0.05^(1/n). For paired policy differences, report identity-level paired outcomes and preselect an interval method. Repeated variants require identity-cluster resampling.

Report raw numerators, denominators, excluded uncertain/probable rows, source failures, and empty pools. A zero observed error is an empirical count, not proof of zero risk. Avoid significance tests unless the null, paired unit, and interpretation are prespecified and justified for this curated sample.
