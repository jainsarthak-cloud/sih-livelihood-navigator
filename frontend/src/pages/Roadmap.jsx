import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import gsap from 'gsap';
import client from '../api/client';
import { useLanguage } from '../context/LanguageContext';
import { CardSkeleton } from '../components/SkeletonLoader';
import { Map, BookOpen, Building2, CheckCircle2, Clock, Sparkles, Trophy, IndianRupee, Briefcase, ArrowUpRight } from 'lucide-react';
import { JourneyMascot, EmptyStateMascot } from '../components/Mascots';
import toast from 'react-hot-toast';

/*
  BACKGROUND & TEXT COLOR CONTRACT DECLARATION:
  - Page Background: var(--color-bg) [#FFF8F0 light / #14141F dark]
  - Card Surface: var(--color-surface) [#FFFFFF light / #1E1E2E dark]
  - Primary Text (Headings): var(--color-text-primary) [#1A1A2E light / #FAFAFA dark]
  - Secondary Text (Body/Labels): var(--color-text-secondary) [#4A4A5E light / #C4C4D4 dark]
  - Muted Text (Placeholders): var(--color-text-muted) [#8B8B9E both]
  - Primary Accent Button: var(--color-accent-primary) [#E85D2E light / #FF8B5E dark]
  - Secondary Accent (Timeline/Badges): var(--color-accent-secondary) [#0F766E light / #2DD4BF dark]
  - Border Color: var(--color-border) [#E8E2D9 light / #2E2E42 dark]
*/

const Roadmap = () => {
  const { t } = useLanguage();
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const containerRef = useRef(null);

  const fetchMyEnrollments = useCallback(async () => {
    try {
      setLoading(true);
      const res = await client.get('/enrollments/me');
      if (res.data.success) {
        setEnrollments(res.data.data || []);
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to fetch journey enrollments');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMyEnrollments();
  }, [fetchMyEnrollments]);

  useEffect(() => {
    if (loading || enrollments.length === 0 || !containerRef.current) return;

    const ctx = gsap.context(() => {
      gsap.utils.toArray('.journey-line-fill').forEach((line) => {
        const targetWidth = line.getAttribute('data-progress') || '0%';
        gsap.fromTo(
          line,
          { width: '0%' },
          { width: targetWidth, duration: 1.2, ease: 'power2.out' }
        );
      });

      gsap.to('.stage-active-pulse', {
        scale: 1.15,
        opacity: 0.8,
        duration: 0.8,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
      });
    }, containerRef);

    return () => ctx.revert();
  }, [loading, enrollments]);

  const stages = [
    { key: 'RECOMMENDED', label: 'Recommended', icon: Sparkles },
    { key: 'ENROLLED', label: 'Enrolled', icon: BookOpen },
    { key: 'IN_PROGRESS', label: 'In Progress', icon: Clock },
    { key: 'COMPLETED', label: 'Completed', icon: CheckCircle2 },
    { key: 'OUTCOME', label: 'Outcome', icon: Trophy },
  ];

  const getActiveStageIndex = (enrollment) => {
    const status = enrollment.status;
    const progress = enrollment.progress;
    const outcome = enrollment.outcome;

    if (outcome) return 4;
    if (status === 'COMPLETED') return 3;
    if (status === 'IN_PROGRESS' || (progress && progress.attendancePercentage > 0)) return 2;
    if (status === 'ENROLLED') return 1;
    return 0;
  };

  return (
    <div ref={containerRef} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 bg-[var(--color-bg)]">
      {/* Header Banner with JourneyMascot */}
      <div className="bg-[var(--color-surface)] rounded-3xl p-8 border border-[var(--color-border)] shadow-lg relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6 transition-colors">
        <div className="flex items-center space-x-4">
          <div className="w-14 h-14 rounded-2xl bg-[var(--color-bg)] border border-[var(--color-border)] flex items-center justify-center text-[var(--color-accent-primary)] shrink-0">
            <Map className="w-7 h-7 stroke-[2.5]" />
          </div>
          <div>
            <h1 className="text-3xl font-black text-[var(--color-text-primary)] tracking-tight">{t('journeyTitle')}</h1>
            <p className="text-[var(--color-text-secondary)] font-medium text-sm mt-1">
              {t('journeySub')}
            </p>
          </div>
        </div>

        <JourneyMascot className="w-36 h-36 hidden sm:block drop-shadow-xs shrink-0" />
      </div>

      {/* Main Content */}
      {loading ? (
        <div className="space-y-6">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : enrollments.length === 0 ? (
        <div className="text-center py-16 bg-[var(--color-surface)] rounded-3xl border border-[var(--color-border)] shadow-md flex flex-col items-center justify-center">
          <EmptyStateMascot className="w-36 h-36 mb-2" />
          <h3 className="text-xl font-black text-[var(--color-text-primary)]">{t('noEnrollmentsYet')}</h3>
          <p className="text-sm text-[var(--color-text-secondary)] font-medium max-w-md mx-auto mt-2 mb-6">
            {t('noEnrollmentsSub')}
          </p>
          <a
            href="/recommendations"
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-2xl btn-accent font-extrabold text-sm shadow-md btn-bouncy"
          >
            <span>{t('exploreRecsBtn')}</span>
            <ArrowUpRight className="w-4 h-4" />
          </a>
        </div>
      ) : (
        <div className="space-y-8">
          {enrollments.map((enrollment, index) => {
            const courseName = enrollment.courseId?.courseName || 'NSQF Training Course';
            const centerName = enrollment.centerId?.name || 'Regional Skill Center';
            const centerLocation = enrollment.centerId?.district || enrollment.centerId?.address || 'Madhya Pradesh';
            const activeStageIdx = getActiveStageIndex(enrollment);
            const progressPct = ((activeStageIdx) / (stages.length - 1)) * 100;
            const progress = enrollment.progress;
            const outcome = enrollment.outcome;

            return (
              <motion.div
                key={enrollment._id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="bg-[var(--color-surface)] rounded-3xl p-6 sm:p-8 border border-[var(--color-border)] shadow-lg relative space-y-6"
              >
                {/* Course Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--color-border)] pb-6">
                  <div>
                    <div className="flex items-center space-x-3 mb-2">
                      <span className="px-3 py-1 rounded-full text-xs font-black border uppercase tracking-wider badge-secondary">
                        {enrollment.status}
                      </span>
                      {enrollment.courseId?.sector && (
                        <span className="text-xs font-extrabold text-[var(--color-accent-primary)] bg-[var(--color-bg)] px-2.5 py-0.5 rounded-md border border-[var(--color-border)]">
                          {enrollment.courseId.sector}
                        </span>
                      )}
                    </div>
                    <h2 className="text-2xl font-black text-[var(--color-text-primary)]">{courseName}</h2>
                    <p className="text-xs font-medium text-[var(--color-text-secondary)] mt-1 flex items-center space-x-1">
                      <Building2 className="w-3.5 h-3.5 text-[var(--color-accent-secondary)] inline" />
                      <span>{centerName} • {centerLocation}</span>
                    </p>
                  </div>

                  {/* Attendance Pill */}
                  {progress && (
                    <div className="bg-[var(--color-bg)] rounded-2xl p-4 border border-[var(--color-border)] text-right min-w-[140px]">
                      <span className="text-[11px] font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider block">{t('attendanceLabel')}</span>
                      <span className="text-2xl font-black text-[var(--color-accent-secondary)]">
                        {progress.attendancePercentage}%
                      </span>
                    </div>
                  )}
                </div>

                {/* VISUAL JOURNEY TIMELINE */}
                <div className="py-4">
                  <p className="text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-6">{t('visualTimeline')}</p>

                  <div className="relative">
                    {/* Background track line */}
                    <div className="absolute top-5 left-6 right-6 h-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-full" />

                    {/* Animated GSAP fill line */}
                    <div
                      className="journey-line-fill absolute top-5 left-6 h-1.5 bg-[var(--color-accent-primary)] rounded-full"
                      data-progress={`${progressPct}%`}
                    />

                    {/* Stages node row */}
                    <div className="relative flex justify-between items-center">
                      {stages.map((stage, sIdx) => {
                        const StageIcon = stage.icon;
                        const isPast = sIdx < activeStageIdx;
                        const isCurrent = sIdx === activeStageIdx;

                        return (
                          <div key={stage.key} className="flex flex-col items-center group">
                            <div
                              className={`w-10 h-10 rounded-2xl flex items-center justify-center border transition-all z-10 ${
                                isCurrent
                                  ? 'btn-accent border-[var(--color-accent-primary)] shadow-md'
                                  : isPast
                                  ? 'badge-secondary'
                                  : 'bg-[var(--color-bg)] text-[var(--color-text-muted)] border-[var(--color-border)]'
                              }`}
                            >
                              <StageIcon className="w-5 h-5 stroke-[2.2]" />
                              {isCurrent && (
                                <div className="stage-active-pulse absolute w-10 h-10 rounded-2xl bg-[var(--color-accent-primary)]/20 border border-[var(--color-accent-primary)] pointer-events-none" />
                              )}
                            </div>
                            <span
                              className={`text-xs font-extrabold mt-3 transition-colors ${
                                isCurrent
                                  ? 'text-[var(--color-accent-primary)]'
                                  : isPast
                                  ? 'text-[var(--color-accent-secondary)]'
                                  : 'text-[var(--color-text-muted)]'
                              }`}
                            >
                              {stage.label}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Additional Details & Outcome Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-[var(--color-border)]">
                  {/* Current Module & Progress Info */}
                  <div className="bg-[var(--color-bg)] rounded-2xl p-5 border border-[var(--color-border)] space-y-2">
                    <p className="text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider">{t('currentModule')}</p>
                    <p className="text-base font-black text-[var(--color-text-primary)]">
                      {progress?.currentModule || 'Orientation & Basics'}
                    </p>
                    {progress?.notes && (
                      <p className="text-xs text-[var(--color-text-secondary)] italic">"{progress.notes}"</p>
                    )}
                  </div>

                  {/* Employment Outcome Card (If exists) */}
                  {outcome ? (
                    <div className="bg-[var(--color-bg)] rounded-2xl p-5 border border-[var(--color-accent-secondary)] space-y-2 relative overflow-hidden">
                      <div className="flex items-center space-x-2 text-[var(--color-accent-secondary)] font-extrabold text-xs uppercase tracking-wider">
                        <Trophy className="w-4 h-4 text-[var(--color-accent-secondary)]" />
                        <span>{t('verifiedOutcome')}</span>
                      </div>
                      <p className="text-lg font-black text-[var(--color-text-primary)]">
                        {outcome.outcomeType?.replace('_', ' ')}: {outcome.employerOrBusinessName || 'Local Enterprise'}
                      </p>
                      <p className="text-sm font-black text-[var(--color-accent-secondary)] flex items-center space-x-1">
                        <IndianRupee className="w-4 h-4" />
                        <span>₹{outcome.monthlyIncome?.toLocaleString()} / month</span>
                      </p>
                    </div>
                  ) : (
                    <div className="bg-[var(--color-bg)] rounded-2xl p-5 border border-[var(--color-border)] flex items-center space-x-3 text-[var(--color-text-secondary)]">
                      <Briefcase className="w-5 h-5 text-[var(--color-accent-primary)] shrink-0" />
                      <p className="text-xs font-medium">
                        {t('outcomePendingNote')}
                      </p>
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Roadmap;
