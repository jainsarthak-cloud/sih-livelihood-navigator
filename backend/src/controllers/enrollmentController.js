const TrainingEnrollment = require('../models/TrainingEnrollment');
const TrainingProgress = require('../models/TrainingProgress');
const BeneficiaryProfile = require('../models/BeneficiaryProfile');
const NSQFCourse = require('../models/NSQFCourse');
const TrainingCenter = require('../models/TrainingCenter');
const Outcome = require('../models/Outcome');

// @desc    Beneficiary self-enrollment in a course and center
// @route   POST /api/enrollments
// @access  Private (BENEFICIARY, OFFICER, ADMIN)
const enrollSelf = async (req, res, next) => {
  try {
    const { courseId, centerId } = req.body;

    if (!courseId || !centerId) {
      return res.status(400).json({
        success: false,
        message: 'courseId and centerId are required',
      });
    }

    const profile = await BeneficiaryProfile.findOne({ userId: req.user._id });
    if (!profile) {
      return res.status(404).json({
        success: false,
        message: 'Beneficiary profile not found. Please create a profile before enrolling.',
      });
    }

    const course = await NSQFCourse.findById(courseId);
    if (!course) {
      return res.status(404).json({ success: false, message: 'NSQF Course not found' });
    }

    const center = await TrainingCenter.findById(centerId);
    if (!center) {
      return res.status(404).json({ success: false, message: 'Training Center not found' });
    }

    // Check if already enrolled in this course
    const existing = await TrainingEnrollment.findOne({
      beneficiaryId: profile._id,
      courseId,
      status: { $in: ['ENROLLED', 'IN_PROGRESS'] },
    });

    if (existing) {
      return res.status(400).json({
        success: false,
        message: 'Already actively enrolled in this course',
      });
    }

    const enrollment = await TrainingEnrollment.create({
      beneficiaryId: profile._id,
      courseId,
      centerId,
      status: 'ENROLLED',
    });

    // Create initial TrainingProgress document
    const progress = await TrainingProgress.create({
      enrollmentId: enrollment._id,
      attendancePercentage: 0,
      milestonesCompleted: [],
      currentModule: 'Orientation',
      notes: 'Enrollment initialized',
    });

    res.status(201).json({
      success: true,
      data: {
        enrollment,
        progress,
      },
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get current logged in user's enrollments and progress
// @route   GET /api/enrollments/me
// @access  Private
const getOwnEnrollments = async (req, res, next) => {
  try {
    const profile = await BeneficiaryProfile.findOne({ userId: req.user._id });
    if (!profile) {
      return res.status(404).json({
        success: false,
        message: 'Beneficiary profile not found',
      });
    }

    const enrollments = await TrainingEnrollment.find({ beneficiaryId: profile._id })
      .populate('courseId')
      .populate('centerId')
      .sort({ createdAt: -1 });

    const enrollmentIds = enrollments.map((e) => e._id);
    const progressList = await TrainingProgress.find({ enrollmentId: { $in: enrollmentIds } });
    const outcomeList = await Outcome.find({ beneficiaryId: profile._id });

    const progressMap = {};
    progressList.forEach((p) => {
      progressMap[p.enrollmentId.toString()] = p;
    });

    const outcomeMap = {};
    outcomeList.forEach((o) => {
      if (o.enrollmentId) {
        outcomeMap[o.enrollmentId.toString()] = o;
      }
    });

    const data = enrollments.map((e) => ({
      ...e.toObject(),
      progress: progressMap[e._id.toString()] || null,
      outcome: outcomeMap[e._id.toString()] || null,
    }));

    res.status(200).json({
      success: true,
      data,
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Update progress for own enrollment (creates/updates TrainingProgress document)
// @route   PATCH /api/enrollments/:id/progress
// @access  Private (BENEFICIARY, OFFICER, ADMIN)
const updateOwnProgress = async (req, res, next) => {
  try {
    const enrollmentId = req.params.id;
    const { attendancePercentage, milestonesCompleted, currentModule, notes } = req.body;

    const profile = await BeneficiaryProfile.findOne({ userId: req.user._id });

    const enrollment = await TrainingEnrollment.findById(enrollmentId);
    if (!enrollment) {
      return res.status(404).json({
        success: false,
        message: 'Training enrollment not found',
      });
    }

    // Verify ownership if role is BENEFICIARY
    if (req.user.role === 'BENEFICIARY') {
      if (!profile || enrollment.beneficiaryId.toString() !== profile._id.toString()) {
        return res.status(403).json({
          success: false,
          message: 'Not authorized to update this enrollment progress',
        });
      }
    }

    const updateFields = { lastUpdated: new Date() };
    if (typeof attendancePercentage === 'number') updateFields.attendancePercentage = attendancePercentage;
    if (Array.isArray(milestonesCompleted)) updateFields.milestonesCompleted = milestonesCompleted;
    if (currentModule !== undefined) updateFields.currentModule = currentModule;
    if (notes !== undefined) updateFields.notes = notes;

    // Upsert TrainingProgress document explicitly
    let progress = await TrainingProgress.findOneAndUpdate(
      { enrollmentId },
      { $set: updateFields },
      { returnDocument: 'after', upsert: true, runValidators: true }
    );

    // If attendance > 0 and status is ENROLLED, move enrollment status to IN_PROGRESS
    if (progress.attendancePercentage > 0 && enrollment.status === 'ENROLLED') {
      enrollment.status = 'IN_PROGRESS';
      await enrollment.save();
    }

    res.status(200).json({
      success: true,
      data: {
        enrollment,
        progress,
      },
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get all enrollments (Officer/Admin only) with district & status filters
// @route   GET /api/enrollments
// @access  Private (OFFICER, ADMIN)
const getAllEnrollments = async (req, res, next) => {
  try {
    const { district, status } = req.query;
    const query = {};

    if (status) {
      query.status = status;
    }

    if (district) {
      const matchingProfiles = await BeneficiaryProfile.find({
        'location.district': new RegExp(district, 'i'),
      }).select('_id');
      const profileIds = matchingProfiles.map((p) => p._id);
      query.beneficiaryId = { $in: profileIds };
    }

    const enrollments = await TrainingEnrollment.find(query)
      .populate({
        path: 'beneficiaryId',
        populate: { path: 'userId', select: 'name email phone district state' },
      })
      .populate('courseId')
      .populate('centerId')
      .sort({ createdAt: -1 });

    const enrollmentIds = enrollments.map((e) => e._id);
    const progressList = await TrainingProgress.find({ enrollmentId: { $in: enrollmentIds } });

    const progressMap = {};
    progressList.forEach((p) => {
      progressMap[p.enrollmentId.toString()] = p;
    });

    const data = enrollments.map((e) => ({
      ...e.toObject(),
      progress: progressMap[e._id.toString()] || null,
    }));

    res.status(200).json({
      success: true,
      data,
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  enrollSelf,
  getOwnEnrollments,
  updateOwnProgress,
  getAllEnrollments,
};
