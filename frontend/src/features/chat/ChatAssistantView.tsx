import React, { useState, useEffect, useRef } from 'react';
import type { UserResponseV1 } from '../../contracts/userResponse';
import { apiClient } from '../../api/client';
import type { ActiveNavView } from '../query/Sidebar';
import { useLocalization } from '../../hooks/useLocalization';
import { FormattedChatContent } from './FormattedChatContent';
import {
  IconFish,
  IconCompass,
  IconWave,
  IconCyclone,
  IconAnchor,
  IconMapPin,
  IconShip,
  IconLightning,
  IconFolder,
  IconLink,
  IconClipboard,
  IconDownload,
  IconDatabase,
  IconSparkles,
} from '../../components/Icons';
import './ChatAssistantView.css';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  text: string;
  thinking?: string[];
  verdict?: 'SAFE' | 'CAUTION' | 'UNSAFE';
  scenarioSyncId?: string;
  metrics?: {
    wave?: string;
    wind?: string;
    pfz?: string;
    confidence?: string;
  };
  actions?: Array<{
    label: string;
    actionType: 'scenario' | 'view';
    target: string;
  }>;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  timeGroup: 'TODAY' | 'YESTERDAY' | 'PREVIOUS 7 DAYS';
  messages: ChatMessage[];
  lastQuery: string;
  scenarioSyncId?: string;
}

interface ChatAssistantViewProps {
  onSelectScenario: (scenarioId: string) => void;
  onChangeView: (view: ActiveNavView) => void;
  currentResponse?: UserResponseV1 | null;
}

const DEFAULT_INITIAL_SESSIONS: ChatSession[] = [
  {
    id: 'sess-1',
    title: 'Ratnagiri PFZ & Convective Storm Risk',
    createdAt: Date.now() - 3600 * 1000 * 2,
    updatedAt: Date.now() - 3600 * 1000 * 2,
    timeGroup: 'TODAY',
    lastQuery: 'Where is the nearest Potential Fishing Zone (PFZ) today from Ratnagiri?',
    scenarioSyncId: 'pfz_but_unsafe',
    messages: [
      {
        id: 'u-1',
        sender: 'user',
        timestamp: '10:15 AM',
        text: 'Where is the nearest Potential Fishing Zone (PFZ) today from Ratnagiri?',
      },
      {
        id: 'a-1',
        sender: 'assistant',
        timestamp: '10:15 AM',
        verdict: 'UNSAFE',
        scenarioSyncId: 'pfz_but_unsafe',
        metrics: {
          wave: '1.04 m (Calm)',
          wind: '13.4 km/h',
          pfz: '3 Zones Active',
          confidence: 'HIGH (IMD / INCOIS Verified)',
        },
        thinking: [
          'Query parsed: Location "Ratnagiri", Domain "PFZ Discovery & Marine Safety Assessment".',
          'Weather check: Wave height 1.04m, Wind speed 13.4 km/h (within standard limits).',
          'Atmospheric Threat: Severe convective storm activity forecast; "high" lightning-risk rating flagged.',
          'Deterministic Rule Engine: IMD severe-lightning rule triggered → Automatic UNSAFE verdict.',
          'Geofencing check: Clear — 97 km clearance from Malvan Marine Sanctuary.',
          'PFZ Retrieval: 3 productive zones identified (Nearshore Bank 12 km, Sector Alpha 21 km, Shelf-break 33 km).',
        ],
        text: `The system's risk engine has marked today's conditions as **UNSAFE**.\n\n**Root Cause:** The only trigger was the **"high" lightning risk** — severe convective storm activity is forecast for the area, and under the IMD severe-lightning rule this automatically makes any offshore movement unsafe, regardless of wave height (**1.04 m**) or wind (**13.4 km/h**).\n\n**Potential Fishing Zones Identified:**\n• **PFZ-IND-169-C "Nearshore Bank"** — about 12 km away, shallow (≈19 m), productivity **0.704** (prawns, croaker, sole).\n• **PFZ-IND-169-A "Offshore Sector Alpha"** — about 21 km away, deeper (≈30 m), productivity **0.710** (mackerel, sardine, anchovy).\n• **PFZ-IND-169-B "Continental Shelf-break"** — about 33 km away, deeper (≈46 m), productivity **0.653** (tuna, pomfret, ribbonfish).\n\n**Geofence Status:** Clear — 97 km from Malvan Marine Sanctuary.\n\n**Action:** Stay in sheltered waters such as **Mirya Bay** or nearshore anchorages within 2–5 km of the coast until the convective storm passes and lightning risk drops to "low" or "none".`,
        actions: [
          { label: 'View Ratnagiri Alert on Map', actionType: 'scenario', target: 'pfz_but_unsafe' },
          { label: 'Check Marine Warnings', actionType: 'view', target: 'alerts' },
        ],
      },
    ],
  },
  {
    id: 'sess-2',
    title: 'Kochi Morning Safety Clearance Check',
    createdAt: Date.now() - 3600 * 1000 * 5,
    updatedAt: Date.now() - 3600 * 1000 * 5,
    timeGroup: 'TODAY',
    lastQuery: 'Is it safe to venture into the sea tomorrow morning off Kochi?',
    scenarioSyncId: 'safe_complete',
    messages: [
      {
        id: 'u-2',
        sender: 'user',
        timestamp: '07:30 AM',
        text: 'Is it safe to venture into the sea tomorrow morning off Kochi?',
      },
      {
        id: 'a-2',
        sender: 'assistant',
        timestamp: '07:30 AM',
        verdict: 'SAFE',
        scenarioSyncId: 'safe_complete',
        metrics: {
          wave: '1.02 m (Calm)',
          wind: '13 km/h W',
          pfz: '3 Zones Safe',
          confidence: 'HIGH (100% Passed)',
        },
        thinking: [
          'Target Sector: Kochi, Kerala / Malabar Coast.',
          'Weather Ingestion: Wave height 1.02 m, Wind 13 km/h from West, Low lightning risk.',
          'Ocean Currents: Gentle 1.1 kts from SSE.',
          'Geofencing: > 269 km from nearest foreign EEZ (Sri Lanka); zero territorial breaches.',
          'Deterministic Rule Engine: All parameters well within limits for 10–15 m trawlers → SAFE verdict.',
        ],
        text: `The system's risk engine has marked tomorrow morning off Kochi as **SAFE**.\n\n**Safety Analysis:**\n• Wave height is **1.02 m** (well under 1.5 m caution threshold).\n• Wind is **13 km/h from the West** (well under 25 km/h caution limit).\n• Lightning risk is **low**, no cyclone alert, and ocean currents are a gentle **1.1 kts SSE**.\n\n**Productive Fishing Zones Identified:**\n1. **Nearshore Bank (PFZ-IND-99-C)** — about 12 km out, depth ~33 m, productivity score **0.703** (prawns, croaker, sole).\n2. **Offshore Sector Alpha (PFZ-IND-99-A)** — roughly 22 km offshore, depth ~57 m, productivity **0.708** (mackerel, sardine, anchovy).\n3. **Continental Shelf-break (PFZ-IND-99-B)** — about 34 km away, depth ~111 m, productivity **0.650** (tuna, pomfret, ribbonfish).\n\n**Geofencing Status:** Clear — > 269 km from nearest foreign EEZ (Sri Lanka).\n\n**Action:** Launch before sunrise, head west-southwest toward the Nearshore Bank (≈12 km, 6 NM), target prawns and croaker, and stay within sight of the coast.`,
        actions: [
          { label: 'View Kochi Map', actionType: 'scenario', target: 'safe_complete' },
          { label: 'Open Navigation Corridor', actionType: 'view', target: 'routing' },
        ],
      },
    ],
  },
  {
    id: 'sess-3',
    title: 'Veraval Tide, Swell & Weather Ingestion',
    createdAt: Date.now() - 3600 * 1000 * 24,
    updatedAt: Date.now() - 3600 * 1000 * 24,
    timeGroup: 'YESTERDAY',
    lastQuery: 'What are the current tide, swell, and weather conditions near Veraval?',
    scenarioSyncId: 'weather_stale',
    messages: [
      {
        id: 'u-3',
        sender: 'user',
        timestamp: 'Yesterday',
        text: 'What are the current tide, swell, and weather conditions near Veraval?',
      },
      {
        id: 'a-3',
        sender: 'assistant',
        timestamp: 'Yesterday',
        verdict: 'UNSAFE',
        scenarioSyncId: 'weather_stale',
        metrics: {
          wave: '1.4 m (Convective)',
          wind: '23.9 km/h (Gusts 49 km/h)',
          pfz: '3 Zones Unsafe',
          confidence: 'HIGH',
        },
        thinking: [
          'Target Sector: Veraval Coastal Waters / Saurashtra Coast.',
          'Atmospheric Ingestion: Wind from West at 23.9 km/h with gale gusts up to 49 km/h.',
          'Wave Telemetry: Wave height 1.4 m, swell period 8.3 s, humidity 82%, 87% chance of rain.',
          'Severe Convective Squall: High lightning risk flagged by rule engine.',
          'Geofencing: Clear — 346 km from Sir Creek boundary.',
        ],
        text: `At Veraval right now the sea is being hammered by a **strong convective storm**.\n\n**Root Cause & Weather Telemetry:**\n• Wind: West at **23.9 km/h** with gusts up to **49 km/h**.\n• Wave Height: **1.4 m** with an **8.3 s swell period**.\n• Precipitation: 87% chance of rain, 82% humidity.\n• **Hazard:** **High lightning risk** triggers the deterministic safety rule.\n\n**Productive Fishing Zones in Area:**\n• **Nearshore Bank**: 11.8 km away (prawn, croaker, sole).\n• **Offshore Sector Alpha**: 20.7 km out (mackerel, sardine, anchovy).\n• **Continental Shelf-break**: 32 km out (tuna, pomfret, ribbonfish).\n\n**Geofencing Status:** Clear — 346 km from the Sir Creek flashpoint.\n\n**Actionable Recommendation:** Remain in the protected bay today, secure your gear, and plan to head out only after the convective storm eases and lightning risk is removed. Stay safe.`,
        actions: [
          { label: 'View Veraval Weather Alert', actionType: 'scenario', target: 'weather_stale' },
          { label: 'Check Active Warnings', actionType: 'view', target: 'alerts' },
        ],
      },
    ],
  },
  {
    id: 'sess-4',
    title: 'Cochin to Gulf Fuel-Optimal Route',
    createdAt: Date.now() - 3600 * 1000 * 48,
    updatedAt: Date.now() - 3600 * 1000 * 48,
    timeGroup: 'PREVIOUS 7 DAYS',
    lastQuery: 'Compute safe navigation corridor and waypoint clearance from Cochin to Gulf',
    scenarioSyncId: 'safe_complete',
    messages: [
      {
        id: 'u-4',
        sender: 'user',
        timestamp: '3 days ago',
        text: 'Compute safe navigation corridor and waypoint clearance from Cochin to Gulf',
      },
      {
        id: 'a-4',
        sender: 'assistant',
        timestamp: '3 days ago',
        verdict: 'SAFE',
        metrics: {
          wave: '1.4 m average',
          wind: '14 kts NW',
          confidence: 'HIGH (99.8%)',
        },
        thinking: [
          'Running multi-objective A* nautical routing solver.',
          'Evaluating weather routing parameters: Current drift + 1.4 kts, wave resistance nominal.',
          'Computing least-fuel optimal corridor from Cochin to Gulf of Oman.',
        ],
        text: `**OPTIMAL ROUTE COMPUTED**:\n\nThe safest and most fuel-efficient corridor from **Cochin to Gulf** has been generated. By staying 18 NM west of Minicoy passage, the vessel saves **4.2% fuel** while maintaining clearance from shallow reef shelves.`,
        actions: [
          { label: 'Open Route Optimization View', actionType: 'view', target: 'routing' },
          { label: 'View Command Map', actionType: 'view', target: 'map' },
        ],
      },
    ],
  },
];

export const ChatAssistantView: React.FC<ChatAssistantViewProps> = ({
  onSelectScenario,
  onChangeView: _onChangeView,
  currentResponse: _currentResponse,
}) => {
  const { currentLang, t } = useLocalization();
  
  // Persistent Sessions state
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    try {
      const saved = localStorage.getItem('varuna_chat_history_v3');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.warn('Could not load chat sessions from localStorage:', e);
    }
    return DEFAULT_INITIAL_SESSIONS;
  });

  const [activeSessionId, setActiveSessionId] = useState<string | null>(() => {
    try {
      const saved = localStorage.getItem('varuna_active_session_id');
      if (saved) return saved;
    } catch {}
    return null;
  });

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const savedActiveId = localStorage.getItem('varuna_active_session_id');
      const savedSessions = localStorage.getItem('varuna_chat_history_v3');
      if (savedActiveId && savedSessions) {
        const parsedSessions: ChatSession[] = JSON.parse(savedSessions);
        const found = parsedSessions.find((s) => s.id === savedActiveId);
        if (found && found.messages && found.messages.length > 0) {
          return found.messages;
        }
      }
    } catch {}
    return [];
  });

  const [inputQuery, setInputQuery] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [expandedThinking, setExpandedThinking] = useState<Record<string, boolean>>({});
  const [isRecording, setIsRecording] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [historySearch, setHistorySearch] = useState('');
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [selectedEngine, setSelectedEngine] = useState('Hydro Engine 2.0');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  // New: Attachment Popover, Chips, Share Dialog & Toast State
  const [attachmentMenuOpen, setAttachmentMenuOpen] = useState(false);
  const [attachedTelemetry, setAttachedTelemetry] = useState<Array<{ id: string; label: string; text: string; icon?: React.ReactNode }>>([]);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const attachmentWrapperRef = useRef<HTMLDivElement>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((current) => (current === msg ? null : current));
    }, 2800);
  };

  // Close attachment menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (attachmentWrapperRef.current && !attachmentWrapperRef.current.contains(e.target as Node)) {
        setAttachmentMenuOpen(false);
      }
    };
    if (attachmentMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [attachmentMenuOpen]);

  // Save sessions to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('varuna_chat_history_v3', JSON.stringify(sessions));
    } catch (e) {
      console.warn('Failed to persist chat sessions:', e);
    }
  }, [sessions]);

  // Persist active session ID to localStorage across tab navigation
  useEffect(() => {
    try {
      if (activeSessionId) {
        localStorage.setItem('varuna_active_session_id', activeSessionId);
      } else {
        localStorage.removeItem('varuna_active_session_id');
      }
    } catch {}
  }, [activeSessionId]);

  // Load session messages when activeSessionId changes
  useEffect(() => {
    if (activeSessionId) {
      const found = sessions.find((s) => s.id === activeSessionId);
      if (found) {
        setMessages(found.messages);
      }
    }
  }, [activeSessionId, sessions]);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isThinking]);

  // Scroll listener for scroll-to-bottom arrow
  const handleScroll = () => {
    if (!messagesContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    if (scrollHeight - scrollTop - clientHeight > 160) {
      setShowScrollBottom(true);
    } else {
      setShowScrollBottom(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const trendingPrompts = [
    { 
      id: '#1', 
      icon: <IconFish size={20} color="#0284C7" />, 
      bgClass: 'v-card-icon--cyan',
      label: 'Ratnagiri PFZ & Lightning Risk', 
      prompt: 'Where is the nearest Potential Fishing Zone (PFZ) today from Ratnagiri?' 
    },
    { 
      id: '#2', 
      icon: <IconCompass size={20} color="#D97706" />, 
      bgClass: 'v-card-icon--amber',
      label: 'Kochi Morning Safety Check', 
      prompt: 'Is it safe to venture into the sea tomorrow morning off Kochi?' 
    },
    { 
      id: '#3', 
      icon: <IconWave size={20} color="#0D9488" />, 
      bgClass: 'v-card-icon--teal',
      label: 'Veraval Swell & Weather', 
      prompt: 'What are the current tide, swell, and weather conditions near Veraval?' 
    },
    { 
      id: '#4', 
      icon: <IconCyclone size={20} color="#7C3AED" />, 
      bgClass: 'v-card-icon--purple',
      label: 'Andhra Cyclone & Lightning Alert', 
      prompt: 'Are there any active lightning or cyclone alerts along the Andhra Pradesh coast?' 
    },
    { 
      id: '#5', 
      icon: <IconAnchor size={20} color="#059669" />, 
      bgClass: 'v-card-icon--emerald',
      label: 'Safe Fishing Zones Ratnagiri', 
      prompt: 'Find me safe fishing zones in Ratnagiri.' 
    },
  ];

  // Start a fresh new chat
  const handleStartNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setInputQuery('');
    setAttachedTelemetry([]);
    setDrawerOpen(false);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Select an existing chat session from history
  const handleSelectSession = (sessionId: string) => {
    setActiveSessionId(sessionId);
    const s = sessions.find((item) => item.id === sessionId);
    if (s) {
      setMessages(s.messages);
    }
    setDrawerOpen(false);
  };

  // Delete a chat session
  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (activeSessionId === sessionId) {
      handleStartNewChat();
    }
  };

  const handleCopyText = (id: string, text: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleActionClick = (act: { label: string; actionType: 'scenario' | 'view'; target: string }) => {
    if (act.actionType === 'scenario') {
      onSelectScenario(act.target);
      _onChangeView('map');
    } else if (act.actionType === 'view') {
      _onChangeView(act.target as ActiveNavView);
    }
  };

  // Attachment Handlers
  const handleAttachItem = (item: { id: string; label: string; text: string; icon?: React.ReactNode }) => {
    if (!attachedTelemetry.some((t) => t.id === item.id)) {
      setAttachedTelemetry((prev) => [...prev, item]);
      showToast(`Attached ${item.label}`);
    }
    setAttachmentMenuOpen(false);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleRemoveAttachment = (id: string) => {
    setAttachedTelemetry((prev) => prev.filter((t) => t.id !== id));
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      const snippet = content.slice(0, 300);
      handleAttachItem({
        id: `file-${Date.now()}`,
        label: file.name,
        icon: <IconFolder size={14} color="#64748B" />,
        text: `\n[Attached File: ${file.name} - ${snippet}...]`,
      });
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  // Share Dialog Actions
  const handleCopyLink = () => {
    const link = window.location.href;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(link);
      showToast('✓ Link copied to clipboard!');
      setShareModalOpen(false);
    }
  };

  const handleCopyTranscript = () => {
    const chatTitle = activeSessionId 
      ? (sessions.find((s) => s.id === activeSessionId)?.title || 'VARUNA Marine Copilot') 
      : 'VARUNA Marine Copilot';
    const textExport = `# VARUNA Marine Copilot: ${chatTitle}\nGenerated: ${new Date().toLocaleString()}\n\n` + 
      messages.map((m) => `### ${m.sender === 'user' ? '👤 Captain' : '⚓ VARUNA Copilot'} (${m.timestamp})\n${m.text}\n`).join('\n---\n');
    
    if (navigator.clipboard) {
      navigator.clipboard.writeText(textExport);
      showToast('✓ Full transcript copied to clipboard!');
      setShareModalOpen(false);
    }
  };

  const handleDownloadMarkdown = () => {
    const chatTitle = activeSessionId 
      ? (sessions.find((s) => s.id === activeSessionId)?.title || 'VARUNA Marine Copilot') 
      : 'VARUNA Marine Copilot';
    const textExport = `# VARUNA Marine Copilot Advisory: ${chatTitle}\nDate: ${new Date().toLocaleString()}\n\n` + 
      messages.map((m) => `### ${m.sender === 'user' ? '👤 Captain' : '⚓ VARUNA Copilot'} (${m.timestamp})\n${m.text}\n`).join('\n---\n');
    
    const blob = new Blob([textExport], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `VARUNA_Advisory_${Date.now()}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('✓ Downloaded Markdown advisory report');
    setShareModalOpen(false);
  };

  const handleDownloadJson = () => {
    const payload = {
      service: 'VARUNA Marine Copilot',
      session_id: activeSessionId,
      exported_at: new Date().toISOString(),
      messages,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `VARUNA_Telemetry_${Date.now()}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('✓ Downloaded JSON telemetry export');
    setShareModalOpen(false);
  };

  const isStoppedRef = useRef(false);

  const handleStopGenerating = () => {
    isStoppedRef.current = true;
    setIsThinking(false);
    showToast('Response generation stopped');
  };

  const handleSendMessage = async (textToSend?: string) => {
    const rawQuery = (textToSend || inputQuery).trim();
    if (!rawQuery && attachedTelemetry.length === 0) return;
    if (isThinking) return;

    isStoppedRef.current = false;
    const telemetryContext = attachedTelemetry.map((t) => t.text).join(' ');
    const query = telemetryContext ? `${rawQuery} ${telemetryContext}`.trim() : rawQuery;

    const userMsgId = `user-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text: query,
    };

    // Append immediately to active messages
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInputQuery('');
    setAttachedTelemetry([]);
    setIsThinking(true);

    try {
      const chatRes = await apiClient.submitChatQuery(query, currentLang);
      if (isStoppedRef.current) return;

      const assistantMsgId = `asst-${Date.now()}`;

      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        text: chatRes.text,
        thinking: chatRes.thinking,
        verdict: chatRes.verdict,
        scenarioSyncId: chatRes.scenarioSyncId,
        metrics: chatRes.metrics,
        actions: chatRes.actions,
      };

      const finalMessages = [...updatedMessages, assistantMsg];
      setMessages(finalMessages);
      setExpandedThinking((prev) => ({ ...prev, [assistantMsgId]: true }));

      // Persist in chat session history
      saveToSessionHistory(query, finalMessages, chatRes.scenarioSyncId);
    } catch (err: any) {
      if (isStoppedRef.current) return;
      console.warn('Chat assistant live fallback trigger:', err);
      generateAgentResponse(query, updatedMessages);
    } finally {
      setIsThinking(false);
    }
  };

  // Helper to persist conversation into sessions
  const saveToSessionHistory = (query: string, msgs: ChatMessage[], scenarioSyncId?: string) => {
    setSessions((prev) => {
      if (activeSessionId) {
        return prev.map((s) => {
          if (s.id === activeSessionId) {
            return {
              ...s,
              updatedAt: Date.now(),
              messages: msgs,
              lastQuery: query,
              scenarioSyncId: scenarioSyncId || s.scenarioSyncId,
            };
          }
          return s;
        });
      } else {
        const newId = `sess-${Date.now()}`;
        const newTitle = query.length > 38 ? `${query.slice(0, 38)}...` : query;
        const newSession: ChatSession = {
          id: newId,
          title: newTitle,
          createdAt: Date.now(),
          updatedAt: Date.now(),
          timeGroup: 'TODAY',
          messages: msgs,
          lastQuery: query,
          scenarioSyncId,
        };
        setActiveSessionId(newId);
        return [newSession, ...prev];
      }
    });
  };

  const generateAgentResponse = (query: string, currentMsgs: ChatMessage[]) => {
    const assistantMsgId = `asst-${Date.now()}`;
    const dynamicRes = apiClient.getMockChatResponse(query);

    const newAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      sender: 'assistant',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text: dynamicRes.text,
      thinking: dynamicRes.thinking,
      verdict: dynamicRes.verdict,
      scenarioSyncId: dynamicRes.scenarioSyncId,
      metrics: dynamicRes.metrics,
      actions: dynamicRes.actions,
    };

    const finalMessages = [...currentMsgs, newAssistantMsg];
    setMessages(finalMessages);
    setExpandedThinking((prev) => ({ ...prev, [assistantMsgId]: true }));

    saveToSessionHistory(query, finalMessages, dynamicRes.scenarioSyncId);

    if (dynamicRes.scenarioSyncId) {
      onSelectScenario(dynamicRes.scenarioSyncId);
    }
  };

  const toggleThinking = (id: string) => {
    setExpandedThinking((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  // Filtered session list based on historySearch
  const filteredSessions = sessions.filter((s) => {
    if (!historySearch.trim()) return true;
    return s.title.toLowerCase().includes(historySearch.toLowerCase()) || 
           s.lastQuery.toLowerCase().includes(historySearch.toLowerCase());
  });

  return (
    <div className="v-claude-shell">
      {/* =========================================================================
          1. CLAUDE-STYLE SIDEBAR HISTORY DRAWER (Matches Reference Image 2)
          ========================================================================= */}
      {drawerOpen && (
        <div 
          className="v-drawer-backdrop"
          onClick={() => setDrawerOpen(false)}
        />
      )}

      <aside className={`v-claude-sidebar-drawer ${drawerOpen ? 'v-claude-sidebar-drawer--open' : ''}`}>
        {/* Drawer Header */}
        <div className="v-drawer-topbar">
          <div className="v-drawer-brand">
            <span className="v-drawer-brand-icon">⚓</span>
            <span className="v-drawer-brand-text">VARUNA</span>
          </div>
          <button
            type="button"
            className="v-topbar-drawer-btn"
            onClick={() => setDrawerOpen(false)}
            aria-label="Collapse sidebar"
            title="Collapse sidebar"
          >
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <line x1="9" y1="3" x2="9" y2="21" />
              <polyline points="16 9 13 12 16 15" />
            </svg>
          </button>
        </div>

        {/* Search Chats Input */}
        <div className="v-drawer-search-wrap">
          <svg className="v-drawer-search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#64748B" strokeWidth="2.2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            className="v-drawer-search-input"
            placeholder="Search chats..."
            value={historySearch}
            onChange={(e) => setHistorySearch(e.target.value)}
          />
        </div>

        {/* Prominent + New Chat Button */}
        <div className="v-drawer-new-chat-section">
          <button
            type="button"
            className="v-drawer-new-chat-btn"
            onClick={handleStartNewChat}
          >
            <span className="v-drawer-new-chat-plus">+</span>
            <span className="v-drawer-new-chat-label">{t('newChats') || 'New chat'}</span>
          </button>
        </div>

        {/* Quick Tools Navigation */}
        <div className="v-drawer-nav-section">
          <button type="button" className="v-drawer-nav-item" onClick={() => handleSendMessage('Where is the nearest Potential Fishing Zone (PFZ) today from Ratnagiri?')}>
            <span className="v-drawer-nav-icon">🐟</span>
            <span className="v-drawer-nav-text">PFZ Hotspots</span>
          </button>
          <button type="button" className="v-drawer-nav-item" onClick={() => handleSendMessage('What are the current tide, swell, and weather conditions near Veraval?')}>
            <span className="v-drawer-nav-icon">🌊</span>
            <span className="v-drawer-nav-text">Ocean Telemetry</span>
          </button>
          <button type="button" className="v-drawer-nav-item" onClick={() => handleSendMessage('Compute safe navigation corridor and waypoint clearance from Cochin to Gulf')}>
            <span className="v-drawer-nav-icon">🧭</span>
            <span className="v-drawer-nav-text">Nautical Routes</span>
          </button>
        </div>

        {/* Grouped Chats & Tasks List */}
        <div className="v-drawer-history-scroll">
          <div className="v-drawer-section-title-row">
            <span className="v-drawer-section-title">Chats and tasks</span>
            <span className="v-drawer-count-badge">{filteredSessions.length}</span>
          </div>

          <div className="v-drawer-sessions-list">
            {filteredSessions.length === 0 ? (
              <div className="v-drawer-empty-state">
                <span>No previous chats found</span>
              </div>
            ) : (
              filteredSessions.map((s) => {
                const isActive = s.id === activeSessionId;
                return (
                  <div
                    key={s.id}
                    className={`v-drawer-session-item ${isActive ? 'v-drawer-session-item--active' : ''}`}
                    onClick={() => handleSelectSession(s.id)}
                  >
                    <span className="v-drawer-session-dot" />
                    <span className="v-drawer-session-title" title={s.title}>
                      {s.title}
                    </span>
                    <button
                      type="button"
                      className="v-drawer-delete-btn"
                      onClick={(e) => handleDeleteSession(e, s.id)}
                      title="Delete chat"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Drawer Profile Footer */}
        <div className="v-drawer-footer">
          <div className="v-drawer-user-pill">
            <div className="v-drawer-avatar">A</div>
            <div className="v-drawer-user-info">
              <span className="v-drawer-user-name">Captain Adeey</span>
              <span className="v-drawer-user-role">Hydro Engine 2.0 • Live</span>
            </div>
          </div>
        </div>
      </aside>

      {/* =========================================================================
          2. MAIN CLAUDE-STYLE CHAT WORKSPACE (Matches Reference Image 1)
          ========================================================================= */}
      <main className="v-claude-main-area">
        {/* Top Claude Chat Bar */}
        <header className="v-claude-topbar">
          <div className="v-topbar-left">
            {!drawerOpen && (
              <button
                type="button"
                className="v-topbar-drawer-btn"
                onClick={() => setDrawerOpen(true)}
                aria-label="Open sidebar"
                title="Open sidebar"
              >
                <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <line x1="9" y1="3" x2="9" y2="21" />
                </svg>
              </button>
            )}

            {/* Title Dropdown */}
            <div className="v-model-selector-wrap">
              <button
                type="button"
                className="v-model-selector-btn"
                onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
              >
                <span className="v-model-title">VARUNA</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>

              {modelDropdownOpen && (
                <div className="v-model-dropdown-menu">
                  <button 
                    type="button" 
                    className={`v-model-dropdown-item ${selectedEngine === 'Hydro Engine 2.0' ? 'v-model-dropdown-item--active' : ''}`}
                    onClick={() => { setSelectedEngine('Hydro Engine 2.0'); setModelDropdownOpen(false); }}
                  >
                    <div className="v-item-title">Hydro Engine 2.0</div>
                    <div className="v-item-sub">FastAPI Marine Multi-Agent Network</div>
                  </button>
                  <button 
                    type="button" 
                    className={`v-model-dropdown-item ${selectedEngine === 'Statutory RAG Legal' ? 'v-model-dropdown-item--active' : ''}`}
                    onClick={() => { setSelectedEngine('Statutory RAG Legal'); setModelDropdownOpen(false); }}
                  >
                    <div className="v-item-title">Statutory Legal Advisor</div>
                    <div className="v-item-sub">MFRA, Wildlife Protection, Monsoon Ban</div>
                  </button>
                </div>
              )}
            </div>

            {/* Quick + New Chat Pill in Topbar */}
            <button
              type="button"
              className="v-topbar-new-chat-pill"
              onClick={handleStartNewChat}
              title="Start a new chat conversation"
            >
              <span className="v-pill-plus">+</span>
              <span>New</span>
            </button>
          </div>

          <div className="v-topbar-right">
            {/* Share / Export button */}
            <button
              type="button"
              className="v-topbar-action-btn"
              onClick={() => setShareModalOpen(true)}
              title="Share conversation"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                <polyline points="16 6 12 2 8 6" />
                <line x1="12" y1="2" x2="12" y2="15" />
              </svg>
              <span className="v-share-text">{t('share') || 'Share'}</span>
            </button>
          </div>
        </header>

        {/* Active Conversation Messages Stream */}
        <div 
          ref={messagesContainerRef}
          className="v-claude-stream-body"
          onScroll={handleScroll}
        >
          {messages.length === 0 ? (
            /* =========================================================================
               WELCOME / DISCOVERY HERO (When starting a fresh conversation)
               ========================================================================= */
            <div className="v-claude-welcome-container">
              <div className="v-claude-welcome-badge">
                <IconAnchor size={14} color="#0284C7" />
                <span>Marine Intelligence Copilot</span>
              </div>

              <h1 className="v-claude-welcome-heading">
                Where Coastal Wisdom Meets Real-Time Intelligence
              </h1>
              <p className="v-claude-welcome-subheading">
                Real-time safety evaluations, PFZ chlorophyll hotspots, deterministic IMD rules, and least-fuel passage routing.
              </p>

              {/* Sample Prompt Chips (All 5 PDF Test Scenarios) */}
              <div className="v-claude-chips-grid">
                {trendingPrompts.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className="v-claude-prompt-card"
                    onClick={() => handleSendMessage(item.prompt)}
                  >
                    <span className={`v-card-icon ${item.bgClass}`}>{item.icon}</span>
                    <div className="v-card-text-col">
                      <span className="v-card-label">{item.label}</span>
                      <span className="v-card-query">{item.prompt}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* =========================================================================
               ACTIVE MESSAGE THREAD
               ========================================================================= */
            <div className="v-claude-messages-wrapper">
              {messages.map((msg) => {
                const isAsst = msg.sender === 'assistant';
                return (
                  <div
                    key={msg.id}
                    className={`v-claude-msg-row ${isAsst ? 'v-claude-msg-row--asst' : 'v-claude-msg-row--user'}`}
                  >
                    {isAsst && (
                      <div className="v-claude-avatar-asst">
                        <IconAnchor size={15} color="#FFFFFF" />
                      </div>
                    )}

                    <div className={`v-claude-bubble ${isAsst ? 'v-claude-bubble--asst' : 'v-claude-bubble--user'}`}>
                      {/* Assistant Multi-Agent Thinking Accordion */}
                      {isAsst && msg.thinking && msg.thinking.length > 0 && (
                        <div className="v-thinking-collapsible">
                          <button
                            type="button"
                            className="v-thinking-toggle"
                            onClick={() => toggleThinking(msg.id)}
                          >
                            <div className="v-thinking-toggle-left">
                              <span className="v-thinking-pulse-dot" />
                              <span>Thought for 2 seconds (Hydro Engine)</span>
                            </div>
                            <svg 
                              className={`v-thinking-chevron ${expandedThinking[msg.id] ? 'v-thinking-chevron--open' : ''}`} 
                              width="14" 
                              height="14" 
                              viewBox="0 0 24 24" 
                              fill="none" 
                              stroke="currentColor" 
                              strokeWidth="2.5"
                            >
                              <polyline points="6 9 12 15 18 9" />
                            </svg>
                          </button>

                          {expandedThinking[msg.id] && (
                            <div className="v-thinking-body">
                              {msg.thinking.map((step, sIdx) => (
                                <div key={sIdx} className="v-thinking-step">
                                  <span className="v-step-bullet">•</span>
                                  <span>{step}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Main Message Text — Structured Markdown, Tables & Oceanic Cards */}
                      <div className="v-claude-text-content">
                        <FormattedChatContent text={msg.text} />
                      </div>

                      {/* Verdict Status Tag */}
                      {msg.verdict && (
                        <div className="v-msg-verdict-row">
                          <span className={`v-verdict-badge v-verdict-badge--${msg.verdict.toLowerCase()}`}>
                            ● {msg.verdict === 'SAFE' ? 'SAFE TO SAIL' : msg.verdict === 'CAUTION' ? 'CAUTION ADVISED' : 'UNSAFE / DANGER'}
                          </span>
                        </div>
                      )}

                      {/* Metrics Cluster */}
                      {msg.metrics && (
                        <div className="v-metrics-cluster">
                          {msg.metrics.wave && (
                            <div className="v-metric-tag">
                              <span className="v-metric-key">Wave:</span>
                              <span className="v-metric-val">{msg.metrics.wave}</span>
                            </div>
                          )}
                          {msg.metrics.wind && (
                            <div className="v-metric-tag">
                              <span className="v-metric-key">Wind:</span>
                              <span className="v-metric-val">{msg.metrics.wind}</span>
                            </div>
                          )}
                          {msg.metrics.pfz && (
                            <div className="v-metric-tag">
                              <span className="v-metric-key">PFZ:</span>
                              <span className="v-metric-val">{msg.metrics.pfz}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Action Buttons */}
                      {msg.actions && msg.actions.length > 0 && (
                        <div className="v-actions-pill-row">
                          {msg.actions.map((act, aIdx) => (
                            <button
                              key={aIdx}
                              type="button"
                              className="v-action-btn"
                              onClick={() => handleActionClick(act)}
                            >
                              <span>{act.label}</span>
                              <span className="v-action-arrow">→</span>
                            </button>
                          ))}
                        </div>
                      )}

                      {/* Message Footer Toolbar */}
                      {isAsst && (
                        <div className="v-msg-footer-bar">
                          <button
                            type="button"
                            className="v-copy-msg-btn"
                            onClick={() => handleCopyText(msg.id, msg.text)}
                            title="Copy response"
                          >
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                            </svg>
                            <span>{copiedId === msg.id ? 'Copied' : 'Copy'}</span>
                          </button>
                          <span className="v-model-tag">VARUNA • Hydro 2.0</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Thinking Aurora Animation */}
              {isThinking && (
                <div className="v-claude-msg-row v-claude-msg-row--asst">
                  <div className="v-claude-avatar-asst">
                    <IconSparkles size={15} color="#FFFFFF" />
                  </div>
                  <div className="v-claude-bubble v-claude-bubble--asst v-bubble-loading">
                    <div className="v-thinking-dots-anim">
                      <span className="v-anim-dot" />
                      <span className="v-anim-dot" />
                      <span className="v-anim-dot" />
                    </div>
                    <span className="v-loading-label">Evaluating oceanographic telemetry & deterministic safety rules...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Scroll to Bottom Floating Button */}
        {showScrollBottom && (
          <button
            type="button"
            className="v-scroll-bottom-fab"
            onClick={scrollToBottom}
            aria-label="Scroll to bottom"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <polyline points="19 12 12 19 5 12" />
            </svg>
          </button>
        )}

        {/* =========================================================================
            3. CLAUDE / GROK STYLE FLOATING COMPOSER CARD
            ========================================================================= */}
        <div className="v-claude-composer-wrapper">
          {/* Hidden File Input for Telemetry Logs */}
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".csv,.json,.txt,.log"
            onChange={handleFileUpload}
          />

          <form
            className="v-claude-composer-card"
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
          >
            {/* Attachment Chips Row */}
            {attachedTelemetry.length > 0 && (
              <div className="v-attachment-chips-row">
                {attachedTelemetry.map((item) => (
                  <span key={item.id} className="v-attachment-chip">
                    {item.icon && <span className="v-chip-icon">{item.icon}</span>}
                    <span>{item.label}</span>
                    <button
                      type="button"
                      className="v-attachment-chip-remove"
                      onClick={() => handleRemoveAttachment(item.id)}
                      title="Remove attachment"
                    >
                      ✕
                    </button>
                  </span>
                ))}
              </div>
            )}

            <input
              ref={inputRef}
              type="text"
              className="v-claude-input"
              placeholder={t('typeMessage') || 'Write a message or ask about marine safety...'}
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={isThinking}
            />

            <div className="v-composer-bottom-row">
              <div className="v-composer-actions-left">
                <span className="v-composer-hint">Press Enter ↵ to send</span>
              </div>

              <div className="v-composer-actions-right">
                {isThinking ? (
                  <button
                    type="button"
                    className="v-claude-send-btn v-claude-send-btn--stop"
                    onClick={handleStopGenerating}
                    title="Stop generating response"
                    aria-label="Stop response"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                      <rect x="4" y="4" width="16" height="16" rx="2" />
                    </svg>
                  </button>
                ) : (
                  <button
                    type="submit"
                    className="v-claude-send-btn"
                    disabled={!inputQuery.trim() && attachedTelemetry.length === 0}
                    title="Send message"
                    aria-label="Send message"
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="22" y1="2" x2="11" y2="13" />
                      <polygon points="22 2 15 22 11 13 2 9 22 2" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          </form>

          {/* Claude / Grok Style Footer Disclaimer */}
          <div className="v-claude-footer-disclaimer">
            <span>VARUNA Copilot provides advisory intelligence backed by INCOIS & IMD deterministic rules.</span>
            <span className="v-footer-engine-tag">VARUNA • Hydro Engine</span>
          </div>
        </div>
      </main>

      {/* Share Modal Dialog */}
      {shareModalOpen && (
        <div className="v-share-modal-backdrop" onClick={() => setShareModalOpen(false)}>
          <div className="v-share-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="v-share-modal-header">
              <h3 className="v-share-modal-title">Share Oceanic Advisory</h3>
              <button
                type="button"
                className="v-share-modal-close"
                onClick={() => setShareModalOpen(false)}
                title="Close"
              >
                ✕
              </button>
            </div>
            <div className="v-share-modal-body">
              <div className="v-share-topic-preview">
                <div className="v-share-topic-title">
                  {activeSessionId 
                    ? (sessions.find((s) => s.id === activeSessionId)?.title || 'Marine Advisory Conversation')
                    : 'Current Advisory Session'}
                </div>
                <div className="v-share-topic-sub">
                  {messages.length} messages • Generated with INCOIS & IMD Rule Engine
                </div>
              </div>

              <div className="v-share-options-grid">
                <button
                  type="button"
                  className="v-share-option-btn"
                  onClick={handleCopyLink}
                >
                  <span className="v-share-option-icon v-share-option-icon--blue"><IconLink size={18} color="#0284C7" /></span>
                  <span>Copy Shareable Link</span>
                </button>

                <button
                  type="button"
                  className="v-share-option-btn"
                  onClick={handleCopyTranscript}
                >
                  <span className="v-share-option-icon v-share-option-icon--teal"><IconClipboard size={18} color="#0D9488" /></span>
                  <span>Copy Markdown Transcript</span>
                </button>

                <button
                  type="button"
                  className="v-share-option-btn"
                  onClick={handleDownloadMarkdown}
                >
                  <span className="v-share-option-icon v-share-option-icon--purple"><IconDownload size={18} color="#7C3AED" /></span>
                  <span>Download Advisory Report (.md)</span>
                </button>

                <button
                  type="button"
                  className="v-share-option-btn"
                  onClick={handleDownloadJson}
                >
                  <span className="v-share-option-icon v-share-option-icon--indigo"><IconDatabase size={18} color="#4F46E5" /></span>
                  <span>Download Telemetry JSON (.json)</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating Animated Toast Notification */}
      {toastMessage && (
        <div className="v-chat-toast">
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
};
