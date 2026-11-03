const assert = require('node:assert/strict');
const motion = require('./motion.js');
for (let phase = 0; phase < 5; phase++) {
  for (const offset of [0, 63, 263]) {
    const state = motion.create();
    motion.advance(state, phase * 264 + offset);
    const before = motion.pose(state);
    motion.pet(state);
    assert.deepEqual(motion.pose(state), { ...before, reacting: true });
    const started = state.elapsed;
    for (const age of [1, 131, 132, 263, 264, 527, 1055, 1056, 1187, 1188, 1320, 1600]) {
      motion.advance(state, started + age - state.elapsed);
      const pose = motion.pose(state);
      assert.equal(pose.phase, Math.floor((started + age) / 264) % 5);
      assert.equal(pose.head, age < 132 ? 0 : age < 264 ? 1 : age < 1056 ? 2 : age < 1188 ? 1 : 0);
    }
    const paused = motion.pose(state);
    assert.deepEqual(motion.pose(state), paused);
    const elapsed = state.elapsed;
    motion.pet(state);
    assert.equal(state.elapsed, elapsed);
    assert.equal(motion.pose(state).phase, paused.phase);
  }
}
console.log('PASS: all five entry phases, subframe remainder, head changes, exit, pause, second click');
