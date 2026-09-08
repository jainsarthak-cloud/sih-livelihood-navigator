"""
Evaluation Harness Placeholder.
Will evaluate AI extraction precision, recommendation alignment, and latency in future phases.
"""

from app.rules.nsqf_rules import NSQF_LEVEL_DESCRIPTORS, PM_AJAY_SCHEME_CRITERIA


def test_nsqf_levels_coverage():
    """Verify NSQF levels 1 through 7 descriptors are mapped."""
    for level in range(1, 8):
        assert level in NSQF_LEVEL_DESCRIPTORS
        assert "description" in NSQF_LEVEL_DESCRIPTORS[level]
        assert "entry_requirement" in NSQF_LEVEL_DESCRIPTORS[level]


def test_pm_ajay_target_criteria():
    """Verify PM-AJAY beneficiary configuration."""
    assert PM_AJAY_SCHEME_CRITERIA["target_community"] == "Scheduled Caste (SC)"
    assert len(PM_AJAY_SCHEME_CRITERIA["beneficiary_eligibility"]["target_sectors"]) > 0
