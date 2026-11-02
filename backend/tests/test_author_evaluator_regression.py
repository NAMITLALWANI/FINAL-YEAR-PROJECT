import json
import pytest
from pathlib import Path

# Resolve project root from backend/tests/ -> backend/ -> project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_evaluator_recognizes_production_status_constants():
    """Verify evaluator maps production status 'auto_selected' correctly."""
    from services.author_resolution import AUTO_RESOLVED, MANUAL_REVIEW, UNRESOLVED
    
    assert AUTO_RESOLVED == "auto_selected"
    assert MANUAL_REVIEW == "manual_selection_required"
    assert UNRESOLVED == "unresolved"

def test_benchmark_v2_status_counts():
    """Verify v2 benchmark yields exactly 13 auto_selected, 52 manual_selection, 35 unresolved."""
    v2_path = _PROJECT_ROOT / "docs/audit/phase4/results/author_resolution_benchmark_100_v2_corrected.json"
    assert v2_path.exists(), f"Benchmark v2 file must exist at {v2_path}"
    
    data = json.loads(v2_path.read_text())
    assert data["total_queries"] == 100
    assert data["decisions"]["auto_selected"] == 13
    assert data["decisions"]["manual_selection_required"] == 52
    assert data["decisions"]["unresolved"] == 35

def test_evaluator_reports_non_zero_auto_coverage():
    """Ensure auto_coverage uses auto_selected rather than obsolete auto_resolved."""
    v2_path = _PROJECT_ROOT / "docs/audit/phase4/results/author_resolution_benchmark_100_v2_corrected.json"
    data = json.loads(v2_path.read_text())
    metrics = data["metrics"]
    
    assert metrics["auto_coverage"] == 0.13
    assert metrics["auto_coverage_denominator"] == 100
    assert metrics["strict_auto_precision"] == 1.0
    assert metrics["precision_denominator"] == 13

def test_original_benchmark_preserved_immutably():
    """Ensure original benchmark artifact is unchanged and present."""
    orig_path = _PROJECT_ROOT / "docs/audit/phase4/results/author_resolution_benchmark_100.json"
    assert orig_path.exists(), f"Original benchmark must be preserved immutably at {orig_path}"
    
    orig_data = json.loads(orig_path.read_text())
    assert orig_data["total_queries"] == 100
    assert orig_data["decisions"]["auto_selected"] == 13
