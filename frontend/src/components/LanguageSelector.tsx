import React, { useState, useRef, useEffect } from 'react';
import { useLocalization } from '../hooks/useLocalization';
import type { LanguageCode } from '../hooks/useLocalization';
import './LanguageSelector.css';

interface LanguageSelectorProps {
  currentLang: LanguageCode;
  onLanguageChange: (lang: LanguageCode) => void;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  currentLang,
  onLanguageChange,
}) => {
  const { supportedLanguages } = useLocalization();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const currentOption = supportedLanguages.find((l) => l.code === currentLang) || supportedLanguages[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (code: LanguageCode) => {
    onLanguageChange(code);
    setDropdownOpen(false);
  };

  return (
    <div className="lang-selector-container" ref={containerRef}>
      {/* Desktop Multi-Pill Bar (Hidden on Mobile via CSS) */}
      <div
        className="lang-selector lang-selector--desktop"
        role="group"
        aria-label="Select Interface Language"
      >
        {supportedLanguages.map((lang) => {
          const isSelected = lang.code === currentLang;
          return (
            <button
              key={lang.code}
              type="button"
              className={`lang-btn ${isSelected ? 'lang-btn--active' : ''}`}
              onClick={() => onLanguageChange(lang.code)}
              aria-pressed={isSelected}
              aria-label={`Switch language to ${lang.label}`}
            >
              <span className="lang-native">{lang.nativeLabel}</span>
              <span className="lang-code">{lang.code.toUpperCase()}</span>
            </button>
          );
        })}
      </div>

      {/* Mobile Compact Dropdown Trigger (Shown only on Mobile) */}
      <div className="lang-selector--mobile">
        <button
          type="button"
          className="lang-trigger-btn"
          onClick={() => setDropdownOpen(!dropdownOpen)}
          aria-expanded={dropdownOpen}
          aria-label={`Current language: ${currentOption.label}. Tap to change language`}
        >
          <span className="lang-trigger-globe">🌐</span>
          <span className="lang-trigger-code">{currentOption.code.toUpperCase()}</span>
          <span className="lang-trigger-arrow">▾</span>
        </button>

        {dropdownOpen && (
          <div className="lang-dropdown-menu">
            {supportedLanguages.map((lang) => {
              const isSelected = lang.code === currentLang;
              return (
                <button
                  key={lang.code}
                  type="button"
                  className={`lang-dropdown-item ${isSelected ? 'lang-dropdown-item--active' : ''}`}
                  onClick={() => handleSelect(lang.code)}
                >
                  <span className="lang-dropdown-native">{lang.nativeLabel}</span>
                  <span className="lang-dropdown-label">({lang.label})</span>
                  {isSelected && <span className="lang-dropdown-check">✓</span>}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

