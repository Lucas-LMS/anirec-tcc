const assert = require('node:assert/strict');
const fs = require('node:fs');
const core = require('./shared/ir-core.js');
const cohorts = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
let maximumDifference = 0, comparisons = 0;
for (const cohort of cohorts) {
  const result = core.rank(cohort.input);
  for (const item of result.general) {
    const expected = cohort.expected[item.key]; assert.ok(expected, 'Expected record missing');
    for (const field of ['base_score', 'personalized_score', 'anchor_topic_overlap', 'preference_affinity', 'profile_text_score']) {
      if (expected[field] === null) { assert.equal(item[field], null); continue; }
      const difference = Math.abs(item[field] - expected[field]); maximumDifference = Math.max(maximumDifference, difference); comparisons++;
      assert.ok(difference < 1e-6, `${cohort.name}/${item.key}/${field}: ${difference}`);
    }
    assert.equal(item.is_seen, expected.is_seen);
  }
  for (const rows of Object.values(result.recommendation_sets)) assert.ok(rows.length <= 10);
  assert.ok(result.recommendation_sets.general_unseen.every(item => !item.is_seen));
  assert.ok(result.recommendation_sets.personal_unseen.every(item => !item.is_seen));
}
console.log(JSON.stringify({ cohorts: cohorts.length, numeric_comparisons: comparisons, maximum_difference: maximumDifference, tolerance: 1e-6, passed: true }));
