#!/usr/bin/env python3
"""Regenerate the manuscript's three vector figures (PDF).

    python3 figures/make_figures.py            # writes architecture.pdf, methodology.pdf, evaluation_pipeline.pdf
    python3 figures/make_figures.py --png DIR  # also writes PNG previews into DIR (not part of the manuscript)

Source of truth for every label is the repository (see sections 03-05 of the manuscript); change the
labels here, not in the PDFs. Fonts are embedded as TrueType (fonttype 42) for IEEE compliance.
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

matplotlib.rcParams.update({
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "font.family": "serif", "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix", "font.size": 7,
})

FIG_DIR = Path(__file__).resolve().parent
INK = "#1a1a1a"
GREY = "#6b6b6b"
STYLES = {
    # fill, edge, linestyle, text colour
    "used":    ("#dce9f7", INK, "-", INK),      # takes part in the author-resolution experiment
    "store":   ("#f3ecd2", INK, "-", INK),      # persistent store
    "unused":  ("#ffffff", INK, "-", INK),      # implemented system component, not used in the experiment
    "out":     ("#e4f1e0", INK, "-", INK),      # decision outcome
    "neutral": ("#f2f2f2", INK, "-", INK),
    "done":    ("#e4f1e0", INK, "-", INK),
    "planned": ("#ffffff", INK, (0, (3, 2)), INK),
    "lane":    ("#fafafa", "#b0b0b0", "-", INK),
}


def new_fig(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, style="used", fs=6.4, bold_first=False, lw=0.7, rounding=0.04, ha="center", head_lines=1):
    fill, edge, ls, tc = STYLES[style]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rounding}",
                                fc=fill, ec=edge, lw=lw, ls=ls, zorder=2))
    tx = x + (w / 2 if ha == "center" else 0.06)
    if bold_first and "\n" in text:
        lines = text.split("\n")
        head, rest = "\n".join(lines[:head_lines]), "\n".join(lines[head_lines:])
        ax.text(tx, y + h - 0.045, head, ha=ha, va="top", fontsize=fs, color=tc, fontweight="bold", zorder=3, linespacing=1.15)
        ax.text(tx, y + h - 0.045 - head_lines * fs / 72 * 1.32 - 0.02, rest, ha=ha, va="top", fontsize=fs - 0.4, color=tc, zorder=3, linespacing=1.15)
    else:
        ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=fs, color=tc, zorder=3, linespacing=1.15)


def arrow(ax, p0, p1, style="-|>", lw=0.8, ls="-", color=INK, rad=0.0):
    ax.annotate("", xy=p1, xytext=p0, zorder=4,
                arrowprops=dict(arrowstyle=style, lw=lw, color=color, ls=ls, shrinkA=0, shrinkB=0,
                                connectionstyle=f"arc3,rad={rad}", mutation_scale=7))


def lane(ax, x, y, w, h, label):
    fill, edge, ls, _ = STYLES["lane"]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.05", fc=fill, ec=edge, lw=0.8, zorder=0))
    ax.text(x + 0.07, y + h - 0.05, label, ha="left", va="top", fontsize=7.2, fontweight="bold", color=INK, zorder=1)


def legend(ax, x, y, items, fs=6.3):
    cx = x
    for style, label, width in items:
        fill, edge, ls, tc = STYLES[style]
        ax.add_patch(FancyBboxPatch((cx, y), 0.22, 0.12, boxstyle="round,pad=0,rounding_size=0.02", fc=fill, ec=edge, lw=0.7, ls=ls, zorder=2))
        ax.text(cx + 0.28, y + 0.06, label, ha="left", va="center", fontsize=fs, color=INK)
        cx += width


def save(fig, name, png_dir):
    fig.savefig(FIG_DIR / f"{name}.pdf")
    if png_dir:
        Path(png_dir).mkdir(parents=True, exist_ok=True)
        fig.savefig(Path(png_dir) / f"{name}.png", dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------- Figure 1: architecture
def architecture(png_dir):
    W, H = 7.16, 3.46
    fig, ax = new_fig(W, H)

    lane(ax, 0.04, 2.04, W - 0.08, 1.20, "Work level: publication matching and deduplication")
    by, bh = 2.12, 0.78
    xs = [0.12, 1.30, 2.48, 3.66]
    box(ax, xs[0], by, 0.98, bh, "Providers\nOpenAlex, Crossref,\nDBLP, arXiv,\nScholar profile,\nfaculty pages", "unused", bold_first=True)
    box(ax, xs[1], by, 0.98, bh, "Connectors\nasync fan-out;\nper-source status;\nraw record kept", "unused", bold_first=True)
    box(ax, xs[2], by, 0.98, bh, "Normalization\nCanonicalRecord:\nDOI, title, authors,\nyear, venue", "unused", bold_first=True)
    box(ax, xs[3], by, 1.22, bh, "Deduplication\nDOI-conflict, edition and\nyear vetoes; fuzzy title,\nauthor, year score", "unused", bold_first=True)
    box(ax, 5.02, by, 1.02, bh, "SQLite\nsource_records,\npublications,\nduplicate_groups", "store", bold_first=True)
    box(ax, 6.14, 2.32, 0.94, 0.54, "ChromaDB index\n(derived) and LLM\nexplanation", "unused", fs=6.0)
    for a, b in [(xs[0] + 0.98, xs[1]), (xs[1] + 0.98, xs[2]), (xs[2] + 0.98, xs[3]), (xs[3] + 1.22, 5.02)]:
        arrow(ax, (a, by + bh / 2), (b, by + bh / 2))
    arrow(ax, (6.04, by + bh / 2 + 0.05), (6.14, by + bh / 2 + 0.05), ls=(0, (2, 1.5)), color=GREY)

    lane(ax, 0.04, 0.46, W - 0.08, 1.48, "Person level: author candidate retrieval and identity resolution")
    by2, bh2 = 0.56, 1.06
    box(ax, 0.12, by2, 0.88, bh2, "Query\nauthor name and\noptional context\n(institution, years,\nDOIs, coauthor IDs)", "used", bold_first=True, fs=6.2)
    box(ax, 1.10, by2, 0.98, bh2, "Candidate retrieval\nOpenAlex author\nsearch, at most\n10 profiles", "used", bold_first=True, fs=6.2)
    box(ax, 2.18, by2, 1.00, bh2, "Enrichment\nbounded OpenAlex\nworks look-ups, only\nif DOIs or coauthor\nIDs were supplied", "used", bold_first=True, fs=6.2)
    box(ax, 3.28, by2, 0.98, bh2, "Evidence\nfive signals, each\nobserved or\nunavailable, with\nprovenance", "used", bold_first=True)
    box(ax, 4.36, by2, 0.94, bh2, "Scoring, ranking\nrenormalised\nheuristic score,\nnot a probability", "used", bold_first=True, fs=6.2)
    box(ax, 5.40, by2, 0.86, bh2, "Decision policy\nscore, margin,\ndominance, signal\ncount, safeguards", "used", bold_first=True, fs=6.2)
    xo = 6.36
    box(ax, xo, 1.18, 0.74, 0.44, "Automatic\nassignment", "out", fs=6.0)
    box(ax, xo, 0.88, 0.74, 0.26, "Manual review", "out", fs=6.0)
    box(ax, xo, 0.56, 0.74, 0.28, "Unresolved", "out", fs=6.0)
    for a, b in [(1.00, 1.10), (2.08, 2.18), (3.18, 3.28), (4.26, 4.36), (5.30, 5.40)]:
        arrow(ax, (a, by2 + bh2 / 2), (b, by2 + bh2 / 2))
    for yy in (1.40, 1.01, 0.70):
        arrow(ax, (6.26, by2 + bh2 / 2), (xo, yy), lw=0.6)
    box(ax, 1.10, 0.06, 5.16, 0.26, "SQLite (application only): author_candidates, author_resolutions, author_resolution_evidence", "store", fs=6.0)
    arrow(ax, (5.83, by2), (5.83, 0.32), lw=0.6)
    ax.text(0.12, 0.19, "Provider failure: no decision\nis recorded", ha="left", va="center", fontsize=5.8, color=INK, linespacing=1.1)
    ax.text(6.36, 0.19, "Empty pool: unresolved", ha="left", va="center", fontsize=5.8, color=INK)

    ax.text(W / 2, 1.99, "no score or confidence passes between the two levels", ha="center", va="center", fontsize=6.2, style="italic", color=INK,
            bbox=dict(fc="white", ec="none", pad=1.2), zorder=5)
    legend(ax, 0.12, 3.32, [("used", "used in the author-resolution experiment", 2.40), ("unused", "implemented, not used in it", 1.85),
                            ("store", "persistent store", 1.2)])
    save(fig, "architecture", png_dir)


# ---------------------------------------------------------------- Figure 2: methodology
def methodology(png_dir):
    W, H = 7.16, 3.06
    fig, ax = new_fig(W, H)
    top, th = 2.16, 0.86
    box(ax, 0.06, top, 1.12, th, "Query context\nC0 name only\nC1 + institution,\none-year range\nC1x + designated DOI", "used", bold_first=True, fs=6.2)
    box(ax, 1.38, top, 1.28, th, "Candidate pool\nR0 raw query; R2 cleaned\nquery + initials fallback\nstatus: ok, empty, failed", "used", bold_first=True, fs=6.2)
    box(ax, 2.86, top, 1.28, th, "Evidence\nname, institution,\npublication, coauthor,\ntemporal: observed\nor unavailable", "used", bold_first=True, fs=6.2)
    box(ax, 4.34, top, 1.30, th, "Score and rank\n$s=\\sum w_k e_k\\,/\\sum w_k$ over\nobserved signals;\nties: higher source ID", "used", bold_first=True, fs=6.2)
    box(ax, 5.84, top, 1.26, th, "Top candidate $c_1$\n$s_1$, second score $s_2$,\nmargin $=s_1-s_2$,\ndominance $=s_1/s_2$", "used", bold_first=True, fs=6.2)
    for a, b in [(1.18, 1.38), (2.66, 2.86), (4.14, 4.34), (5.64, 5.84)]:
        arrow(ax, (a, top + th / 2), (b, top + th / 2))

    py, ph = 0.88, 1.00
    ax.add_patch(FancyBboxPatch((0.06, py), 7.04, ph, boxstyle="round,pad=0,rounding_size=0.04", fc="#f2f2f2", ec=INK, lw=0.7, zorder=1))
    ax.text(0.12, py + ph - 0.05, "Decision policy (applied to the ranked pool)", ha="left", va="top", fontsize=6.6, fontweight="bold", zorder=3)
    ax.text(0.12, py + ph - 0.22,
            "Threshold gates, all required\n"
            "G1  $s_1\\geq 0.75$ and at least two observed signals for $c_1$\n"
            "G2  margin $\\geq 0.15$ and dominance $\\geq 1.35$ against the best\n"
            "      scored competitor (dominance skipped if $s_2=0$);\n"
            "      fails if no competitor has a score\n"
            "G3  single-candidate pool: G2 is waived; G1 and B1-B5 apply",
            ha="left", va="top", fontsize=6.0, zorder=3, linespacing=1.18)
    ax.plot([3.30, 3.30], [py + 0.06, py + ph - 0.08], color=GREY, lw=0.6, zorder=2)
    ax.text(3.38, py + ph - 0.22,
            "Safeguards, any one withholds automatic assignment\n"
            "B1  at least one competitor has no score\n"
            "B2  no observed, non-zero institution, publication or coauthor signal for $c_1$\n"
            "B3  $c_1$ has an observed signal equal to 0\n"
            "B4  a competitor was scored on a different signal set than $c_1$\n"
            "B5  an enrichment request failed, or a candidate was unreadable",
            ha="left", va="top", fontsize=6.0, zorder=3, linespacing=1.18)
    arrow(ax, (6.47, top), (6.47, py + ph))

    oy, oh = 0.14, 0.50
    box(ax, 0.06, oy, 2.15, oh, "Automatic assignment\nG1 and G2 pass (or G3 applies) and no safeguard applies", "out", bold_first=True, fs=6.4)
    box(ax, 2.31, oy, 2.28, oh, "Manual review\nnot automatic and $s_1\\geq 0.45$", "out", bold_first=True, fs=6.4)
    box(ax, 4.69, oy, 2.41, oh, "Unresolved\nnot automatic and $s_1<0.45$", "out", bold_first=True, fs=6.4)
    for x in (1.14, 3.45, 5.90):
        arrow(ax, (x, py), (x, oy + oh))
    ax.text(0.06, 0.04, "Reported as separate categories, not as unresolved: provider failure (no decision recorded), successful empty pool, no defined score.",
            ha="left", va="bottom", fontsize=5.8, color=INK)
    save(fig, "methodology", png_dir)


# ---------------------------------------------------------------- Figure 3: experimental workflow
def evaluation_pipeline(png_dir):
    W, H = 7.16, 2.02
    fig, ax = new_fig(W, H)
    n, gap = 7, 0.075
    bw = (W - 0.12 - gap * (n - 1)) / n
    bh, by = 0.98, 0.58
    stages = [
        ("1 Benchmark\nand frame", "archive verified;\ntest frame counted;\n50-case smoke set", "done"),
        ("2 Pilot and\nsizing", "label-free coverage\npilot; stratified\npredictive sizing", "planned"),
        ("3 Sample and\ncapture", "one case per block;\nfrozen manifest;\nhashed responses", "planned"),
        ("4 Replay and\nfreeze", "offline replay;\npredictions hashed\nbefore any label", "planned"),
        ("5 Blinded\nverification", "allow-list packets;\ntwo reviewers +\nadjudicator", "planned"),
        ("6 Metrics", "denominators fixed;\nverified and\nbenchmark apart", "done"),
        ("7 Inference", "exact and stratified\nintervals; sparse\nrules", "done"),
    ]
    for i, (head, body, st) in enumerate(stages):
        x = 0.06 + i * (bw + gap)
        box(ax, x, by, bw, bh, "", st)
        nh = head.count("\n") + 1
        ax.text(x + bw / 2, by + bh - 0.06, head, ha="center", va="top", fontsize=6.5, fontweight="bold", zorder=4, linespacing=1.15)
        ax.text(x + bw / 2, by + bh - 0.06 - nh * 0.125 - 0.06, body, ha="center", va="top", fontsize=6.0, zorder=4, linespacing=1.15)
        if i < n - 1:
            arrow(ax, (x + bw, by + bh / 2), (x + bw + gap, by + bh / 2), lw=0.7)
    ax.text(0.06, 0.48, "Green stages are complete: stage 1 at smoke scale (no correctness scored) and stages 6 and 7 as validated tooling on synthetic data.\n"
                        "Dashed stages are planned for the main evaluation and have not been run.", ha="left", va="top", fontsize=6.0, linespacing=1.2)
    legend(ax, 0.06, 1.84, [("done", "complete (smoke scale or validated tooling)", 2.9), ("planned", "planned (main evaluation)", 1.9)])
    save(fig, "evaluation_pipeline", png_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--png", default=None, help="optional directory for PNG previews")
    args = parser.parse_args()
    architecture(args.png)
    methodology(args.png)
    evaluation_pipeline(args.png)
    print("figures written to", FIG_DIR)
