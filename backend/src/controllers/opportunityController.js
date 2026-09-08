const Opportunity = require('../models/Opportunity');

const getOpportunities = async (req, res, next) => {
  try {
    const opportunities = await Opportunity.find();
    res.status(200).json({ success: true, count: opportunities.length, data: opportunities });
  } catch (error) {
    next(error);
  }
};

const getOpportunityById = async (req, res, next) => {
  try {
    const opportunity = await Opportunity.findById(req.params.id);
    if (!opportunity) {
      return res.status(404).json({ success: false, message: 'Opportunity not found' });
    }
    res.status(200).json({ success: true, data: opportunity });
  } catch (error) {
    next(error);
  }
};

const createOpportunity = async (req, res, next) => {
  try {
    const opportunity = await Opportunity.create(req.body);
    res.status(201).json({ success: true, data: opportunity });
  } catch (error) {
    next(error);
  }
};

const updateOpportunity = async (req, res, next) => {
  try {
    const opportunity = await Opportunity.findByIdAndUpdate(req.params.id, req.body, {
      returnDocument: 'after',
      runValidators: true,
    });
    if (!opportunity) {
      return res.status(404).json({ success: false, message: 'Opportunity not found' });
    }
    res.status(200).json({ success: true, data: opportunity });
  } catch (error) {
    next(error);
  }
};

const deleteOpportunity = async (req, res, next) => {
  try {
    const opportunity = await Opportunity.findByIdAndDelete(req.params.id);
    if (!opportunity) {
      return res.status(404).json({ success: false, message: 'Opportunity not found' });
    }
    res.status(200).json({ success: true, message: 'Opportunity deleted successfully' });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getOpportunities,
  getOpportunityById,
  createOpportunity,
  updateOpportunity,
  deleteOpportunity,
};
