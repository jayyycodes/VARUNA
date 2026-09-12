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
    // App-level titles
    appTitle: 'VARUNA Maritime Intelligence',
    pageMapTitle: 'Marine Intelligence Command',
    pageRoutingTitle: 'Route Optimization & Safe Passage',
    pageChatTitle: 'VARUNA Copilot — Marine AI Intelligence',
    pageReasoningTitle: 'Agentic Reasoning',
    pageAlertsTitle: 'Active Marine Alerts',
    pageFleetTitle: 'Fleet Operations',
    pageTrendsTitle: 'Fishery Trends & Anomalies (SIH Query #7)',

    // Verdict states
    safe: 'SAFE TO SAIL',
    caution: 'GO WITH CAUTION',
    unsafe: 'DO NOT GO (UNSAFE)',
    unknown: 'DATA INCOMPLETE (CHECK)',
    safeSubtext: 'Weather and marine parameters are within safe thresholds.',
    cautionSubtext: 'Marginal swell or wave conditions. Stay within shelter limits.',
    unsafeSubtext: 'Severe marine conditions or active ban. Total departure suspension.',
    unknownSubtext: 'Critical sensor telemetry is incomplete. Do not depart without official clearance.',

    // Metric labels
    waveHeight: 'Wave Height',
    windSpeed: 'Wind Speed',
    nearestZone: 'Nearest Zone',
    weatherAlert: 'Weather Status',

    // Audio / TTS
    listenAudio: 'Listen (Audio)',
    listening: 'Playing...',
    stopAudio: 'Stop Audio',
    speechStarted: 'Voice advisory playback started.',
    speechEnded: 'Voice advisory playback completed.',

    // Mode & Theme
    fishermanMode: 'Fisherman View',
    commandMode: 'Operations View',
    sunlightMode: 'Sunlight Mode',
    darkMode: 'Dark Mode',
    switchView: 'Switch Mode',

    // Evidence & Inspection
    inspectTrace: 'Inspect Rules & Evidence →',
    inspectDetails: 'Inspect full audit trace and statutory citations',

    // Units
    meters: 'm',
    kmh: 'km/h',
    knots: 'kts',
    nm: 'NM',

    // Sidebar
    scenarios: 'Scenarios',
    scenariosSubtitle: 'Grounding & Test Suite',
    searchPlaceholder: 'Search coastal scenario...',
    recentQueries: 'RECENT QUERIES',
    total: 'Total',
    safeStat: 'Safe',
    cautionStat: 'Caution',
    unsafeStat: 'Unsafe',
    unknownStat: 'Unknown',
    coastal: 'COASTAL',

    // Topbar
    askCopilot: 'Ask Copilot',
    askVarunaAI: 'Ask VARUNA AI',
    live: 'LIVE',
    locationContext: 'Arabian Sea & Bay of Bengal • Today',

    // Loading / Error / Idle
    analyzingDomains: 'ANALYZING DOMAINS',
    assessingRisk: 'Assessing Maritime Risk...',
    loadingMessage: 'Checking weather, marine conditions, and boundaries...',
    systemError: 'SYSTEM ERROR',
    unableToAssess: 'Unable to Complete Assessment',
    retryAssessment: 'Retry Assessment',
    systemReady: 'System Ready',
    coastalIntelligence: 'Coastal Marine Intelligence',
    idleHint: 'Select a coastal scenario or enter coordinates to evaluate weather, wave swell, and regulatory compliance.',

    // VerdictCard - Command Mode
    confidence: 'CONFIDENCE',
    directive: 'DIRECTIVE',
    keyFactors: 'KEY FACTORS (TAP TO INSPECT)',

    // Degradation
    degradedMode: 'Degraded Mode',

    // Evidence Panel
    rulesAndChecks: 'Rules & Checks',
    freshness: 'Freshness',
    citations: 'Citations',
    deterministicEngine: 'DETERMINISTIC EVALUATION ENGINE',
    noRuleTraces: 'No active rule threshold breaches recorded for this query.',
    noRuleTracesIndeterminate: 'No rule traces could be executed due to missing critical sensors.',
    emptyEvidence: 'Submit a marine query or select a scenario to inspect deterministic rule traces, data freshness, and legal citations.',
    passed: 'PASSED',
    breach: 'BREACH',
    measured: 'Measured',
    op: 'Op',
    threshold: 'Threshold',
    rule: 'Rule',
    version: 'Ver',
    missingInputs: 'MISSING INPUTS',
    fallback: 'Fallback',

    // Freshness Panel
    telemetrySources: 'TELEMETRY SOURCES & SENSOR TIMELINESS',
    domain: 'Domain',
    observed: 'Observed',
    retrieved: 'Retrieved',
    validTo: 'Valid to',

    // Citations Panel
    legalCitations: 'AUTHORITATIVE LEGAL & ADVISORY CITATIONS',
    notVerified: 'NOT VERIFIED',
    ragGroundingGuard: 'RAG Grounding Guard',
    unverifiedCopy: 'We could not verify this from the available official sources.',
    unverifiedExplain: 'VARUNA strictly refuses to synthesize legal permissions without direct statutory citations.',
    noCitations: 'No statutory or regulatory document citations attached to this operational query.',
    published: 'Published',
    sourceDoc: 'Source Doc',
    original: 'ORIGINAL',

    // Fisherman tile statuses
    highSwell: 'High Swell',
    safeHeight: 'Safe Height',
    squallWarning: 'Squall Warning',
    normalBreeze: 'Normal Breeze',
    productiveSector: 'Productive Sector',
    action: 'ACTION',
    verdictStatus: 'STATUS',
    noAlerts: 'No alerts active',
  },
  hi: {
    appTitle: 'वरुण समुद्री सूचना प्रणाली',
    pageMapTitle: 'समुद्री सूचना कमांड',
    pageRoutingTitle: 'मार्ग अनुकूलन एवं सुरक्षित मार्ग',
    pageChatTitle: 'वरुण कोपायलट — समुद्री AI सूचना',
    pageReasoningTitle: 'एजेंटिक रीज़निंग',
    pageAlertsTitle: 'सक्रिय समुद्री चेतावनियां',
    pageFleetTitle: 'बेड़ा संचालन',
    pageTrendsTitle: 'मत्स्य प्रवृत्तियां और विसंगतियां (SIH प्रश्न #7)',

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
    speechStarted: 'वॉइस एडवाइजरी शुरू हुई।',
    speechEnded: 'वॉइस एडवाइजरी समाप्त हुई।',

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

    scenarios: 'परिदृश्य',
    scenariosSubtitle: 'ग्राउंडिंग एवं परीक्षण',
    searchPlaceholder: 'तटीय परिदृश्य खोजें...',
    recentQueries: 'हाल की खोजें',
    total: 'कुल',
    safeStat: 'सुरक्षित',
    cautionStat: 'सावधानी',
    unsafeStat: 'असुरक्षित',
    unknownStat: 'अज्ञात',
    coastal: 'तटीय',

    askCopilot: 'कोपायलट पूछें',
    askVarunaAI: 'वरुण AI से पूछें',
    live: 'लाइव',
    locationContext: 'अरब सागर और बंगाल की खाड़ी • आज',

    analyzingDomains: 'डोमेन का विश्लेषण',
    assessingRisk: 'समुद्री जोखिम मूल्यांकन...',
    loadingMessage: 'मौसम, समुद्री स्थितियों और सीमाओं की जांच...',
    systemError: 'सिस्टम त्रुटि',
    unableToAssess: 'मूल्यांकन पूरा नहीं हो सका',
    retryAssessment: 'पुनः प्रयास करें',
    systemReady: 'सिस्टम तैयार',
    coastalIntelligence: 'तटीय समुद्री सूचना',
    idleHint: 'मौसम, लहर और विनियामक अनुपालन का मूल्यांकन करने के लिए एक तटीय परिदृश्य चुनें।',

    confidence: 'विश्वसनीयता',
    directive: 'निर्देश',
    keyFactors: 'मुख्य कारण (निरीक्षण के लिए टैप करें)',

    degradedMode: 'अधोगति मोड',

    rulesAndChecks: 'नियम और जांच',
    freshness: 'ताज़गी',
    citations: 'उद्धरण',
    deterministicEngine: 'निर्धारणात्मक मूल्यांकन',
    noRuleTraces: 'इस प्रश्न के लिए कोई नियम उल्लंघन दर्ज नहीं।',
    noRuleTracesIndeterminate: 'महत्वपूर्ण सेंसर गायब होने के कारण नियम ट्रेस निष्पादित नहीं हुए।',
    emptyEvidence: 'नियम ट्रेस और उद्धरण देखने के लिए कोई परिदृश्य चुनें।',
    passed: 'पास',
    breach: 'उल्लंघन',
    measured: 'मापा गया',
    op: 'ऑपरेटर',
    threshold: 'सीमा',
    rule: 'नियम',
    version: 'संस्करण',
    missingInputs: 'लापता इनपुट',
    fallback: 'फ़ॉलबैक',

    telemetrySources: 'टेलीमेट्री स्रोत और सेंसर समयबद्धता',
    domain: 'डोमेन',
    observed: 'अवलोकित',
    retrieved: 'प्राप्त',
    validTo: 'मान्य तक',

    legalCitations: 'आधिकारिक कानूनी और सलाहकार उद्धरण',
    notVerified: 'सत्यापित नहीं',
    ragGroundingGuard: 'RAG ग्राउंडिंग गार्ड',
    unverifiedCopy: 'हम उपलब्ध आधिकारिक स्रोतों से इसकी पुष्टि नहीं कर सके।',
    unverifiedExplain: 'वरुण बिना प्रत्यक्ष वैधानिक उद्धरण के कानूनी अनुमतियां संश्लेषित करने से इनकार करता है।',
    noCitations: 'इस प्रश्न से कोई वैधानिक या विनियामक उद्धरण नहीं जुड़ा है।',
    published: 'प्रकाशित',
    sourceDoc: 'स्रोत दस्तावेज़',
    original: 'मूल',

    highSwell: 'उच्च लहर',
    safeHeight: 'सुरक्षित ऊंचाई',
    squallWarning: 'स्क्वॉल चेतावनी',
    normalBreeze: 'सामान्य हवा',
    productiveSector: 'उत्पादक क्षेत्र',
    action: 'कार्रवाई',
    verdictStatus: 'स्थिति',
    noAlerts: 'कोई चेतावनी नहीं',
  },
  mr: {
    appTitle: 'वरुण सागरी माहिती प्रणाली',
    pageMapTitle: 'सागरी माहिती कमांड',
    pageRoutingTitle: 'मार्ग अनुकूलन आणि सुरक्षित मार्ग',
    pageChatTitle: 'वरुण कोपायलट — सागरी AI माहिती',
    pageReasoningTitle: 'एजेंटिक रिझनिंग',
    pageAlertsTitle: 'सक्रिय सागरी सूचना',
    pageFleetTitle: 'ताफा व्यवस्थापन',
    pageTrendsTitle: 'मत्स्य ट्रेंड आणि विसंगती (SIH प्रश्न #7)',

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
    speechStarted: 'आवाज सल्ला सुरू झाला.',
    speechEnded: 'आवाज सल्ला पूर्ण झाला.',

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

    scenarios: 'परिस्थिती',
    scenariosSubtitle: 'ग्राउंडिंग आणि चाचणी',
    searchPlaceholder: 'किनारपट्टी परिस्थिती शोधा...',
    recentQueries: 'अलीकडील शोध',
    total: 'एकूण',
    safeStat: 'सुरक्षित',
    cautionStat: 'सावध',
    unsafeStat: 'असुरक्षित',
    unknownStat: 'अज्ञात',
    coastal: 'किनारपट्टी',

    askCopilot: 'कोपायलट विचारा',
    askVarunaAI: 'वरुण AI ला विचारा',
    live: 'लाइव्ह',
    locationContext: 'अरबी समुद्र आणि बंगालचा उपसागर • आज',

    analyzingDomains: 'डोमेन विश्लेषण',
    assessingRisk: 'सागरी जोखीम मूल्यांकन...',
    loadingMessage: 'हवामान, सागरी स्थिती आणि सीमा तपासत आहे...',
    systemError: 'सिस्टम त्रुटी',
    unableToAssess: 'मूल्यांकन पूर्ण होऊ शकले नाही',
    retryAssessment: 'पुन्हा प्रयत्न करा',
    systemReady: 'सिस्टम तयार',
    coastalIntelligence: 'किनारपट्टी सागरी माहिती',
    idleHint: 'हवामान, लाट आणि नियमांचे मूल्यांकन करण्यासाठी किनारपट्टी परिस्थिती निवडा.',

    confidence: 'विश्वसनीयता',
    directive: 'निर्देश',
    keyFactors: 'मुख्य कारणे (तपासण्यासाठी टॅप करा)',

    degradedMode: 'अधोगती मोड',

    rulesAndChecks: 'नियम आणि तपासणी',
    freshness: 'ताजेपणा',
    citations: 'उद्धरण',
    deterministicEngine: 'निश्चित मूल्यांकन इंजिन',
    noRuleTraces: 'या प्रश्नासाठी कोणतेही नियम उल्लंघन नोंदलेले नाही.',
    noRuleTracesIndeterminate: 'गंभीर सेंसर गहाळ असल्यामुळे नियम ट्रेस अंमलात आणता आले नाही.',
    emptyEvidence: 'नियम ट्रेस आणि उद्धरण पाहण्यासाठी परिस्थिती निवडा.',
    passed: 'उत्तीर्ण',
    breach: 'उल्लंघन',
    measured: 'मोजलेले',
    op: 'ऑपरेटर',
    threshold: 'मर्यादा',
    rule: 'नियम',
    version: 'आवृत्ती',
    missingInputs: 'गहाळ इनपुट्स',
    fallback: 'फॉलबॅक',

    telemetrySources: 'टेलिमेट्री स्रोत आणि सेंसर वेळबद्धता',
    domain: 'डोमेन',
    observed: 'अवलोकन',
    retrieved: 'प्राप्त',
    validTo: 'वैध',

    legalCitations: 'अधिकृत कायदेशीर आणि सल्लागार उद्धरण',
    notVerified: 'सत्यापित नाही',
    ragGroundingGuard: 'RAG ग्राउंडिंग गार्ड',
    unverifiedCopy: 'उपलब्ध अधिकृत स्रोतांमधून याची पडताळणी होऊ शकली नाही.',
    unverifiedExplain: 'वरुण प्रत्यक्ष वैधानिक उद्धरणाशिवाय कायदेशीर परवानग्या तयार करण्यास नकार देतो.',
    noCitations: 'या प्रश्नाशी कोणतेही वैधानिक उद्धरण जोडलेले नाही.',
    published: 'प्रकाशित',
    sourceDoc: 'स्रोत दस्तऐवज',
    original: 'मूळ',

    highSwell: 'उच्च लाट',
    safeHeight: 'सुरक्षित उंची',
    squallWarning: 'स्क्वॉल चेतावणी',
    normalBreeze: 'सामान्य वारे',
    productiveSector: 'उत्पादक क्षेत्र',
    action: 'कार्यवाही',
    verdictStatus: 'स्थिती',
    noAlerts: 'कोणतीही धोक्याची सूचना नाही',
  },
  ta: {
    appTitle: 'வருணா கடல்சார் தகவல் அமைப்பு',
    pageMapTitle: 'கடல்சார் தகவல் கட்டுப்பாடு',
    pageRoutingTitle: 'பாதை மேம்படுத்தல் & பாதுகாப்பான பயணம்',
    pageChatTitle: 'வருணா கோபைலட் — கடல்சார் AI தகவல்',
    pageReasoningTitle: 'ஏஜென்டிக் ரீசனிங்',
    pageAlertsTitle: 'செயலில் உள்ள கடல் எச்சரிக்கைகள்',
    pageFleetTitle: 'கப்பற்படை செயல்பாடுகள்',
    pageTrendsTitle: 'மீன்பிடி போக்குகள் & முரண்பாடுகள் (SIH கேள்வி #7)',

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
    speechStarted: 'ஆடியோ வழிகாட்டுதல் தொடங்கியது.',
    speechEnded: 'ஆடியோ வழிகாட்டுதல் முடிந்தது.',

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

    scenarios: 'காட்சிகள்',
    scenariosSubtitle: 'அடிப்படை & சோதனை',
    searchPlaceholder: 'கடலோர காட்சியைத் தேடு...',
    recentQueries: 'சமீபத்திய தேடல்கள்',
    total: 'மொத்தம்',
    safeStat: 'பாதுகாப்பு',
    cautionStat: 'எச்சரிக்கை',
    unsafeStat: 'ஆபத்து',
    unknownStat: 'தெரியாத',
    coastal: 'கடலோரம்',

    askCopilot: 'கோபைலட் கேளுங்கள்',
    askVarunaAI: 'வருணா AI கேளுங்கள்',
    live: 'நேரடி',
    locationContext: 'அரபிக் கடல் & வங்காள விரிகுடா • இன்று',

    analyzingDomains: 'டொமைன் பகுப்பாய்வு',
    assessingRisk: 'கடல்சார் ஆபத்து மதிப்பீடு...',
    loadingMessage: 'வானிலை, கடல் நிலைகள் மற்றும் எல்லைகளை சோதிக்கிறது...',
    systemError: 'அமைப்பு பிழை',
    unableToAssess: 'மதிப்பீடு நிறைவு செய்ய இயலவில்லை',
    retryAssessment: 'மீண்டும் முயற்சிக்கவும்',
    systemReady: 'அமைப்பு தயார்',
    coastalIntelligence: 'கடலோர கடல்சார் தகவல்',
    idleHint: 'வானிலை, அலை மற்றும் விதி இணக்கத்தை மதிப்பிட ஒரு காட்சியைத் தேர்வு செய்யுங்கள்.',

    confidence: 'நம்பகத்தன்மை',
    directive: 'உத்தரவு',
    keyFactors: 'முக்கிய காரணிகள் (ஆய்வு செய்ய தட்டவும்)',

    degradedMode: 'தரமிறக்கம் முறை',

    rulesAndChecks: 'விதிகள் & சோதனைகள்',
    freshness: 'புத்தம்',
    citations: 'மேற்கோள்கள்',
    deterministicEngine: 'தீர்மானகரமான மதிப்பீட்டு இயந்திரம்',
    noRuleTraces: 'இந்த வினவலுக்கு எந்த விதி மீறலும் பதிவாகவில்லை.',
    noRuleTracesIndeterminate: 'முக்கிய உணர்விகள் இல்லாததால் விதி ட்ரேஸ்கள் செயல்படுத்தப்படவில்லை.',
    emptyEvidence: 'விதி ட்ரேஸ்கள் மற்றும் மேற்கோள்களைப் பார்க்க ஒரு காட்சியைத் தேர்வு செய்யுங்கள்.',
    passed: 'தேர்ச்சி',
    breach: 'மீறல்',
    measured: 'அளவிடப்பட்டது',
    op: 'ஆப்.',
    threshold: 'வரம்பு',
    rule: 'விதி',
    version: 'பதிப்பு',
    missingInputs: 'காணாத உள்ளீடுகள்',
    fallback: 'மாற்று',

    telemetrySources: 'டெலிமெட்ரி மூலங்கள் & உணர்வி நேரம்',
    domain: 'டொமைன்',
    observed: 'கவனிக்கப்பட்டது',
    retrieved: 'பெறப்பட்டது',
    validTo: 'செல்லுபடி',

    legalCitations: 'அங்கீகார சட்ட & ஆலோசனை மேற்கோள்கள்',
    notVerified: 'சரிபார்க்கப்படவில்லை',
    ragGroundingGuard: 'RAG அடிப்படை காவலர்',
    unverifiedCopy: 'கிடைக்கக்கூடிய அதிகாரப்பூர்வ ஆதாரங்களிலிருந்து இதை சரிபார்க்க முடியவில்லை.',
    unverifiedExplain: 'வருணா நேரடி சட்ட மேற்கோள்கள் இல்லாமல் சட்ட அனுமதிகளை உருவாக்க மறுக்கிறது.',
    noCitations: 'இந்த வினவலுடன் எந்த சட்ட மேற்கோளும் இணைக்கப்படவில்லை.',
    published: 'வெளியிடப்பட்டது',
    sourceDoc: 'மூல ஆவணம்',
    original: 'அசல்',

    highSwell: 'உயர் அலை',
    safeHeight: 'பாதுகாப்பான உயரம்',
    squallWarning: 'புயல் எச்சரிக்கை',
    normalBreeze: 'சாதாரண காற்று',
    productiveSector: 'உற்பத்தி பகுதி',
    action: 'நடவடிக்கை',
    verdictStatus: 'நிலை',
    noAlerts: 'எச்சரிக்கை எதுவும் இல்லை',
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
