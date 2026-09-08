const test = require('node:test');
const assert = require('node:assert/strict');
const request = require('supertest');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');

const app = require('../src/app');
const User = require('../src/models/User');
const BeneficiaryProfile = require('../src/models/BeneficiaryProfile');
const NSQFCourse = require('../src/models/NSQFCourse');
const TrainingCenter = require('../src/models/TrainingCenter');

let mongoServer;
let beneficiaryToken;
let courseId;
let centerId;
let enrollmentId;

test.before(async () => {
  mongoServer = await MongoMemoryServer.create();
  const uri = mongoServer.getUri();
  await mongoose.connect(uri);
});

test.after(async () => {
  await mongoose.disconnect();
  if (mongoServer) {
    await mongoServer.stop();
  }
});

test('GET /api/health - should return status OK', async () => {
  const res = await request(app).get('/api/health');
  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.equal(res.body.message, 'Server is healthy');
});

test('POST /api/auth/register - should register a new beneficiary user', async () => {
  const res = await request(app)
    .post('/api/auth/register')
    .send({
      name: 'Ramesh Kumar',
      email: 'ramesh@example.com',
      phone: '9876543210',
      password: 'password123',
      district: 'Bhopal',
      state: 'Madhya Pradesh',
    });

  assert.equal(res.status, 201);
  assert.equal(res.body.success, true);
  assert.equal(res.body.data.role, 'BENEFICIARY');
  assert.ok(res.body.data.token);

  beneficiaryToken = res.body.data.token;
});

test('POST /api/auth/login - should authenticate registered user', async () => {
  const res = await request(app)
    .post('/api/auth/login')
    .send({
      emailOrPhone: 'ramesh@example.com',
      password: 'password123',
    });

  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.ok(res.body.data.token);
});

test('GET /api/auth/me - should get current user profile', async () => {
  const res = await request(app)
    .get('/api/auth/me')
    .set('Authorization', `Bearer ${beneficiaryToken}`);

  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.equal(res.body.data.email, 'ramesh@example.com');
});

test('POST /api/beneficiaries/profile - should create beneficiary profile', async () => {
  const res = await request(app)
    .post('/api/beneficiaries/profile')
    .set('Authorization', `Bearer ${beneficiaryToken}`)
    .send({
      personal: { age: 24, gender: 'Male' },
      education: { level: '10th Pass', field: 'General' },
      location: { state: 'Madhya Pradesh', district: 'Bhopal', block: 'Fanda', village: 'Karond' },
      livelihood: { currentOccupation: 'Handloom Weaver', familyOccupation: 'Agriculture', currentIncomeRange: '< 50000' },
      skills: ['Weaving', 'Embroidery'],
      traditionalSkills: ['Handloom'],
      interests: ['Textiles', 'Tailoring'],
      aspirations: ['Micro Enterprise Owner'],
      employmentPreference: 'SELF_EMPLOYMENT',
      preferredLanguage: 'Hindi',
      source: 'FORM',
    });

  assert.equal(res.status, 201);
  assert.equal(res.body.success, true);
  assert.equal(res.body.data.profileCompletion, 100);
});

test('GET /api/beneficiaries/profile/me - should fetch created profile', async () => {
  const res = await request(app)
    .get('/api/beneficiaries/profile/me')
    .set('Authorization', `Bearer ${beneficiaryToken}`);

  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.equal(res.body.data.livelihood.currentOccupation, 'Handloom Weaver');
});

test('Seed Courses and Centers & GET /api/recommendations', async () => {
  const course = await NSQFCourse.create({
    qpCode: 'QP-TEX-001',
    courseName: 'Handloom Weaving Assistant',
    sector: 'Textiles & Apparel',
    nsqfLevel: 3,
    durationHours: 300,
    minEducationRequired: '8th Pass',
    description: 'Basic handloom weaving and yarn processing.',
  });
  courseId = course._id;

  const center = await TrainingCenter.create({
    centerCode: 'TC-BHO-001',
    name: 'Bhopal Rural Skill Development Institute',
    state: 'Madhya Pradesh',
    district: 'Bhopal',
    address: 'Karond Circle, Bhopal',
    coursesOffered: [course._id],
    contactInfo: { phone: '0755123456', email: 'bhopal@skill.gov.in' },
  });
  centerId = center._id;

  const res = await request(app)
    .get('/api/recommendations')
    .set('Authorization', `Bearer ${beneficiaryToken}`);

  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.ok(Array.isArray(res.body.data.recommendations));
});

test('POST /api/enrollments - should self enroll beneficiary in course', async () => {
  const res = await request(app)
    .post('/api/enrollments')
    .set('Authorization', `Bearer ${beneficiaryToken}`)
    .send({
      courseId,
      centerId,
    });

  assert.equal(res.status, 201);
  assert.equal(res.body.success, true);
  assert.equal(res.body.data.enrollment.status, 'ENROLLED');
  enrollmentId = res.body.data.enrollment._id;
});

test('GET /api/enrollments/me - should fetch user enrollments', async () => {
  const res = await request(app)
    .get('/api/enrollments/me')
    .set('Authorization', `Bearer ${beneficiaryToken}`);

  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.equal(res.body.data.length, 1);
  assert.equal(res.body.data[0].status, 'ENROLLED');
});

test('PATCH /api/enrollments/:id/progress - should update progress', async () => {
  const res = await request(app)
    .patch(`/api/enrollments/${enrollmentId}/progress`)
    .set('Authorization', `Bearer ${beneficiaryToken}`)
    .send({
      attendancePercentage: 75,
      currentModule: 'Weaving Fundamentals',
      notes: 'Active participant',
    });

  assert.equal(res.status, 200);
  assert.equal(res.body.success, true);
  assert.equal(res.body.data.enrollment.status, 'IN_PROGRESS');
  assert.equal(res.body.data.progress.attendancePercentage, 75);
});

test('Bootstrap Admin User & Test Admin Routes', async () => {
  await User.create({
    name: 'District Admin',
    email: 'admin@gov.in',
    phone: '9999999999',
    passwordHash: 'adminpass123',
    role: 'ADMIN',
    district: 'Bhopal',
    state: 'Madhya Pradesh',
  });

  const loginRes = await request(app)
    .post('/api/auth/login')
    .send({
      emailOrPhone: 'admin@gov.in',
      password: 'adminpass123',
    });

  const adminToken = loginRes.body.data.token;

  // Test Admin Dashboard Summary
  const dashRes = await request(app)
    .get('/api/admin/dashboard/summary')
    .set('Authorization', `Bearer ${adminToken}`);

  assert.equal(dashRes.status, 200);
  assert.equal(dashRes.body.success, true);
  assert.equal(dashRes.body.data.totalBeneficiaries, 1);
  assert.equal(dashRes.body.data.activeEnrollments, 1);
});
