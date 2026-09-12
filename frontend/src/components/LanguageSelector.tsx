import React from 'react';
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

  return (
    <div
      className="lang-selector"
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
  );
};
