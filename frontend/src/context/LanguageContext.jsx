import React, { createContext, useContext, useState } from 'react';

/*
  GLOBAL MULTI-LANGUAGE CONTEXT SYSTEM FOR LIVELIHOOD NAVIGATOR
  Supported Indian Languages:
  - en: English
  - hi: Hindi (हिन्दी)
  - mr: Marathi (मराठी)
  - bn: Bengali (বাংলা)
  - ta: Tamil (தமிழ்)
  - te: Telugu (తెలుగు)
  - gu: Gujarati (ગુજરાતી)
  - kn: Kannada (ಕನ್ನಡ)
  - pa: Punjabi (ਪੰਜਾਬੀ)
  - or: Odia (ଓଡ଼ିଆ)
*/

export const LANGUAGES = [
  { code: 'en', name: 'English', native: 'English' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी' },
  { code: 'mr', name: 'Marathi', native: 'मराठी' },
  { code: 'bn', name: 'Bengali', native: 'বাংলা' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు' },
  { code: 'gu', name: 'Gujarati', native: 'ગુજરાતી' },
  { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ' },
  { code: 'pa', name: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
  { code: 'or', name: 'Odia', native: 'ଓଡ଼ିଆ' },
];

const TRANSLATIONS = {
  en: {
    // Nav
    appName: 'Livelihood Navigator',
    appSubtitle: 'AI Career & Opportunity Platform',
    navRecs: 'Recommendations',
    navJourney: 'My Journey',
    navProfile: 'My Profile',
    navOfficer: 'Officer Dashboard',
    logIn: 'Log In',
    getStarted: 'Get Started',
    logout: 'Logout',

    // Recommendations Page
    aiEngineBadge: 'AI Recommendation Engine',
    heroRecsTitle: 'Personalized Livelihood Pathways',
    heroRecsSub: 'Matched tailored courses, regional training centers, and local employment opportunities based on your skills and location.',
    updateProfileBtn: 'Update Profile',
    allRecs: 'All Recommendations',
    nsqfCourses: 'NSQF Courses',
    trainingCentres: 'Training Centres',
    employmentOpps: 'Employment Opportunities',
    noRecsFound: 'No Recommendations Found',
    noRecsSub: 'Try updating your profile skills or location preferences to unlock more tailored opportunities!',
    enrollInTraining: 'Enroll in Training',
    viewDetails: 'View Details',
    matchScore: 'Match',
    whyRecommended: 'Why Recommended',
    sectorLabel: 'Sector',

    // Details Modal
    centreDetailsTitle: 'Training Centre & Opportunity Details',
    centreNameLabel: 'Centre Name',
    addressLabel: 'Address & Location',
    contactLabel: 'Contact Information',
    capacityLabel: 'Training Capacity / Openings',
    facilitiesLabel: 'Facility Highlights',
    closeBtn: 'Close',

    // Profile Form
    profileTitle: 'Beneficiary Profile',
    profileSub: 'Complete structured form fields or use real Web Speech API transcription',
    personalTab: 'Personal',
    educationTab: 'Education & Location',
    occupationTab: 'Occupation & Income',
    skillsTab: 'Skills & Preferences',
    ageLabel: 'Age',
    genderLabel: 'Gender',
    educationLevelLabel: 'Education Level',
    stateLabel: 'State',
    districtLabel: 'District',
    blockLabel: 'Block / Village',
    currentOccupationLabel: 'Current Occupation',
    annualIncomeLabel: 'Annual Household Income',
    existingSkillsLabel: 'Existing Skills (comma separated)',
    employmentPrefLabel: 'Employment Preference',
    saveProfileBtn: 'Save & Generate Recommendations',
    nextSectionBtn: 'Next Section',
    backBtn: 'Back',

    // Roadmap
    journeyTitle: 'My Livelihood Journey',
    journeySub: 'Track your training progress, module milestones, and employment outcomes in real time',
    noEnrollmentsYet: 'No Active Enrollments Yet',
    noEnrollmentsSub: 'Browse tailored course recommendations and enroll to start your personalized training pathway.',
    exploreRecsBtn: 'Explore Recommendations',
    attendanceLabel: 'Attendance',
    visualTimeline: 'Visual Milestone Timeline',
    currentModule: 'Current Training Module',
    verifiedOutcome: 'Verified Employment Outcome',
    outcomePendingNote: 'Post-training job placement and self-employment outcomes will be verified here by your District Officer.',

    // Officer Dashboard
    officerTitle: 'District Officer Command',
    officerSub: 'Real-time livelihood metrics, skill demand analytics, and risk interventions',
    totalBeneficiaries: 'Total Beneficiaries',
    activeEnrollments: 'Active Enrollments',
    completedTrainings: 'Completed Trainings',
    openInterventions: 'Open Interventions',
    skillDemandTitle: 'Regional Skill Demand Analytics',
    atRiskTitle: 'At-Risk Beneficiaries & Dropout Alerts',
  },

  hi: {
    // Nav
    appName: 'आजीविका नेविगेटर',
    appSubtitle: 'एआई करियर और अवसर प्लेटफॉर्म',
    navRecs: 'सिफारिशें',
    navJourney: 'मेरी यात्रा',
    navProfile: 'मेरी प्रोफाइल',
    navOfficer: 'अधिकारी डैशबोर्ड',
    logIn: 'लॉग इन करें',
    getStarted: 'शुरू करें',
    logout: 'लॉग आउट',

    // Recommendations Page
    aiEngineBadge: 'एआई सिफारिश इंजन',
    heroRecsTitle: 'व्यक्तिगत आजीविका मार्ग',
    heroRecsSub: 'आपकी क्षमताओं और स्थान के आधार पर विशेष पाठ्यक्रम, क्षेत्रीय प्रशिक्षण केंद्र और स्थानीय रोजगार अवसर।',
    updateProfileBtn: 'प्रोफाइल अपडेट करें',
    allRecs: 'सभी सिफारिशें',
    nsqfCourses: 'एनएसक्यूएफ पाठ्यक्रम',
    trainingCentres: 'प्रशिक्षण केंद्र',
    employmentOpps: 'रोजगार अवसर',
    noRecsFound: 'कोई सिफारिश नहीं मिली',
    noRecsSub: 'अधिक अवसर देखने के लिए अपने कौशल या स्थान प्राथमिकताओं को अपडेट करें!',
    enrollInTraining: 'प्रशिक्षण में नामांकन करें',
    viewDetails: 'विवरण देखें',
    matchScore: 'मैच',
    whyRecommended: 'सिफारिश का कारण',
    sectorLabel: 'क्षेत्र',

    // Details Modal
    centreDetailsTitle: 'प्रशिक्षण केंद्र और अवसर विवरण',
    centreNameLabel: 'केंद्र का नाम',
    addressLabel: 'पता और स्थान',
    contactLabel: 'संपर्क जानकारी',
    capacityLabel: 'प्रशिक्षण क्षमता / सीटें',
    facilitiesLabel: 'सुविधाएं और विशेषताएं',
    closeBtn: 'बंद करें',

    // Profile Form
    profileTitle: 'लाभार्थी प्रोफाइल',
    profileSub: 'फॉर्म भरें या वेब स्पीच आवाज सुविधा का उपयोग करें',
    personalTab: 'व्यक्तिगत',
    educationTab: 'शिक्षा और स्थान',
    occupationTab: 'व्यवसाय और आय',
    skillsTab: 'कौशल और आकांक्षाएं',
    ageLabel: 'आयु',
    genderLabel: 'लिंग',
    educationLevelLabel: 'शिक्षा स्तर',
    stateLabel: 'राज्य',
    districtLabel: 'जिला',
    blockLabel: 'ब्लॉक / गांव',
    currentOccupationLabel: 'वर्तमान व्यवसाय',
    annualIncomeLabel: 'वार्षिक पारिवारिक आय',
    existingSkillsLabel: 'मौजूदा कौशल (कॉमा से अलग करें)',
    employmentPrefLabel: 'रोजगार प्राथमिकता',
    saveProfileBtn: 'सहेजें और सिफारिशें प्राप्त करें',
    nextSectionBtn: 'अगला भाग',
    backBtn: 'पीछे',

    // Roadmap
    journeyTitle: 'मेरी आजीविका यात्रा',
    journeySub: 'अपने प्रशिक्षण प्रगति, मॉड्यूल मील के पत्थर और रोजगार परिणामों को ट्रैक करें',
    noEnrollmentsYet: 'कोई सक्रिय नामांकन नहीं',
    noEnrollmentsSub: 'अपनी व्यक्तिगत प्रशिक्षण यात्रा शुरू करने के लिए अनुशंसित पाठ्यक्रमों को ब्राउज़ करें।',
    exploreRecsBtn: 'सिफारिशें देखें',
    attendanceLabel: 'उपस्थिति',
    visualTimeline: 'मील का पत्थर समयरेखा',
    currentModule: 'वर्तमान प्रशिक्षण मॉड्यूल',
    verifiedOutcome: 'सत्यापित रोजगार परिणाम',
    outcomePendingNote: 'प्रशिक्षण के बाद नौकरी और स्वरोजगार के परिणामों को जिला अधिकारी द्वारा सत्यापित किया जाएगा।',

    // Officer Dashboard
    officerTitle: 'जिला अधिकारी कमान',
    officerSub: 'वास्तविक समय आजीविका मेट्रिक्स, कौशल मांग विश्लेषण और जोखिम हस्तक्षेप',
    totalBeneficiaries: 'कुल लाभार्थी',
    activeEnrollments: 'सक्रिय नामांकन',
    completedTrainings: 'पूर्ण प्रशिक्षण',
    openInterventions: 'खुले हस्तक्षेप',
    skillDemandTitle: 'क्षेत्रीय कौशल मांग विश्लेषण',
    atRiskTitle: 'जोखिम में लाभार्थी और चेतावनी',
  },

  mr: {
    // Nav
    appName: 'उपजीविका नेव्हिगेटर',
    appSubtitle: 'एआय करिअर आणि संधी व्यासपीठ',
    navRecs: 'शिफारसी',
    navJourney: 'माझा प्रवास',
    navProfile: 'माझे प्रोफाइल',
    navOfficer: 'अधिकारी डॅशबोर्ड',
    logIn: 'लॉग इन करा',
    getStarted: 'सुरू करा',
    logout: 'लॉग आउट',

    // Recommendations Page
    aiEngineBadge: 'एआय शिफारस इंजिन',
    heroRecsTitle: 'वैयक्तिकृत उपजीविका मार्ग',
    heroRecsSub: 'तुमचे कौशल्य आणि स्थानावर आधारित विशेष अभ्यासक्रम, प्रादेशिक प्रशिक्षण केंद्रे आणि स्थानिक रोजगार संधी.',
    updateProfileBtn: 'प्रोफाइल अद्ययावत करा',
    allRecs: 'सर्व शिफारसी',
    nsqfCourses: 'NSQF अभ्यासक्रम',
    trainingCentres: 'प्रशिक्षण केंद्रे',
    employmentOpps: 'रोजगार संधी',
    noRecsFound: 'कोणतीही शिफारस आढळली नाही',
    noRecsSub: 'अधिक शिफारसी मिळवण्यासाठी तुमचे कौशल्य किंवा स्थान अपडेट करा!',
    enrollInTraining: 'प्रशिक्षणात प्रवेश घ्या',
    viewDetails: 'तपशील पहा',
    matchScore: 'साम्य',
    whyRecommended: 'शिफारस करण्याचे कारण',
    sectorLabel: 'क्षेत्र',

    // Details Modal
    centreDetailsTitle: 'प्रशिक्षण केंद्र आणि संधी तपशील',
    centreNameLabel: 'केंद्राचे नाव',
    addressLabel: 'पत्ता आणि स्थान',
    contactLabel: 'संपर्क माहिती',
    capacityLabel: 'प्रशिक्षण क्षमता / जागा',
    facilitiesLabel: 'सुविधा आणि वैशिष्ट्ये',
    closeBtn: 'बंद करा',

    // Profile Form
    profileTitle: 'लाभार्थी प्रोफाइल',
    profileSub: 'फॉर्म भरा किंवा व्हॉइस स्पीच वापरून माहिती द्या',
    personalTab: 'वैयक्तिक',
    educationTab: 'शिक्षण आणि स्थान',
    occupationTab: 'व्यवसाय आणि उत्पन्न',
    skillsTab: 'कौशल्य आणि आकांक्षा',
    ageLabel: 'वय',
    genderLabel: 'लिंग',
    educationLevelLabel: 'शिक्षण पातळी',
    stateLabel: 'राज्य',
    districtLabel: 'जिल्हा',
    blockLabel: 'ब्लॉक / गाव',
    currentOccupationLabel: 'सध्याचा व्यवसाय',
    annualIncomeLabel: 'वार्षिक कौटुंबिक उत्पन्न',
    existingSkillsLabel: 'सध्याची कौशल्ये (स्वल्पविरामाने वेगळे करा)',
    employmentPrefLabel: 'रोजगार पसंती',
    saveProfileBtn: 'जतन करा आणि शिफारसी मिळवा',
    nextSectionBtn: 'पुढील भाग',
    backBtn: 'मागे',

    // Roadmap
    journeyTitle: 'माझा उपजीविका प्रवास',
    journeySub: 'तुमचा प्रशिक्षण प्रगती आलेख आणि रोजगार निकाल थेट पहा',
    noEnrollmentsYet: 'कोणतेही सक्रिय प्रवेश नाहीत',
    noEnrollmentsSub: 'तुमचा वैयक्तिक प्रशिक्षण प्रवास सुरू करण्यासाठी शिफारस केलेले अभ्यासक्रम पहा.',
    exploreRecsBtn: 'शिफारसी शोधा',
    attendanceLabel: 'उपस्थिती',
    visualTimeline: 'टप्प्यांची कालरेषा',
    currentModule: 'सध्याचे प्रशिक्षण मॉड्यूल',
    verifiedOutcome: 'प्रमाणित रोजगार निकाल',
    outcomePendingNote: 'प्रशिक्षणानंतरचा रोजगार निकाल जिल्हा अधिकाऱ्यांकडून सत्यापित केला जाईल.',

    // Officer Dashboard
    officerTitle: 'जिल्हा अधिकारी कमांड',
    officerSub: 'रिअल-टाइम उपजीविका आकडेवारी आणि कौशल्य मागणी विश्लेषण',
    totalBeneficiaries: 'एकूण लाभार्थी',
    activeEnrollments: 'सक्रिय प्रवेश',
    completedTrainings: 'पूर्ण झालेले प्रशिक्षण',
    openInterventions: 'सक्रिय हस्तक्षेप',
    skillDemandTitle: 'प्रादेशिक कौशल्य मागणी विश्लेषण',
    atRiskTitle: 'जोखिम असलेले लाभार्थी आणि इशारे',
  },

  bn: {
    appName: 'জীবিকা নেভিগেটর',
    appSubtitle: 'এআই ক্যারিয়ার ও সুযোগ প্ল্যাটফর্ম',
    navRecs: 'সুপারিশ',
    navJourney: 'আমার যাত্রা',
    navProfile: 'আমার প্রোফাইল',
    navOfficer: 'অফিসার ড্যাশবোর্ড',
    logIn: 'লগ ইন',
    getStarted: 'শুরু করুন',
    logout: 'লগ আউট',
    heroRecsTitle: 'ব্যক্তিগতকৃত জীবিকা পথ',
    heroRecsSub: 'আপনার দক্ষতা ও অবস্থানের ওপর ভিত্তি করে উপযুক্ত কোর্স, প্রশিক্ষণ কেন্দ্র ও কর্মসংস্থান।',
    enrollInTraining: 'প্রশিক্ষণে নাম নথিভুক্ত করুন',
    viewDetails: 'বিস্তারিত দেখুন',
    centreDetailsTitle: 'প্রশিক্ষণ কেন্দ্র ও সুযোগের বিস্তারিত',
    closeBtn: 'বন্ধ করুন',
  },

  ta: {
    appName: 'வாழ்வாதார வழிகாட்டி',
    appSubtitle: 'AI தொழில் மற்றும் வாய்ப்பு தளம்',
    navRecs: 'பரிந்துரைகள்',
    navJourney: 'என் பயணம்',
    navProfile: 'என் சுயவிவரம்',
    navOfficer: 'அதிகாரி டேஷ்போர்டு',
    logIn: 'உள்நுழைக',
    getStarted: 'தொடங்கவும்',
    logout: 'வெளியேறு',
    heroRecsTitle: 'தனிப்பயனாக்கப்பட்ட வாழ்வாதார வழிகள்',
    heroRecsSub: 'உங்கள் திறமைகள் மற்றும் இருப்பிடத்தின் அடிப்படையில் பயிற்சிகள் மற்றும் வேலைவாய்ப்புகள்.',
    enrollInTraining: 'பயிற்சியில் சேரவும்',
    viewDetails: 'விவரங்களைக் காண்க',
    centreDetailsTitle: 'பயிற்சி மையம் மற்றும் வாய்ப்பு விவரங்கள்',
    closeBtn: 'மூடுக',
  },

  te: {
    appName: 'జీవనోపాధి నావిగేటర్',
    appSubtitle: 'AI కెరీర్ మరియు అవకాశాల వేదిక',
    navRecs: 'సిఫార్సులు',
    navJourney: 'నా ప్రయాణం',
    navProfile: 'నా ప్రొఫైల్',
    navOfficer: 'అధికారి డాష్‌బోర్డ్',
    logIn: 'లాగిన్ చేయండి',
    getStarted: 'ప్రారంభించండి',
    logout: 'లాగౌట్',
    heroRecsTitle: 'వ్యక్తిగతీకరించిన జీవనోపాధి మార్గాలు',
    heroRecsSub: 'మీ నైపుణ్యాలు మరియు ప్రాంతం ఆధారంగా శిక్షణ కోర్సులు మరియు ఉపాధి అవకాశాలు.',
    enrollInTraining: 'శిక్షణలో చేరండి',
    viewDetails: 'వివరాలు చూడండి',
    centreDetailsTitle: 'శిక్షణ కేంద్రం మరియు వివరాలు',
    closeBtn: 'మూసివేయి',
  },

  gu: {
    appName: 'આજીવિકા નેવિગેટર',
    appSubtitle: 'AI કરિયર અને તકોનું પ્લેટફોર્મ',
    navRecs: 'ભલામણો',
    navJourney: 'મારી યાત્રા',
    navProfile: 'મારું પ્રોફાઇલ',
    navOfficer: 'અધિકારી ડેશબોર્ડ',
    logIn: 'લોગ ઇન કરો',
    getStarted: 'શરૂ કરો',
    logout: 'લોગ આઉટ',
    heroRecsTitle: 'વ્યક્તિગત આજીવિકા માર્ગ',
    heroRecsSub: 'તમારી કુશળતા અને સ્થાન પર આધારિત કોર્સ અને તાલીમ કેન્દ્રો.',
    enrollInTraining: 'તાલીમમાં પ્રવેશ લો',
    viewDetails: 'વિગતો જુઓ',
    centreDetailsTitle: 'તાલીમ કેન્દ્ર અને વિગતો',
    closeBtn: 'બંધ કરો',
  },

  kn: {
    appName: 'ಜೀವನೋಪಾಯ ನ್ಯಾವಿಗೇಟರ್',
    appSubtitle: 'AI ವೃತ್ತಿ ಮತ್ತು ಅವಕಾಶ ವೇದಿಕೆ',
    navRecs: 'ಶಿಫಾರಸುಗಳು',
    navJourney: 'ನನ್ನ ಪ್ರಯಾಣ',
    navProfile: 'ನನ್ನ ಪ್ರೊಫೈಲ್',
    navOfficer: 'ಅಧಿಕಾರಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
    logIn: 'ಲಾಗಿನ್ ಮಾಡಿ',
    getStarted: 'ಪ್ರಾರಂಭಿಸಿ',
    logout: 'ಲಾಗ್‌ಔಟ್',
    heroRecsTitle: 'ವೈಯಕ್ತಿಕಗೊಳಿಸಿದ ಜೀವನೋಪಾಯ ಮಾರ್ಗಗಳು',
    heroRecsSub: 'ನಿಮ್ಮ ಕೌಶಲ್ಯ ಮತ್ತು ಸ್ಥಳದ ಆಧಾರದ ಮೇಲೆ ತರಬೇತಿ ಕೋರ್ಸ್‌ಗಳು ಮತ್ತು ಉದ್ಯೋಗ ಅವಕಾಶಗಳು.',
    enrollInTraining: 'ತರಬೇತಿಗೆ ನೋಂದಾಯಿಸಿ',
    viewDetails: 'ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ',
    centreDetailsTitle: 'ತರಬೇತಿ ಕೇಂದ್ರದ ವಿವರಗಳು',
    closeBtn: 'ಮುಚ್ಚಿ',
  },

  pa: {
    appName: 'ਰੋਜ਼ੀ-ਰੋਟੀ ਨੈਵੀਗੇਟਰ',
    appSubtitle: 'AI ਕਰੀਅਰ ਅਤੇ ਅਵਸਰ ਪਲੇਟਫਾਰਮ',
    navRecs: 'ਸਿਫ਼ਾਰਸ਼ਾਂ',
    navJourney: 'ਮੇਰੀ ਯਾਤਰਾ',
    navProfile: 'ਮੇਰੀ ਪ੍ਰੋਫਾਈਲ',
    navOfficer: 'ਅਧਿਕਾਰੀ ਡੈਸ਼ਬੋਰਡ',
    logIn: 'ਲੌਗ ਇਨ ਕਰੋ',
    getStarted: 'ਸ਼ੁਰੂ ਕਰੋ',
    logout: 'ਲੌਗ ਆਉਟ',
    heroRecsTitle: 'ਨਿੱਜੀ ਰੋਜ਼ੀ-ਰੋਟੀ ਦੇ ਰਸਤੇ',
    heroRecsSub: 'ਤੁਹਾਡੇ ਹੁਨਰ ਅਤੇ ਸਥਾਨ ਦੇ ਆਧਾਰ \'ਤੇ ਸਿਖਲਾਈ ਕੋਰਸ ਅਤੇ ਰੋਜ਼ਗਾਰ ਦੇ ਮੌਕੇ।',
    enrollInTraining: 'ਸਿਖਲਾਈ ਵਿੱਚ ਦਾਖਲਾ ਲਵੋ',
    viewDetails: 'ਵੇਰਵੇ ਦੇਖੋ',
    centreDetailsTitle: 'ਸਿਖਲਾਈ ਕੇਂਦਰ ਅਤੇ ਵੇਰਵੇ',
    closeBtn: 'ਬੰਦ ਕਰੋ',
  },

  or: {
    appName: 'ଜୀବିକା ନାଭିଗେଟର',
    appSubtitle: 'AI କ୍ୟାରିଅର୍ ଏବଂ ସୁଯୋଗ ପ୍ଲାଟଫର୍ମ',
    navRecs: 'ସୁପାରିଶ୍',
    navJourney: 'ମୋର ଯାତ୍ରା',
    navProfile: 'ମୋର ପ୍ରୋଫାଇଲ୍',
    navOfficer: 'ଅଧିକାରୀ ଡ୍ୟାସବୋର୍ଡ',
    logIn: 'ଲଗ୍ ଇନ୍ କରନ୍ତୁ',
    getStarted: 'ଆରମ୍ଭ କରନ୍ତୁ',
    logout: 'ଲଗ୍ ଆଉଟ୍',
    heroRecsTitle: 'ବ୍ୟକ୍ତିଗତ ଜୀବିକା ପଥ',
    heroRecsSub: 'ଆପଣଙ୍କ କୌଶଳ ଏବଂ ସ୍ଥାନ ଉପରେ ଆଧାରିତ ତାଲିମ ପାଠ୍ୟକ୍ରମ ଏବଂ ନିଯୁକ୍ତି ସୁଯୋଗ।',
    enrollInTraining: 'ତାଲିମରେ ନାମ ଲେଖାନ୍ତୁ',
    viewDetails: 'ବିବରଣୀ ଦେଖନ୍ତୁ',
    centreDetailsTitle: 'ତାଲିମ କେନ୍ଦ୍ର ବିବରଣୀ',
    closeBtn: 'ବନ୍ଦ କରନ୍ତୁ',
  },
};

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
  const [language, setLanguageState] = useState(() => {
    return localStorage.getItem('app_language') || 'en';
  });

  const setLanguage = (langCode) => {
    setLanguageState(langCode);
    localStorage.setItem('app_language', langCode);
  };

  const t = (key) => {
    const langDict = TRANSLATIONS[language] || TRANSLATIONS.en;
    return langDict[key] || TRANSLATIONS.en[key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, LANGUAGES }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
