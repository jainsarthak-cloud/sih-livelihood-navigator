const BeneficiaryProfile = require('../models/BeneficiaryProfile');

// Helper to compute dynamic profile completion percentage
const calculateProfileCompletion = (profileData) => {
  let score = 0;
  const totalSections = 6;

  if (profileData.personal && (profileData.personal.age || profileData.personal.gender)) score++;
  if (profileData.education && profileData.education.level) score++;
  if (profileData.location && (profileData.location.state || profileData.location.district)) score++;
  if (profileData.livelihood && profileData.livelihood.currentOccupation) score++;
  if ((profileData.skills && profileData.skills.length > 0) || (profileData.traditionalSkills && profileData.traditionalSkills.length > 0)) score++;
  if (profileData.employmentPreference) score++;

  return Math.round((score / totalSections) * 100);
};

// @desc    Create or update current user's profile
// @route   POST /api/beneficiaries/profile
// @access  Private (Beneficiary/Officer/Admin)
const createOrUpdateProfile = async (req, res, next) => {
  try {
    const userId = req.user._id;

    const profileFields = {
      ...req.body,
      userId,
    };

    profileFields.profileCompletion = calculateProfileCompletion(profileFields);

    let profile = await BeneficiaryProfile.findOne({ userId });

    if (profile) {
      profile = await BeneficiaryProfile.findOneAndUpdate(
        { userId },
        { $set: profileFields },
        { returnDocument: 'after', runValidators: true }
      );
      return res.status(200).json({
        success: true,
        data: profile,
      });
    }

    profile = await BeneficiaryProfile.create(profileFields);

    res.status(201).json({
      success: true,
      data: profile,
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get current user's profile
// @route   GET /api/beneficiaries/profile/me
// @access  Private
const getOwnProfile = async (req, res, next) => {
  try {
    const profile = await BeneficiaryProfile.findOne({ userId: req.user._id }).populate(
      'userId',
      'name email phone role district state'
    );

    if (!profile) {
      return res.status(404).json({
        success: false,
        message: 'Beneficiary profile not found',
      });
    }

    res.status(200).json({
      success: true,
      data: profile,
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get beneficiary profile by ID
// @route   GET /api/beneficiaries/profile/:id
// @access  Private (Officer/Admin only)
const getProfileById = async (req, res, next) => {
  try {
    const profile = await BeneficiaryProfile.findById(req.params.id).populate(
      'userId',
      'name email phone role district state'
    );

    if (!profile) {
      return res.status(404).json({
        success: false,
        message: 'Beneficiary profile not found',
      });
    }

    res.status(200).json({
      success: true,
      data: profile,
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  createOrUpdateProfile,
  getOwnProfile,
  getProfileById,
};
