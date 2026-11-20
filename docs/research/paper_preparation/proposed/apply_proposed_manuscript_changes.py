"""Apply the proposed manuscript changes (Section 5 final protocol, Section 6 scaffold, Section 8 limitations, the \\tbd macro) to a paper directory.
Refuses to run without --apply. Backs up every file it changes into <paper>/_backup_before_final_protocol/ (new directory; refuses to overwrite).
  python docs/research/paper_preparation/proposed/apply_proposed_manuscript_changes.py --paper-dir paper/HAMMER_IEEE_PAPER --apply
Validation without touching the real manuscript: run it on a COPY of the paper directory, then run paper/check_manuscript.py on the copy."""
import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper-dir", type=Path, required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("refused: pass --apply to change the manuscript", file=sys.stderr)
        return 2
    paper = a.paper_dir
    backup = paper / "_backup_before_final_protocol"
    backup.mkdir(parents=False, exist_ok=False)
    targets = ["main.tex", "sections/05_experimental_design.tex", "sections/06_results.tex", "sections/08_threats_limitations.tex"]
    for t in targets:
        shutil.copy2(paper / t, backup / t.replace("/", "__"))

    main = (paper / "main.tex").read_text(encoding="utf-8")
    anchor = "\\newcommand{\\hammer}{\\textsc{HAMMER}}"
    assert main.count(anchor) == 1
    main = main.replace(anchor, anchor + "\n% Visible placeholder for a value that is fixed at the evaluation freeze (never a result).\n\\newcommand{\\tbd}[1]{\\textcolor{red}{[#1]}}")
    (paper / "main.tex").write_text(main, encoding="utf-8")

    s5 = (paper / "sections/05_experimental_design.tex").read_text(encoding="utf-8")
    cut = s5.index("\\subsection{Independent Label Audit}")
    head = s5[:cut]
    edits = [
        ("This section separates what has been done from what is planned. Three things have been done: the benchmark was downloaded, verified and sampled; a 50-case seed set was frozen; and an operational smoke capture of OpenAlex responses was captured and replayed offline. Everything else is planned: the independent label audit, the affiliation-cleaning decision, the main sample, the main evaluation and the statistical analysis. Fig.~\\ref{fig:pipeline} shows the workflow, and the planned stages are drawn with dashed outlines.",
         "This section separates what has been done from what is planned. Four things have been done: the benchmark was downloaded, verified, sampled and re-verified, and its eligible frame was counted; a 50-case seed set was frozen; an operational smoke capture of OpenAlex responses was captured and replayed offline; and the tooling that will run the evaluation was implemented and validated on synthetic data. Everything else is planned: the coverage pilot, the main sample, the independent verification, the main evaluation and its analysis. Fig.~\\ref{fig:pipeline} shows the workflow, and the planned stages are drawn with dashed outlines."),
        ("The archive was processed by streaming and deleted afterwards. Table~\\ref{tab:dataset} gives the characteristics we measured.",
         "The archive was processed by streaming. It was obtained a second time and verified again against the same size, MD5 and SHA-256 checksums, and the block catalog built from it reproduced every count in Table~\\ref{tab:dataset} and the size-band counts of Section~\\ref{sec:seeds}. Table~\\ref{tab:dataset} gives the characteristics we measured."),
        ("\\subsection{Seed Preparation}", "\\subsection{Smoke Sample}"),
        ("These are the reasons for the independent audit of Section~\\ref{sec:audit}.", "These are the reasons for the independent verification of Sections~\\ref{sec:labels} and~\\ref{sec:audit}."),
    ]
    for old, new in edits:
        assert head.count(old) == 1, old[:60]
        head = head.replace(old, new)
    tail = (HERE / "SECTION5_tail_final_protocol.tex").read_text(encoding="utf-8")
    tail = "\n".join(l for l in tail.splitlines() if not l.startswith("% PROPOSED") and not l.startswith("% NOT APPLIED")) + "\n"
    (paper / "sections/05_experimental_design.tex").write_text(head + tail, encoding="utf-8")
    for src, dst in (("SECTION6_results_scaffold.tex", "sections/06_results.tex"), ("SECTION8_threats_limitations.tex", "sections/08_threats_limitations.tex")):
        (paper / dst).write_text((HERE / src).read_text(encoding="utf-8"), encoding="utf-8")
    checker = paper.parent / "check_manuscript.py"
    if checker.exists():
        shutil.copy2(checker, backup / "check_manuscript.py")
        c = checker.read_text(encoding="utf-8")
        old_loop = '    for inc in re.findall(r"\\\\input\\{([^}]+)\\}", text):\n        p = ROOT / (inc if inc.endswith(".tex") else inc + ".tex")\n        if not p.exists():\n            errors.append(f"missing \\\\input file: {inc}")'
        new_loop = '    optional = set(re.findall(r"\\\\IfFileExists\\{([^}]+)\\}\\{\\\\input", text))   # generated tables that appear only after a frozen evaluation\n    for inc in re.findall(r"\\\\input\\{([^}]+)\\}", text):\n        p = ROOT / (inc if inc.endswith(".tex") else inc + ".tex")\n        if not p.exists() and inc in optional:\n            warnings.append(f"optional \\\\input file not generated yet: {inc}")\n        elif not p.exists():\n            errors.append(f"missing \\\\input file: {inc}")'
        if c.count(old_loop) == 1 and "warnings" in c:
            checker.write_text(c.replace(old_loop, new_loop), encoding="utf-8")
            print("checker updated: guarded optional inputs are warnings")
        else:
            print("checker not changed (unexpected layout)")
    print("applied; originals saved in", backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
