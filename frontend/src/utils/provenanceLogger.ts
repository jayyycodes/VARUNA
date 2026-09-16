/**
 * Structured, sanitized request logging keyed by query_run_id.
 * Adheres strictly to security & safety policies:
 * - NO raw credentials, tokens, or authorization headers logged.
 * - NO internal stack traces surfaced to client console.
 * - High-integrity audit trail for data provenance verification.
 */

export type ProvenanceLogStage = 
  | 'REQUEST_START' 
  | 'RESPONSE_RECEIVED' 
  | 'VALIDATION_PASS' 
  | 'VALIDATION_FAIL' 
  | 'RENDER_COMPLETE';

export interface ProvenanceLogEntry {
  query_run_id: string;
  stage: ProvenanceLogStage;
  timestamp: string;
  endpoint?: string;
  source?: 'live' | 'fixture' | 'cache';
  httpStatus?: number;
  latencyMs?: number;
  component?: string;
  details?: string;
}

class ProvenanceLogger {
  private logBuffer: ProvenanceLogEntry[] = [];
  private readonly maxBufferSize = 200;

  private sanitize(input: string | undefined): string | undefined {
    if (!input) return undefined;
    // Strip possible API keys, bearer tokens, or password queries
    return input
      .replace(/bearer\s+[a-zA-Z0-9_\-\.]+/gi, 'bearer [REDACTED]')
      .replace(/(key|token|secret|password)=([^\s&]+)/gi, '$1=[REDACTED]');
  }

  public log(entry: Omit<ProvenanceLogEntry, 'timestamp'>): ProvenanceLogEntry {
    const sanitizedEntry: ProvenanceLogEntry = {
      ...entry,
      endpoint: this.sanitize(entry.endpoint),
      details: this.sanitize(entry.details),
      timestamp: new Date().toISOString(),
    };

    this.logBuffer.unshift(sanitizedEntry);
    if (this.logBuffer.length > this.maxBufferSize) {
      this.logBuffer.pop();
    }

    // Pretty-print to dev console
    if (import.meta.env.DEV) {
      const stageColors: Record<ProvenanceLogStage, string> = {
        REQUEST_START: '#3B82F6',
        RESPONSE_RECEIVED: '#10B981',
        VALIDATION_PASS: '#059669',
        VALIDATION_FAIL: '#EF4444',
        RENDER_COMPLETE: '#8B5CF6',
      };
      
      const badgeStyle = `background: ${stageColors[sanitizedEntry.stage]}; color: #FFFFFF; font-weight: bold; padding: 2px 6px; border-radius: 4px; font-size: 10px;`;
      const idStyle = 'color: #94A3B8; font-family: monospace; font-size: 11px;';
      
      console.debug(
        `%c[VARUNA:PROVENANCE]%c %c${sanitizedEntry.stage}%c [${sanitizedEntry.query_run_id}]`,
        'background: #0F172A; color: #38BDF8; font-weight: bold; padding: 2px 4px; border-radius: 3px;',
        '',
        badgeStyle,
        idStyle,
        {
          source: sanitizedEntry.source,
          endpoint: sanitizedEntry.endpoint,
          latencyMs: sanitizedEntry.latencyMs ? `${sanitizedEntry.latencyMs.toFixed(1)}ms` : undefined,
          status: sanitizedEntry.httpStatus,
          details: sanitizedEntry.details,
        }
      );
    }

    return sanitizedEntry;
  }

  public getHistory(query_run_id?: string): ProvenanceLogEntry[] {
    if (!query_run_id) return [...this.logBuffer];
    return this.logBuffer.filter((item) => item.query_run_id === query_run_id);
  }

  public clear(): void {
    this.logBuffer = [];
  }
}

export const provenanceLogger = new ProvenanceLogger();
