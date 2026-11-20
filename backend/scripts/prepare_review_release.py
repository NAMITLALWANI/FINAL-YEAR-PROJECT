"""Prepare the blinded reviewer release (Stage A and Stage B packets, scan reports, queue) and the separate protected directory. Offline; refuses to overwrite.

  python scripts/prepare_review_release.py --manifest main_manifest.json --audit-manifest audit/manifest.json --predictions replay/predictions.csv \
      --seeds capture/seeds.csv --capture-dir capture/captures --works-capture-dir works_capture --gold-register PROTECTED/gold_identity_register.csv \
      --archive LAGOS.tar.gz --freeze freeze_F1.json --reviewer-dir out/reviewer --protected-dir out/protected
K and the works cap come from the freeze parameters; the packet seed is the freeze's derived `packets` seed. The gold register is read into memory only (leak scan)."""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hammer_lagos import prep
from hammer_pilot import dossier
from hammer_pilot import review_driver as rd


def rows(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for n in ("manifest", "audit-manifest", "predictions", "seeds", "capture-dir", "gold-register", "archive", "freeze", "reviewer-dir", "protected-dir"):
        ap.add_argument(f"--{n}", type=Path, required=True)
    ap.add_argument("--works-capture-dir", type=Path, default=None)
    a = ap.parse_args()
    try:
        manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
        audit = json.loads(a.audit_manifest.read_text(encoding="utf-8"))
        freeze = json.loads(a.freeze.read_text(encoding="utf-8"))
        review = freeze["parameters"]["review"]
        primary = [c["case_id"] for c in manifest["cases"] if c.get("is_primary", True)]
        reviewed, flags = rd.plan_reviewed(primary, rows(a.predictions), audit["audit_case_ids"])
        gold = {r["case_id"]: r for r in rows(a.gold_register)}
        seeds = {r["case_id"]: r for r in rows(a.seeds)}
        blocks = {gold[c]["source_block_fullname"] for c in reviewed}
        block_rows = prep.collect_rows(prep.open_csv_rows(a.archive), blocks)
        inputs = {}
        for c in reviewed:
            g = gold[c]
            seen, papers = set(), []
            for r in block_rows[g["source_block_fullname"]]:
                doi, _ = prep.normalize_doi(r["doi"])
                if r["orcid"] != g["gold_orcid"] or not doi or doi in seen:
                    continue
                seen.add(doi)
                co = prep.parse_name_list(r["coauthors"]) or []
                co, _ = prep.strip_own_name(co, r["author_name"])
                aff, _ = prep.normalize_affiliation(r["author_affiliation"])
                papers.append({"title": r["paper_title"], "doi": doi, "year": r["pub_year"], "venue": r["venue"], "author_names": r["author_name"], "affiliation": aff, "coauthor_names": co})
            items = rd.pool_items(a.capture_dir, c)
            ids = [str(i["id"]).rsplit("/", 1)[-1] for i in items]
            works = rd.load_works(a.works_capture_dir, ids, review["works_per_candidate"]) if a.works_capture_dir else {}
            inputs[c] = {"query_name": seeds[c]["query_text"], "papers": papers, "designated_doi": prep.normalize_doi(g["designated_doi"])[0], "pool_items": items,
                         "works_by_candidate": works}
        seed = freeze["seeds"]["packets"]
        res = rd.build_release(inputs, flags, seed=seed, k=review["group_paper_cap_K"], works_cap=review["works_per_candidate"],
                               gold_values=sorted({g["gold_orcid"] for g in gold.values()}), reviewer_dir=a.reviewer_dir, protected_dir=a.protected_dir)
    except (rd.DriverError, dossier.DossierError, KeyError, FileExistsError) as exc:
        print(f"refused: {exc!r}", file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in res.items() if k != "packet_hashes"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
