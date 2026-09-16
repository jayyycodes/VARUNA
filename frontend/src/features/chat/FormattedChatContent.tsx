import React from 'react';
import './FormattedChatContent.css';

interface FormattedChatContentProps {
  text: string;
}

/**
 * Helper to parse inline markdown (bold, italic, code, badges) into React elements.
 */
function renderInline(text: string): React.ReactNode {
  if (!text) return null;

  // Split by bold (**text**), code (`code`), or italic (*text*)
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*.*?\*\*|`.*?`|\*.*?\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    const token = match[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      const inner = token.slice(2, -2);
      // Special badge styling for verdicts
      if (['SAFE', 'SAFE TO SAIL'].includes(inner.toUpperCase())) {
        parts.push(<span key={match.index} className="v-inline-badge v-inline-badge--safe">{inner}</span>);
      } else if (['CAUTION', 'CAUTION ADVISED'].includes(inner.toUpperCase())) {
        parts.push(<span key={match.index} className="v-inline-badge v-inline-badge--caution">{inner}</span>);
      } else if (['UNSAFE', 'DO NOT GO', 'DANGER'].includes(inner.toUpperCase())) {
        parts.push(<span key={match.index} className="v-inline-badge v-inline-badge--unsafe">{inner}</span>);
      } else {
        parts.push(<strong key={match.index} className="v-chat-strong">{renderInline(inner)}</strong>);
      }
    } else if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(<code key={match.index} className="v-chat-code">{token.slice(1, -1)}</code>);
    } else if (token.startsWith('*') && token.endsWith('*')) {
      parts.push(<em key={match.index} className="v-chat-em">{token.slice(1, -1)}</em>);
    }

    lastIndex = match.index + token.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

/**
 * FormattedChatContent — Structured Markdown & Table Renderer for Marine Copilot Responses.
 * Eliminates raw hashes (###), unformatted pipes (|), and irregular linebreaks.
 */
export const FormattedChatContent: React.FC<FormattedChatContentProps> = ({ text }) => {
  if (!text) return null;

  // Clean raw artifacts like "# # #" or trailing cutoffs
  const cleanedText = text
    .replace(/^#\s*#\s*#\s*/gm, '### ')
    .replace(/^#\s*#\s*/gm, '## ')
    .trim();

  const lines = cleanedText.split('\n');
  const elements: React.ReactNode[] = [];

  let i = 0;
  while (i < lines.length) {
    const rawLine = lines[i];
    const line = rawLine.trim();

    // 1. Skip empty lines
    if (!line) {
      i++;
      continue;
    }

    // 2. Horizontal Rules (--- or ***)
    if (/^(\-{3,}|\*{3,}|_{3,})$/.test(line)) {
      elements.push(<hr key={`hr-${i}`} className="v-chat-divider" />);
      i++;
      continue;
    }

    // 3. Headings (###, ##, #)
    const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const title = headingMatch[2].replace(/^[*_]+|[*_]+$/g, '').trim();
      
      if (level === 1) {
        elements.push(<h2 key={`h1-${i}`} className="v-chat-h1">{title}</h2>);
      } else if (level === 2) {
        elements.push(<h3 key={`h2-${i}`} className="v-chat-h2">{title}</h3>);
      } else {
        elements.push(<h4 key={`h3-${i}`} className="v-chat-h3">{title}</h4>);
      }
      i++;
      continue;
    }

    // 4. Markdown Tables (| Col 1 | Col 2 | ...)
    if (line.startsWith('|') && line.endsWith('|')) {
      const tableRows: string[][] = [];
      let isHeader = true;
      let colHeaders: string[] = [];

      while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
        const rowText = lines[i].trim();
        // Check if delimiter row (|---|---|)
        if (/^\|[\s\-:|]+\|$/.test(rowText)) {
          isHeader = false;
          i++;
          continue;
        }

        const cells = rowText
          .slice(1, -1)
          .split('|')
          .map((c) => c.trim());

        if (isHeader) {
          colHeaders = cells;
          isHeader = false;
        } else {
          tableRows.push(cells);
        }
        i++;
      }

      if (colHeaders.length > 0 || tableRows.length > 0) {
        elements.push(
          <div key={`tbl-wrap-${i}`} className="v-chat-table-container">
            <table className="v-chat-table">
              {colHeaders.length > 0 && (
                <thead>
                  <tr>
                    {colHeaders.map((header, hIdx) => (
                      <th key={`th-${hIdx}`}>{renderInline(header)}</th>
                    ))}
                  </tr>
                </thead>
              )}
              <tbody>
                {tableRows.map((row, rIdx) => (
                  <tr key={`tr-${rIdx}`}>
                    {row.map((cell, cIdx) => {
                      const trimmed = cell.trim();
                      // Check for productivity score cell (e.g. 0.710)
                      const isScore = /^\(?0\.\d+\)?$/.test(trimmed);
                      // Check for Gear Compatibility "Yes" / "No"
                      const isYes = /^yes$/i.test(trimmed);
                      const isNo = /^no$/i.test(trimmed);

                      return (
                        <td key={`td-${rIdx}-${cIdx}`} className={`v-table-col-${cIdx}`}>
                          {isScore ? (
                            <span className="v-table-score-badge">{trimmed}</span>
                          ) : isYes ? (
                            <span className="v-table-gear-badge v-table-gear-badge--yes">✓ Yes</span>
                          ) : isNo ? (
                            <span className="v-table-gear-badge v-table-gear-badge--no">✕ No</span>
                          ) : (
                            renderInline(trimmed)
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }
      continue;
    }

    // 5. Unordered List Items (- , * , • )
    if (/^[\-\*•]\s+/.test(line)) {
      const listItems: string[] = [];
      while (i < lines.length && /^[\-\*•]\s+/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^[\-\*•]\s+/, ''));
        i++;
      }

      elements.push(
        <ul key={`ul-${i}`} className="v-chat-list">
          {listItems.map((item, lIdx) => (
            <li key={`li-${lIdx}`} className="v-chat-list-item">
              <span className="v-chat-list-dot" />
              <div className="v-chat-list-content">{renderInline(item)}</div>
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 6. Ordered List Items (1. , 2. )
    if (/^\d+\.\s+/.test(line)) {
      const numItems: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        numItems.push(lines[i].trim().replace(/^\d+\.\s+/, ''));
        i++;
      }

      elements.push(
        <ol key={`ol-${i}`} className="v-chat-num-list">
          {numItems.map((item, nIdx) => (
            <li key={`nli-${nIdx}`} className="v-chat-num-item">
              <span className="v-chat-num-badge">{nIdx + 1}</span>
              <div className="v-chat-list-content">{renderInline(item)}</div>
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // 7. Safety Verdict Highlight Callout Card
    if (line.toLowerCase().includes('safety verdict') || line.toLowerCase().includes('operational safety verdict')) {
      elements.push(
        <div key={`verdict-${i}`} className="v-chat-verdict-callout">
          <div className="v-verdict-callout-icon">🛡️</div>
          <div className="v-verdict-callout-text">{renderInline(line)}</div>
        </div>
      );
      i++;
      continue;
    }

    // 8. Standard Paragraph
    elements.push(
      <p key={`p-${i}`} className="v-chat-paragraph">
        {renderInline(line)}
      </p>
    );
    i++;
  }

  return <div className="v-formatted-chat-body">{elements}</div>;
};
