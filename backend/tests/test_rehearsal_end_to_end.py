"""T010: end-to-end rehearsal of the whole evaluation pipeline on a SYNTHETIC world, plus small seeded checks of the statistical methodology.

The rehearsal wires together: selector (pilot, main, audit) -> sizing -> simulated resolver outputs and frozen predictions -> blinded packets with leak scan and a
separate crosswalk -> simulated two-reviewer records with an adjudicator -> C7 metrics. Because the synthetic world has a known hidden truth, every verified result
is compared with an independently computed answer. Nothing here uses the LAGOS archive, a provider, real parameters or real labels."""
import csv
import hashlib
import inspect
import json
import random
import re
from collections import Counter

import pytest

import validate_methodology_by_simulation as sim
from hammer_pilot import dossier, review_records as rr, selector_c1c as sel, sizing_c9 as z
from hammer_pilot import metrics_c7 as m
from test_selector_c1c import make_catalog

ORCID = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")
COVERAGE = {"S": 0.10, "M": 0.18, "L": 0.30, "XL": 0.40}
FLOORS = {"S": 0, "M": 0, "L": 0, "XL": 0}


def run_world(tmp_path, seed=4, reviewer_noise=0.30, n_audit=25):
    tmp_path.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    catalog = make_catalog(900, seed=seed)
    frame0 = sel.eligible_frame(catalog, split="test")
    smoke = frame0["strata"]["S"][:5]
    # 1 pilot (label-free) and sizing --------------------------------------------------------------------------------------------------
    pilot = sel.draw_pilot(catalog, seed=101, dataset_version="synthetic", split="test", smoke_blocks=smoke, per_stratum={"S": 30, "M": 30, "L": 15, "XL": 1})
    post = {s: n for s, n in pilot["post_exclusion_frame"]["sizes"].items() if n > 0}
    pilot_counts = {}
    for c in pilot["manifest"]["cases"]:
        d = pilot_counts.setdefault(c["stratum"], {"automatic": 0, "cases": 0})
        d["cases"] += 1
        d["automatic"] += rng.random() < COVERAGE[c["stratum"]]
    sizing = z.size_sample({s: post[s] for s in post}, {s: 0 for s in post}, pilot_counts, m_prime=6, beta=0.20, gamma=0.10, n_max=min(sum(post.values()), 300))
    n_main = sizing["primary_jeffreys"]["N"]
    assert n_main is not None
    # 2 main draw ----------------------------------------------------------------------------------------------------------------------
    pilot_blocks = [c["block_id"] for c in pilot["manifest"]["cases"]]
    main = sel.draw_main(catalog, seed=202, dataset_version="synthetic", split="test", smoke_blocks=smoke, pilot_blocks=pilot_blocks, n_total=n_main, floors=FLOORS)
    disjoint = sel.disjointness_report(smoke, pilot["manifest"], main["manifest"])
    # 3 simulated resolver outputs with a hidden truth ---------------------------------------------------------------------------------
    world = {}
    for c in main["manifest"]["cases"]:
        cid, h = c["case_id"], c["stratum"]
        u = rng.random()
        outcome = "provider_failed" if u < 0.03 else "empty_pool" if u < 0.08 else "auto" if rng.random() < COVERAGE[h] else rng.choice(["manual", "manual", "unresolved"])
        n_cand = 0 if outcome in ("provider_failed", "empty_pool") else rng.randint(1, 6)
        pool = tuple(f"A{int(hashlib.sha256((cid + str(k)).encode()).hexdigest()[:8], 16) % 10**9 + 10**9:010d}" for k in range(n_cand))
        unique = rng.random() < 0.95
        pure = rng.random() < 0.92
        truth_cand = rng.choice(pool) if (pool and unique and rng.random() < 0.8) else None
        mapped = set()
        if pool and rng.random() < 0.9:
            mapped = {truth_cand} if truth_cand and rng.random() < 0.9 else {rng.choice(pool)}
        selected = ""
        if outcome == "auto":
            selected = truth_cand if (truth_cand and rng.random() < 0.85) else rng.choice(pool)
        world[cid] = dict(outcome=outcome, pool=pool, unique=unique, pure=pure, truth=truth_cand, mapped=mapped, selected=selected, stratum=h, block=c["block_id"],
                          g=c["case_eligible_groups"])
    # 4 frozen predictions and the audit draw ------------------------------------------------------------------------------------------
    pred_path = tmp_path / "predictions.csv"
    with open(pred_path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["case_id", "stratum", "outcome", "selected"])
        for cid in sorted(world):
            w.writerow([cid, world[cid]["stratum"], world[cid]["outcome"], world[cid]["selected"]])
    pred_hash = hashlib.sha256(pred_path.read_bytes()).hexdigest()
    auto = [c for c in world if world[c]["outcome"] == "auto"]
    rest = [{"case_id": c, "stratum": world[c]["stratum"]} for c in world if world[c]["outcome"] != "auto"]
    audit = sel.draw_audit(rest, auto, seed=303, dataset_version="synthetic", n_audit=min(n_audit, len(rest)), merge_rule=None, predictions_sha256=pred_hash)
    reviewed = sorted(set(auto) | set(audit["audit_case_ids"]))
    # 5 packets, leak scan, crosswalk -------------------------------------------------------------------------------------------------
    packets, crosswalks, flags = [], {}, {}
    for cid in reviewed:
        w_ = world[cid]
        papers = [{"title": f"T{i}", "doi": f"10.9999/{cid}-{i}", "year": 2012 + i, "venue": "J", "author_names": ["X Y"], "affiliation": "U", "coauthor_names": ["Z"],
                   "orcid": "0000-0003-1111-2222", "pid": "1"} for i in range(8)]
        a_pkt = dossier.build_stage_a_packet(cid, "X Y", papers, seed=404, k=5, designated_doi=f"10.9999/{cid}-0")
        packets.append(dossier.release(a_pkt, gold_values=["0000-0003-1111-2222"]))
        if w_["pool"]:
            cands = [{"id": f"https://openalex.org/{a}", "orcid": "https://orcid.org/0000-0003-1111-2222", "observed_orcids": ["0000-0003-1111-2222"], "display_name": f"X Y {i}",
                      "relevance_score": 90 - i, "works_count": 5 + i, "affiliations": [], "topics": []} for i, a in enumerate(w_["pool"])]
            b_pkt, cw = dossier.build_stage_b_packet(cid, cands, seed=404, works_cap=0)
            packets.append(dossier.release(b_pkt, gold_values=["0000-0003-1111-2222"]))
            crosswalks[cid] = cw
        flags[cid] = "automatic" if cid in auto else "audit_sample"
    hashes = dossier.write_release(tmp_path / "reviewer", tmp_path / "protected", packets, crosswalks, flags)
    # 6 simulated reviewers and adjudication ------------------------------------------------------------------------------------------
    stage_a, stage_b, finals = [], [], {}
    for cid in reviewed:
        w_ = world[cid]
        cw = crosswalks.get(cid, {})
        status = "resolved" if w_["unique"] else "unresolved"
        purity = "pure" if w_["pure"] else "impure"
        truth_judg = {op: ("same" if w_["truth"] == prov else "different") for op, prov in cw.items()}
        for rv in ("r1", "r2"):
            noisy = rv == "r2" and rng.random() < reviewer_noise
            st, pu = ("uncertain", purity) if noisy else (status, purity)
            stage_a.append({"case_id": cid, "reviewer_id": rv, "status": st, "group_purity": pu, "confidence": 4, "rationale": "", "evidence_refs": "", "searches": "",
                            "orcid_encountered": "false", "minutes": 10})
            for op, j in truth_judg.items():
                stage_b.append({"case_id": cid, "reviewer_id": rv, "candidate": op, "judgment": ("cannot_tell" if noisy else j), "confidence": 3, "evidence_refs": "",
                                "orcid_encountered": "false", "minutes": 2})
        finals[cid] = {"case_id": cid, "adjudicator_id": "judge", "final_status": status, "final_group_purity": purity,
                       "candidate_judgments": ";".join(f"{op}:{j}" for op, j in truth_judg.items()), "rationale": "adjudicated"}
    labels = {cid: rr.resolve_case(cid, stage_a, stage_b, finals[cid], candidates=list(crosswalks.get(cid, {})), builder_id="builder") for cid in reviewed}
    # 7 C7 cases -----------------------------------------------------------------------------------------------------------------------
    def case(cid, verified):
        w_ = world[cid]
        extra = {}
        if verified and cid in labels:
            extra = rr.to_c7_fields(labels[cid], crosswalks.get(cid, {}), audit_subset=flags[cid], selected_candidate=w_["selected"] or None)
        return m.Case(case_id=cid, block_id=w_["block"], stratum=w_["stratum"], outcome=w_["outcome"], pool_ids=w_["pool"], mapped_ids=frozenset(w_["mapped"]),
                      selected_id=w_["selected"], group_count=w_["g"], **extra)
    frame = main["manifest"]["frame_post_exclusion"]
    frame = {s: n for s, n in frame.items() if n > 0}
    settings = m.InferenceSettings(bootstrap_resamples=50, bootstrap_min_stratum_n=5)
    return dict(world=world, labels=labels, stage_a=stage_a, stage_b=stage_b, pilot=pilot, main=main, audit=audit, auto=auto, hashes=hashes, tmp=tmp_path, frame=frame, settings=settings,
                sizing=sizing, disjoint=disjoint, case=case, reviewed=reviewed, flags=flags, n_main=n_main, pred_hash=pred_hash, pred_path=pred_path)


@pytest.fixture(scope="module")
def rehearsal(tmp_path_factory):
    return run_world(tmp_path_factory.mktemp("rehearsal"))


def test_rehearsal_structure_and_manifests(rehearsal):
    r = rehearsal
    assert r["disjoint"]["disjoint"] and r["disjoint"]["main"] == r["n_main"] == len(r["main"]["manifest"]["cases"])
    for obj in (r["pilot"]["manifest"], r["main"]["manifest"], r["audit"]):
        assert sel.verify_manifest(obj)
    assert r["audit"]["predictions_sha256"] == r["pred_hash"] == hashlib.sha256(r["pred_path"].read_bytes()).hexdigest()
    assert set(r["audit"]["audit_case_ids"]).isdisjoint(r["auto"]) and r["audit"]["verification_population"] == sorted(r["auto"])
    assert not ORCID.search(json.dumps(r["main"]["manifest"])) and not ORCID.search(json.dumps(r["audit"]))
    assert r["sizing"]["primary_jeffreys"]["status"] == "found" and r["sizing"]["primary_jeffreys"]["N"] == r["n_main"]


def test_reviewer_facing_files_are_leak_free_and_the_crosswalk_is_elsewhere(rehearsal):
    r = rehearsal
    reviewer, protected = r["tmp"] / "reviewer", r["tmp"] / "protected"
    texts = [p.read_text() for p in reviewer.iterdir()]
    assert texts and not any(ORCID.search(t) or "openalex.org" in t.lower() or "relevance" in t for t in texts)
    assert {p.name for p in protected.iterdir()} == {"crosswalk.json", "case_flags.json"} and not (reviewer / "crosswalk.json").exists()
    scans = [json.loads(p.read_text()) for p in reviewer.glob("*.scan.json")]
    assert scans and all(s["released"] and not s["findings"] for s in scans)
    flags = json.loads((protected / "case_flags.json").read_text())
    assert set(flags.values()) == {"automatic", "audit_sample"} and not any(v in " ".join(texts) for v in ("automatic", "audit_sample"))      # nothing reveals the case origin


def test_the_reviewer_queue_does_not_reveal_which_cases_were_automatic(rehearsal):
    r = rehearsal
    pkts = [json.loads(p.read_text()) for p in (r["tmp"] / "reviewer").glob("*.json") if not p.name.endswith(".scan.json")]
    queue = dossier.build_queue(pkts, seed=404)
    assert sorted(queue) == sorted(p["packet_id"] for p in pkts)
    kinds = [p["packet_type"] for p in pkts]
    assert set(kinds) == {"stage_a", "stage_b"}


def test_noisy_reviewers_disagree_but_adjudication_recovers_the_hidden_truth(rehearsal):
    r = rehearsal
    rep = rr.agreement_report(r["stage_a"], r["stage_b"])
    assert rep["stage_a_status"]["raw_agreement"] < 1.0 and (rep["stage_a_status"]["kappa"] is None or rep["stage_a_status"]["kappa"] < 1.0)
    assert any(l["source"] == "adjudication" for l in r["labels"].values()) and any(l["source"] == "agreement" for l in r["labels"].values())
    for cid, label in r["labels"].items():
        w = r["world"][cid]
        assert label["status"] == ("resolved" if w["unique"] else "unresolved") and label["group_purity"] == ("pure" if w["pure"] else "impure")


def test_verified_precision_matches_an_independent_computation_from_the_hidden_truth(rehearsal):
    r = rehearsal
    cases = [r["case"](cid, True) for cid in r["world"]]
    rep = m.evaluate_primary(cases, r["frame"], r["settings"], seed=9)
    est = rep["selective_verified"]["estimates"]
    autos = [c for c in r["world"] if r["world"][c]["outcome"] == "auto"]
    correct = sum(1 for c in autos if r["world"][c]["unique"] and r["world"][c]["truth"] and r["world"][c]["selected"] == r["world"][c]["truth"])
    prec = est["verified_automatic_precision"]["per_stratum"]
    assert sum(v["numerator"] for v in prec.values()) == correct and sum(v["denominator"] for v in prec.values()) == len(autos)      # every automatic case is verified and definite
    assert rep["selective_verified"]["scoring"]["verification_complete"] is True and rep["selective_verified"]["scoring"]["automatic_assignments"] == len(autos)
    risk = est["verified_selective_risk"]["per_stratum"]
    assert sum(v["numerator"] for v in risk.values()) == len(autos) - correct


def test_a_wrong_crosswalk_would_be_caught_by_the_independent_comparison(rehearsal):
    r = rehearsal
    rotated = {}
    for cid in r["world"]:
        w = r["world"][cid]
        if cid in r["labels"] and len(w["pool"]) >= 2:
            ids = list(w["pool"])
            rotated[cid] = ids[1:] + ids[:1]
    assert rotated
    cases = []
    for cid in r["world"]:
        c = r["case"](cid, cid not in rotated)                                                       # reviewed cases with a rotated pool keep unverified fields
        cases.append(c)
    good = m.evaluate_primary([r["case"](cid, True) for cid in r["world"]], r["frame"], r["settings"], seed=9)["selective_verified"]["scoring"]["status_counts"]
    bad = m.evaluate_primary(cases, r["frame"], r["settings"], seed=9)["selective_verified"]["scoring"]["status_counts"]
    assert bad != good and bad["unverified"] > good["unverified"]                                    # dropping or corrupting verification changes the counts visibly


def test_audit_error_rate_matches_an_independent_computation_from_the_hidden_truth(rehearsal):
    r = rehearsal
    cases = [r["case"](cid, True) for cid in r["world"]]
    a = m.evaluate_primary(cases, r["frame"], r["settings"], seed=9)["audit_label_error"]
    audited = r["audit"]["audit_case_ids"]
    contradicted = consistent = indeterminate = impure = 0
    for cid in audited:
        w = r["world"][cid]
        impure += not w["pure"]
        mapped_in_pool = set(w["mapped"]) & set(w["pool"])
        false_map = any(c != w["truth"] for c in mapped_in_pool)
        missed = bool(w["truth"]) and w["truth"] in w["pool"] and w["truth"] not in w["mapped"]
        if not w["pure"] or false_map or missed:
            contradicted += 1
        elif not w["unique"]:
            indeterminate += 1                                                              # a pure group with no unique person: indeterminate (T005)
        else:
            consistent += 1
    assert (a["contradicted"], a["consistent"], a["indeterminate"]) == (contradicted, consistent, indeterminate) and a["audited"] == len(audited)
    assert a["group_validity"]["purity_counts"]["impure"] == impure
    assert a["error_rate"]["numerator"] == contradicted and a["error_rate"]["denominator"] == contradicted + consistent


def test_overall_retrieval_is_identical_with_and_without_any_verification(rehearsal):
    r = rehearsal
    with_v = m.evaluate_primary([r["case"](c, True) for c in r["world"]], r["frame"], r["settings"], seed=9)
    without = m.evaluate_primary([r["case"](c, False) for c in r["world"]], r["frame"], r["settings"], seed=9)
    for section in ("retrieval_benchmark_derived", "label_free", "selective_benchmark_derived"):
        assert json.dumps(with_v[section], sort_keys=True) == json.dumps(without[section], sort_keys=True)
    acc = with_v["case_accounting"]
    assert acc["n_primary"] == r["n_main"] and sum(acc["reporting_class_counts"].values()) == r["n_main"] and sum(acc["outcome_counts"].values()) == r["n_main"]
    assert acc["reporting_class_counts"]["benchmark_derived"] == r["n_main"] - len(r["reviewed"]) and without["case_accounting"]["reporting_class_counts"]["benchmark_derived"] == r["n_main"]


def test_the_rehearsal_is_reproducible_end_to_end(tmp_path):
    a = run_world(tmp_path / "a")
    b = run_world(tmp_path / "b")
    assert a["main"]["manifest"]["manifest_sha256"] == b["main"]["manifest"]["manifest_sha256"] and a["audit"]["manifest_sha256"] == b["audit"]["manifest_sha256"]
    assert a["pred_hash"] == b["pred_hash"] and a["hashes"] == b["hashes"] and a["n_main"] == b["n_main"]


# ---------------------------------------------------------------- small seeded checks of the statistical methodology (full runs are in the T010 raw outputs)
def test_estimators_are_unbiased_for_their_own_estimand_and_the_weights_matter():
    r = sim.simulate_estimators(reps=120, seed=11, resamples=60)
    assert abs(r["E1_bias_in_se"]) < 4 and abs(r["E2_bias_in_se"]) < 4
    assert abs(r["negative_control_E1_weights_for_E2_truth_bias_in_se"]) > 8                    # block-level weights are biased for the person-level truth
    assert all(v is not None and v >= 0.88 for k, v in r["cp_coverage_by_stratum"].items() if k != "XL") and r["cp_coverage_by_stratum"]["XL"] is None   # census: no interval
    assert r["pooled_bootstrap_E1_coverage"] >= 0.85


def test_predictive_sizing_reaches_the_target_when_the_prior_matches_and_the_plug_in_rule_does_not():
    r = sim.simulate_sizing(reps=80, seed=5, generator="jeffreys")
    assert r["predictive_found"] >= 70 and r["predictive_success_frequency"] >= 0.90 - 3 * 0.035 and r["plug_in_success_frequency"] < 0.80
    assert r["lower_bound_success_frequency"] is None or r["lower_bound_success_frequency"] >= 0.90


def test_simulation_parameters_are_test_values_and_the_script_requires_every_argument():
    sig = inspect.signature(sim.simulate_estimators)
    assert all(p.default is inspect.Parameter.empty for p in sig.parameters.values())
    assert inspect.signature(sim.simulate_sizing).parameters["generator"].default is inspect.Parameter.empty
