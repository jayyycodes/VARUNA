import safeComplete from './safe_complete.json';
import cautionWave from './caution_wave.json';
import unsafeCyclone from './unsafe_cyclone.json';
import pfzButUnsafe from './pfz_but_unsafe.json';
import geofenceRestricted from './geofence_restricted.json';
import weatherStale from './weather_stale.json';
import indeterminate from './indeterminate.json';
import ragCited from './rag_cited.json';
import ragInsufficient from './rag_insufficient.json';
import invalidGeometry from './invalid_geometry.json';

import { UserResponseV1Schema } from '../contracts/userResponse';
import type { UserResponseV1 } from '../contracts/userResponse';

export interface ScenarioFixture {
  id: string;
  name: string;
  description: string;
  data: unknown;
  expectedVerdict: 'SAFE' | 'CAUTION' | 'UNSAFE' | 'UNKNOWN' | 'INVALID';
  expectedStatus: 'complete' | 'degraded' | 'indeterminate' | 'error' | 'INVALID';
}

export const FIXTURES: Record<string, ScenarioFixture> = {
  safe_complete: {
    id: 'safe_complete',
    name: '1. Safe / Complete (Ratnagiri)',
    description: 'Normal coastal conditions, all 4 domains current within 30 min, active PFZ.',
    data: safeComplete,
    expectedVerdict: 'SAFE',
    expectedStatus: 'complete',
  },
  caution_wave: {
    id: 'caution_wave',
    name: '2. Caution / High Wave (Kochi)',
    description: 'Wave swell 2.8m > 2.5m threshold; medium confidence due to unavailable lightning feed.',
    data: cautionWave,
    expectedVerdict: 'CAUTION',
    expectedStatus: 'complete',
  },
  unsafe_cyclone: {
    id: 'unsafe_cyclone',
    name: '3. Unsafe / Cyclone (Visakhapatnam)',
    description: 'Severe cyclonic storm warning, 48 kt winds, 5.2m waves. Mandatory zero-departure.',
    data: unsafeCyclone,
    expectedVerdict: 'UNSAFE',
    expectedStatus: 'complete',
  },
  pfz_but_unsafe: {
    id: 'pfz_but_unsafe',
    name: '4. PFZ Productive but Unsafe (Ratnagiri)',
    description: 'High chlorophyll PFZ zone, but 34 kt squall. Favorable fish aggregations do NOT override risk.',
    data: pfzButUnsafe,
    expectedVerdict: 'UNSAFE',
    expectedStatus: 'complete',
  },
  geofence_restricted: {
    id: 'geofence_restricted',
    name: '5. Geofence Restricted (Malvan MPA)',
    description: 'Target coordinates inside Malvan Marine Sanctuary No-Take Core Zone. Regulatory violation.',
    data: geofenceRestricted,
    expectedVerdict: 'UNSAFE',
    expectedStatus: 'complete',
  },
  weather_stale: {
    id: 'weather_stale',
    name: '6. Weather Stale (Veraval)',
    description: 'Weather telemetry 6 hours old. Verdict clamped to UNKNOWN, decision_status: degraded.',
    data: weatherStale,
    expectedVerdict: 'UNKNOWN',
    expectedStatus: 'degraded',
  },
  indeterminate: {
    id: 'indeterminate',
    name: '7. Indeterminate Sensor Blackout (Paradip)',
    description: 'Missing critical wind and wave data. System refuses to issue reassuring verdict.',
    data: indeterminate,
    expectedVerdict: 'UNKNOWN',
    expectedStatus: 'indeterminate',
  },
  rag_cited: {
    id: 'rag_cited',
    name: '8. RAG Cited Advisory (Mandapam)',
    description: 'Regulation inquiry with exact statutory citations, Tamil excerpts, and rule traces.',
    data: ragCited,
    expectedVerdict: 'SAFE',
    expectedStatus: 'complete',
  },
  rag_insufficient: {
    id: 'rag_insufficient',
    name: '9. RAG Insufficient Evidence (Lakshadweep)',
    description: 'Query with no verified statutory basis; exact fallback copy displayed.',
    data: ragInsufficient,
    expectedVerdict: 'UNKNOWN',
    expectedStatus: 'degraded',
  },
  invalid_geometry: {
    id: 'invalid_geometry',
    name: '10. Invalid Geometry (Regression Test)',
    description: 'Malformed schema payload designed to fail Zod validation.',
    data: invalidGeometry,
    expectedVerdict: 'INVALID',
    expectedStatus: 'INVALID',
  },
};

/**
 * Validates a fixture against the canonical UserResponseV1Schema.
 */
export function validateFixture(fixtureData: unknown): {
  success: boolean;
  data?: UserResponseV1;
  error?: string;
} {
  const result = UserResponseV1Schema.safeParse(fixtureData);
  if (result.success) {
    return { success: true, data: result.data };
  } else {
    return {
      success: false,
      error: result.error.issues.map((i) => `[${i.path.join('.')}] ${i.message}`).join('; '),
    };
  }
}

export {
  safeComplete,
  cautionWave,
  unsafeCyclone,
  pfzButUnsafe,
  geofenceRestricted,
  weatherStale,
  indeterminate,
  ragCited,
  ragInsufficient,
  invalidGeometry,
};
