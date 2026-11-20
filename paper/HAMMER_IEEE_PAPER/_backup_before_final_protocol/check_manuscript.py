#!/usr/bin/env python3
"""Static consistency checks for the HAMMER IEEE manuscript (no LaTeX engine required).

This does NOT replace a real compile. It catches: missing citation keys, unused or malformed
bibliography entries, missing \\input files, undefined/unused labels, unbalanced braces and
mismatched environments. Run: python3 check_manuscript.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent / "HAMMER_IEEE_PAPER"
errors, warnings = [], []


def strip_comments(text):
    out = []
    for line in text.splitlines():
        m = re.search(r"(?<!\\)%", line)
        out.append(line[: m.start()] if m else line)
    return "\n".join(out)


def read_tex(path, seen):
    text = strip_comments(path.read_text(encoding="utf-8"))
    for inc in re.findall(r"\\input\{([^}]+)\}", text):
        p = ROOT / (inc if inc.endswith(".tex") else inc + ".tex")
        if not p.exists():
            errors.append(f"missing \\input file: {inc}")
        elif p not in seen:
            seen.add(p)
            text += "\n" + read_tex(p, seen)
    return text


seen = {ROOT / "main.tex"}
tex = read_tex(ROOT / "main.tex", seen)
files = sorted(seen)

for f in files:
    t = strip_comments(f.read_text(encoding="utf-8"))
    depth = 0
    for i, ch in enumerate(t):
        if ch in "{}" and (i == 0 or t[i - 1] != "\\"):
            depth += 1 if ch == "{" else -1
            if depth < 0:
                errors.append(f"{f.name}: unmatched closing brace")
                depth = 0
    if depth != 0:
        errors.append(f"{f.name}: {depth} unclosed brace(s)")
    begins = re.findall(r"\\begin\{([^}]+)\}", t)
    ends = re.findall(r"\\end\{([^}]+)\}", t)
    if sorted(begins) != sorted(ends):
        errors.append(f"{f.name}: \\begin/\\end mismatch {sorted(begins)} vs {sorted(ends)}")

bib_text = (ROOT / "references.bib").read_text(encoding="utf-8")
bib_text_nc = "\n".join(l for l in bib_text.splitlines() if not l.lstrip().startswith("%"))
entries = {}
for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)(?=\n@|\Z)", bib_text_nc, re.S):
    kind, key, body = m.groups()
    if key in entries:
        errors.append(f"duplicate bib key: {key}")
    entries[key] = (kind.lower(), body)
    for field in ("author", "title", "year"):
        if not re.search(rf"\b{field}\s*=", body):
            errors.append(f"bib {key}: missing {field}")
    if not re.search(r"\b(doi|url|eprint)\s*=", body):
        warnings.append(f"bib {key}: no doi/url/eprint")

cited = set()
for grp in re.findall(r"\\cite\w*\{([^}]+)\}", tex):
    cited.update(k.strip() for k in grp.split(","))
for k in sorted(cited - set(entries)):
    errors.append(f"cited but not in references.bib: {k}")
for k in sorted(set(entries) - cited):
    warnings.append(f"in references.bib but not cited (will not print): {k}")

labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
refs = set()
for grp in re.findall(r"\\ref\{([^}]+)\}", tex):
    refs.add(grp.strip())
for k in sorted(refs - labels):
    errors.append(f"\\ref to undefined label: {k}")
for k in sorted(labels - refs):
    warnings.append(f"label never referenced: {k}")


# ---- figures, captions, numbering (added in Stage 2)
figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
for f in figs:
    if not (ROOT / f).is_file():
        errors.append(f"missing figure file: {f}")
    elif not (ROOT / "figures" / "make_figures.py").is_file():
        errors.append("figure source figures/make_figures.py missing")
for env in ("figure", "figure*", "table", "table*"):
    n_begin = len(re.findall(r"\\begin\{" + re.escape(env) + r"\}", tex))
    n_cap = 0
    for m in re.finditer(r"\\begin\{" + re.escape(env) + r"\}(.*?)\\end\{" + re.escape(env) + r"\}", tex, re.S):
        body = m.group(1)
        if "\\caption" not in body:
            errors.append(f"{env} without caption")
        if "\\label" not in body:
            errors.append(f"{env} without label")
        n_cap += 1
fig_labels = [l for l in labels if l.startswith("fig:")]
tab_labels = [l for l in labels if l.startswith("tab:")]
print(f"figures: {len(fig_labels)} labelled ({len(figs)} included); tables: {len(tab_labels)} labelled")
for l in fig_labels + tab_labels:
    if l not in refs:
        warnings.append(f"float label never referenced in text: {l}")
for f in sorted((ROOT / "figures").glob("*.pdf")):
    if f.stat().st_size < 1000:
        errors.append(f"suspiciously small figure: {f.name}")

if not re.search(r"\\documentclass\[[^\]]*conference[^\]]*\]\{IEEEtran\}", (ROOT / "main.tex").read_text()):
    errors.append("main.tex is not IEEEtran conference mode")

print(f"files checked: {len(files)}; bib entries: {len(entries)}; distinct citations: {len(cited)}; labels: {len(labels)}")
for w in warnings:
    print("WARN ", w)
for e in errors:
    print("ERROR", e)
print("RESULT:", "FAIL" if errors else "PASS (static checks only; not a compile)")
sys.exit(1 if errors else 0)
