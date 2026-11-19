"""Run the replay pipeline twice on the same frozen inputs and byte-compare all outputs."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from hammer_pilot.manifest import git_state
from hammer_pilot.pipeline import run_pipeline


RUN_ID = "reproducibility-check"     # fixed across both comparison replays


async def verify_reproducibility(pilot_dir: Path, work_dir: Path) -> dict[str, Any]:
    work_dir = Path(work_dir)
    if work_dir.exists() and any(work_dir.iterdir()):
        raise FileExistsError(f"work directory must be new or empty: {work_dir}")
    state = git_state()          # captured once so run_a's own output cannot change run_b's manifest
    a, b = work_dir / "run_a", work_dir / "run_b"
    await run_pipeline(pilot_dir, a, git=state, run_id=RUN_ID)
    await run_pipeline(pilot_dir, b, git=state, run_id=RUN_ID)
    names_a = sorted(p.name for p in a.iterdir())
    names_b = sorted(p.name for p in b.iterdir())
    differing = [n for n in names_a if n in names_b and (a / n).read_bytes() != (b / n).read_bytes()]
    return {"identical": names_a == names_b and not differing, "files": names_a, "differing": differing, "run_id": RUN_ID,
            "bytes_compared": sum((a / n).stat().st_size for n in names_a)}
