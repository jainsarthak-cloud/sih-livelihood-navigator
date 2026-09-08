"""Data-driven, reproducible evaluation of current deterministic pipeline behavior."""

import asyncio
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import Settings
from app.data.loaders.domain_loaders import CourseLoader, OccupationLoader, OpportunityLoader, SkillLoader
from app.data.repositories.domain_repositories import CourseRepository, OccupationRepository, OpportunityRepository, SkillRepository
from app.schemas.common import EducationLevel, EmploymentPreference, GeographicLocation
from app.schemas.eligibility import EligibilityStatus
from app.schemas.opportunity import OpportunityMatchRequest
from app.schemas.profile import BeneficiaryProfile
from app.schemas.roadmap import RoadmapRequest
from app.schemas.recommendation import RecommendationRequest
from app.schemas.skill import Skill
from app.services.normalization.skill_normalizer import SkillNormalizationService
from app.services.opportunity.intelligence import OpportunityIntelligenceService
from app.services.recommendation.recommender import RecommendationService
from app.services.roadmap.generator import RoadmapService


class EvaluationRecord(BaseModel):
    case_id: str = Field(min_length=1)
    synthetic_evaluation: bool = True
    rationale: str = Field(min_length=1)
    input: dict[str, Any] = Field(min_length=1)
    expected: dict[str, Any] = Field(min_length=1)


def load_records(path: Path) -> list[EvaluationRecord]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Evaluation dataset must be an array: {path}")
    records = [EvaluationRecord.model_validate(item) for item in raw]
    if not records:
        raise ValueError(f"Evaluation dataset is empty: {path}")
    if len({record.case_id for record in records}) != len(records):
        raise ValueError(f"Evaluation dataset contains duplicate case IDs: {path}")
    if not all("synthetic_evaluation" in record.model_fields_set for record in records):
        raise ValueError(f"Evaluation records must explicitly declare synthetic_evaluation: {path}")
    if not all(record.synthetic_evaluation for record in records):
        raise ValueError(f"Evaluation records must be explicitly synthetic: {path}")
    return records


def build_services():
    root = Path(__file__).resolve().parents[2]
    seed = root / "data" / "seed"
    repositories = (SkillRepository(), OccupationRepository(), CourseRepository(), OpportunityRepository())
    loaders = (SkillLoader(seed / "skills.json"), OccupationLoader(seed / "occupations.json"),
               CourseLoader(seed / "courses.json"), OpportunityLoader(seed / "opportunities.json"))
    for repository, loader in zip(repositories, loaders):
        loaded = loader.load()
        if loaded.errors:
            raise ValueError(f"Cannot load seed data: {loaded.errors[0].reason}")
        for record in loaded.records:
            repository.add(record)
    skills, occupations, courses, opportunities = repositories
    config = Settings()
    normalizer = SkillNormalizationService(skills, config)
    intelligence = OpportunityIntelligenceService(opportunities, occupations, normalizer)
    recommendation = RecommendationService(occupations, courses, opportunities, skills, normalizer, config)
    roadmap = RoadmapService(occupations, courses, opportunities, skills, normalizer)
    return normalizer, recommendation, intelligence, roadmap, skills


def profile_from(data: dict[str, Any]) -> BeneficiaryProfile:
    values = dict(data)
    if "location" in values and values["location"] is not None:
        values["location"] = GeographicLocation.model_validate(values["location"])
    values["education_level"] = EducationLevel(values.get("education_level", "unknown"))
    values["employment_preference"] = EmploymentPreference(values.get("employment_preference", "unknown"))
    values["normalized_skills"] = [Skill(skill_id=skill_id, name=skill_id) for skill_id in values.pop("skill_ids", [])]
    return BeneficiaryProfile(**values)


def metric(correct: int, total: int) -> dict[str, Any]:
    return {"cases": total, "correct": correct, "accuracy": round(correct / total, 6) if total else None}


def run_evaluation(data_dir: Path | None = None) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    data_dir = data_dir or root / "data" / "evaluation"
    normalization_cases = load_records(data_dir / "skill_normalization.json")
    recommendation_cases = load_records(data_dir / "recommendations.json")
    eligibility_cases = load_records(data_dir / "eligibility.json")
    opportunity_cases = load_records(data_dir / "opportunity_matching.json")
    roadmap_cases = load_records(data_dir / "roadmap_validity.json")
    normalizer, recommendation, intelligence, roadmap, skills = build_services()

    normalization_correct = sum(
        normalizer.normalize(record.input["raw_skill"]).canonical_skill_id == record.expected["canonical_skill_id"]
        for record in normalization_cases
    )
    unknown_total = sum(record.expected["canonical_skill_id"] is None for record in normalization_cases)
    unknown_correct = sum(
        record.expected["canonical_skill_id"] is None and normalizer.normalize(record.input["raw_skill"]).canonical_skill_id is None
        for record in normalization_cases
    )

    top1 = top3 = evaluated = consistent = end_to_end_consistent = 0
    for record in recommendation_cases:
        profile = profile_from(record.input["profile"])
        response_one = asyncio.run(recommendation.get_recommendations(RecommendationRequest(profile=profile)))
        response_two = asyncio.run(recommendation.get_recommendations(RecommendationRequest(profile=profile)))
        expected = record.expected.get("acceptable_occupation_ids", [])
        ids = [item.occupation_reference for item in response_one.recommendations]
        if expected:
            evaluated += 1
            top1 += bool(ids and ids[0] in expected)
            top3 += bool(set(ids) & set(expected))
        consistent += response_one.model_dump() == response_two.model_dump()

        # Exercise the connected deterministic path using the selected pathway.
        # A model dump comparison includes ordered scores, skill gaps, opportunity
        # evidence, and roadmap evidence without manufacturing any labels.
        opportunity_one = asyncio.run(intelligence.match_opportunities(OpportunityMatchRequest(profile=profile)))
        opportunity_two = asyncio.run(intelligence.match_opportunities(OpportunityMatchRequest(profile=profile)))
        same_pathway = response_one.model_dump() == response_two.model_dump()
        same_opportunities = opportunity_one.model_dump() == opportunity_two.model_dump()
        same_roadmap = True
        if response_one.recommendations:
            occupation_id = response_one.recommendations[0].occupation_reference
            request = RoadmapRequest(profile=profile, target_occupation_id=occupation_id)
            roadmap_one = asyncio.run(roadmap.generate_roadmap(request))
            roadmap_two = asyncio.run(roadmap.generate_roadmap(request))
            same_roadmap = roadmap_one.model_dump() == roadmap_two.model_dump()
        end_to_end_consistent += same_pathway and same_opportunities and same_roadmap

    eligibility_correct = false_positive = false_negative = 0
    for record in eligibility_cases:
        profile = profile_from(record.input["profile"])
        course = recommendation._courses.get_by_id(record.input["course_id"])
        actual = recommendation._course_eligibility(profile, course, None).status.value
        expected = record.expected["status"]
        eligibility_correct += actual == expected
        false_positive += actual == "eligible" and expected == "ineligible"
        false_negative += actual == "ineligible" and expected == "eligible"

    opportunity_correct = 0
    for record in opportunity_cases:
        profile = profile_from(record.input["profile"])
        response = asyncio.run(intelligence.match_opportunities(OpportunityMatchRequest(profile=profile)))
        ids = [match.opportunity.opportunity_id for match in response.matches]
        opportunity_correct += ids == record.expected["opportunity_ids"]

    roadmap_valid = 0
    for record in roadmap_cases:
        profile = profile_from(record.input["profile"])
        response = asyncio.run(roadmap.generate_roadmap(RoadmapRequest(profile=profile, target_occupation_id=record.input["occupation_id"])))
        valid = response.roadmap is not None
        if valid:
            valid &= all(skills.exists(gap.skill_id) for gap in response.roadmap.skill_gaps)
            valid &= all(course_id in {course.course_id for course in recommendation._courses.list_all()} for step in response.roadmap.steps for course_id in step.course_references)
            valid &= [step.step_number for step in response.roadmap.steps] == list(range(1, len(response.roadmap.steps) + 1))
            valid &= [evidence.source_id for evidence in response.roadmap.evidence] == record.expected.get("evidence_ids", [])
            valid &= response.model_dump() == asyncio.run(roadmap.generate_roadmap(RoadmapRequest(profile=profile, target_occupation_id=record.input["occupation_id"]))).model_dump()
        roadmap_valid += valid == record.expected["valid"]

    return {
        "dataset": {"skill_normalization": len(normalization_cases), "recommendations": len(recommendation_cases),
                    "eligibility": len(eligibility_cases), "opportunity_matching": len(opportunity_cases), "roadmap_validity": len(roadmap_cases)},
        "skill_normalization": {**metric(normalization_correct, len(normalization_cases)), "unknown_cases": unknown_total, "unknown_correct": unknown_correct},
        "recommendations": {"evaluated_cases": evaluated, "top_1_accuracy": round(top1 / evaluated, 6) if evaluated else None,
                            "top_3_recall": round(top3 / evaluated, 6) if evaluated else None,
                            "ranking_consistency": round(consistent / len(recommendation_cases), 6)},
        "eligibility": {**metric(eligibility_correct, len(eligibility_cases)), "false_positives": false_positive, "false_negatives": false_negative},
        "opportunity_matching": metric(opportunity_correct, len(opportunity_cases)),
        "roadmap_validity": {"cases": len(roadmap_cases), "valid": roadmap_valid},
        "end_to_end_consistency": {"cases": len(recommendation_cases), "consistent": end_to_end_consistent,
                                     "accuracy": round(end_to_end_consistent / len(recommendation_cases), 6)},
        "limitations": ["All labels and records are synthetic evaluation data based only on the repository's synthetic/demo ontology.",
                        "Recommendation metric excludes scenarios without an explicitly labeled acceptable pathway.",
                        "The seed roadmaps have no source evidence, so only empty-evidence preservation/no-fabrication is measured.",
                        "Market forecasts, external data, LLM extraction, and ASR are not evaluated."],
    }
