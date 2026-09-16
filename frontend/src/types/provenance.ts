export interface DataProvenance {
  source: 'live' | 'fixture' | 'cache';
  endpoint: string;
  query_run_id: string;
  httpStatus: number;
  latencyMs: number;
  timestamp: string;
  validationPassed: boolean;
  validationError?: string | null;
  fixtureName?: string;
  renderCompletedAt?: string;
}
