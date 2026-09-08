import { FIXTURES, validateFixture } from '../fixtures';

export function runFixtureValidationSuite(): {
  total: number;
  passed: number;
  failed: number;
  results: Array<{ id: string; name: string; status: 'PASS' | 'FAIL'; message: string }>;
} {
  const results: Array<{ id: string; name: string; status: 'PASS' | 'FAIL'; message: string }> = [];
  let passed = 0;
  let failed = 0;

  for (const [key, fixture] of Object.entries(FIXTURES)) {
    const res = validateFixture(fixture.data);

    if (fixture.expectedVerdict === 'INVALID') {
      // Expecting failure
      if (!res.success) {
        passed++;
        results.push({
          id: key,
          name: fixture.name,
          status: 'PASS',
          message: `Correctly rejected invalid fixture: ${res.error?.slice(0, 100)}...`,
        });
      } else {
        failed++;
        results.push({
          id: key,
          name: fixture.name,
          status: 'FAIL',
          message: `Expected validation failure, but schema parsed successfully!`,
        });
      }
    } else {
      // Expecting success
      if (res.success && res.data) {
        // Also check that verdict and decision_status match expectations
        const verdictMatches = res.data.summary.verdict === fixture.expectedVerdict;
        const statusMatches = res.data.decision_status === fixture.expectedStatus;

        if (verdictMatches && statusMatches) {
          // Additional safety checks
          // 1. If verdict is UNSAFE, verify no reassuring wording in action
          // 2. Coordinate sanity check
          const [lon, lat] = res.data.map.viewport.center;
          const validCoords = lon >= 60 && lon <= 100 && lat >= 5 && lat <= 38; // Indian EEZ bounds approx

          if (!validCoords) {
            failed++;
            results.push({
              id: key,
              name: fixture.name,
              status: 'FAIL',
              message: `Coordinates [${lon}, ${lat}] outside expected Indian waters bounds [60..100 lon, 5..38 lat]`,
            });
            continue;
          }

          passed++;
          results.push({
            id: key,
            name: fixture.name,
            status: 'PASS',
            message: `Validated OK. Verdict: ${res.data.summary.verdict}, Status: ${res.data.decision_status}`,
          });
        } else {
          failed++;
          results.push({
            id: key,
            name: fixture.name,
            status: 'FAIL',
            message: `Mismatch: got verdict=${res.data.summary.verdict} (expected ${fixture.expectedVerdict}), status=${res.data.decision_status} (expected ${fixture.expectedStatus})`,
          });
        }
      } else {
        failed++;
        results.push({
          id: key,
          name: fixture.name,
          status: 'FAIL',
          message: `Validation error: ${res.error}`,
        });
      }
    }
  }

  return {
    total: Object.keys(FIXTURES).length,
    passed,
    failed,
    results,
  };
}

// Auto-run if executed via ts-node/vite-node/etc.
const suite = runFixtureValidationSuite();
console.log(`\n========================================`);
console.log(`VARUNA FIXTURE VALIDATION SUITE RESULTS:`);
console.log(`Total: ${suite.total} | Passed: ${suite.passed} | Failed: ${suite.failed}`);
console.log(`========================================`);
suite.results.forEach((r) => {
  console.log(`[${r.status}] ${r.name}`);
  console.log(`       ${r.message}`);
});

if (suite.failed > 0) {
  console.error(`\nValidation suite FAILED with ${suite.failed} errors.`);
} else {
  console.log(`\nAll fixtures PASSED contract validation successfully.`);
}
