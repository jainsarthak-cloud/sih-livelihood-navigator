"""
NSQF (National Skills Qualifications Framework) & PM-AJAY Static Rules.
"""

from typing import Any, Dict, Optional

NSQF_LEVEL_DESCRIPTORS: Dict[int, Dict[str, Any]] = {
    1: {
        "level": 1,
        "description": "Pre-vocational / basic routine work under direct supervision",
        "entry_requirement": "No formal schooling required or 5th class",
    },
    2: {
        "level": 2,
        "description": "Repetitive tasks with limited context under supervision",
        "entry_requirement": "5th class pass",
    },
    3: {
        "level": 3,
        "description": "Job with narrow range of application using basic tools and quality checks",
        "entry_requirement": "8th class pass",
    },
    4: {
        "level": 4,
        "description": "Work in familiar, predictable, routine environment with clear personal responsibility",
        "entry_requirement": "10th class pass",
    },
    5: {
        "level": 5,
        "description": "Job involving well-developed skills and broad range of activities with some supervisory capacity",
        "entry_requirement": "10th + 2-year ITI or 12th pass",
    },
    6: {
        "level": 6,
        "description": "Technical and supervisory skills with wide range of specialized technical functions",
        "entry_requirement": "Diploma or 12th + related vocational training",
    },
    7: {
        "level": 7,
        "description": "Professional practice requiring comprehensive theoretical knowledge",
        "entry_requirement": "Bachelor's Degree",
    },
}

PM_AJAY_SCHEME_CRITERIA: Dict[str, Any] = {
    "target_community": "Scheduled Caste (SC)",
    "components": [
        "Development of SC dominated villages into Adarsh Gram",
        "Grants-in-aid for District/State-level Projects for socio-economic betterment",
        "Construction of Hostels in higher educational institutions",
    ],
    "beneficiary_eligibility": {
        "community": "SC",
        "minimum_age": 18,
        "target_sectors": [
            "Agriculture & Allied",
            "Apparel & Handicrafts",
            "Automotive",
            "Construction",
            "Electronics & Hardware",
            "Healthcare & Sanitation",
            "Logistics & Transport",
            "Retail & Micro-Enterprise",
            "Green Jobs & Solar",
        ],
    },
}


def get_nsqf_level_info(level: int) -> Optional[Dict[str, Any]]:
    """Lookup NSQF level descriptor details."""
    return NSQF_LEVEL_DESCRIPTORS.get(level)
