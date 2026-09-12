import { useState, useEffect, useCallback } from 'react';

export type LanguageCode = 'en' | 'hi' | 'mr' | 'ta';

export interface LanguageOption {
  code: LanguageCode;
  label: string;
  nativeLabel: string;
  speechLocale: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'en', label: 'English', nativeLabel: 'English', speechLocale: 'en-IN' },
  { code: 'hi', label: 'Hindi', nativeLabel: 'हिंदी', speechLocale: 'hi-IN' },
  { code: 'mr', label: 'Marathi', nativeLabel: 'मराठी', speechLocale: 'mr-IN' },
  { code: 'ta', label: 'Tamil', nativeLabel: 'தமிழ்', speechLocale: 'ta-IN' },
];

export const TRANSLATIONS: Record<LanguageCode, Record<string, string>> = {
  en: {
    appTitle: 'VARUNA Maritime Intelligence',
    safe: 'SAFE TO SAIL',
    caution: 'GO WITH CAUTION',
    unsafe: 'DO NOT GO (UNSAFE)',
    unknown: 'DATA INCOMPLETE (CHECK)',
    safeSubtext: 'Weather and marine parameters are within safe thresholds.',
    cautionSubtext: 'Marginal swell or wave conditions. Stay within shelter limits.',
    unsafeSubtext: 'Severe marine conditions or active ban. Total departure suspension.',
    unknownSubtext: 'Critical sensor telemetry is incomplete. Do not depart without official clearance.',
    waveHeight: 'Wave Height',
    windSpeed: 'Wind Speed',
    nearestZone: 'Nearest Zone',
    weatherAlert: 'Weather Status',
    listenAudio: 'Listen (Audio)',
    listening: 'Playing...',
    stopAudio: 'Stop Audio',
    fishermanMode: 'Fisherman View',
    commandMode: 'Operations View',
    sunlightMode: 'Sunlight Mode',
    darkMode: 'Dark Mode',
    switchView: 'Switch Mode',
    inspectTrace: 'Inspect Rules & Evidence →',
    inspectDetails: 'Inspect full audit trace and statutory citations',
    meters: 'm',
    kmh: 'km/h',
    knots: 'kts',
    nm: 'NM',
    noAlerts: 'No alerts active',
    speechStarted: 'Voice advisory playback started.',
    speechEnded: 'Voice advisory playback completed.',
  },
  hi: {
    appTitle: 'वरुण समुद्री सूचना प्रणाली',
    safe: 'समुद्र में जाना सुरक्षित है',
    caution: 'सावधानी से जाएं',
    unsafe: 'समुद्र में न जाएं (खतरा)',
    unknown: 'डेटा अधूरा (पुष्टि करें)',
    safeSubtext: 'मौसम और समुद्र की स्थिति पूरी तरह सुरक्षित सीमा में है।',
    cautionSubtext: 'लहरें मध्यम हैं। तट के पास रहें और सावधानी बरतें।',
    unsafeSubtext: 'भीषण तूफान या प्रतिबंध। किसी भी नाव को जाने की अनुमति नहीं है।',
    unknownSubtext: 'मौसम डेटा अधूरा है। आधिकारिक पुष्टि के बिना प्रस्थान न करें।',
    waveHeight: 'लहरों की ऊंचाई',
    windSpeed: 'हवा की गति',
    nearestZone: 'निकटतम मछली क्षेत्र',
    weatherAlert: 'मौसम चेतावनी',
    listenAudio: 'सलाह सुनें (आवाज)',
    listening: 'चल रहा है...',
    stopAudio: 'आवाज रोकें',
    fishermanMode: 'मछुआरा दृश्य',
    commandMode: 'कमांड दृश्य',
    sunlightMode: 'धूप मोड',
    darkMode: 'डार्क मोड',
    switchView: 'मोड बदलें',
    inspectTrace: 'नियम और प्रमाण जांचें →',
    inspectDetails: 'पूर्ण ऑडिट और कानूनी संदर्भ देखें',
    meters: 'मी.',
    kmh: 'किमी/घं',
    knots: 'नॉट्स',
    nm: 'समुद्री मील',
    noAlerts: 'कोई चेतावनी नहीं',
    speechStarted: 'वॉइस एडवाइजरी शुरू हुई।',
    speechEnded: 'वॉइस एडवाइजरी समाप्त हुई।',
  },
  mr: {
    appTitle: 'वरुण सागरी माहिती प्रणाली',
    safe: 'समुद्रात जाणे सुरक्षित आहे',
    caution: 'सावधगिरी बाळगा',
    unsafe: 'समुद्रात जाऊ नका (धोका)',
    unknown: 'माहिती अपुरी (तपासा)',
    safeSubtext: 'हवामान आणि समुद्राच्या लाटा सुरक्षित मर्यादेत आहेत.',
    cautionSubtext: 'लाटांचा वेग मध्यम आहे. किनाऱ्याजवळ राहा आणि सतर्क राहा.',
    unsafeSubtext: 'तीव्र वादळ किंवा बंदी. समुद्रात जाण्यास पूर्ण मनाई आहे.',
    unknownSubtext: 'हवामानाची माहिती अपुरी आहे. अधिकृत खात्रीशिवाय बाहेर पडू नका.',
    waveHeight: 'लाटांची उंची',
    windSpeed: 'वाऱ्याचा वेग',
    nearestZone: 'जवळचे मासेमारी क्षेत्र',
    weatherAlert: 'हवामान स्थिती',
    listenAudio: 'माहिती ऐका (आवाज)',
    listening: 'चालू आहे...',
    stopAudio: 'आवाज थांबवा',
    fishermanMode: 'कोळी बांधव दृश्य',
    commandMode: 'कमांड दृश्य',
    sunlightMode: 'उजेड मोड',
    darkMode: 'गडद मोड',
    switchView: 'मोड बदला',
    inspectTrace: 'नियम आणि पुरावे तपासा →',
    inspectDetails: 'सविस्तर पडताळणी आणि कायदेशीर संदर्भ पाहा',
    meters: 'मी.',
    kmh: 'किमी/तास',
    knots: 'नॉट्स',
    nm: 'सागरी मैल',
    noAlerts: 'कोणतीही धोक्याची सूचना नाही',
    speechStarted: 'आवाज सल्ला सुरू झाला.',
    speechEnded: 'आवाज सल्ला पूर्ण झाला.',
  },
  ta: {
    appTitle: 'வருணா கடல்சார் தகவல் அமைப்பு',
    safe: 'கடலுக்குச் செல்ல பாதுகாப்பானது',
    caution: 'எச்சரிக்கையுடன் செல்லவும்',
    unsafe: 'கடலுக்குச் செல்ல வேண்டாம் (ஆபத்து)',
    unknown: 'தகவல் முழுமையடையவில்லை (சரிபார்க்கவும்)',
    safeSubtext: 'வானிலை மற்றும் கடல் அலைகள் பாதுகாப்பான வரம்பில் உள்ளன.',
    cautionSubtext: 'அலைகள் சற்று அதிகம். கரையோரமாக இருங்கள்.',
    unsafeSubtext: 'கடும் புயல் அல்லது தடை. கடலுக்குச் செல்வது முழுமையாக நிறுத்தப்பட்டுள்ளது.',
    unknownSubtext: 'முழுமையான தகவல் கிடைக்கவில்லை. துறைமுக அனுமதி இல்லாமல் செல்ல வேண்டாம்.',
    waveHeight: 'அலை உயரம்',
    windSpeed: 'காற்றின் வேகம்',
    nearestZone: 'அருகிலுள்ள மீன்பிடி பகுதி',
    weatherAlert: 'வானிலை எச்சரிக்கை',
    listenAudio: 'ஆடியோ கேளுங்கள்',
    listening: 'இயங்குகிறது...',
    stopAudio: 'ஆடியோ நிறுத்து',
    fishermanMode: 'மீனவர் பார்வை',
    commandMode: 'செயல்பாட்டு பார்வை',
    sunlightMode: 'சூரிய ஒளி பயன்முறை',
    darkMode: 'இருண்ட பயன்முறை',
    switchView: 'பார்வை மாற்று',
    inspectTrace: 'விதிகளை சரிபார்க்கவும் →',
    inspectDetails: 'முழு விவரங்கள் மற்றும் சட்ட குறிப்புகளைப் பார்க்கவும்',
    meters: 'மீ.',
    kmh: 'கி.மீ/மணி',
    knots: 'நாட்ஸ்',
    nm: 'கடல் மைல்',
    noAlerts: 'எச்சரிக்கை எதுவும் இல்லை',
    speechStarted: 'ஆடியோ வழிகாட்டுதல் தொடங்கியது.',
    speechEnded: 'ஆடியோ வழிகாட்டுதல் முடிந்தது.',
  },
};

const STORAGE_KEY = 'varuna_preferred_lang';

export function useLocalization() {
  const [currentLang, setCurrentLang] = useState<LanguageCode>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY) as LanguageCode;
      if (saved && ['en', 'hi', 'mr', 'ta'].includes(saved)) {
        return saved;
      }
    } catch {}
    return 'en';
  });

  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [liveAnnouncement, setLiveAnnouncement] = useState<string>('');

  const setLanguage = (lang: LanguageCode) => {
    setCurrentLang(lang);
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {}
  };

  const t = useCallback(
    (key: string): string => {
      const langDict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
      return langDict[key] || TRANSLATIONS.en[key] || key;
    },
    [currentLang]
  );

  // Deterministic Text-to-Speech (TTS)
  const speakDeterministicText = useCallback(
    (textToSpeak: string) => {
      if (!('speechSynthesis' in window)) {
        console.warn('Speech synthesis is not supported by this browser.');
        return;
      }

      window.speechSynthesis.cancel();

      if (isSpeaking) {
        setIsSpeaking(false);
        setLiveAnnouncement(t('speechEnded'));
        return;
      }

      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      const currentOpt = SUPPORTED_LANGUAGES.find((l) => l.code === currentLang);
      utterance.lang = currentOpt?.speechLocale || 'en-IN';
      utterance.rate = 0.95; // Slightly slower for crisp clarity on marine radios / mobile

      utterance.onstart = () => {
        setIsSpeaking(true);
        setLiveAnnouncement(t('speechStarted'));
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        setLiveAnnouncement(t('speechEnded'));
      };

      utterance.onerror = () => {
        setIsSpeaking(false);
        setLiveAnnouncement(t('speechEnded'));
      };

      window.speechSynthesis.speak(utterance);
    },
    [currentLang, isSpeaking, t]
  );

  const stopSpeaking = useCallback(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
    setLiveAnnouncement(t('speechEnded'));
  }, [t]);

  // Clean up speech on unmount
  useEffect(() => {
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return {
    currentLang,
    setLanguage,
    t,
    supportedLanguages: SUPPORTED_LANGUAGES,
    isSpeaking,
    speakDeterministicText,
    stopSpeaking,
    liveAnnouncement,
  };
}
