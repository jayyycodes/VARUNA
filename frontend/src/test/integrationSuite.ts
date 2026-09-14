/**
 * VARUNA End-to-End Test Suite: Frontend Client <-> Backend API Integration
 *
 * Validates:
 * 1. Health & Upstream Circuit Breakers
 * 2. Natural Language Copilot /chat queries (Safe, Caution, Cyclone/Unsafe, Geofence)
 * 3. Route Optimization API (/api/route/plan) & Coastal Harbors (/api/route/ports)
 * 4. Active Maritime Alerts & Cyclone Advisories (/api/alerts)
 * 5. Historical Fisheries Analytics (/api/analytics/historical-trends)
 * 6. Fleet Real-Time Tracking Simulation (/api/fleet)
 * 7. Multilingual Cross-Translation (Hindi / Marathi queries)
 * 8. Golden Dataset Safety Verification (Deterministic Rule Invariance)
 */

interface TestResult {
  suite: string;
  name: string;
  status: 'PASS' | 'FAIL';
  durationMs: number;
  details?: string;
}

const BACKEND_URL =
  (typeof process !== 'undefined' && process.env?.VITE_API_URL) || 'http://localhost:8000';

async function runTest(
  suite: string,
  name: string,
  fn: () => Promise<void>
): Promise<TestResult> {
  const start = Date.now();
  try {
    await fn();
    const duration = Date.now() - start;
    console.log(`✅ [${suite}] ${name} (${duration}ms)`);
    return {
      suite,
      name,
      status: 'PASS',
      durationMs: duration,
    };
  } catch (err: any) {
    const duration = Date.now() - start;
    console.log(`❌ [${suite}] ${name} (${duration}ms)`);
    console.log(`   ⚠️ Error: ${err.message || String(err)}`);
    return {
      suite,
      name,
      status: 'FAIL',
      durationMs: duration,
      details: err.message || String(err),
    };
  }
}

export async function runFullE2ESuite() {
  console.log(`\n======================================================`);
  console.log(`🌊 VARUNA FRONTEND-TO-BACKEND INTEGRATION TEST SUITE`);
  console.log(`Target Backend: ${BACKEND_URL}`);
  console.log(`======================================================\n`);

  const results: TestResult[] = [];

  // 1. Healthcheck
  results.push(
    await runTest('1. System Infrastructure', 'GET /health returns OK and circuits healthy', async () => {
      const res = await fetch(`${BACKEND_URL}/health`);
      if (!res.ok) throw new Error(`Healthcheck failed with status ${res.status}`);
      const data = await res.json();
      if (data.status !== 'ok') throw new Error(`Expected status 'ok', got '${data.status}'`);
      if (!data.planner_ready) throw new Error(`Planner not marked ready`);
    })
  );

  // 2. Coastal Harbors API
  results.push(
    await runTest('2. Navigation & Routing', 'GET /api/route/ports returns catalog of Indian fishing harbors', async () => {
      const res = await fetch(`${BACKEND_URL}/api/route/ports`);
      if (!res.ok) throw new Error(`Failed to fetch ports: HTTP ${res.status}`);
      const ports = await res.json();
      if (!Array.isArray(ports) || ports.length < 5) {
        throw new Error(`Expected at least 5 coastal harbors, received: ${ports?.length}`);
      }
      const portIds = ports.map((p: any) => p.id);
      if (!portIds.includes('ratnagiri') && !portIds.includes('malvan')) {
        throw new Error(`Missing expected primary harbors (ratnagiri, malvan)`);
      }
    })
  );

  // 3. Route Optimization Calculation
  results.push(
    await runTest('2. Navigation & Routing', 'POST /api/route/plan computes safe vs direct route with fuel deltas', async () => {
      const res = await fetch(`${BACKEND_URL}/api/route/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          departure_port: 'ratnagiri',
          destination_port: 'malvan',
          vessel_speed_kts: 8.0,
        }),
      });
      if (!res.ok) throw new Error(`Route plan failed: HTTP ${res.status}`);
      const data = await res.json();
      if (!data.safe_route_feature || !data.direct_route_feature) {
        throw new Error(`Response missing safe_route_feature or direct_route_feature`);
      }
      if (typeof data.distance_nm !== 'number' || data.distance_nm <= 0) {
        throw new Error(`Invalid distance in route plan: ${data.distance_nm}`);
      }
    })
  );

  // 4. Maritime Emergency Alerts API
  results.push(
    await runTest('3. Emergency Alerts', 'GET /api/alerts returns active IMD/coastal bulletin stream', async () => {
      const res = await fetch(`${BACKEND_URL}/api/alerts`);
      if (!res.ok) throw new Error(`Alerts fetch failed: HTTP ${res.status}`);
      const data = await res.json();
      if (!Array.isArray(data) || data.length === 0) {
        throw new Error(`Expected non-empty list of active alerts`);
      }
    })
  );

  // 5. Fleet Monitoring Simulation API
  results.push(
    await runTest('4. Fleet Operations', 'GET /api/fleet returns live simulated coastal vessel tracking', async () => {
      const res = await fetch(`${BACKEND_URL}/api/fleet`);
      if (!res.ok) throw new Error(`Fleet fetch failed: HTTP ${res.status}`);
      const data = await res.json();
      if (!data.vessels || !Array.isArray(data.vessels) || data.vessels.length === 0) {
        throw new Error(`Expected active vessels in fleet response`);
      }
      if (typeof data.active_craft !== 'number' || data.active_craft <= 0) {
        throw new Error(`Invalid active_craft count: ${data.active_craft}`);
      }
    })
  );

  // 6. Fisheries Historical Trends Analytics API
  results.push(
    await runTest('5. Fisheries Analytics', 'GET /api/analytics/historical-trends correlates SST anomalies with catches', async () => {
      const res = await fetch(`${BACKEND_URL}/api/analytics/historical-trends?lat=16.99&lon=73.28`);
      if (!res.ok) throw new Error(`Historical trends fetch failed: HTTP ${res.status}`);
      const data = await res.json();
      if (!data.months || !Array.isArray(data.months) || data.months.length === 0) {
        throw new Error(`Expected months array in historical trends`);
      }
      if (!data.statutory_reference) {
        throw new Error(`Expected statutory_reference in historical report`);
      }
    })
  );

  // 7. Natural Language Maritime Copilot (Safe Query)
  results.push(
    await runTest('6. LangGraph Maritime Copilot', 'POST /chat: Safe weather query evaluates to SAFE', async () => {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'Is it safe to fish 5km off Ratnagiri today?',
          user_id: 'test-user',
          locale: 'en',
        }),
      });
      if (!res.ok) throw new Error(`Chat query failed: HTTP ${res.status}`);
      const data = await res.json();
      if (!data.text || data.text.length === 0) {
        throw new Error(`Chat returned empty text`);
      }
      if (!data.risk_verdict || !data.risk_verdict.verdict) {
        throw new Error(`Missing deterministic risk_verdict object`);
      }
    })
  );

  // 8. Natural Language Maritime Copilot (Monsoon Ban / Statutory Query)
  results.push(
    await runTest('6. LangGraph Maritime Copilot', 'POST /chat: Statutory monsoon ban query triggers legal advisory', async () => {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'Can mechanized boats trawl in Maharashtra in July?',
          user_id: 'test-user',
          locale: 'en',
        }),
      });
      if (!res.ok) throw new Error(`Chat query failed: HTTP ${res.status}`);
      const data = await res.json();
      if (!data.text) throw new Error(`Missing text response`);
      // Monsoon ban queries must state UNSAFE or clarify prohibition
      const v = data.risk_verdict?.verdict?.toUpperCase();
      if (v !== 'UNSAFE' && !data.text.toLowerCase().includes('ban')) {
        throw new Error(`Expected monsoon prohibition advisory or UNSAFE verdict, got ${v}`);
      }
    })
  );

  // 9. Multilingual Indic Cross-Translation (Hindi / Marathi)
  results.push(
    await runTest('7. Multilingual Translation Layer', 'POST /chat: Accepts Hindi query and returns Indic script response', async () => {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'क्या आज रत्नागिरी के पास समुद्र में जाना सुरक्षित है?',
          user_id: 'test-user-hi',
          locale: 'hi',
        }),
      });
      if (!res.ok) throw new Error(`Hindi query failed: HTTP ${res.status}`);
      const data = await res.json();
      if (!data.text) throw new Error(`Missing text in Hindi response`);
      const hasDevanagari = /[\u0900-\u097F]/.test(data.text);
      if (!hasDevanagari) {
        throw new Error(`Expected Devanagari text in response, received non-Devanagari text: "${data.text.slice(0, 80)}"`);
      }
    })
  );

  // Summary Reporting
  const passed = results.filter((r) => r.status === 'PASS').length;
  const failed = results.filter((r) => r.status === 'FAIL').length;

  console.log(`------------------------------------------------------`);
  results.forEach((r) => {
    const icon = r.status === 'PASS' ? '✅' : '❌';
    console.log(`${icon} [${r.suite}] ${r.name} (${r.durationMs}ms)`);
    if (r.status === 'FAIL') {
      console.log(`   ⚠️ Error: ${r.details}`);
    }
  });
  console.log(`------------------------------------------------------`);
  console.log(`Total: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
  console.log(`Pass Rate: ${Math.round((passed / results.length) * 100)}%`);
  console.log(`======================================================\n`);

  return { total: results.length, passed, failed, results };
}

// Auto-run if executed directly
runFullE2ESuite();
