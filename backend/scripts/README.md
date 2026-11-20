# backend/scripts: which script is for what

Tests import several of these by name, so the files stay in one folder. Read them in these groups.

**Current research evaluation (HAMMER pilot toolkit; logic lives in `hammer_pilot/`)**
`capture_hammer_pilot.py` (record provider responses with hashes) · `replay_hammer_pilot.py` (offline replay) · `validate_hammer_pilot.py` · `verify_hammer_pilot_reproducibility.py` · `build_block_catalog.py` · `build_selection_manifest.py` (draw pilot, main or audit sample) · `run_helpers.py` (capture inputs, pilot counts, audit frame) · `size_hammer_main_sample.py` (sample-size planning) · `freeze_evaluation.py` (record code, settings, seeds) · `assemble_c7_report.py` · `prepare_review_release.py` (blinded reviewer packets) · `analyze_free_evaluation.py` (exploratory results) · `validate_methodology_by_simulation.py` · `prepare_lagos_and_seeds.py` · `analyze_lagos_smoke_capture.py`

**Earlier evaluation chain (kept because tests still use it; the numbers it produced are historical)**
`evaluation_dataset.py` · `build_benchmark_v3.py` · `evaluate_benchmark.py` · `evaluate_resolution_pilot.py` · `capture_retrieval_predictions.py` · `replay_frozen_resolver.py` · `seal_evaluation_manifest.py` · `freeze_split_manifest.py` · `validate_evaluation_dataset.py` · `prepare_identity_review.py` · `prepare_retrieval_review.py` · `merge_identity_reviews.py` · `merge_retrieval_reviews.py` · `run_day4_shadow_evaluation.py` · `run_day5_e2e_evaluation.py` · `run_phase4_evaluations.py` · `run_remaining_evaluations.py` · `generate_*_report.py`

**Application utilities**
`build_vector_index.py` (rebuild the semantic search index) · `prewarm_cache.py` · `smoke_llm_provider.py` (check the Gemini connection)
