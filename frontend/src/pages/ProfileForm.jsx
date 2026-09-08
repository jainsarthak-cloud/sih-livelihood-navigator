import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import client from '../api/client';
import { useLanguage } from '../context/LanguageContext';
import { User, GraduationCap, MapPin, Briefcase, Mic, MicOff, CheckCircle, ArrowRight, ArrowLeft, Volume2, Globe } from 'lucide-react';
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

const INDIAN_STATES_DISTRICTS = {
  'Madhya Pradesh': ['Bhopal', 'Indore', 'Ujjain', 'Gwalior', 'Jabalpur', 'Sagar', 'Satna', 'Rewa'],
  'Bihar': ['Patna', 'Muzaffarpur', 'Gaya', 'Bhagalpur', 'Darbhanga', 'Purnia', 'Rohtas'],
  'Uttar Pradesh': ['Varanasi', 'Lucknow', 'Kanpur', 'Agra', 'Prayagraj', 'Gorakhpur', 'Noida'],
  'Rajasthan': ['Jaipur', 'Jodhpur', 'Udaipur', 'Kota', 'Ajmer', 'Bikaner', 'Alwar'],
  'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Nashik', 'Thane', 'Aurangabad'],
  'Delhi': ['Central Delhi', 'East Delhi', 'New Delhi', 'North Delhi', 'South Delhi'],
  'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar'],
  'West Bengal': ['Kolkata', 'Howrah', 'Hooghly', 'Darjeeling', 'Murshidabad'],
  'Karnataka': ['Bengaluru', 'Mysuru', 'Hubballi', 'Mangaluru', 'Belagavi'],
  'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem'],
};

const ProfileForm = () => {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);

  // Web Speech API state
  const [isListening, setIsListening] = useState(false);
  const [speechLang, setSpeechLang] = useState('hi-IN');
  const [liveTranscript, setLiveTranscript] = useState('');
  const [activeVoiceField, setActiveVoiceField] = useState('skills');
  const recognitionRef = useRef(null);

  const [formData, setFormData] = useState({
    personal: { age: '', gender: 'Male' },
    education: { level: '10th Pass', field: 'General' },
    location: { state: 'Madhya Pradesh', district: 'Bhopal', block: 'Fanda', village: 'Karond' },
    livelihood: { currentOccupation: 'Weaver', familyOccupation: 'Agriculture', currentIncomeRange: '< 50000' },
    skills: 'Weaving, Embroidery',
    traditionalSkills: 'Handloom',
    interests: 'Textiles, Tailoring',
    aspirations: 'Small Business Owner',
    employmentPreference: 'ANY',
    preferredLanguage: 'Hindi',
    source: 'FORM',
  });

  const currentDistricts = INDIAN_STATES_DISTRICTS[formData.location.state] || [
    'Bhopal', 'Indore', 'Patna', 'Muzaffarpur', 'Varanasi', 'Lucknow', 'Jaipur', 'Jodhpur',
  ];

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = speechLang;

      recognition.onstart = () => {
        setIsListening(true);
        setFormData((prev) => ({ ...prev, source: 'VOICE' }));
        toast.success(`Microphone active (${speechLang === 'hi-IN' ? 'Hindi - hi-IN' : 'English - en-US'})! Speak now.`, { id: 'speech-toast' });
      };

      recognition.onresult = (event) => {
        let currentTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript;
        }
        setLiveTranscript(currentTranscript);

        if (currentTranscript.trim()) {
          mapTranscriptToFormState(currentTranscript.trim());
        }
      };

      recognition.onerror = (event) => {
        if (event.error !== 'no-speech') {
          toast.error(`Speech recognition: ${event.error}`, { id: 'speech-toast' });
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {}
      }
    };
  }, [speechLang]);

  useEffect(() => {
    const fetchExistingProfile = async () => {
      try {
        const res = await client.get('/beneficiaries/profile/me');
        if (res.data.success && res.data.data) {
          const p = res.data.data;
          setFormData({
            personal: { age: p.personal?.age || '', gender: p.personal?.gender || 'Male' },
            education: { level: p.education?.level || '10th Pass', field: p.education?.field || 'General' },
            location: {
              state: p.location?.state || 'Madhya Pradesh',
              district: p.location?.district || 'Bhopal',
              block: p.location?.block || '',
              village: p.location?.village || '',
            },
            livelihood: {
              currentOccupation: p.livelihood?.currentOccupation || '',
              familyOccupation: p.livelihood?.familyOccupation || '',
              currentIncomeRange: p.livelihood?.currentIncomeRange || '< 50000',
            },
            skills: Array.isArray(p.skills) ? p.skills.join(', ') : p.skills || '',
            traditionalSkills: Array.isArray(p.traditionalSkills) ? p.traditionalSkills.join(', ') : p.traditionalSkills || '',
            interests: Array.isArray(p.interests) ? p.interests.join(', ') : p.interests || '',
            aspirations: Array.isArray(p.aspirations) ? p.aspirations.join(', ') : p.aspirations || '',
            employmentPreference: p.employmentPreference || 'ANY',
            preferredLanguage: p.preferredLanguage || 'Hindi',
            source: p.source || 'FORM',
          });
        }
      } catch (err) {
        console.log('No pre-existing profile found, starting fresh form.');
      } finally {
        setFetching(false);
      }
    };
    fetchExistingProfile();
  }, []);

  const mapTranscriptToFormState = (text) => {
    setFormData((prev) => {
      const updated = { ...prev };
      if (activeVoiceField === 'skills') updated.skills = text;
      else if (activeVoiceField === 'interests') updated.interests = text;
      else if (activeVoiceField === 'aspirations') updated.aspirations = text;
      else if (activeVoiceField === 'currentOccupation') updated.livelihood.currentOccupation = text;
      else if (activeVoiceField === 'age') {
        const num = text.match(/\d+/);
        if (num) updated.personal.age = num[0];
      } else if (activeVoiceField === 'block') updated.location.block = text;
      return updated;
    });
  };

  const handleNestedChange = (category, field, value) => {
    setFormData((prev) => ({
      ...prev,
      [category]: { ...prev[category], [field]: value },
    }));
  };

  const handleStateChange = (newState) => {
    const defaultDistrict = INDIAN_STATES_DISTRICTS[newState]?.[0] || 'Default District';
    setFormData((prev) => ({
      ...prev,
      location: { ...prev.location, state: newState, district: defaultDistrict },
    }));
  };

  const toggleSpeechRecognition = (targetField) => {
    setActiveVoiceField(targetField);
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      try {
        setLiveTranscript('');
        recognitionRef.current?.start();
      } catch (err) {
        console.error('Speech start error:', err);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const payload = {
      personal: {
        age: Number(formData.personal.age) || 25,
        gender: formData.personal.gender,
      },
      education: formData.education,
      location: formData.location,
      livelihood: formData.livelihood,
      skills: formData.skills.split(',').map((s) => s.trim()).filter(Boolean),
      traditionalSkills: formData.traditionalSkills.split(',').map((s) => s.trim()).filter(Boolean),
      interests: formData.interests.split(',').map((s) => s.trim()).filter(Boolean),
      aspirations: formData.aspirations.split(',').map((s) => s.trim()).filter(Boolean),
      employmentPreference: formData.employmentPreference,
      preferredLanguage: formData.preferredLanguage,
      source: formData.source,
    };

    try {
      const res = await client.post('/beneficiaries/profile', payload);
      if (res.data.success) {
        toast.success('Beneficiary profile updated successfully!');
        navigate('/recommendations');
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { title: t('personalTab'), icon: User },
    { title: t('educationTab'), icon: MapPin },
    { title: t('occupationTab'), icon: Briefcase },
    { title: t('skillsTab'), icon: GraduationCap },
  ];

  if (fetching) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)]">
        <div className="w-10 h-10 border-4 border-[var(--color-accent-primary)] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6 bg-[var(--color-bg)]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-2">
        <div>
          <h1 className="text-3xl font-black text-[var(--color-text-primary)] tracking-tight">{t('profileTitle')}</h1>
          <p className="text-sm text-[var(--color-text-secondary)] font-medium mt-1">{t('profileSub')}</p>
        </div>

        {/* Voice Controls & Language Switcher */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => {
              const nextLang = speechLang === 'hi-IN' ? 'en-US' : 'hi-IN';
              setSpeechLang(nextLang);
              toast.success(`Speech language changed to ${nextLang === 'hi-IN' ? 'Hindi (hi-IN)' : 'English (en-US)'}`);
            }}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-xs font-bold text-[var(--color-text-primary)] shadow-xs btn-bouncy"
          >
            <Globe className="w-3.5 h-3.5 text-[var(--color-accent-primary)]" />
            <span>{speechLang === 'hi-IN' ? 'हिन्दी (hi-IN)' : 'English (en-US)'}</span>
          </button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => toggleSpeechRecognition('skills')}
            type="button"
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl border text-xs font-extrabold transition-all btn-bouncy ${
              isListening
                ? 'bg-rose-600 text-white border-rose-700 shadow-md animate-pulse'
                : 'bg-[var(--color-surface)] text-[var(--color-accent-secondary)] border-[var(--color-accent-secondary)]'
            }`}
          >
            {isListening ? (
              <>
                <MicOff className="w-4 h-4 text-white animate-bounce" />
                <span>Mic Active (Stop)</span>
              </>
            ) : (
              <>
                <Mic className="w-4 h-4 text-[var(--color-accent-secondary)]" />
                <span>Web Speech Mic</span>
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* Live Voice Transcription Banner */}
      <AnimatePresence>
        {isListening && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-4 bg-[var(--color-surface)] border border-[var(--color-accent-secondary)] rounded-2xl p-4 flex items-center space-x-3 shadow-md"
          >
            <div className="w-8 h-8 rounded-full bg-[var(--color-accent-secondary)] text-white flex items-center justify-center shrink-0">
              <Volume2 className="w-4 h-4 animate-ping" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-extrabold text-[var(--color-accent-secondary)] uppercase tracking-wider">
                Listening ({speechLang === 'hi-IN' ? 'Hindi - hi-IN' : 'English - en-US'}) → Target Field: <span className="underline">{activeVoiceField}</span>
              </p>
              <p className="text-sm font-bold text-[var(--color-text-primary)] truncate mt-0.5">
                {liveTranscript ? `"${liveTranscript}"` : 'Speak into microphone to populate field live...'}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Progress Steps */}
      <div className="grid grid-cols-4 gap-2 mb-6">
        {steps.map((s, idx) => {
          const isDone = step > idx + 1;
          const isCurrent = step === idx + 1;
          return (
            <div
              key={idx}
              onClick={() => setStep(idx + 1)}
              className={`cursor-pointer p-3 rounded-2xl border text-center transition-all ${
                isCurrent
                  ? 'btn-accent shadow-md'
                  : isDone
                  ? 'badge-secondary'
                  : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-accent-primary)]'
              }`}
            >
              <div className="flex justify-center mb-1">
                {isDone ? <CheckCircle className="w-4 h-4 text-[var(--color-accent-secondary)]" /> : <s.icon className="w-4 h-4" />}
              </div>
              <p className="text-[11px] font-extrabold tracking-wider uppercase">{s.title}</p>
            </div>
          );
        })}
      </div>

      {/* Form Container */}
      <div className="bg-[var(--color-surface)] rounded-3xl p-8 border border-[var(--color-border)] shadow-lg relative overflow-hidden">
        <form onSubmit={handleSubmit}>
          <AnimatePresence mode="wait">
            {/* STEP 1: PERSONAL DETAILS */}
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <h3 className="text-xl font-black text-[var(--color-text-primary)] flex items-center space-x-2">
                  <User className="w-5 h-5 text-[var(--color-accent-primary)]" />
                  <span>{t('personalTab')}</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider">{t('ageLabel')}</label>
                      <button
                        type="button"
                        onClick={() => toggleSpeechRecognition('age')}
                        className="text-xs text-[var(--color-accent-primary)] hover:underline flex items-center space-x-1 font-bold"
                      >
                        <Mic className="w-3 h-3 text-[var(--color-accent-primary)]" />
                        <span>Speak Age</span>
                      </button>
                    </div>
                    <input
                      type="number"
                      value={formData.personal.age}
                      onChange={(e) => handleNestedChange('personal', 'age', e.target.value)}
                      placeholder="e.g. 26"
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] font-medium outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5">{t('genderLabel')}</label>
                    <select
                      value={formData.personal.gender}
                      onChange={(e) => handleNestedChange('personal', 'gender', e.target.value)}
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] font-medium outline-none cursor-pointer"
                    >
                      <option value="Female" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">Female</option>
                      <option value="Male" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">Male</option>
                      <option value="Other" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">Other</option>
                    </select>
                  </div>
                </div>
              </motion.div>
            )}

            {/* STEP 2: EDUCATION & LOCATION */}
            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <h3 className="text-xl font-black text-[var(--color-text-primary)] flex items-center space-x-2">
                  <GraduationCap className="w-5 h-5 text-[var(--color-accent-primary)]" />
                  <span>{t('educationTab')}</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5">{t('educationLevelLabel')}</label>
                    <select
                      value={formData.education.level}
                      onChange={(e) => handleNestedChange('education', 'level', e.target.value)}
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] font-medium outline-none cursor-pointer"
                    >
                      <option value="Below 8th" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">Below 8th</option>
                      <option value="8th Pass" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">8th Pass</option>
                      <option value="10th Pass" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">10th Pass</option>
                      <option value="12th Pass" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">12th Pass</option>
                      <option value="ITI/Diploma" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">ITI / Diploma</option>
                      <option value="Graduate" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">Graduate</option>
                      <option value="Post Graduate" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">Post Graduate</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5">{t('stateLabel')}</label>
                    <select
                      value={formData.location.state}
                      onChange={(e) => handleStateChange(e.target.value)}
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] font-medium outline-none cursor-pointer"
                    >
                      {Object.keys(INDIAN_STATES_DISTRICTS).map((st) => (
                        <option key={st} value={st} className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">
                          {st}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5">{t('districtLabel')}</label>
                    <select
                      value={formData.location.district}
                      onChange={(e) => handleNestedChange('location', 'district', e.target.value)}
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] font-medium outline-none cursor-pointer"
                    >
                      {currentDistricts.map((dist) => (
                        <option key={dist} value={dist} className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">
                          {dist}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider">{t('blockLabel')}</label>
                      <button
                        type="button"
                        onClick={() => toggleSpeechRecognition('block')}
                        className="text-xs text-[var(--color-accent-primary)] hover:underline flex items-center space-x-1 font-bold"
                      >
                        <Mic className="w-3 h-3 text-[var(--color-accent-primary)]" />
                        <span>Speak Block</span>
                      </button>
                    </div>
                    <input
                      type="text"
                      value={formData.location.block}
                      onChange={(e) => handleNestedChange('location', 'block', e.target.value)}
                      placeholder="Block or Village name"
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] font-medium outline-none"
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {/* STEP 3: OCCUPATION & LIVELIHOOD */}
            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <h3 className="text-xl font-black text-[var(--color-text-primary)] flex items-center space-x-2">
                  <Briefcase className="w-5 h-5 text-[var(--color-accent-primary)]" />
                  <span>{t('occupationTab')}</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider">{t('currentOccupationLabel')}</label>
                      <button
                        type="button"
                        onClick={() => toggleSpeechRecognition('currentOccupation')}
                        className="text-xs text-[var(--color-accent-primary)] hover:underline flex items-center space-x-1 font-bold"
                      >
                        <Mic className="w-3.5 h-3.5 text-[var(--color-accent-primary)]" />
                        <span>Speak Occupation</span>
                      </button>
                    </div>
                    <input
                      type="text"
                      value={formData.livelihood.currentOccupation}
                      onChange={(e) => handleNestedChange('livelihood', 'currentOccupation', e.target.value)}
                      placeholder="e.g. Handloom Artisan, Weaver, Farmer"
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] font-medium outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5">{t('annualIncomeLabel')}</label>
                    <select
                      value={formData.livelihood.currentIncomeRange}
                      onChange={(e) => handleNestedChange('livelihood', 'currentIncomeRange', e.target.value)}
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] font-medium outline-none cursor-pointer"
                    >
                      <option value="< 50000" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">&lt; ₹50,000</option>
                      <option value="50000-100000" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">₹50,000 - ₹1,00,000</option>
                      <option value="100000-200000" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">₹1,00,000 - ₹2,00,000</option>
                      <option value="> 200000" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">&gt; ₹2,00,000</option>
                    </select>
                  </div>
                </div>
              </motion.div>
            )}

            {/* STEP 4: SKILLS & PREFERENCES */}
            {step === 4 && (
              <motion.div
                key="step4"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <h3 className="text-xl font-black text-[var(--color-text-primary)] flex items-center space-x-2">
                  <GraduationCap className="w-5 h-5 text-[var(--color-accent-primary)]" />
                  <span>{t('skillsTab')}</span>
                </h3>

                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider">
                        {t('existingSkillsLabel')}
                      </label>
                      <button
                        type="button"
                        onClick={() => toggleSpeechRecognition('skills')}
                        className="text-xs text-[var(--color-accent-primary)] hover:underline flex items-center space-x-1 font-bold"
                      >
                        <Mic className="w-3.5 h-3.5 text-[var(--color-accent-primary)]" />
                        <span>Speak Skills</span>
                      </button>
                    </div>
                    <input
                      type="text"
                      value={formData.skills}
                      onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
                      placeholder="Weaving, Stitching, Computer basics"
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] font-medium outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-extrabold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5">
                      {t('employmentPrefLabel')}
                    </label>
                    <select
                      value={formData.employmentPreference}
                      onChange={(e) => setFormData({ ...formData, employmentPreference: e.target.value })}
                      className="w-full bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary)]/20 rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] font-extrabold outline-none cursor-pointer"
                    >
                      <option value="SELF_EMPLOYMENT" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">SELF_EMPLOYMENT (Self Employment / Enterprise)</option>
                      <option value="WAGE_EMPLOYMENT" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">WAGE_EMPLOYMENT (Wage Job / Employment)</option>
                      <option value="HYBRID" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">HYBRID (Hybrid / Both)</option>
                      <option value="ANY" className="bg-[var(--color-surface)] text-[var(--color-text-primary)]">ANY (Any Opportunity)</option>
                    </select>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Form Actions */}
          <div className="mt-8 pt-6 border-t border-[var(--color-border)] flex justify-between items-center">
            {step > 1 ? (
              <button
                type="button"
                onClick={() => setStep(step - 1)}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text-primary)] hover:opacity-90 text-sm font-extrabold btn-bouncy"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>{t('backBtn')}</span>
              </button>
            ) : <div />}

            {step < 4 ? (
              <button
                type="button"
                onClick={() => setStep(step + 1)}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl btn-accent font-extrabold text-sm shadow-md btn-bouncy"
              >
                <span>{t('nextSectionBtn')}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                disabled={loading}
                type="submit"
                className="px-8 py-3 rounded-xl btn-accent font-black text-sm shadow-md flex items-center space-x-2 btn-bouncy"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <span>{t('saveProfileBtn')}</span>
                    <CheckCircle className="w-4 h-4" />
                  </>
                )}
              </motion.button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileForm;
