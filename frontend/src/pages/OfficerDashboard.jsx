import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import AnimatedCounter from '../components/AnimatedCounter';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { DashboardSkeleton } from '../components/SkeletonLoader';
import { LayoutDashboard, Users, GraduationCap, CheckCircle2, AlertTriangle, BarChart3, Filter, ShieldAlert } from 'lucide-react';
import { OfficerMascot } from '../components/Mascots';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from 'recharts';
import toast from 'react-hot-toast';

/*
  BACKGROUND & TEXT COLOR CONTRACT DECLARATION:
  - Page Background: var(--color-bg) [#FFF8F0 light / #14141F dark]
  - Card Surface: var(--color-surface) [#FFFFFF light / #1E1E2E dark]
  - Primary Text (Headings): var(--color-text-primary) [#1A1A2E light / #FAFAFA dark]
  - Secondary Text (Body/Labels): var(--color-text-secondary) [#4A4A5E light / #C4C4D4 dark]
  - Muted Text (Placeholders): var(--color-text-muted) [#8B8B9E both]
  - Primary Accent Button: var(--color-accent-primary) [#E85D2E light / #FF8B5E dark]
  - Secondary Accent: var(--color-accent-secondary) [#0F766E light / #2DD4BF dark]
  - Border Color: var(--color-border) [#E8E2D9 light / #2E2E42 dark]
*/

const OfficerDashboard = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [skillDemand, setSkillDemand] = useState([]);
  const [atRiskData, setAtRiskData] = useState(null);
  const [selectedDistrict, setSelectedDistrict] = useState('');

  // Role Protection check
  useEffect(() => {
    if (user && user.role !== 'OFFICER' && user.role !== 'ADMIN') {
      toast.error('Access restricted to Officers & Administrators');
      navigate('/recommendations');
    }
  }, [user, navigate]);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const districtQuery = selectedDistrict ? `?district=${encodeURIComponent(selectedDistrict)}` : '';

      const [sumRes, demandRes, riskRes] = await Promise.all([
        client.get(`/admin/dashboard/summary${districtQuery}`),
        client.get('/admin/dashboard/skill-demand'),
        client.get('/admin/dashboard/at-risk'),
      ]);

      if (sumRes.data.success) setSummary(sumRes.data.data);
      if (demandRes.data.success) setSkillDemand(demandRes.data.data || []);
      if (riskRes.data.success) setAtRiskData(riskRes.data.data);
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to fetch dashboard statistics');
    } finally {
      setLoading(false);
    }
  }, [selectedDistrict]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 bg-[var(--color-bg)] min-h-screen">
        <DashboardSkeleton />
      </div>
    );
  }

  // Locked color palette array for Recharts bars
  const BAR_COLORS = ['#E85D2E', '#0F766E', '#FF8B5E', '#2DD4BF', '#4A4A5E', '#1A1A2E'];

  return (
    <div className="bg-[var(--color-bg)] min-h-screen pb-12 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Dashboard Top Header with OfficerMascot */}
        <div className="bg-[var(--color-surface)] rounded-3xl p-8 border border-[var(--color-border)] relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-lg">
          <div className="flex items-center space-x-4">
            <div className="w-14 h-14 rounded-2xl bg-[var(--color-bg)] border border-[var(--color-border)] flex items-center justify-center text-[var(--color-accent-primary)] shrink-0">
              <LayoutDashboard className="w-7 h-7 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-3xl font-black text-[var(--color-text-primary)] tracking-tight">{t('officerTitle')}</h1>
                <span className="px-2.5 py-0.5 rounded-full badge-secondary text-xs font-bold">
                  {user?.role}
                </span>
              </div>
              <p className="text-[var(--color-text-secondary)] text-sm mt-1">{t('officerSub')}</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <OfficerMascot className="w-24 h-24 hidden sm:block drop-shadow-md shrink-0" />
            
            {/* District Filter Selector */}
            <div className="flex items-center space-x-3 bg-[var(--color-bg)] p-3 rounded-2xl border border-[var(--color-border)] shadow-md">
              <Filter className="w-4 h-4 text-[var(--color-accent-primary)] shrink-0 ml-1" />
              <select
                value={selectedDistrict}
                onChange={(e) => setSelectedDistrict(e.target.value)}
                className="bg-transparent text-sm font-bold text-[var(--color-text-primary)] outline-none pr-4 cursor-pointer"
              >
                <option value="" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">All Districts</option>
                <option value="Bhopal" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">Bhopal</option>
                <option value="Indore" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">Indore</option>
                <option value="Ujjain" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">Ujjain</option>
                <option value="Gwalior" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">Gwalior</option>
              </select>
            </div>
          </div>
        </div>

        {/* STAT CARDS (CountUp Animated) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              title: t('totalBeneficiaries'),
              val: summary?.totalBeneficiaries || 0,
              icon: Users,
              color: 'text-[var(--color-accent-primary)]',
            },
            {
              title: t('activeEnrollments'),
              val: summary?.activeEnrollments || 0,
              icon: GraduationCap,
              color: 'text-[var(--color-accent-secondary)]',
            },
            {
              title: t('completedTrainings'),
              val: summary?.completedTrainings || 0,
              icon: CheckCircle2,
              color: 'text-[var(--color-accent-secondary)]',
            },
            {
              title: t('openInterventions'),
              val: summary?.openInterventions || 0,
              icon: AlertTriangle,
              color: 'text-[var(--color-accent-primary)]',
            },
          ].map((stat, idx) => {
            const Icon = stat.icon;
            return (
              <motion.div
                key={stat.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: idx * 0.08 }}
                className="bg-[var(--color-surface)] rounded-3xl p-6 border border-[var(--color-border)] shadow-md flex items-center justify-between"
              >
                <div>
                  <p className="text-xs font-bold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1">{stat.title}</p>
                  <div className={`text-3xl font-black ${stat.color}`}>
                    <AnimatedCounter start={0} end={stat.val} duration={1.5} />
                  </div>
                </div>

                <div className="w-12 h-12 rounded-2xl flex items-center justify-center border border-[var(--color-border)] bg-[var(--color-bg)]">
                  <Icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* RECHARTS SKILL DEMAND BAR CHART */}
        <div className="bg-[var(--color-surface)] rounded-3xl p-8 border border-[var(--color-border)] shadow-xl space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] flex items-center justify-center text-[var(--color-accent-primary)]">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-black text-[var(--color-text-primary)]">{t('skillDemandTitle')}</h2>
                <p className="text-xs text-[var(--color-text-secondary)]">Training enrollment distribution grouped by NSQF sector (Recharts)</p>
              </div>
            </div>
          </div>

          {skillDemand.length === 0 ? (
            <div className="text-center py-10 text-[var(--color-text-muted)] text-sm italic">
              No sector enrollment data currently available.
            </div>
          ) : (
            <div className="w-full h-80 pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={skillDemand} margin={{ top: 10, right: 30, left: 0, bottom: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.7} />
                  <XAxis 
                    dataKey="sector" 
                    stroke="var(--color-text-secondary)" 
                    fontSize={12}
                    tickLine={false}
                    interval={0}
                    angle={-15}
                    textAnchor="end"
                  />
                  <YAxis stroke="var(--color-text-secondary)" fontSize={12} tickLine={false} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '12px', color: 'var(--color-text-primary)' }}
                    cursor={{ fill: 'rgba(0, 0, 0, 0.04)' }}
                  />
                  <Bar dataKey="enrollmentCount" name="Enrollments" radius={[8, 8, 0, 0]}>
                    {skillDemand.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* AT-RISK BENEFICIARIES & INTERVENTIONS SECTION */}
        {atRiskData && (
          <div className="bg-[var(--color-surface)] rounded-3xl p-8 border border-[var(--color-border)] shadow-xl space-y-6">
            <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-4">
              <div className="flex items-center space-x-3">
                <ShieldAlert className="w-6 h-6 text-[var(--color-accent-primary)]" />
                <h2 className="text-xl font-black text-[var(--color-text-primary)]">{t('atRiskTitle')}</h2>
              </div>
              <span className="px-3 py-1 rounded-full badge-secondary text-xs font-bold">
                {atRiskData.totalAtRiskCount || 0} Flagged
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Low Attendance List */}
              <div className="bg-[var(--color-bg)] rounded-2xl p-5 border border-[var(--color-border)] space-y-4">
                <h3 className="text-sm font-bold text-[var(--color-text-secondary)] uppercase tracking-wider">Low Attendance (&lt; 50%)</h3>
                {atRiskData.lowAttendanceEnrollments?.length === 0 ? (
                  <p className="text-xs text-[var(--color-text-muted)] italic">No low-attendance alerts.</p>
                ) : (
                  <div className="space-y-3">
                    {atRiskData.lowAttendanceEnrollments?.slice(0, 3).map((item, idx) => (
                      <div key={idx} className="flex justify-between items-center bg-[var(--color-surface)] p-3 rounded-xl border border-[var(--color-border)]">
                        <div>
                          <p className="text-sm font-bold text-[var(--color-text-primary)]">
                            {item.enrollmentId?.beneficiaryId?.userId?.name || 'Beneficiary'}
                          </p>
                          <p className="text-xs text-[var(--color-text-secondary)]">{item.enrollmentId?.courseId?.courseName}</p>
                        </div>
                        <span className="text-xs font-black text-[var(--color-accent-primary)] bg-[var(--color-bg)] px-2.5 py-1 rounded-lg border border-[var(--color-border)]">
                          {item.attendancePercentage}% Att.
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* High Risk Interventions */}
              <div className="bg-[var(--color-bg)] rounded-2xl p-5 border border-[var(--color-border)] space-y-4">
                <h3 className="text-sm font-bold text-[var(--color-text-secondary)] uppercase tracking-wider">High Risk Interventions</h3>
                {atRiskData.highRiskInterventions?.length === 0 ? (
                  <p className="text-xs text-[var(--color-text-muted)] italic">No high-risk intervention tickets active.</p>
                ) : (
                  <div className="space-y-3">
                    {atRiskData.highRiskInterventions?.slice(0, 3).map((item, idx) => (
                      <div key={idx} className="flex justify-between items-center bg-[var(--color-surface)] p-3 rounded-xl border border-[var(--color-border)]">
                        <div>
                          <p className="text-sm font-bold text-[var(--color-text-primary)]">
                            {item.beneficiaryId?.userId?.name || 'Beneficiary'}
                          </p>
                          <p className="text-xs text-[var(--color-text-secondary)]">{item.reason}</p>
                        </div>
                        <span className="text-xs font-bold text-[var(--color-accent-secondary)] bg-[var(--color-bg)] px-2 py-1 rounded-lg border border-[var(--color-border)]">
                          {item.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OfficerDashboard;
