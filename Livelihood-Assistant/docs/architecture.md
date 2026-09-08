# Architecture Overview

## Project Summary
**Livelihood-Assistant** is an AI-driven, standalone voice and livelihood mapping assistant designed for Scheduled Caste (SC) communities under the **Pradhan Mantri Anusuchit Jaati Abhyuday Yojana (PM-AJAY)**. The service aligns beneficiary aspirations and existing skills with **NSQF (National Skills Qualifications Framework)** levels and local labor market demands.

## Canonical Domain Model Pipeline

The end-to-end livelihood progression and skilling recommendation pipeline is modeled using canonical Pydantic v2 schemas:

```mermaid
graph TD
    Beneficiary["BeneficiaryProfile<br/>(Demographics, Location, Education, Preferences)"]
    Skills["Skills<br/>(RawSkill & Canonical Skill)"]
    Occupation["Occupation<br/>(NCO/NOS Aligned Roles)"]
    NSQFCourse["NSQF Course<br/>(Levels 1-10, QP Codes, Acquired Skills)"]
    Eligibility["Eligibility<br/>(Eligible / Ineligible / Explicit UNKNOWN)"]
    Opportunity["Opportunity<br/>(Wage & Self-Employment, Lifecycle: Reported->Active)"]
    Recommendation["Recommendation<br/>(Pathways, Multidimensional Scores, Top 3-5)"]
    SkillGap["Skill Gap<br/>(Current vs Target Proficiency, Priority)"]
    Roadmap["Roadmap<br/>(Ordered Milestone Steps & Duration)"]
    Assessment["Livelihood Assessment<br/>(Structured orchestration)"]
    SourceEvidence["SourceEvidence<br/>(Traceability, Gazettes, Timezone-aware)"]

    Beneficiary -->|has| Skills
    Skills -->|mapped to| Occupation
    Occupation -->|aligned with| NSQFCourse
    Beneficiary -->|evaluated for| Eligibility
    Eligibility -->|validates| Opportunity
    NSQFCourse -->|generates| Recommendation
    Opportunity -->|included in| Recommendation
    Opportunity -->|observed local counts| MarketEvidence["Market Observation Evidence<br/>(Repository-scoped, no forecast)"]
    Recommendation -->|identifies| SkillGap
    SkillGap -->|converted to| Roadmap
    Recommendation --> Assessment
    Opportunity --> Assessment
    MarketEvidence --> Assessment
    Roadmap --> Assessment

    SourceEvidence -.->|grounds| Beneficiary
    SourceEvidence -.->|grounds| Skills
    SourceEvidence -.->|grounds| Occupation
    SourceEvidence -.->|grounds| NSQFCourse
    SourceEvidence -.->|grounds| Eligibility
    SourceEvidence -.->|grounds| Opportunity
    SourceEvidence -.->|grounds| Recommendation
    SourceEvidence -.->|grounds| Roadmap
```

## High-Level System Architecture

```mermaid
graph TD
    Client["Client / External Web & Mobile Frontend"] -->|REST / JSON| Gateway["FastAPI Service (app.main)"]
    Gateway --> Middleware["CORS & Error Handling Middleware"]
    Middleware --> APIRouter["API Router (/v1)"]
    
    APIRouter --> HealthRoute["/v1/health"]
    APIRouter --> ProfileRoute["/v1/profile/*"]
    APIRouter --> RecRoute["/v1/recommendations"]
    APIRouter --> SpeechRoute["/v1/speech/*"]
    APIRouter --> OppRoute["/v1/opportunities/*"]
    APIRouter --> MarketRoute["/v1/market/*"]
    APIRouter --> RoadmapRoute["/v1/roadmap"]

    ProfileRoute --> ProfileService["ProfileExtractionService"]
    SpeechRoute --> SpeechService["SpeechTranscriptionService"]
    RecRoute --> RecService["RecommendationService"]
    RecRoute --> MatchService["SkillMatchingService"]
    MarketRoute --> MarketService["MarketDemandService"]
    RoadmapRoute --> RoadmapService["RoadmapService"]
    Gateway --> AssessmentRoute["/v1/livelihood/assess"]
    AssessmentRoute --> AssessmentService["LivelihoodAssessmentService"]
    AssessmentService --> RecService
    AssessmentService --> OppIntelligence
    AssessmentService --> MarketEvidenceService
    AssessmentService --> RoadmapService
    OppRoute --> OppIntelligence["Opportunity Intelligence<br/>(Normalization & Profile Matching)"]
    MarketRoute --> MarketEvidenceService["MarketDemandService<br/>(Active-record observation counts)"]

    RecService --> Rules["NSQF & PM-AJAY Rules (app.rules)"]
    RecService --> DataLoaders["Data Loaders & Repositories (app.data)"]
```

## Layered Design Principles
1. **Standalone & Decoupled**:
   - Zero hardcoded dependency on other repositories or external MongoDB instances.
   - Any client frontend or administrative backend can consume standard REST APIs.
2. **Canonical Domain Representation**:
   - Explicit `UNKNOWN` state support preventing ungrounded assumptions (e.g., eligibility, baseline proficiencies).
   - Traceable metadata across all entities via timezone-aware `SourceEvidence`.
3. **Contract-First & Type-Safe**:
   - Strictly validated Pydantic v2 domain models with bounds checking (coordinates, scores, NSQF levels 1–10).
4. **Clean Separation of Concerns**:
   - `routes/`: Handles HTTP parameters, status codes, and delegates logic to services.
   - `schemas/`: Defines canonical domain models and API contracts.
   - `services/`: Encapsulates business logic, AI interfaces, and integration adapters.
   - `rules/`: Static standards and policy criteria (NSQF levels, PM-AJAY eligibility).
   - `data/`: Ingestion loaders and repositories without direct DB coupling.
   - `core/`: Environment settings, custom exceptions, and logging configuration.
