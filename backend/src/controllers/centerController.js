const TrainingCenter = require('../models/TrainingCenter');

const getCenters = async (req, res, next) => {
  try {
    const centers = await TrainingCenter.find().populate('coursesOffered');
    res.status(200).json({ success: true, count: centers.length, data: centers });
  } catch (error) {
    next(error);
  }
};

const getCenterById = async (req, res, next) => {
  try {
    const center = await TrainingCenter.findById(req.params.id).populate('coursesOffered');
    if (!center) {
      return res.status(404).json({ success: false, message: 'Training center not found' });
    }
    res.status(200).json({ success: true, data: center });
  } catch (error) {
    next(error);
  }
};

const createCenter = async (req, res, next) => {
  try {
    const center = await TrainingCenter.create(req.body);
    res.status(201).json({ success: true, data: center });
  } catch (error) {
    next(error);
  }
};

const updateCenter = async (req, res, next) => {
  try {
    const center = await TrainingCenter.findByIdAndUpdate(req.params.id, req.body, {
      returnDocument: 'after',
      runValidators: true,
    });
    if (!center) {
      return res.status(404).json({ success: false, message: 'Training center not found' });
    }
    res.status(200).json({ success: true, data: center });
  } catch (error) {
    next(error);
  }
};

const deleteCenter = async (req, res, next) => {
  try {
    const center = await TrainingCenter.findByIdAndDelete(req.params.id);
    if (!center) {
      return res.status(404).json({ success: false, message: 'Training center not found' });
    }
    res.status(200).json({ success: true, message: 'Training center deleted successfully' });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getCenters,
  getCenterById,
  createCenter,
  updateCenter,
  deleteCenter,
};
