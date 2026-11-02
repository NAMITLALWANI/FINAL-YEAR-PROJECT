"""Day 5: Production-integrated candidate normalization tests.

These tests verify the normalization functions that are now deployed in
backend/services/author_candidates.py as part of the live candidate
generation pipeline.
"""
import pytest
import sys
from pathlib import Path

# Add backend to path for direct imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.author_candidates import clean_query_name, is_institutional_input, _has_initial_token


class TestCleanQueryName:
    """Tests for conservative query normalization."""

    def test_whitespace_normalization(self):
        assert clean_query_name("  Yann   LeCun  ") == "Yann LeCun"
        assert clean_query_name("Geoffrey\t\tHinton\n") == "Geoffrey Hinton"

    def test_unicode_nfc_normalization(self):
        """Composed vs decomposed accents must converge."""
        decomposed = "Ju\u0308rgen Schmidhuber"  # u + combining umlaut
        composed = "Jürgen Schmidhuber"
        assert clean_query_name(decomposed) == composed

    def test_compound_name_merge(self):
        """'Le Cun' merges to 'LeCun' (Day 4 verified recovery)."""
        assert clean_query_name("Yann Le Cun") == "Yann LeCun"
        assert clean_query_name("Yann  Le Cun") == "Yann LeCun"

    def test_preserve_legitimate_particles(self):
        """Surname particles von/van/de must never be concatenated."""
        assert clean_query_name("Ludwig von Mises") == "Ludwig von Mises"
        assert clean_query_name("Guido van Rossum") == "Guido van Rossum"
        assert clean_query_name("Paul de Man") == "Paul de Man"
        assert clean_query_name("Otto von Bismarck") == "Otto von Bismarck"

    def test_empty_and_malformed_inputs(self):
        assert clean_query_name("") == ""
        assert clean_query_name("   ") == ""

    def test_single_token_passthrough(self):
        assert clean_query_name("Hinton") == "Hinton"

    def test_initial_not_merged(self):
        """Initial tokens (e.g. 'Y.') should not trigger merge."""
        assert clean_query_name("Y. LeCun") == "Y. LeCun"
        assert clean_query_name("M. I. Jordan") == "M. I. Jordan"


class TestInstitutionalInputDetection:
    """Tests for is_institutional_input guard."""

    def test_detect_department_strings(self):
        assert is_institutional_input("Department of Statistics UC Berkeley") is True
        assert is_institutional_input("Dept. of Computer Science") is True
        assert is_institutional_input("Division of Engineering") is True

    def test_detect_institute_strings(self):
        assert is_institutional_input("UW Institute for Protein Design") is True
        assert is_institutional_input("Center for AI Research") is True

    def test_detect_lab_strings(self):
        assert is_institutional_input("Microsoft Research Lab") is True
        assert is_institutional_input("Google Labs") is True

    def test_reject_person_names(self):
        assert is_institutional_input("Yann LeCun") is False
        assert is_institutional_input("Michael I. Jordan") is False
        assert is_institutional_input("Brian Smith") is False
        assert is_institutional_input("Christopher Bishop") is False

    def test_empty_input(self):
        assert is_institutional_input("") is False
        assert is_institutional_input("   ") is False


class TestInitialTokenDetection:
    """Tests for _has_initial_token helper."""

    def test_detect_initials(self):
        assert _has_initial_token("Y. LeCun") is True
        assert _has_initial_token("M. I. Jordan") is True
        assert _has_initial_token("A. Ng") is True

    def test_no_initials(self):
        assert _has_initial_token("Yann LeCun") is False
        assert _has_initial_token("Geoffrey Hinton") is False

def test_clean_query_name_does_not_merge_short_given_names():
    assert clean_query_name("Ian Goodfellow") == "Ian Goodfellow"
    assert clean_query_name("Dan Klein") == "Dan Klein"
    assert clean_query_name("Rob Pike") == "Rob Pike"
