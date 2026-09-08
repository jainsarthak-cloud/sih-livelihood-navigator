import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import AnimatedCounter from '../components/AnimatedCounter';
import client from '../api/client';
import { useLanguage } from '../context/LanguageContext';
import { CardSkeleton } from '../components/SkeletonLoader';
import { Sparkles, BookOpen, Building2, Briefcase, CheckCircle2, ArrowRight, MapPin, Award, Layers, X, Phone, Users, ShieldCheck, Info } from 'lucide-react';
import { MatchMascot, EmptyStateMascot } from '../components/Mascots';
import confetti from 'canvas-confetti';
import toast from 'react-hot-toast';

/*
  BACKGROUND & TEXT COLOR CONTRACT DECLARATION:
  - Page Background: var(--color-bg) [#FFF8F0 light / #14141F dark]
  - Card Surface: var(--color-surface) [#FFFFFF light / #1E1E2E dark]
  - Primary Text (Headings): var(--color-text-primary) [#1A1A2E light / #FAFAFA dark]
  - Secondary Text (Body/Labels): var(--color-text-secondary) [#4A4A5E light / #C4C4D4 dark]
  - Muted Text (Placeholders): var(--color-text-muted) [#8B8B9E both]
  - Primary Accent Button: var(--color-accent-primary) [#E85D2E light / #FF8B5E dark]
  - Secondary Accent (Badges): var(--color-accent-secondary) [#0F766E light / #2DD4BF dark]
  - Border Color: var(--color-border) [#E8E2D9 light / #2E2E42 dark]
*/

const Recommendations = () => {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [loading, setLoading] = useState(true);
  const [recommendations, setRecommendations] = useState([]);
  const [centers, setCenters] = useState([]);
  const [enrollmentCenters, setEnrollmentCenters] = useState([]);
  const [filter, setFilter] = useState('ALL');

  // Modal State for Enrollment
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [selectedCenterId, setSelectedCenterId] = useState('');
  const [enrolling, setEnrolling] = useState(false);

  // Modal State for Training Centre / Opportunity View Details
  const [selectedDetailsItem, setSelectedDetailsItem] = useState(null);

  useEffect(() => {
    fetchRecommendationsAndCenters();
  }, []);

  const fetchRecommendationsAndCenters = async () => {
    try {
      setLoading(true);
      const [recRes, centerRes] = await Promise.all([
        client.get('/recommendations').catch((err) => err.response || { data: { success: false } }),
        client.get('/centres').catch((err) => err.response || { data: { success: false, data: [] } }),
      ]);

      if (recRes?.data?.success) {
        const recList = recRes.data.data?.recommendations || recRes.data.data || [];
        setRecommendations(Array.isArray(recList) ? recList : []);
      } else {
        setRecommendations([]);
        if (recRes?.status === 404) {
          toast.error('Please complete your profile first');
          navigate('/profile');
          return;
        }
      }

      if (centerRes?.data?.success) {
        setCenters(Array.isArray(centerRes.data.data) ? centerRes.data.data : []);
      }
    } catch (err) {
      console.error('Failed to fetch recommendations:', err);
      toast.error('Failed to load recommendations');
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenEnrollModal = (item) => {
    setSelectedCourse(item);
    const matchedCenters = item.details?.trainingCenters;
    const availableCenters = Array.isArray(matchedCenters) && matchedCenters.length > 0 ? matchedCenters : centers;
    setEnrollmentCenters(availableCenters);
    if (availableCenters.length > 0) {
      setSelectedCenterId(availableCenters[0]._id);
    }
  };

  const handleConfirmEnroll = async () => {
    if (!selectedCourse || !selectedCenterId) {
      toast.error('Please select a training center');
      return;
    }

    setEnrolling(true);
    try {
      const res = await client.post('/enrollments', {
        courseId: selectedCourse.id,
        centerId: selectedCenterId,
      });

      if (res.data.success) {
        confetti({
          particleCount: 90,
          spread: 70,
          origin: { y: 0.6 }
        });
        toast.success(`Successfully enrolled in ${selectedCourse.details?.courseName || 'Training Course'}! 🎉`);
        setSelectedCourse(null);
        navigate('/roadmap');
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Enrollment failed');
    } finally {
      setEnrolling(false);
    }
  };

  const filteredRecs = recommendations.filter((r) => {
    if (filter === 'ALL') return true;
    return r.type === filter;
  });

  const getTypeBadge = (type) => {
    switch (type) {
      case 'COURSE':
        return { label: t('nsqfCourses'), icon: BookOpen };
      case 'CENTER':
        return { label: t('trainingCentres'), icon: Building2 };
      case 'OPPORTUNITY':
        return { label: t('employmentOpps'), icon: Briefcase };
      default:
        return { label: type, icon: Sparkles };
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 bg-[var(--color-bg)]">
      {/* Hero Banner with MatchMascot */}
      <div className="bg-[var(--color-surface)] rounded-3xl p-8 border border-[var(--color-border)] shadow-lg relative overflow-hidden transition-colors">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex-1">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full badge-secondary text-xs font-black uppercase tracking-wider mb-3">
              <Sparkles className="w-3.5 h-3.5 text-[var(--color-accent-secondary)]" />
              <span>{t('aiEngineBadge')}</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-[var(--color-text-primary)] tracking-tight">
              {t('heroRecsTitle')}
            </h1>
            <p className="text-[var(--color-text-secondary)] font-medium mt-2 max-w-2xl text-sm sm:text-base">
              {t('heroRecsSub')}
            </p>
          </div>

          <div className="flex items-center space-x-4">
            <MatchMascot className="w-32 h-32 hidden sm:block drop-shadow-xs shrink-0" />
            <Link to="/profile">
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                className="px-5 py-3 rounded-2xl bg-[var(--color-bg)] text-[var(--color-text-primary)] font-extrabold text-sm border border-[var(--color-border)] flex items-center space-x-2 whitespace-nowrap shadow-xs btn-bouncy"
              >
                <span>{t('updateProfileBtn')}</span>
                <ArrowRight className="w-4 h-4 text-[var(--color-accent-primary)]" />
              </motion.button>
            </Link>
          </div>
        </div>
      </div>

      {/* Category Filter Tabs */}
      <div className="flex flex-wrap items-center gap-3">
        {[
          { key: 'ALL', label: t('allRecs'), icon: Layers },
          { key: 'COURSE', label: t('nsqfCourses'), icon: BookOpen },
          { key: 'CENTER', label: t('trainingCentres'), icon: Building2 },
          { key: 'OPPORTUNITY', label: t('employmentOpps'), icon: Briefcase },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = filter === tab.key;
          return (
            <motion.button
              key={tab.key}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setFilter(tab.key)}
              className={`flex items-center space-x-2 px-4 py-2.5 rounded-2xl text-sm font-extrabold border transition-all btn-bouncy ${
                isActive
                  ? 'btn-accent border-[var(--color-accent-primary)] shadow-md'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg)]'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </motion.button>
          );
        })}
      </div>

      {/* Grid of Recommendation Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : filteredRecs.length === 0 ? (
        <div className="text-center py-16 bg-[var(--color-surface)] rounded-3xl border border-[var(--color-border)] shadow-md flex flex-col items-center justify-center">
          <EmptyStateMascot className="w-36 h-36 mb-2" />
          <h3 className="text-xl font-black text-[var(--color-text-primary)]">{t('noRecsFound')}</h3>
          <p className="text-sm text-[var(--color-text-secondary)] font-medium max-w-md mx-auto mt-2">
            {t('noRecsSub')}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRecs.map((item, index) => {
            const badge = getTypeBadge(item?.type);
            const BadgeIcon = badge.icon;
            const matchScorePct = Math.round((item?.score || 0) * 100);
            const title = item?.details?.courseName || item?.details?.name || item?.details?.title || 'Opportunity';
            const reasons = Array.isArray(item?.reasons) ? item.reasons : [];

            return (
              <motion.div
                key={(item?.id || index) + '-' + index}
                initial={{ opacity: 0, y: 25 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.08, ease: 'easeOut' }}
                whileHover={{ y: -4 }}
                className="bg-[var(--color-surface)] rounded-3xl p-6 border border-[var(--color-border)] hover:border-[var(--color-accent-primary)] transition-all flex flex-col justify-between shadow-md relative overflow-hidden group"
              >
                <div>
                  {/* Top Badge & Score */}
                  <div className="flex justify-between items-start mb-4">
                    <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-black border uppercase tracking-wider badge-secondary">
                      <BadgeIcon className="w-3.5 h-3.5" />
                      <span>{badge.label}</span>
                    </span>

                    {/* Animated Match Score Pill */}
                    <div className="text-right">
                      <div className="inline-flex items-center space-x-1 text-sm font-black text-[var(--color-accent-primary)] bg-[var(--color-bg)] px-3 py-1 rounded-xl border border-[var(--color-border)] shadow-xs">
                        <span>{t('matchScore')}:</span>
                        <AnimatedCounter start={0} end={matchScorePct} duration={1.2} suffix="%" />
                      </div>
                    </div>
                  </div>

                  {/* Score Progress Bar Fill */}
                  <div className="w-full h-2 bg-[var(--color-bg)] rounded-full overflow-hidden mb-5 border border-[var(--color-border)]">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${matchScorePct}%` }}
                      transition={{ duration: 1, delay: 0.2 + index * 0.08 }}
                      className="h-full bg-[var(--color-accent-primary)] rounded-full"
                    />
                  </div>

                  {/* Title & Details */}
                  <h3 className="text-lg font-black text-[var(--color-text-primary)] group-hover:text-[var(--color-accent-primary)] transition-colors">
                    {title}
                  </h3>

                  {item?.details?.sector && (
                    <p className="text-xs font-medium text-[var(--color-text-secondary)] mt-1 flex items-center space-x-1">
                      <Award className="w-3.5 h-3.5 text-[var(--color-accent-primary)] inline" />
                      <span>{t('sectorLabel')}: {item.details.sector}</span>
                    </p>
                  )}

                  {(item?.details?.address || item?.details?.district) && (
                    <p className="text-xs font-medium text-[var(--color-text-secondary)] mt-1 flex items-center space-x-1">
                      <MapPin className="w-3.5 h-3.5 text-[var(--color-accent-secondary)] inline" />
                      <span>{item.details.address || `${item.details.district}, ${item.details.state || 'MP'}`}</span>
                    </p>
                  )}

                  {/* Reasons list */}
                  <div className="mt-4 pt-4 border-t border-[var(--color-border)] space-y-2">
                    <p className="text-[11px] font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider">{t('whyRecommended')}:</p>
                    {reasons.slice(0, 2).map((reason, rIdx) => (
                      <div key={rIdx} className="flex items-start space-x-2 text-xs text-[var(--color-text-secondary)] font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-accent-secondary)] shrink-0 mt-0.5" />
                        <span>{reason}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Card Action */}
                <div className="mt-6 pt-4 border-t border-[var(--color-border)] flex gap-2 justify-between items-center">
                  {item.type === 'COURSE' ? (
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleOpenEnrollModal(item)}
                      className="w-full py-2.5 rounded-xl btn-accent font-extrabold text-xs shadow-md flex items-center justify-center space-x-1.5 btn-bouncy"
                    >
                      <span>{t('enrollInTraining')}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </motion.button>
                  ) : (
                    <button
                      onClick={() => setSelectedDetailsItem(item)}
                      className="w-full py-2.5 rounded-xl bg-[var(--color-bg)] text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] text-xs font-extrabold border border-[var(--color-border)] transition-colors btn-bouncy flex items-center justify-center space-x-1.5"
                    >
                      <Info className="w-3.5 h-3.5 text-[var(--color-accent-primary)]" />
                      <span>{t('viewDetails')}</span>
                    </button>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* VIEW DETAILS MODAL FOR TRAINING CENTRES & OPPORTUNITIES */}
      <AnimatePresence>
        {selectedDetailsItem && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="w-full max-w-xl bg-[var(--color-surface)] rounded-3xl p-6 sm:p-8 border border-[var(--color-border)] shadow-2xl relative space-y-6 max-h-[90vh] overflow-y-auto"
            >
              {/* Close Button */}
              <button
                onClick={() => setSelectedDetailsItem(null)}
                className="absolute top-4 right-4 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] p-2 rounded-xl bg-[var(--color-bg)] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              {/* Modal Header */}
              <div className="flex items-center space-x-3 pr-8">
                <div className="w-12 h-12 rounded-2xl bg-[var(--color-bg)] border border-[var(--color-border)] flex items-center justify-center text-[var(--color-accent-primary)] shrink-0">
                  {selectedDetailsItem.type === 'CENTER' ? <Building2 className="w-6 h-6" /> : <Briefcase className="w-6 h-6" />}
                </div>
                <div>
                  <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase border badge-secondary mb-1">
                    {getTypeBadge(selectedDetailsItem.type).label}
                  </span>
                  <h3 className="text-xl font-black text-[var(--color-text-primary)]">
                    {selectedDetailsItem.details?.name || selectedDetailsItem.details?.title || selectedDetailsItem.details?.courseName || 'Details View'}
                  </h3>
                </div>
              </div>

              {/* Match Score Banner */}
              <div className="bg-[var(--color-bg)] p-4 rounded-2xl border border-[var(--color-border)] flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-5 h-5 text-[var(--color-accent-secondary)]" />
                  <span className="text-xs font-bold text-[var(--color-text-secondary)]">AI Match Compatibility Score</span>
                </div>
                <span className="text-base font-black text-[var(--color-accent-primary)]">
                  {Math.round((selectedDetailsItem.score || 0) * 100)}% Match
                </span>
              </div>

              {/* Detailed Grid Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* Location / Address */}
                <div className="bg-[var(--color-bg)] p-4 rounded-2xl border border-[var(--color-border)] space-y-1">
                  <p className="font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider flex items-center space-x-1">
                    <MapPin className="w-3.5 h-3.5 text-[var(--color-accent-primary)]" />
                    <span>{t('addressLabel')}</span>
                  </p>
                  <p className="font-bold text-[var(--color-text-primary)]">
                    {selectedDetailsItem.details?.address || `${selectedDetailsItem.details?.district || 'Bhopal'}, ${selectedDetailsItem.details?.state || 'Madhya Pradesh'}`}
                  </p>
                </div>

                {/* Sector / Industry */}
                <div className="bg-[var(--color-bg)] p-4 rounded-2xl border border-[var(--color-border)] space-y-1">
                  <p className="font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider flex items-center space-x-1">
                    <Award className="w-3.5 h-3.5 text-[var(--color-accent-secondary)]" />
                    <span>{t('sectorLabel')}</span>
                  </p>
                  <p className="font-bold text-[var(--color-text-primary)]">
                    {selectedDetailsItem.details?.sector || 'Handlooms, Handicrafts & Textiles'}
                  </p>
                </div>

                {/* Contact Information */}
                <div className="bg-[var(--color-bg)] p-4 rounded-2xl border border-[var(--color-border)] space-y-1">
                  <p className="font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider flex items-center space-x-1">
                    <Phone className="w-3.5 h-3.5 text-[var(--color-accent-secondary)]" />
                    <span>{t('contactLabel')}</span>
                  </p>
                  <p className="font-bold text-[var(--color-text-primary)]">
                    {selectedDetailsItem.details?.contactNumber || '+91 98765 43210 (District Hub Helpdesk)'}
                  </p>
                </div>

                {/* Capacity / Openings */}
                <div className="bg-[var(--color-bg)] p-4 rounded-2xl border border-[var(--color-border)] space-y-1">
                  <p className="font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider flex items-center space-x-1">
                    <Users className="w-3.5 h-3.5 text-[var(--color-accent-primary)]" />
                    <span>{t('capacityLabel')}</span>
                  </p>
                  <p className="font-bold text-[var(--color-text-primary)]">
                    {selectedDetailsItem.details?.capacity ? `${selectedDetailsItem.details.capacity} Seats Available` : 'Open Batch / Regional Enrolment Active'}
                  </p>
                </div>
              </div>

              {/* Facility Highlights / Requirements */}
              <div className="bg-[var(--color-bg)] p-4 rounded-2xl border border-[var(--color-border)] space-y-2">
                <p className="text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider">{t('facilitiesLabel')}:</p>
                <div className="flex flex-wrap gap-2">
                  {['NSQF Certified Instructors', 'Stipend Support Available', 'Local Transport & Hostel Facility', 'Post-Training Placement Assistance'].map((feat, fIdx) => (
                    <span key={fIdx} className="px-3 py-1 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-xs font-bold text-[var(--color-text-primary)] flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3 text-[var(--color-accent-secondary)]" />
                      <span>{feat}</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Why Recommended Reasons */}
              {selectedDetailsItem.reasons?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider">{t('whyRecommended')}:</p>
                  <div className="space-y-1.5">
                    {selectedDetailsItem.reasons.map((r, rIdx) => (
                      <div key={rIdx} className="flex items-start space-x-2 text-xs text-[var(--color-text-secondary)] font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-accent-secondary)] shrink-0 mt-0.5" />
                        <span>{r}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Modal Actions */}
              <div className="flex justify-end space-x-3 pt-4 border-t border-[var(--color-border)]">
                <button
                  type="button"
                  onClick={() => setSelectedDetailsItem(null)}
                  className="px-5 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text-primary)] text-xs font-extrabold hover:opacity-90 btn-bouncy"
                >
                  {t('closeBtn')}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Enrollment Confirmation Modal */}
      <AnimatePresence>
        {selectedCourse && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="w-full max-w-lg bg-[var(--color-surface)] rounded-3xl p-6 sm:p-8 border border-[var(--color-border)] shadow-2xl relative"
            >
              <button
                onClick={() => setSelectedCourse(null)}
                className="absolute top-4 right-4 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] p-2 rounded-xl bg-[var(--color-bg)]"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] flex items-center justify-center text-[var(--color-accent-primary)]">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-black text-[var(--color-text-primary)]">Course Enrollment</h3>
                  <p className="text-xs text-[var(--color-text-secondary)] font-medium">Confirm your training center selection</p>
                </div>
              </div>

              <div className="space-y-4 my-6">
                <div className="bg-[var(--color-bg)] rounded-2xl p-4 border border-[var(--color-border)]">
                  <p className="text-xs text-[var(--color-accent-primary)] font-extrabold uppercase tracking-wider">Selected Course</p>
                  <p className="text-base font-black text-[var(--color-text-primary)] mt-1">{selectedCourse.details?.courseName}</p>
                  <p className="text-xs text-[var(--color-text-secondary)] font-medium mt-1">Sector: {selectedCourse.details?.sector} | NSQF Level {selectedCourse.details?.nsqfLevel || '4'}</p>
                </div>

                <div>
                  <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-2">Select Regional Training Center</label>
                  {enrollmentCenters.length === 0 ? (
                    <p className="text-xs text-[var(--color-text-muted)] italic">No specific centers loaded. Using default regional hub.</p>
                  ) : (
                    <select
                      value={selectedCenterId}
                      onChange={(e) => setSelectedCenterId(e.target.value)}
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] font-bold outline-none cursor-pointer"
                    >
                      {enrollmentCenters.map((c) => (
                        <option key={c._id} value={c._id} className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">
                          {c.name} - {c.district || c.address}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-[var(--color-border)]">
                <button
                  type="button"
                  onClick={() => setSelectedCourse(null)}
                  className="px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text-primary)] text-sm font-extrabold hover:opacity-90 btn-bouncy"
                >
                  Cancel
                </button>
                <motion.button
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  disabled={enrolling}
                  onClick={handleConfirmEnroll}
                  className="px-6 py-2.5 rounded-xl btn-accent font-black text-sm shadow-md flex items-center space-x-2 btn-bouncy disabled:opacity-50"
                >
                  {enrolling ? (
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <span>Confirm & Enroll</span>
                      <CheckCircle2 className="w-4 h-4" />
                    </>
                  )}
                </motion.button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Recommendations;
