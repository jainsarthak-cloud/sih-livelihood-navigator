const BeneficiaryProfile = require('../models/BeneficiaryProfile');
const TrainingCenter = require('../models/TrainingCenter');
const recommendationService = require('../services/recommendation/recommendationService');
const { assessLivelihood } = require('../services/ai/livelihoodAssessmentClient');

const normalizedText = (value) => String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

const attachTrainingCenters = async (result) => {
  const centers = await TrainingCenter.find().populate('coursesOffered');

  return {
    ...result,
    recommendations: result.recommendations.map((recommendation) => {
      const courseName = normalizedText(recommendation.details?.courseName);
      const sector = normalizedText(recommendation.details?.sector);
      const trainingCenters = centers
        .filter((center) => (center.coursesOffered || []).some((course) => {
          const offeredName = normalizedText(course.courseName || course.qualificationName);
          const offeredSector = normalizedText(course.sector);
          return (courseName && offeredName && (courseName.includes(offeredName) || offeredName.includes(courseName)))
            || (sector && offeredSector && (sector.includes(offeredSector) || offeredSector.includes(sector)));
        }))
        .map((center) => ({
          _id: center._id,
          name: center.name,
          address: center.address,
          capacity: center.capacity,
          contactInfo: center.contactInfo,
        }));

      return {
        ...recommendation,
        details: { ...recommendation.details, trainingCenters },
      };
    }),
  };
};

// @desc    Get rule-based recommendations for logged in beneficiary
// @route   GET /api/recommendations
// @access  Private (BENEFICIARY)
const getRecommendationsForCurrentUser = async (req, res, next) => {
  try {
    const profile = await BeneficiaryProfile.findOne({ userId: req.user._id });

    if (!profile) {
      return res.status(404).json({
        success: false,
        message: 'Beneficiary profile not found. Please create your profile first.',
      });
    }

    let result;
    let source = 'ai-assessment';

    try {
      result = await assessLivelihood(profile);
      result = await attachTrainingCenters(result);
    } catch (aiError) {
      source = 'rule-based-fallback';
      console.warn(`AI assessment unavailable: ${aiError.message}`);
      result = await recommendationService.getRecommendations(profile);
    }

    res.status(200).json({
      success: true,
      data: { ...result, source },
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getRecommendationsForCurrentUser,
};
