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
    pageRoutingTitle: 'Route Optimization',
    pageChatTitle: 'VARUNA AI',
    pageReasoningTitle: 'Agentic Reasoning',
    pageAlertsTitle: 'Active Marine Alerts',
    pageFleetTitle: 'Fleet Operations',
    pageTrendsTitle: 'Fishery Trends & Anomalies',

    // Navigation
    navMap: 'Map',
    navAlerts: 'Alerts',
    navAssistant: 'Assistant',
    navTrends: 'Trends',
    navMore: 'More',
    navOverview: 'Dashboard',
    navFleet: 'Fleet Ops',
    navRouting: 'Passage Route',
    navReasoning: 'Rule Engine',
    closeMenu: 'Close Menu',


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

    // Dashboard
    marineAdvisoryCards: 'Marine Advisory Cards',
    viewMapView: 'View Map View ↗',
    oceanTelemetry: 'OCEAN TELEMETRY',
    sensorsOn: 'Sensors Active',
    routeOptimize: 'Route Optimize',
    rulesEngine: 'Rules Engine',
    fleetOps: 'Fleet Ops',
    fisheryTrends: 'Fishery Trends',
    activeAlerts: 'Active Alerts',
    recentScenariosTitle: 'Recent Coastal Scenarios & Queries',
    tapToEvaluate: 'Tap any row to evaluate immediate marine safety',
    zoneVessel: 'Zone / Vessel',
    timestamp: 'Timestamp',
    safetyVerdict: 'Safety Verdict',
    coordinates: 'Coordinates',
    statistic: 'Statistic',
    integrity: 'Integrity',
    passedChecks: 'Passed',
    violations: 'Violations',

    // Alerts
    coastalHazardBroadcast: 'COASTAL HAZARD BROADCAST',
    activeAlertsTitle: 'Active Marine Alerts & Restrictions',
    activeAlertsSubtitle: 'Live emergency notices, INCOIS high wave bulletins, IMD cyclone warnings, and MPA boundary geofences.',
    authority: 'Authority',
    validity: 'Validity',
    evaluateOnMap: 'Evaluate Impact on Map →',

    // Fleet Ops
    fleetMonitorBadge: 'FLEET TELEMETRY & AIS MONITOR',
    fleetTitle: 'Coastal Fleet Operations',
    fleetSubtitle: 'Live positioning, geofence compliance, safety advisories, and harbor moorings.',
    activeCraft: 'ACTIVE CRAFT',
    inPfzZones: 'IN PFZ ZONES',
    weatherClear: 'WEATHER CLEAR',
    vesselIdName: 'Vessel ID / Name',
    vesselType: 'Type',
    homePort: 'Home Port',
    vesselCoords: 'Coordinates',
    operatingStatus: 'Operating Status',
    safetyState: 'Safety State',
    aisRelay: 'AIS Relay',

    // Historical Trends
    sihQuery7: 'SIH NATIONAL EVALUATION QUERY #7',
    trendsTitle: 'Coastal Fishery Productivity & Anomaly Analysis',
    trendsSubtitle: 'Multi-agent historical analysis explaining coastal fish decline via satellite SST anomalies, chlorophyll cycles, and monsoon trawl bans.',
    environmentalDrivers: 'PRIMARY ENVIRONMENTAL DRIVERS IDENTIFIED',
    sstTab: 'Sea Surface Temperature (SST)',
    chlTab: 'Chlorophyll-a Biomass',
    annualDecline: 'Annual Yield Decline',
    statutoryBasis: 'Statutory Basis & Legal Gazette Reference',

    // Route Optimization
    routeCorridorBadge: 'SAFE PASSAGE CORRIDOR',
    routeTitle: 'Passage Route Optimization',
    routeSubtitle: 'Dual bathymetric corridor vs. direct rhumb line baseline avoiding protected coastal sanctuaries.',
    departure: 'DEPARTURE',
    transitCorridor: 'TRANSIT CORRIDOR',
    destination: 'DESTINATION',
    calculateRoute: 'Calculate Safe Passage',
    calculatingRoute: 'Computing Safe Corridor...',
    hazardsAvoidedLabel: 'Hazards Avoided',
    fuelEstimate: 'Fuel Estimate',
    etaHours: 'Estimated Time',
    selectDeparturePort: 'Departure Port',
    selectDestinationPort: 'Destination Port',

    // Assistant & Chat
    assistantTitle: 'AI Assistant',
    assistantConnected: 'Connected to Marine Analytics Engine',
    newChat: 'New Chat',
    share: 'Share',
    export: 'Export',
    welcomeAnalyze: 'What would you like to analyze today?',
    shortcutCyclone: 'Assess Cyclone Fengal risk',
    shortcutRoute: 'Optimize Cochin → Gulf route',
    shortcutCollision: 'Check vessel collision vectors',
    typeMessage: 'Type a message...',
    whereCuriosity: 'Where Coastal Wisdom Meets Real-Time Intelligence',
    searchPrompt: 'Search Prompt',
    chatSearchPlaceholder: 'Search here...',
    trendingPrompt: 'Trending Prompts',
    seeAll: 'See All',
    recentlyChat: 'Recently Chat',
    historyChat: 'History Chat',
    today: 'TODAY',
    yesterday: 'YESTERDAY',
    oneWeekAgo: '1 WEEK AGO',
    newChats: 'New Chats',
    timelineTitle: 'AI Insights Timeline',
    tabAll: 'All',
    tabAlerts: 'Alerts',
    tabForecast: 'Forecast',
    tabHistory: 'History',

    // Scenarios Drawer
    scenariosTitle: 'Scenarios',
    testScenarios: 'Test Scenarios',
    searchScenarios: 'Search coastal scenario...',
    groundingTestSuite: 'Grounding & Test Suite',
    totalLabel: 'Total',

    // Dynamic Dashboard & Telemetry
    activePfzCount: '3 PFZ ZONES ACTIVE',
    zoneIdRatnagiri: 'ZONE ID • RATNAGIRI-WZ-04',
    validToday: 'VALID: TODAY',
    incoisImdVerified: 'INCOIS / IMD VERIFIED',
    updatedLiveApi: 'UPDATED: LIVE API',
    updatedLive: 'UPDATED: LIVE',
    incoisWaveBuoy: 'INCOIS Wave Buoy',
    incoisWaveBuoySub: 'Swell 1.8m • Normal',
    coastGuardMpa: 'Coast Guard MPA',
    coastGuardMpaSub: 'Geofence Boundary',
    imdCycloneRadar: 'IMD Cyclone Radar',
    imdCycloneRadarSub: 'Wind Gust 24kt',
    varunaCopilot: 'VARUNA Copilot',
    varunaCopilotSub: 'AI Advisory Ready',
    badgeOk: 'OK',
    badgeClear: 'Clear',
    badgeMonitor: 'Monitor',
    badgeActive: 'Active',
    scenario_safe_complete_name: '1. Safe / Complete (Ratnagiri)',
    scenario_safe_complete_desc: 'Normal coastal conditions, all 4 domains current within 30 min, active PFZ.',
    scenario_caution_wave_name: '2. Caution / High Wave (Kochi)',
    scenario_caution_wave_desc: 'Wave swell 2.8m > 2.5m threshold; medium confidence due to unavailable lightning feed.',
    scenario_unsafe_cyclone_name: '3. Unsafe / Cyclone (Visakhapatnam)',
    scenario_unsafe_cyclone_desc: 'Severe cyclonic storm warning, 48 kt winds, 5.2m waves. Mandatory zero-departure.',
    scenario_pfz_but_unsafe_name: '4. PFZ Productive but Unsafe (Ratnagiri)',
    scenario_pfz_but_unsafe_desc: 'High chlorophyll PFZ zone, but 34 kt squall. Favorable fish aggregations do NOT override risk.',
    scenario_geofence_restricted_name: '5. Geofence Restricted (Malvan MPA)',
    scenario_geofence_restricted_desc: 'Target coordinates inside Malvan Marine Sanctuary No-Take Core Zone. Regulatory violation.',
    scenario_weather_stale_name: '6. Weather Stale (Veraval)',
    scenario_weather_stale_desc: 'Weather data > 90 min old; system triggers degraded confidence fallback.',
  },
  hi: {
    appTitle: 'वरुण समुद्री सूचना प्रणाली',
    pageMapTitle: 'समुद्री सूचना कमांड',
    pageRoutingTitle: 'मार्ग अनुकूलन',
    pageChatTitle: 'वरुण AI',
    pageReasoningTitle: 'एजेंटिक रीज़निंग',
    pageAlertsTitle: 'सक्रिय समुद्री चेतावनियां',
    pageFleetTitle: 'बेड़ा संचालन',
    pageTrendsTitle: 'मत्स्य प्रवृत्तियां और विसंगतियां',

    // Navigation
    navMap: 'नक्शा',
    navAlerts: 'अलर्ट',
    navAssistant: 'सहायक',
    navTrends: 'ट्रेंड्स',
    navMore: 'अन्य',
    navOverview: 'डैशबोर्ड',
    navFleet: 'बेड़ा',
    navRouting: 'मार्ग',
    navReasoning: 'नियम',
    closeMenu: 'मेनू बंद करें',

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

    // Dashboard
    marineAdvisoryCards: 'समुद्री सलाह कार्ड',
    viewMapView: 'नक्शा देखें ↗',
    oceanTelemetry: 'समुद्र टेलीमेट्री',
    sensorsOn: 'सेंसर सक्रिय',
    routeOptimize: 'मार्ग अनुकूलन',
    rulesEngine: 'नियम इंजन',
    fleetOps: 'बेड़ा संचालन',
    fisheryTrends: 'मत्स्य प्रवृत्तियां',
    activeAlerts: 'सक्रिय चेतावनियां',
    recentScenariosTitle: 'हाल के तटीय परिदृश्य और प्रश्न',
    tapToEvaluate: 'सुरक्षा मूल्यांकन के लिए किसी भी पंक्ति को दबाएं',
    zoneVessel: 'क्षेत्र / नाव',
    timestamp: 'समय',
    safetyVerdict: 'सुरक्षा निर्णय',
    coordinates: 'निर्देशांक',
    statistic: 'आंकड़े',
    integrity: 'सुरक्षा अखंडता',
    passedChecks: 'सफल जांच',
    violations: 'उल्लंघन',

    // Alerts
    coastalHazardBroadcast: 'तटीय आपदा प्रसारण',
    activeAlertsTitle: 'सक्रिय समुद्री चेतावनियां और प्रतिबंध',
    activeAlertsSubtitle: 'लाइव आपातकालीन सूचनाएं, INCOIS उच्च तरंग बुलेटिन और IMD चक्रवात चेतावनियां।',
    authority: 'प्राधिकरण',
    validity: 'वैधता',
    evaluateOnMap: 'नक्शे पर प्रभाव देखें →',

    // Fleet Ops
    fleetMonitorBadge: 'बेड़ा टेलीमेट्री एवं AIS निगरानी',
    fleetTitle: 'तटीय बेड़ा संचालन',
    fleetSubtitle: 'लाइव स्थिति, जियोफेंस अनुपालन, सुरक्षा सलाह और बंदरगाह लंगर।',
    activeCraft: 'सक्रिय नावें',
    inPfzZones: 'मछली क्षेत्रों में',
    weatherClear: 'मौसम अनुकूलता',
    vesselIdName: 'नाव संख्या / नाम',
    vesselType: 'प्रकार',
    homePort: 'मूल बंदरगाह',
    vesselCoords: 'निर्देशांक',
    operatingStatus: 'संचालन स्थिति',
    safetyState: 'सुरक्षा स्थिति',
    aisRelay: 'AIS रिले',

    // Historical Trends
    sihQuery7: 'SIH राष्ट्रीय मूल्यांकन प्रश्न #7',
    trendsTitle: 'तटीय मत्स्य उत्पादकता एवं विसंगति विश्लेषण',
    trendsSubtitle: 'उपग्रह SST विसंगतियों, क्लोरोफिल चक्रों और मानसून प्रतिबंधों के माध्यम से मछली उत्पादन में कमी का विश्लेषण।',
    environmentalDrivers: 'पहचाने गए मुख्य पर्यावरणीय कारक',
    sstTab: 'समुद्र सतह का तापमान (SST)',
    chlTab: 'क्लोरोफिल-ए बायोमास',
    annualDecline: 'वार्षिक उत्पादन में कमी',
    statutoryBasis: 'वैधानिक आधार और सरकारी राजपत्र संदर्भ',

    // Route Optimization
    routeCorridorBadge: 'सुरक्षित समुद्री गलियारा',
    routeTitle: 'मार्ग अनुकूलन एवं सुरक्षित मार्ग',
    routeSubtitle: 'संरक्षित क्षेत्रों से बचते हुए सुरक्षित गलियारा बनाम सीधा मार्ग तुलना।',
    departure: 'प्रस्थान',
    transitCorridor: 'पारगमन गलियारा',
    destination: 'गंतव्य',
    calculateRoute: 'सुरक्षित मार्ग की गणना करें',
    calculatingRoute: 'सुरक्षित मार्ग निकाला जा रहा है...',
    hazardsAvoidedLabel: 'बचाए गए खतरे',
    fuelEstimate: 'ईंधन अनुमान',
    etaHours: 'अनुमानित समय',
    selectDeparturePort: 'प्रस्थान बंदरगाह',
    selectDestinationPort: 'गंतव्य बंदरगाह',

    // Assistant & Chat
    assistantTitle: 'वरुण AI सहायक',
    assistantConnected: 'समुद्री विश्लेषिकी इंजन से जुड़ा हुआ है',
    newChat: 'नई बातचीत',
    share: 'शेयर करें',
    export: 'निर्यात करें',
    welcomeAnalyze: 'आज आप किस समुद्री स्थिति का विश्लेषण करना चाहते हैं?',
    shortcutCyclone: 'चक्रवात फेंगल जोखिम का आकलन करें',
    shortcutRoute: 'कोचीन → गल्फ सुरक्षित मार्ग अनुकूलित करें',
    shortcutCollision: 'जहाज टकराव जोखिम व AIS बफर जांचें',
    typeMessage: 'संदेश या प्रश्न टाइप करें...',
    whereCuriosity: 'जहाँ तटीय ज्ञान वास्तविक समय की बुद्धिमत्ता से मिलता है',
    searchPrompt: 'प्रॉम्प्ट खोजें',
    chatSearchPlaceholder: 'यहाँ खोजें...',
    trendingPrompt: 'प्रचलित प्रश्न',
    seeAll: 'सभी देखें',
    recentlyChat: 'हाल की बातचीत',
    historyChat: 'चैट इतिहास',
    today: 'आज',
    yesterday: 'कल',
    oneWeekAgo: '1 सप्ताह पहले',
    newChats: 'नई चैट',
    timelineTitle: 'AI अंतर्दृष्टि टाइमलाइन',
    tabAll: 'सभी',
    tabAlerts: 'चेतावनियां',
    tabForecast: 'पूर्वानुमान',
    tabHistory: 'इतिहास',

    // Scenarios Drawer
    scenariosTitle: 'परिदृश्य',
    testScenarios: 'परीक्षण परिदृश्य',
    searchScenarios: 'तटीय परिदृश्य खोजें...',
    groundingTestSuite: 'तटीय प्रमाणन व परीक्षण सूट',
    totalLabel: 'कुल',

    // Dynamic Dashboard & Telemetry
    activePfzCount: '3 PFZ क्षेत्र सक्रिय',
    zoneIdRatnagiri: 'क्षेत्र आईडी • रत्नागिरी-WZ-04',
    validToday: 'वैधता: आज',
    incoisImdVerified: 'INCOIS / IMD द्वारा सत्यापित',
    updatedLiveApi: 'अद्यतन: लाइव API',
    updatedLive: 'अद्यतन: लाइव',
    incoisWaveBuoy: 'INCOIS तरंग प्लव',
    incoisWaveBuoySub: 'लहरें 1.8 मी • सामान्य',
    coastGuardMpa: 'तटरक्षक समुद्री संरक्षित क्षेत्र (MPA)',
    coastGuardMpaSub: 'भू-सीमा परिधि',
    imdCycloneRadar: 'IMD चक्रवात रडार',
    imdCycloneRadarSub: 'हवा के झोंके 24 नॉट',
    varunaCopilot: 'वरुण कोपायलट',
    varunaCopilotSub: 'AI सलाह उपलब्ध',
    badgeOk: 'ठीक',
    badgeClear: 'सुरक्षित',
    badgeMonitor: 'निगरानी',
    badgeActive: 'सक्रिय',
    scenario_safe_complete_name: '1. सुरक्षित / पूर्ण (रत्नागिरी)',
    scenario_safe_complete_desc: 'सामान्य तटीय स्थिति, सभी 4 डोमेन 30 मिनट में अद्यतन, सक्रिय मछली क्षेत्र।',
    scenario_caution_wave_name: '2. सावधानी / उच्च तरंग (कोच्चि)',
    scenario_caution_wave_desc: 'लहरें 2.8 मी > 2.5 मी सीमा; बिजली डेटा अनुपलब्ध होने से मध्यम विश्वास।',
    scenario_unsafe_cyclone_name: '3. असुरक्षित / चक्रवात (विशाखापट्टनम)',
    scenario_unsafe_cyclone_desc: 'भीषण चक्रवाती तूफान चेतावनी, 48 नॉट हवा, 5.2 मी लहरें। प्रस्थान पूर्णतः स्थगित।',
    scenario_pfz_but_unsafe_name: '4. मछली क्षेत्र उत्पादक पर असुरक्षित (रत्नागिरी)',
    scenario_pfz_but_unsafe_desc: 'उच्च क्लोरोफिल क्षेत्र, लेकिन 34 नॉट स्क्वॉल। अनुकूल मछली समूह जोखिम को रद्द नहीं करते।',
    scenario_geofence_restricted_name: '5. भू-सीमा प्रतिबंधित (मालवन MPA)',
    scenario_geofence_restricted_desc: 'मालवन समुद्री अभयारण्य कोर ज़ोन के भीतर लक्षित निर्देशांक। विनियामक उल्लंघन।',
    scenario_weather_stale_name: '6. पुराना मौसम डेटा (वेरावल)',
    scenario_weather_stale_desc: 'मौसम डेटा 90 मिनट से पुराना; सिस्टम अधोगति विश्वसनीयता फ़ॉलबैक सक्रिय करता है।',
  },
  mr: {
    appTitle: 'वरुण सागरी माहिती प्रणाली',
    pageMapTitle: 'सागरी माहिती कमांड',
    pageRoutingTitle: 'मार्ग अनुकूलन',
    pageChatTitle: 'वरुण AI',
    pageReasoningTitle: 'एजेंटिक रिझनिंग',
    pageAlertsTitle: 'सक्रिय सागरी सूचना',
    pageFleetTitle: 'ताफा व्यवस्थापन',
    pageTrendsTitle: 'मत्स्य ट्रेंड आणि विसंगती',

    // Navigation
    navMap: 'नकाशा',
    navAlerts: 'इशारे',
    navAssistant: 'सहायक',
    navTrends: 'ट्रेंड्स',
    navMore: 'अधिक',
    navOverview: 'डॅशबोर्ड',
    navFleet: 'ताफा',
    navRouting: 'मार्ग',
    navReasoning: 'नियम',
    closeMenu: 'मेनू बंद करा',

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

    // Dashboard
    marineAdvisoryCards: 'सागरी सल्ला कार्ड',
    viewMapView: 'नकाशा पाहा ↗',
    oceanTelemetry: 'समुद्र टेलीमेट्री',
    sensorsOn: 'सेन्सर सक्रिय',
    routeOptimize: 'मार्ग अनुकूलन',
    rulesEngine: 'नियम इंजिन',
    fleetOps: 'ताफा व्यवस्थापन',
    fisheryTrends: 'मत्स्य ट्रेंड',
    activeAlerts: 'सक्रिय सूचना',
    recentScenariosTitle: 'अलीकडील सागरी परिस्थिती आणि प्रश्न',
    tapToEvaluate: 'सुरक्षा तपासणीसाठी कोणत्याही ओळीवर टॅप करा',
    zoneVessel: 'विभाग / बोट',
    timestamp: 'वेळ',
    safetyVerdict: 'सुरक्षा निर्णय',
    coordinates: 'अक्षांश-रेखांश',
    statistic: 'आकडेवारी',
    integrity: 'सुरक्षा अखंडता',
    passedChecks: 'पास झालेली तपासणी',
    violations: 'धोकादायक घटक',

    // Alerts
    coastalHazardBroadcast: 'किनारपट्टी धोक्याची सूचना',
    activeAlertsTitle: 'सक्रिय सागरी सूचना आणि निर्बंध',
    activeAlertsSubtitle: 'तातडीच्या सूचना, INCOIS लाटांचे बुलेटिन आणि IMD चक्रीवादळ सूचना.',
    authority: 'प्राधिकरण',
    validity: 'वैधता',
    evaluateOnMap: 'नकाशावर तपासा →',

    // Fleet Ops
    fleetMonitorBadge: 'ताफा टेलीमेट्री आणि AIS मॉनिटर',
    fleetTitle: 'किनारपट्टी ताफा व्यवस्थापन',
    fleetSubtitle: 'थेट स्थान, जिओफेन्स पालन, सुरक्षा सूचना आणि बंदरातील नौका.',
    activeCraft: 'सक्रिय नौका',
    inPfzZones: 'मासेमारी क्षेत्रात',
    weatherClear: 'हवामान अनुकूलता',
    vesselIdName: 'नाव / नोंदणी क्रमांक',
    vesselType: 'प्रकार',
    homePort: 'मुख्य बंदर',
    vesselCoords: 'अक्षांश-रेखांश',
    operatingStatus: 'सद्यस्थिती',
    safetyState: 'सुरक्षा स्थिती',
    aisRelay: 'AIS रिले',

    // Historical Trends
    sihQuery7: 'SIH राष्ट्रीय मूल्यमापन प्रश्न #7',
    trendsTitle: 'किनारपट्टी मत्स्य उत्पादकता आणि विसंगती विश्लेषण',
    trendsSubtitle: 'उपग्रह SST विसंगती, क्लोरोफिल चक्र आणि मान्सून मासेमारी बंदीद्वारे उत्पादनातील घटीचे विश्लेषण.',
    environmentalDrivers: 'ओळखलेले मुख्य पर्यावरणीय घटक',
    sstTab: 'समुद्र पृष्ठभागाचे तापमान (SST)',
    chlTab: 'क्लोरोफिल-ए बायोमास',
    annualDecline: 'वार्षिक उत्पादनातील घट',
    statutoryBasis: 'कायदेशीर संदर्भ आणि शासकीय राजपत्र',

    // Route Optimization
    routeCorridorBadge: 'सुरक्षित सागरी मार्ग',
    routeTitle: 'मार्ग अनुकूलन आणि सुरक्षित सागरी मार्ग',
    routeSubtitle: 'संरक्षित क्षेत्रांपासून सुरक्षित अंतर ठेवून आखलेला अनुकूल मार्ग.',
    departure: 'प्रस्थान',
    transitCorridor: 'सुरक्षित मार्ग',
    destination: 'गंतव्य',
    calculateRoute: 'सुरक्षित मार्ग शोधा',
    calculatingRoute: 'सुरक्षित मार्ग शोधत आहे...',
    hazardsAvoidedLabel: 'टाळलेले धोके',
    fuelEstimate: 'अंदाजे इंधन',
    etaHours: 'अंदाजे वेळ',
    selectDeparturePort: 'प्रस्थान बंदर',
    selectDestinationPort: 'गंतव्य बंदर',

    // Assistant & Chat
    assistantTitle: 'वरुण AI सहाय्यक',
    assistantConnected: 'सागरी विश्लेषण इंजिनशी जोडलेले',
    newChat: 'नवीन चर्चा',
    share: 'शेअर करा',
    export: 'निर्यात करा',
    welcomeAnalyze: 'आज आपण कोणत्या सागरी घटकांचे विश्लेषण करू इच्छिता?',
    shortcutCyclone: 'चक्रीवादळ फेंगल जोखमीचे मूल्यांकन करा',
    shortcutRoute: 'कोची → गल्फ सुरक्षित मार्ग ऑप्टिमाइझ करा',
    shortcutCollision: 'जहाज धडक जोखीम व AIS बफर तपासा',
    typeMessage: 'संदेश टाइप करा...',
    whereCuriosity: 'जिथे किनारपट्टी ज्ञान आणि सागरी बुद्धिमत्ता एकत्र येतात',
    searchPrompt: 'प्रॉम्प्ट शोधा',
    chatSearchPlaceholder: 'येथे शोधा...',
    trendingPrompt: 'ट्रेंडिंग प्रश्न',
    seeAll: 'सर्व पाहा',
    recentlyChat: 'नुकतीच झालेली चर्चा',
    historyChat: 'संवाद इतिहास',
    today: 'आज',
    yesterday: 'काल',
    oneWeekAgo: '1 आठवड्यापूर्वी',
    newChats: 'नवीन संवाद',
    timelineTitle: 'AI अंतर्दृष्टी टाइमलाइन',
    tabAll: 'सर्व',
    tabAlerts: 'इशारे',
    tabForecast: 'अंदाज',
    tabHistory: 'इतिहास',

    // Scenarios Drawer
    scenariosTitle: 'परिदृश्ये',
    testScenarios: 'चाचणी परिदृश्ये',
    searchScenarios: 'किनारपट्टी परिदृश्य शोधा...',
    groundingTestSuite: 'प्रमाणीकरण आणि चाचणी संच',
    totalLabel: 'एकूण',

    // Dynamic Dashboard & Telemetry
    activePfzCount: '3 PFZ क्षेत्र सक्रिय',
    zoneIdRatnagiri: 'झोन आयडी • रत्नागिरी-WZ-04',
    validToday: 'वैधता: आज',
    incoisImdVerified: 'INCOIS / IMD प्रमाणित',
    updatedLiveApi: 'अपडेट: थेट API',
    updatedLive: 'अपडेट: थेट',
    incoisWaveBuoy: 'INCOIS लाटांची तरंग-बॉय',
    incoisWaveBuoySub: 'लाटा 1.8 मी • सामान्य',
    coastGuardMpa: 'किनारपट्टी रक्षक सागरी संरक्षित क्षेत्र (MPA)',
    coastGuardMpaSub: 'जिओफेन्स सीमा',
    imdCycloneRadar: 'IMD चक्रीवादळ रडार',
    imdCycloneRadarSub: 'वादळी वारे 24 नॉट्स',
    varunaCopilot: 'वरुण कोपायलट',
    varunaCopilotSub: 'AI सल्ला सज्ज',
    badgeOk: 'ठीक',
    badgeClear: 'सुरक्षित',
    badgeMonitor: 'निरीक्षण',
    badgeActive: 'सक्रिय',
    scenario_safe_complete_name: '1. सुरक्षित / पूर्ण (रत्नागिरी)',
    scenario_safe_complete_desc: 'सामान्य किनारपट्टी स्थिती, चारही डोमेन 30 मिनिटांत ताजे, सक्रिय PFZ.',
    scenario_caution_wave_name: '2. सावधगिरी / उंच लाटा (कोची)',
    scenario_caution_wave_desc: 'लाटा 2.8 मी > 2.5 मी मर्यादा; विजांचा डेटा उपलब्ध नसल्याने मध्यम विश्वास.',
    scenario_unsafe_cyclone_name: '3. धोकादायक / चक्रीवादळ (विशाखापट्टणम)',
    scenario_unsafe_cyclone_desc: 'तीव्र चक्रीवादळ चेतावणी, 48 नॉट वारे, 5.2 मी लाटा. समुद्रात जाण्यास पूर्ण बंदी.',
    scenario_pfz_but_unsafe_name: '4. PFZ उत्पादक पण असुरक्षित (रत्नागिरी)',
    scenario_pfz_but_unsafe_desc: 'उच्च क्लोरोफिल क्षेत्र, पण 34 नॉट सोसाट्याचा वारा. माशांचे प्रमाण धोक्यापेक्षा मोठे नाही.',
    scenario_geofence_restricted_name: '5. जिओफेन्स प्रतिबंधित (मालवण MPA)',
    scenario_geofence_restricted_desc: 'मालवण सागरी अभयारण्य नो-टेक कोअर झोनच्या आत. कायदेशीर उल्लंघन.',
    scenario_weather_stale_name: '6. जुना हवामान डेटा (वेरावळ)',
    scenario_weather_stale_desc: 'हवामान डेटा 90 मिनिटांपेक्षा जुना; सिस्टीम अधोगती विश्वासार्हता मोड सुरू करते.',
  },
  ta: {
    appTitle: 'வருணா கடல்சார் தகவல் அமைப்பு',
    pageMapTitle: 'கடல்சார் தகவல் கட்டுப்பாடு',
    pageRoutingTitle: 'பாதை உகப்பாக்கம்',
    pageChatTitle: 'வருணா AI',
    pageReasoningTitle: 'ஏஜென்டிக் ரீசனிங்',
    pageAlertsTitle: 'செயலில் உள்ள கடல் எச்சரிக்கைகள்',
    pageFleetTitle: 'கப்பற்படை செயல்பாடுகள்',
    pageTrendsTitle: 'மீன்பிடி போக்குகள் & முரண்பாடுகள்',

    // Navigation
    navMap: 'வரைபடம்',
    navAlerts: 'எச்சரிக்கை',
    navAssistant: 'உதவி',
    navTrends: 'போக்கு',
    navMore: 'மேலும்',
    navOverview: 'முகப்பு',
    navFleet: 'கப்பற்படை',
    navRouting: 'பாதை',
    navReasoning: 'ரீசனிங்',
    closeMenu: 'மெனுவை மூடு',

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

    // Assistant & Chat
    assistantTitle: 'வருணா AI உதவியாளர்',
    assistantConnected: 'கடல்சார் பகுப்பாய்வு இயந்திரத்துடன் இணைக்கப்பட்டுள்ளது',
    newChat: 'புதிய உரையாடல்',
    share: 'பகிர்',
    export: 'ஏற்றுமதி',
    welcomeAnalyze: 'இன்று நீங்கள் எதைப் பகுப்பாய்வு செய்ய விரும்புகிறீர்கள்?',
    shortcutCyclone: 'ஃபெங்கல் புयல் ஆபத்தை மதிப்பிடுங்கள்',
    shortcutRoute: 'கொச்சி → வளைகுடா பாதுகாப்பான பாதையை மேம்படுத்துங்கள்',
    shortcutCollision: 'கப்பல் மோதல் அபாயங்களைச் சரிபார்க்கவும்',
    typeMessage: 'செய்தி அல்லது கேள்வியை உள்ளிடவும்...',
    whereCuriosity: 'கடற்கரை அறிவும் நிகழ்நேர நுண்ணறிவும் இணையும் தளம்',
    searchPrompt: 'கேள்வியைத் தேடுங்கள்',
    chatSearchPlaceholder: 'இங்கே தேடுங்கள்...',
    trendingPrompt: 'பிரபலமான கேள்விகள்',
    seeAll: 'அனைத்தையும் காண்க',
    recentlyChat: 'சமீபத்திய உரையாடல்கள்',
    historyChat: 'உரையாடல் வரலாறு',
    today: 'இன்று',
    yesterday: 'நேற்று',
    oneWeekAgo: '1 வாரத்திற்கு முன்பு',
    newChats: 'புதிய உரையாடல்',
    timelineTitle: 'AI நுண்ணறிவு காலவரிசை',
    tabAll: 'அனைத்தும்',
    tabAlerts: 'எச்சரிக்கைகள்',
    tabForecast: 'வானிலை முன்னறிவிப்பு',
    tabHistory: 'வரலாறு',

    // Scenarios Drawer
    scenariosTitle: 'சூழ்நிலைகள்',
    testScenarios: 'சோதனை சூழ்நிலைகள்',
    searchScenarios: 'கடற்கரை சூழ்நிலையைத் தேடுங்கள்...',
    groundingTestSuite: 'சரிபார்ப்பு & சோதனைத் தொகுப்பு',
    totalLabel: 'மொத்தம்',

    // Dynamic Dashboard & Telemetry
    activePfzCount: '3 PFZ மண்டலங்கள் செயலில்',
    zoneIdRatnagiri: 'மண்டல ஐடி • ரத்னகிரி-WZ-04',
    validToday: 'செல்லுபடியாகும்: இன்று',
    incoisImdVerified: 'INCOIS / IMD சரிபார்க்கப்பட்டது',
    updatedLiveApi: 'புதுப்பிக்கப்பட்டது: நேரலை API',
    updatedLive: 'புதுப்பிக்கப்பட்டது: நேரலை',
    incoisWaveBuoy: 'INCOIS அலை மிதவை',
    incoisWaveBuoySub: 'அலை 1.8 மீ • இயல்பானது',
    coastGuardMpa: 'கடலோர காவல்படை MPA',
    coastGuardMpaSub: 'புவிசார் எல்லை',
    imdCycloneRadar: 'IMD புயல் ரேடார்',
    imdCycloneRadarSub: 'காற்று வீச்சு 24 நாட்ஸ்',
    varunaCopilot: 'வருணா கோபைலட்',
    varunaCopilotSub: 'AI வழிகாட்டுதல் தயார்',
    badgeOk: 'சரி',
    badgeClear: 'தெளிவு',
    badgeMonitor: 'கண்காணிப்பு',
    badgeActive: 'செயலில்',
    scenario_safe_complete_name: '1. பாதுகாப்பானது / முழுமை (ரத்னகிரி)',
    scenario_safe_complete_desc: 'சாதாரண கடலோர நிலைமைகள், 30 நிமிடங்களில் 4 களங்களும் புதுப்பிக்கப்பட்டன.',
    scenario_caution_wave_name: '2. எச்சரிக்கை / உயர் அலை (கொச்சி)',
    scenario_caution_wave_desc: 'அலை உயரம் 2.8 மீ > 2.5 மீ வரம்பு; மின்னல் தகவல் கிடைக்காததால் நடுத்தர நம்பிக்கை.',
    scenario_unsafe_cyclone_name: '3. ஆபத்தானது / புயல் (விசாகப்பட்டினம்)',
    scenario_unsafe_cyclone_desc: 'கடும் புயல் எச்சரிக்கை, 48 நாட் காற்று, 5.2 மீ அலைகள். கட்டாய புறப்பாடு நிறுத்தம்.',
    scenario_pfz_but_unsafe_name: '4. PFZ உற்பத்தி திறன் கொண்டது ஆனால் ஆபத்தானது (ரத்னகிரி)',
    scenario_pfz_but_unsafe_desc: 'அதிக குளோரோபில் PFZ மண்டலம், ஆனால் 34 நாட் காற்று. மீன் வளம் ஆபத்தை மீறாது.',
    scenario_geofence_restricted_name: '5. புவிசார் தடைசெய்யப்பட்டது (மால்வன் MPA)',
    scenario_geofence_restricted_desc: 'மால்வன் கடல் சரணாலய எல்லைக்குள் இலக்கு ஒருங்கிணைப்புகள். சட்ட மீறல்.',
    scenario_weather_stale_name: '6. காலாவதியான வானிலை (வேராவல்)',
    scenario_weather_stale_desc: 'வானிலை தகவல் 90 நிமிடங்களுக்கும் பழையது; கணினி எச்சரிக்கை விடுக்கிறது.',
  },
};

const STORAGE_KEY = 'varuna_preferred_lang';

// Global reactive subscriber bus for language synchronization across all components
const languageListeners = new Set<(lang: LanguageCode) => void>();

function getInitialLanguage(): LanguageCode {
  try {
    const saved = localStorage.getItem(STORAGE_KEY) as LanguageCode;
    if (saved && ['en', 'hi', 'mr', 'ta'].includes(saved)) {
      return saved;
    }
  } catch {}
  return 'en';
}

export function setGlobalLanguage(lang: LanguageCode) {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {}
  languageListeners.forEach((listener) => listener(lang));
}

export function useLocalization() {
  const [currentLang, setCurrentLang] = useState<LanguageCode>(getInitialLanguage);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [liveAnnouncement, setLiveAnnouncement] = useState<string>('');

  useEffect(() => {
    languageListeners.add(setCurrentLang);
    return () => {
      languageListeners.delete(setCurrentLang);
    };
  }, []);

  const setLanguage = (lang: LanguageCode) => {
    setGlobalLanguage(lang);
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
