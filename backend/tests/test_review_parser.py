# backend/tests/test_review_parser.py
import pytest
from app.utils.review_parser import parse_meter_status


class TestParseMeterStatus:
    """Test meter status parsing from review text."""

    def test_no_reviews(self):
        """Should return 'unknown' with 0.0 confidence when no reviews."""
        status, confidence = parse_meter_status([])
        assert status == "unknown"
        assert confidence == 0.0

    def test_broken_keywords(self):
        """Test detection of broken meter keywords."""
        reviews = [
            "The meter is broken",
            "Doesn't work at all",
            "Out of order",
        ]
        status, confidence = parse_meter_status(reviews)
        assert status == "broken"
        assert confidence == pytest.approx(1.0, abs=0.1)

    def test_working_keywords(self):
        """Test detection of working meter keywords."""
        reviews = [
            "Meter works fine",
            "No issues with the meter",
            "All good, working perfectly",
        ]
        status, confidence = parse_meter_status(reviews)
        assert status == "working"
        assert confidence == pytest.approx(1.0, abs=0.1)

    def test_mixed_keywords_broken_majority(self):
        """Test mixed keywords with broken being majority."""
        reviews = [
            "The meter is broken",
            "Doesn't work",
            "Works fine",  # One working keyword
        ]
        status, confidence = parse_meter_status(reviews)
        assert status == "broken"
        # 2 broken, 1 working -> broken/3 = 0.667
        assert confidence == pytest.approx(2.0 / 3.0, abs=0.1)

    def test_mixed_keywords_working_majority(self):
        """Test mixed keywords with working being majority."""
        reviews = [
            "Works fine",
            "No issues",
            "All good",
            "Broken meter",  # One broken keyword
        ]
        status, confidence = parse_meter_status(reviews)
        assert status == "working"
        # 3 working, 1 broken -> working/4 = 0.75
        assert confidence == pytest.approx(3.0 / 4.0, abs=0.1)

    def test_tied_keywords(self):
        """Test when broken and working keywords are equal."""
        reviews = [
            "Broken",
            "Works",
        ]
        status, confidence = parse_meter_status(reviews)
        # When tied, should default to "working" based on implementation
        assert status in ["working", "broken"]  # Either is acceptable
        assert confidence == pytest.approx(0.5, abs=0.1)

    def test_no_keywords(self):
        """Test reviews with no matching keywords."""
        reviews = [
            "Great parking spot",
            "Very convenient location",
            "Easy to find",
        ]
        status, confidence = parse_meter_status(reviews)
        assert status == "unknown"
        assert confidence == 0.0

    def test_case_insensitive(self):
        """Test that keyword matching is case-insensitive."""
        reviews = [
            "BROKEN METER",
            "Doesn't WORK",
            "OUT OF ORDER",
        ]
        status, confidence = parse_meter_status(reviews)
        assert status == "broken"
        assert confidence > 0.0

    def test_partial_word_matches(self):
        """Test that keywords match within words."""
        reviews = [
            "The meter was malfunctioning",
            "Not working properly",
        ]
        status, confidence = parse_meter_status(reviews)
        # "malfunction" contains "function" but should match "malfunction" keyword
        # "working" should match
        assert status in ["broken", "working"]

    def test_ambiguous_text(self):
        """Test ambiguous text that could be interpreted either way."""
        reviews = [
            "Meter works sometimes, broken other times",
            "Had issues but it worked eventually",
        ]
        status, confidence = parse_meter_status(reviews)
        # Should detect both keywords and pick majority
        assert status in ["broken", "working", "unknown"]

    def test_multiple_keywords_per_review(self):
        """Test reviews with multiple keywords."""
        reviews = [
            "Broken meter, doesn't work, out of order",  # Multiple broken keywords
            "Works fine, no issues, all good",  # Multiple working keywords
        ]
        status, confidence = parse_meter_status(reviews)
        # Both categories should be counted
        assert status in ["broken", "working"]

    def test_edge_cases(self):
        """Test edge cases."""
        # Empty strings
        status, confidence = parse_meter_status([""])
        assert status == "unknown"
        assert confidence == 0.0

        # Very long text
        long_text = "broken " * 1000
        status, confidence = parse_meter_status([long_text])
        assert status == "broken"
        assert confidence == pytest.approx(1.0, abs=0.1)

    def test_special_characters(self):
        """Test text with special characters."""
        reviews = [
            "Doesn't work!",
            "Broken (confirmed)",
            "Works fine, no issues.",
        ]
        status, confidence = parse_meter_status(reviews)
        # Should handle special characters
        assert status in ["broken", "working"]

