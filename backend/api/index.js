const app = require('../src/app');
const connectWithRetry = require('../src/config/db');

// Ensure DB connection in serverless environment
connectWithRetry();

module.exports = app;
