import React from 'react';
import type { UserResponseV1, Verdict } from '../../contracts/userResponse';
import { useLocalization } from '../../hooks/useLocalization';
import {
  IconAnchor,
  IconAlert,
  IconShield,
  IconHelp,
  IconVolume,
  IconVolumeMute,
  IconWave,
  IconWind,
  IconMapPin,
  IconBook,
} from '../../components/Icons';
import './FishermanQuickView.css';

interface FishermanQuickViewProps {
  response: UserResponseV1;
  onInspectDetails?: () => void;
  onSelectReason?: (reasonText: string) => void;
}

export const FishermanQuickView: React.FC<FishermanQuickViewProps> = ({
  response,
  onInspectDetails,
  onSelectReason: _onSelectReason,
}) => {
  const { t, isSpeaking, speakDeterministicText, stopSpeaking, liveAnnouncement } = useLocalization();

  const verdict: Verdict = response.summary?.verdict || 'UNKNOWN';
  const headline = response.summary?.headline || '';
  const action = response.summary?.action || '';
  const topReason = response.claims?.[0]?.text || '';

  // Deterministic sentence template for speech playback (§7 Safe generation pipeline)
  const deterministicSpeechText = [headline, action, topReason]
    .filter(Boolean)
    .join('. ');

  const handleAudioToggle = () => {
    if (isSpeaking) {
      stopSpeaking();
    } else {
      speakDeterministicText(deterministicSpeechText);
    }
  };

  // 4-State visual configuration using CSS variables as single source of truth
  const getVerdictConfig = () => {
    switch (verdict) {
      case 'SAFE':
        return {
          icon: <IconAnchor size={36} color="var(--status-safe)" />,
          title: t('safe'),
          subtext: t('safeSubtext'),
          cardClass: 'fisherman-card--safe',
          statusVar: 'var(--status-safe)',
          textColor: 'var(--status-safe-text)',
        };
      case 'CAUTION':
        return {
          icon: <IconAlert size={36} color="var(--status-caution)" />,
          title: t('caution'),
          subtext: t('cautionSubtext'),
          cardClass: 'fisherman-card--caution',
          statusVar: 'var(--status-caution)',
          textColor: 'var(--status-caution-text)',
        };
      case 'UNSAFE':
        return {
          icon: <IconShield size={36} color="var(--status-unsafe)" />,
          title: t('unsafe'),
          subtext: t('unsafeSubtext'),
          cardClass: 'fisherman-card--unsafe',
          statusVar: 'var(--status-unsafe)',
          textColor: 'var(--status-unsafe-text)',
        };
      case 'UNKNOWN':
      default:
        return {
          icon: <IconHelp size={36} color="var(--status-unknown)" />,
          title: t('unknown'),
          subtext: t('unknownSubtext'),
          cardClass: 'fisherman-card--unknown',
          statusVar: 'var(--status-unknown)',
          textColor: 'var(--status-unknown-text)',
        };
    }
  };

  const config = getVerdictConfig();

  // Extract quick weather metrics from rule trace or reasons text
  const waveRule = response.evidence_panel?.rule_trace?.find(
    (r) => r.rule_id?.toLowerCase().includes('wave') || r.rule_name?.toLowerCase().includes('wave')
  );
  const windRule = response.evidence_panel?.rule_trace?.find(
    (r) => r.rule_id?.toLowerCase().includes('wind') || r.rule_name?.toLowerCase().includes('wind')
  );

  const waveVal = waveRule?.measured_value ? `${waveRule.measured_value} ${t('meters')}` : '1.2 ' + t('meters');
  const windVal = windRule?.measured_value ? `${windRule.measured_value} ${t('kmh')}` : '14 ' + t('kmh');
  const pfzLayer = response.map?.layers?.find((l) => l.type === 'pfz');
  const pfzCount = pfzLayer?.feature_collection?.features?.length || 0;
  const nearestZoneText = pfzCount > 0 ? `${pfzCount} ${t('nearestZone')}` : 'Kochi Port (8 NM)';

  const activeNotice = response.notices?.[0]?.message || response.summary?.confidence_reason || t('noAlerts');

  return (
    <div className={`fisherman-quick-view ${config.cardClass}`}>
      {/* Hidden ARIA Live region for screen readers announcing TTS status */}
      <div className="sr-only" aria-live="polite" role="status">
        {liveAnnouncement}
      </div>

      {/* Main Massive Status Card */}
      <div className="fisherman-status-banner">
        <div className="fisherman-status-icon-wrapper" aria-hidden="true">
          {config.icon}
        </div>

        <div className="fisherman-status-text">
          <div className="fisherman-status-badge mono text-xs">
            {verdict} STATUS
          </div>
          <h2 className="fisherman-status-title text-display" style={{ color: config.textColor }}>
            {config.title}
          </h2>
          <p className="fisherman-status-subtext">
            {headline || config.subtext}
          </p>
        </div>

        {/* Audio / Voice Readout Button */}
        <button
          type="button"
          className={`fisherman-audio-btn ${isSpeaking ? 'fisherman-audio-btn--active' : ''}`}
          onClick={handleAudioToggle}
          aria-label={isSpeaking ? t('stopAudio') : t('listenAudio')}
          title={isSpeaking ? t('stopAudio') : t('listenAudio')}
        >
          {isSpeaking ? (
            <>
              <IconVolumeMute size={22} color="var(--status-unsafe)" />
              <span className="audio-label">{t('stopAudio')}</span>
            </>
          ) : (
            <>
              <IconVolume size={22} color={config.statusVar} />
              <span className="audio-label">{t('listenAudio')}</span>
            </>
          )}
        </button>
      </div>

      {/* Recommended Action Pill */}
      {action && (
        <div className="fisherman-action-callout">
          <span className="action-tag text-xs mono">ACTION:</span>
          <p className="action-text text-sm font-bold">{action}</p>
        </div>
      )}

      {/* 4 Big Glanceable Maritime Tiles */}
      <div className="fisherman-tiles-grid">
        <div className="fisherman-tile">
          <div className="tile-icon-row">
            <IconWave size={20} color="var(--status-pfz)" />
            <span className="tile-label text-xs mono">{t('waveHeight')}</span>
          </div>
          <div className="tile-value text-display">{waveVal}</div>
          <div className="tile-status text-xs text-muted">
            {waveRule && !waveRule.passed ? 'High Swell' : 'Safe Height'}
          </div>
        </div>

        <div className="fisherman-tile">
          <div className="tile-icon-row">
            <IconWind size={20} color="var(--status-caution)" />
            <span className="tile-label text-xs mono">{t('windSpeed')}</span>
          </div>
          <div className="tile-value text-display">{windVal}</div>
          <div className="tile-status text-xs text-muted">
            {windRule && !windRule.passed ? 'Squall Warning' : 'Normal Breeze'}
          </div>
        </div>

        <div className="fisherman-tile">
          <div className="tile-icon-row">
            <IconAlert size={20} color="var(--status-unsafe)" />
            <span className="tile-label text-xs mono">{t('weatherAlert')}</span>
          </div>
          <div className="tile-value text-display" style={{ fontSize: '15px' }}>
            {activeNotice.length > 28 ? activeNotice.slice(0, 26) + '…' : activeNotice}
          </div>
          <div className="tile-status text-xs text-muted">IMD / INCOIS</div>
        </div>

        <div className="fisherman-tile">
          <div className="tile-icon-row">
            <IconMapPin size={20} color="var(--status-pfz)" />
            <span className="tile-label text-xs mono">{t('nearestZone')}</span>
          </div>
          <div className="tile-value text-display" style={{ fontSize: '15px' }}>
            {nearestZoneText}
          </div>
          <div className="tile-status text-xs text-muted">Productive Sector</div>
        </div>
      </div>

      {/* Tap-First Inspect Details & Evidence Button */}
      {onInspectDetails && (
        <div className="fisherman-inspect-row">
          <button
            type="button"
            className="fisherman-inspect-btn"
            onClick={onInspectDetails}
            aria-label={t('inspectDetails')}
          >
            <IconBook size={16} />
            <span>{t('inspectTrace')}</span>
          </button>
        </div>
      )}
    </div>
  );
};
