"""Create blinded, local HTML annotation packets from query/evidence CSVs."""
from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import urlparse

try:
    from .evaluation_dataset import read_csv, unique_rows
except ImportError:
    from evaluation_dataset import read_csv, unique_rows


def prepare_packets(queries_path: Path, evidence_path: Path, output_dir: Path) -> list[Path]:
    queries = read_csv(queries_path, {"query_id", "query_text", "context_json"})
    query_map = unique_rows(queries, "query_id", queries_path)
    with evidence_path.open(newline="", encoding="utf-8-sig") as stream:
        evidence_reader = csv.DictReader(stream)
        evidence_required = {"query_id", "source", "reference", "captured_at", "evidence_type", "excerpt_or_locator"}
        if not evidence_reader.fieldnames or evidence_required - set(evidence_reader.fieldnames):
            raise ValueError(f"Evidence packet is missing required columns: {sorted(evidence_required - set(evidence_reader.fieldnames or []))}")
        evidence = list(evidence_reader)
    by_query: dict[str, list[dict[str, str]]] = {qid: [] for qid in query_map}
    for row in evidence:
        qid = row["query_id"].strip()
        if qid not in query_map:
            raise ValueError(f"Evidence references unknown query_id {qid!r}")
        if not all(row.get(field, "").strip() for field in ("source", "reference", "captured_at", "evidence_type")):
            raise ValueError(f"Evidence row for {qid} is missing a required reference field")
        if urlparse(row["reference"].strip()).scheme not in {"http", "https"}:
            raise ValueError(f"Evidence reference for {qid} must use http or https")
        if not all(row.get(field, "").strip() for field in ("source", "reference", "captured_at", "evidence_type")):
            raise ValueError(f"Evidence row for {qid} is missing a required reference field")
        if urlparse(row["reference"].strip()).scheme not in {"http", "https"}:
            raise ValueError(f"Evidence reference for {qid} must use http or https")
        by_query[qid].append(row)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for reviewer_slot in ("reviewer_1", "reviewer_2"):
        cards = []
        for qid, row in query_map.items():
            context = json.loads(row["context_json"])
            evidence_html = "".join(
                "<li><a rel=\"noreferrer\" target=\"_blank\" href=\"{url}\">{source}</a> Â· {kind} Â· captured {captured}<br><small>{locator}</small></li>".format(
                    url=html.escape(item["reference"], quote=True), source=html.escape(item["source"]),
                    kind=html.escape(item["evidence_type"]), captured=html.escape(item["captured_at"]),
                    locator=html.escape(item["excerpt_or_locator"]),
                ) for item in by_query[qid]
            ) or "<li>No evidence preloaded. Reviewer must locate and document source evidence.</li>"
            cards.append(f"""<section><h2>{html.escape(qid)}</h2>
<p><b>Query:</b> {html.escape(row['query_text'])}</p>
<pre>{html.escape(json.dumps(context, ensure_ascii=False, indent=2))}</pre>
<h3>Source evidence</h3><ul>{evidence_html}</ul>
<label>Your reviewer ID <input name="reviewer_id" required></label>
<label>Status <select name="status" required><option value="">Chooseâ¦</option><option>resolved</option><option>unresolved</option><option>uncertain</option></select></label>
<label>Confidence (1 low â 5 high) <input name="confidence" type="number" min="1" max="5" required></label>
<label>Gold source (resolved only) <input name="gold_source"></label><label>Source-scoped author ID (resolved only) <input name="gold_author_id"></label>
<label>Rationale / sources checked <textarea name="rationale" required></textarea></label>
<label>Evidence references JSON (array with source, reference, captured_at, evidence_type) <textarea name="evidence_refs_json" required>{html.escape(json.dumps([{"source":item["source"],"reference":item["reference"],"captured_at":item["captured_at"],"evidence_type":item["evidence_type"]} for item in by_query[qid]], ensure_ascii=False))}</textarea></label>
<button type="button" onclick="save(this)">Save annotation row</button><output></output></section>""")
        destination = output_dir / f"{reviewer_slot}.html"
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite reviewer packet: {destination}")
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite reviewer packet: {destination}")
        # Each reviewer gets a separate file with no candidate, rank, score, or other review fields.
        content = """<!doctype html><meta charset="utf-8"><title>Independent author review</title>
<style>body{font:16px system-ui;max-width:900px;margin:2rem auto;padding:0 1rem}section{border:1px solid #bbb;padding:1rem;margin:1rem 0}label{display:block;margin:.8rem 0}input,textarea,select{display:block;width:100%;max-width:800px;padding:.45rem}textarea{min-height:4rem}pre{white-space:pre-wrap}small{color:#555}</style>
<h1>Independent author identity review</h1><p>Review the source evidence independently. Do not consult resolver candidates or another reviewer's decision. Download each saved row as CSV and submit it to the dataset coordinator.</p>
<script>const reviewerSlot=""" + json.dumps(reviewer_slot) + ";""" + """
function save(button){let s=button.closest('section'), vals={};s.querySelectorAll('[name]').forEach(e=>vals[e.name]=e.value);let row={query_id:s.querySelector('h2').textContent,reviewer_id:vals.reviewer_id,status:vals.status,confidence:vals.confidence,rationale:vals.rationale,gold_source:vals.gold_source,gold_author_id:vals.gold_author_id,evidence_refs_json:vals.evidence_refs_json};let keys=Object.keys(row), quote=v=>'"'+String(v).replaceAll('"','""')+'"';let csv=keys.join(',')+'\\n'+keys.map(k=>quote(row[k])).join(',')+'\\n';let a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download=row.query_id+'-'+reviewerSlot+'.csv';a.click();s.querySelector('output').textContent='CSV downloaded.'}</script>""" + "".join(cards)
        destination.write_text(content, encoding="utf-8")
        paths.append(destination)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    for path in prepare_packets(args.queries, args.evidence, args.output_dir):
        print(path)


if __name__ == "__main__":
    main()