"""Edition guard regression tests. Same-year pairs are used so the year-gap veto cannot mask the edition guard."""
import re

from deduplication import engine
from pipeline.deduplicate import deduplicate
from pipeline.normalize import normalize


def record(source_id, title, year=2018, doi=""):
    return normalize({"source": "crossref", "source_id": source_id, "title": title, "authors": ["R. Sutton", "A. Barto"], "year": year, "doi": doi})


def test_regex_contains_word_boundaries_not_backspace_bytes():
    assert "\x08" not in engine._EDITION_RE.pattern
    assert engine._EDITION_RE.pattern.startswith(r"\b") and engine._EDITION_RE.pattern.endswith(r"\b")


def test_edition_extraction_cases():
    assert engine._extract_edition("Reinforcement Learning (1st Edition)") == 1
    assert engine._extract_edition("Reinforcement Learning (2nd Edition)") == 2
    assert engine._extract_edition("Reinforcement Learning, second edition") == 2
    assert engine._extract_edition("Reinforcement Learning 3rd ed") == 3
    assert engine._extract_edition("Reinforcement Learning: An Introduction") is None
    assert engine._extract_edition("The 20th Century Games") is None           # "th" without "ed" is not an edition


def test_edition_conflict_detection():
    assert engine._has_edition_conflict("RL (1st Edition)", "RL (2nd Edition)")
    assert engine._has_edition_conflict("RL second edition", "RL 3rd ed")
    assert not engine._has_edition_conflict("RL (2nd Edition)", "RL (2nd Edition)")
    assert not engine._has_edition_conflict("RL", "RL (2nd Edition)")           # missing edition is not a conflict
    assert not engine._has_edition_conflict("RL", "RL")


def test_same_year_different_editions_do_not_merge():
    pubs, _ = deduplicate([
        record("s1", "Reinforcement Learning: An Introduction (1st Edition)"),
        record("s2", "Reinforcement Learning: An Introduction (2nd Edition)"),
    ])
    assert len(pubs) == 2


def test_same_year_word_and_abbreviated_editions_do_not_merge():
    pubs, _ = deduplicate([
        record("s1", "Reinforcement Learning: An Introduction, second edition"),
        record("s2", "Reinforcement Learning: An Introduction 3rd ed"),
    ])
    assert len(pubs) == 2


def test_same_edition_still_merges():
    pubs, _ = deduplicate([
        record("s1", "Reinforcement Learning: An Introduction (2nd Edition)"),
        record("s2", "Reinforcement Learning: An Introduction (2nd Edition)"),
    ])
    assert len(pubs) == 1


def test_records_without_edition_information_still_merge():
    pubs, _ = deduplicate([
        record("s1", "Reinforcement Learning: An Introduction"),
        record("s2", "Reinforcement Learning: An Introduction"),
    ])
    assert len(pubs) == 1
