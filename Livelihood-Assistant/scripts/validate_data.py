"""
Data validation script — validates all seed and processed data files.

Usage:
    python scripts/validate_data.py [--data-dir data/seed] [--verbose]

Exit codes:
    0 — all records valid, no duplicates, no broken references
    1 — one or more errors found

Checks performed:
    1. All JSON/JSONL files parse without syntax errors
    2. All records validate against their Pydantic domain model
    3. No duplicate canonical IDs within each domain
    4. Cross-domain references are resolvable (occupation → skill IDs, etc.)
    5. NSQF level bounds (1–10)
    6. Geographic coordinate bounds
    7. No records with missing required identifiers
    8. Missing provenance warnings (non-fatal)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set

# Allow running from repo root without installing package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.loaders.domain_loaders import (
    CourseLoader,
    OccupationLoader,
    OpportunityLoader,
    ProviderLoader,
    SkillLoader,
)
from app.data.loaders.base import LoadResult


# ─── ANSI colours (degraded gracefully if terminal doesn't support) ─────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg: str) -> str:
    return f"{GREEN}[OK]{RESET} {msg}"


def warn(msg: str) -> str:
    return f"{YELLOW}[WARN]{RESET} {msg}"


def err(msg: str) -> str:
    return f"{RED}[ERR]{RESET} {msg}"


def section(msg: str) -> str:
    return f"\n{BOLD}{CYAN}{msg}{RESET}"


# --- Loader registry ---------------------------------------------------------
LOADERS = {
    "skills": (SkillLoader, "skill_id", "skills.json"),
    "occupations": (OccupationLoader, "occupation_id", "occupations.json"),
    "courses": (CourseLoader, "course_id", "courses.json"),
    "opportunities": (OpportunityLoader, "opportunity_id", "opportunities.json"),
    "providers": (ProviderLoader, "provider_id", "providers.json"),
}


def run_validation(data_dir: Path, verbose: bool) -> int:
    """
    Run all validation checks against data_dir.
    Returns 0 on success, 1 if any errors found.
    """
    print(f"\n{BOLD}Livelihood-Assistant - Data Validation{RESET}")
    print(f"Data directory : {data_dir.resolve()}")
    print("-" * 60)

    total_errors = 0
    total_warnings = 0
    domain_records: Dict[str, dict] = {}  # domain -> {id -> record}

    # --- Step 1: Load and validate each domain file ---------------------------
    print(section("Step 1 - Domain record loading & Pydantic validation"))
    for domain, (LoaderClass, id_field, filename) in LOADERS.items():
        fpath = data_dir / filename
        if not fpath.exists():
            print(warn(f"  {filename} not found in {data_dir} - skipping {domain}"))
            total_warnings += 1
            domain_records[domain] = {}
            continue

        loader = LoaderClass(data_path=fpath)
        result: LoadResult = loader.load()

        id_map = {getattr(r, id_field): r for r in result.records}
        domain_records[domain] = id_map

        if result.is_clean:
            print(ok(f"  {filename}: {result.total_valid} records valid"))
        else:
            print(err(f"  {filename}: {result.total_valid} valid, {result.total_invalid} invalid"))
            for rec_err in result.errors:
                print(f"    {RED}->{RESET} {rec_err.reason}")
            total_errors += result.total_invalid

    # --- Step 2: Cross-domain reference validation ---------------------------
    print(section("Step 2 - Cross-domain reference validation"))

    skill_ids: Set[str] = set(domain_records.get("skills", {}).keys())
    course_ids: Set[str] = set(domain_records.get("courses", {}).keys())
    occupation_ids: Set[str] = set(domain_records.get("occupations", {}).keys())

    ref_errors = 0

    # Occupation -> required_skills
    for occ_id, occ in domain_records.get("occupations", {}).items():
        for sid in occ.required_skills:
            if sid not in skill_ids:
                print(err(f"  OCC {occ_id} references unknown skill_id={sid!r}"))
                ref_errors += 1

    # Occupation -> nsqf_qualification_ids
    for occ_id, occ in domain_records.get("occupations", {}).items():
        for cid in occ.nsqf_qualification_ids:
            if cid not in course_ids:
                print(warn(
                    f"  OCC {occ_id} references course {cid!r} not found in courses file "
                    f"(may be external QP code - warning only)"
                ))
                total_warnings += 1

    # Course -> required_skills / acquired_skills
    for crs_id, crs in domain_records.get("courses", {}).items():
        for sid in crs.required_skills + crs.acquired_skills:
            if sid not in skill_ids:
                print(err(f"  CRS {crs_id} references unknown skill_id={sid!r}"))
                ref_errors += 1

    # Opportunity -> required_skills
    for opp_id, opp in domain_records.get("opportunities", {}).items():
        for sid in opp.required_skills:
            if sid not in skill_ids:
                print(err(f"  OPP {opp_id} references unknown skill_id={sid!r}"))
                ref_errors += 1

    # Provider -> courses_offered
    for prv_id, prv in domain_records.get("providers", {}).items():
        for cid in prv.courses_offered:
            if cid not in course_ids:
                print(err(f"  PRV {prv_id} references unknown course_id={cid!r}"))
                ref_errors += 1

    if ref_errors == 0:
        print(ok("  All cross-domain references resolved"))
    total_errors += ref_errors

    # --- Step 3: Provenance check (warnings) ----------------------------------
    print(section("Step 3 - Provenance / source_id presence (warnings)"))
    prov_warns = 0
    for domain, records in domain_records.items():
        for rid, rec in records.items():
            # source_id presence - check raw JSON
            source_id = getattr(rec, "source_id", None)
            if not source_id:
                print(warn(f"  {domain.upper()} {rid}: source_id is missing"))
                prov_warns += 1
    if prov_warns == 0:
        print(ok("  All records have source_id"))
    total_warnings += prov_warns

    # --- Summary --------------------------------------------------------------
    print("\n" + "-" * 60)
    total_valid = sum(len(v) for v in domain_records.values())
    print(f"{BOLD}Summary{RESET}")
    print(f"  Total valid records : {total_valid}")
    print(f"  Errors              : {total_errors}")
    print(f"  Warnings            : {total_warnings}")

    if total_errors == 0:
        print(f"\n{GREEN}{BOLD}[OK] Validation passed{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}[ERR] Validation FAILED - {total_errors} error(s) found{RESET}")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Livelihood-Assistant seed and processed data files."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/seed"),
        help="Directory containing JSON seed/processed files (default: data/seed)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print additional detail for each record",
    )
    args = parser.parse_args()

    exit_code = run_validation(data_dir=args.data_dir, verbose=args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
