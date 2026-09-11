import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { User, Mail, Phone, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { WelcomeMascot } from '../components/Mascots';
import toast from 'react-hot-toast';

/*
  BACKGROUND & TEXT COLOR CONTRACT DECLARATION:
  - Page Background: var(--color-bg) [#FFF8F0 light / #14141F dark]
  - Card Surface: var(--color-surface) [#FFFFFF light / #1E1E2E dark]
  - Primary Text (Headings): var(--color-text-primary) [#1A1A2E light / #FAFAFA dark]
  - Secondary Text (Body/Labels): var(--color-text-secondary) [#4A4A5E light / #C4C4D4 dark]
  - Muted Text (Placeholders): var(--color-text-muted) [#8B8B9E both]
  - Primary Accent Button: var(--color-accent-primary) [#E85D2E light / #FF8B5E dark]
  - Border Color: var(--color-border) [#E8E2D9 light / #2E2E42 dark]
*/

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);

  const { register } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email || !phone || !password) {
      toast.error('Please fill in all required fields');
      triggerShake();
      return;
    }

    setLoading(true);
    try {
      const user = await register(name, email, phone, password);
      toast.success(`Account created! Welcome, ${user.name}`);
      navigate('/profile');
    } catch (err) {
      const msg =
        err.response?.data?.message ||
        (!err.response && err.message === 'Network Error'
          ? 'Unable to connect to backend server. Please verify backend is running on port 5000.'
          : err.message || 'Registration failed');
      toast.error(msg);
      triggerShake();
    } finally {
      setLoading(false);
    }
  };

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 500);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 bg-[var(--color-bg)] transition-colors">
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.96 }}
        animate={
          shake
            ? { x: [-10, 10, -8, 8, -4, 4, 0], opacity: 1, y: 0, scale: 1 }
            : { opacity: 1, y: 0, scale: 1 }
        }
        transition={{ duration: shake ? 0.4 : 0.5, ease: 'easeOut' }}
        className="w-full max-w-xl bg-[var(--color-surface)] rounded-3xl p-8 sm:p-10 border border-[var(--color-border)] shadow-lg relative overflow-hidden flex flex-col md:flex-row items-center gap-8"
      >
        {/* Left Side: Mascot & Welcome text */}
        <div className="flex flex-col items-center text-center md:w-1/2">
          <WelcomeMascot className="w-44 h-44 drop-shadow-xs" />
          <h2 className="text-2xl font-black text-[var(--color-text-primary)] tracking-tight mt-2">{t('getStarted')}</h2>
          <p className="text-sm text-[var(--color-text-secondary)] font-medium mt-1">
            Build your skills and unlock high-potential opportunities.
          </p>
        </div>

        {/* Right Side: Register Form */}
        <div className="w-full md:w-1/2">
          <form onSubmit={handleSubmit} className="space-y-3.5">
            <div>
              <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ramesh Kumar"
                  className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl pl-10 pr-3 py-2 text-xs sm:text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] font-medium transition-all outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ramesh@example.com"
                  className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl pl-10 pr-3 py-2 text-xs sm:text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] font-medium transition-all outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1">
                Phone Number
              </label>
              <div className="relative">
                <Phone className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="9876543210"
                  className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl pl-10 pr-3 py-2 text-xs sm:text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] font-medium transition-all outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl pl-10 pr-10 py-2 text-xs sm:text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] font-medium transition-all outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors focus:outline-none"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              disabled={loading}
              type="submit"
              className="w-full py-2.5 rounded-xl btn-accent font-extrabold text-sm shadow-md flex items-center justify-center space-x-2 transition-all btn-bouncy disabled:opacity-50 mt-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>{t('getStarted')}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </motion.button>
          </form>

          <div className="mt-4 pt-3 border-t border-[var(--color-border)] text-center">
            <p className="text-xs text-[var(--color-text-secondary)] font-medium">
              Already registered?{' '}
              <Link to="/login" className="text-[var(--color-accent-primary)] hover:underline font-extrabold transition-colors">
                {t('logIn')}
              </Link>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Register;
