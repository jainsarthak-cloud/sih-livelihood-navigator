const env = require('../../config/env');

const EDUCATION_LEVELS = {
  '1st Pass': 'primary',
  '5th Pass': 'primary',
  '8th Pass': 'middle',
  '10th Pass': 'secondary_10th',
  '12th Pass': 'higher_secondary_12th',
  Diploma: 'diploma',
  ITI: 'iti',
  Graduate: 'graduate',
  'Post Graduate': 'post_graduate',
};

const normalizeGender = (gender) => {
  const value = String(gender || '').toLowerCase();
  if (['female', 'male', 'transgender', 'other'].includes(value)) return value;
  return 'unknown';
};

const normalizeEmploymentPreference = (preference) => {
  const value = String(preference || '').toUpperCase();
  const mapping = {
    WAGE_EMPLOYMENT: 'wage_employment',
    SELF_EMPLOYMENT: 'self_employment',
    APPRENTICESHIP: 'apprenticeship',
    HOME_BASED: 'home_based',
    HYBRID: 'any',
    ANY: 'any',
  };
  return mapping[value] || 'unknown';
};

const toAiProfile = (profile) => ({
  beneficiary_id: String(profile._id || profile.userId || ''),
  age: profile.personal?.age ?? null,
  gender: normalizeGender(profile.personal?.gender),
  community: 'SC',
  education_level: EDUCATION_LEVELS[profile.education?.level] || 'unknown',
  education_field: profile.education?.field || null,
  location: profile.location?.state && profile.location?.district
    ? {
        state: profile.location.state,
        district: profile.location.district,
        block: profile.location.block || null,
        village: profile.location.village || null,
      }
    : null,
  current_occupation: profile.livelihood?.currentOccupation || null,
  family_occupation: profile.livelihood?.familyOccupation || null,
  current_income_range: profile.livelihood?.currentIncomeRange || null,
  traditional_skills: [
    ...(profile.skills || []),
    ...(profile.traditionalSkills || []),
  ],
  interests: profile.interests || [],
  aspirations: profile.aspirations || [],
  employment_preference: normalizeEmploymentPreference(profile.employmentPreference),
  willingness_to_travel: profile.mobility?.willingToTravel ?? null,
  max_travel_distance_km: profile.mobility?.maxDistanceKm ?? null,
  physical_constraints: Array.isArray(profile.physicalConstraints)
    ? profile.physicalConstraints.join(', ')
    : profile.physicalConstraints || null,
  preferred_language: String(profile.preferredLanguage || 'hi').toLowerCase().slice(0, 2),
  profile_completion_pct: profile.profileCompletion ?? null,
  profile_source: profile.source === 'VOICE' ? 'voice_interview' : 'text_input',
});

const toRecommendationCard = (pathway) => {
  const recommendation = pathway.recommendation;
  const course = recommendation.target_course;
  const occupation = recommendation.target_occupation;

  return {
    type: recommendation.target_course ? 'COURSE' : 'OPPORTUNITY',
    id: recommendation.recommendation_id,
    score: recommendation.overall_score,
    reasons: [recommendation.explanation, ...pathway.limitations].filter(Boolean),
    details: {
      courseName: course?.course_name,
      qualificationName: course?.qualification_name || course?.qp_code,
      sector: occupation?.sector || course?.sector,
      nsqfLevel: course?.nsqf_level,
      duration: course?.duration_hours,
      name: occupation?.name,
      occupationId: recommendation.occupation_reference,
      pathwayType: recommendation.pathway_type,
      skillGaps: recommendation.skill_gaps,
      roadmap: pathway.roadmap,
    },
    ai: {
      deterministic: true,
      modelVersion: recommendation.model_version,
      metadata: recommendation.score_breakdown,
    },
  };
};

const assessLivelihood = async (profile) => {
  const response = await fetch(`${env.AI_SERVICE_URL}/v1/livelihood/assess`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile: toAiProfile(profile), max_recommendations: 3 }),
    signal: AbortSignal.timeout(env.AI_SERVICE_TIMEOUT_MS),
  });

  if (!response.ok) {
    throw new Error(`AI service responded with HTTP ${response.status}`);
  }

  const assessment = await response.json();
  return {
    recommendations: (assessment.pathways || []).map(toRecommendationCard),
    modelVersion: assessment.metadata?.recommendation_model_version || 'ai-assessment',
    generatedAt: new Date().toISOString(),
    assessmentStatus: assessment.status,
    limitations: assessment.limitations || [],
  };
};

module.exports = { assessLivelihood };