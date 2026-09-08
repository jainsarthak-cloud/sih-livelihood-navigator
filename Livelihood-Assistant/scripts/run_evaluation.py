"""Run reproducible synthetic evaluation and emit JSON plus a concise summary."""

import json
import sys
from pathlib import Path

# Allow direct `python scripts/run_evaluation.py` execution from any cwd.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation.runner import run_evaluation


if __name__ == "__main__":
    report = run_evaluation()
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Skill Normalization: {report['skill_normalization']['correct']}/{report['skill_normalization']['cases']}")
    print(f"Recommendation: Top-1={report['recommendations']['top_1_accuracy']}, Top-3={report['recommendations']['top_3_recall']}, ranking consistency={report['recommendations']['ranking_consistency']}")
    print(f"Eligibility: {report['eligibility']['correct']}/{report['eligibility']['cases']}, FP={report['eligibility']['false_positives']}, FN={report['eligibility']['false_negatives']}")
    print(f"Opportunity Matching: {report['opportunity_matching']['correct']}/{report['opportunity_matching']['cases']}")
    print(f"Roadmap Validation: {report['roadmap_validity']['valid']}/{report['roadmap_validity']['cases']}")
    print(f"End-to-end Consistency: {report['end_to_end_consistency']['consistent']}/{report['end_to_end_consistency']['cases']}")
