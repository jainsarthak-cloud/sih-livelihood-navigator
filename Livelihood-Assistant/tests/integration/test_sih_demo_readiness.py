"""Final Phase 16 synthetic/demo scenario validation over the public assessment composition."""

import asyncio
import json
from pathlib import Path

from app.routes.livelihood import get_livelihood_assessment_service
from app.schemas.livelihood import LivelihoodAssessRequest
from app.schemas.profile import BeneficiaryProfile
from app.schemas.skill import Skill


SCENARIOS = Path("data/demo/sih_final_demo_scenarios.json")


def _profile(data):
    values = dict(data)
    skill_ids = values.pop("normalized_skill_ids", [])
    values["normalized_skills"] = [Skill(skill_id=skill_id, name=skill_id) for skill_id in skill_ids]
    return BeneficiaryProfile.model_validate(values)


def test_final_sih_scenarios_are_marked_synthetic_and_validate_the_complete_deterministic_pipeline():
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    assert len(scenarios) == 7
    assert all(item["synthetic_demo"] is True and item["rationale"] for item in scenarios)

    for scenario in scenarios:
        response = asyncio.run(get_livelihood_assessment_service().assess(
            LivelihoodAssessRequest(profile=_profile(scenario["profile"]))
        ))
        expected = scenario["expected"]
        occupation_ids = [pathway.recommendation.occupation_reference for pathway in response.pathways]
        if "occupation_id" in expected:
            assert occupation_ids[0] == expected["occupation_id"]
            roadmap = response.pathways[0].roadmap
            assert roadmap is not None
            if "roadmap_gap_status" in expected:
                assert any(gap.gap_status.value == expected["roadmap_gap_status"] for gap in roadmap.skill_gaps)
        if "pathway_count" in expected:
            assert len(response.pathways) == expected["pathway_count"]
        if "local_opportunity_count" in expected:
            assert len(response.local_opportunity_evidence) == expected["local_opportunity_count"]
        if expected.get("requires_unknown_limitations"):
            assert any("unknown" in limitation.casefold() for limitation in response.limitations)

        assert all("SYN" in pathway.recommendation.occupation_reference for pathway in response.pathways)
        assert response.model_dump() == asyncio.run(get_livelihood_assessment_service().assess(
            LivelihoodAssessRequest(profile=_profile(scenario["profile"]))
        )).model_dump()
