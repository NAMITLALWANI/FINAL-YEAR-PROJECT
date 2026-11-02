"""Create blinded local HTML packets for query/publication relevance review."""
from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from urllib.parse import urlparse

try:
    from .evaluation_dataset import read_csv
except ImportError:
    from evaluation_dataset import read_csv


def prepare_packets(path: Path, output_dir: Path) -> list[Path]:
    rows = read_csv(path, {"query_id", "query_text", "canonical_publication_id", "title", "abstract", "doi", "url", "pool_protocol_version"})
    keys = [(row["query_id"].strip(), row["canonical_publication_id"].strip()) for row in rows]
    if any(not qid or not pid for qid, pid in keys) or len(keys) != len(set(keys)):
        raise ValueError("Retrieval review packet requires unique non-empty query/publication pairs")
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for reviewer_slot in ("reviewer_1", "reviewer_2"):
        cards = []
        for row in rows:
            url = row["url"].strip()
            if url and urlparse(url).scheme not in {"http", "https"}:
                raise ValueError(f"Publication URL must use http or https: {url!r}")
            link = f'<p><a rel="noreferrer" target="_blank" href="{html.escape(url, quote=True)}">Open publication source</a></p>' if url else ""
            cards.append(f"""<section data-query="{html.escape(row['query_id'], quote=True)}" data-publication="{html.escape(row['canonical_publication_id'], quote=True)}">
<h2>{html.escape(row['query_id'])} Â· {html.escape(row['canonical_publication_id'])}</h2><p><b>Information need:</b> {html.escape(row['query_text'])}</p>
<h3>{html.escape(row['title'])}</h3><p>{html.escape(row['abstract'])}</p><p>DOI: {html.escape(row['doi'])}</p>{link}
<label>Reviewer ID <input name="reviewer_id" required></label><label>Relevance <select name="relevance"><option value="">Chooseâ¦</option><option value="0">0 â not relevant</option><option value="1">1 â relevant</option><option value="2">2 â strongly relevant</option></select></label>
<label>Evidence note <textarea name="evidence_note" required></textarea></label><button type="button" onclick="save(this)">Download judgment row</button><output></output></section>""")
        destination = output_dir / f"{reviewer_slot}.html"
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite reviewer packet: {destination}")
        script = """<script>const reviewerSlot=""" + json.dumps(reviewer_slot) + ";""" + """
function save(button){let s=button.closest('section'),v={};s.querySelectorAll('[name]').forEach(e=>v[e.name]=e.value);let row={query_id:s.dataset.query,canonical_publication_id:s.dataset.publication,reviewer_id:v.reviewer_id,relevance:v.relevance,evidence_note:v.evidence_note};let keys=Object.keys(row),q=x=>'"'+String(x).replaceAll('"','""')+'"';let csv=keys.join(',')+'\\n'+keys.map(k=>q(row[k])).join(',')+'\\n';let a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download=row.query_id+'-'+row.canonical_publication_id+'-'+reviewerSlot+'.csv';a.click();s.querySelector('output').textContent='CSV downloaded.'}</script>"""
        destination.write_text("<!doctype html><meta charset='utf-8'><title>Blinded publication relevance review</title><style>body{font:16px system-ui;max-width:900px;margin:2rem auto}section{border:1px solid #aaa;padding:1rem;margin:1rem 0}label{display:block;margin:.8rem 0}input,textarea,select{display:block;width:100%;padding:.4rem}textarea{min-height:4rem}</style><h1>Blinded publication relevance review</h1><p>Judge only the information need against each publication. Download every row and submit every pooled pair.</p>" + "".join(cards) + script, encoding="utf-8")
        paths.append(destination)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    for path in prepare_packets(args.packet_csv, args.output_dir):
        print(path)


if __name__ == "__main__":
    main()