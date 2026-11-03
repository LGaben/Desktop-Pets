// The idle clock belongs to the fox, not to the petting gesture.
const FoxMotion = {
  tailMs: 264,
  create() { return { elapsed: 0, petAt: null }; },
  advance(state, delta) { state.elapsed += delta; },
  pet(state) { state.petAt = state.elapsed; },
  pose(state) {
    const age = state.petAt === null ? Infinity : state.elapsed - state.petAt;
    const head = age < 132 ? 0 : age < 264 ? 1 : age < 1056 ? 2 : age < 1188 ? 1 : 0;
    return { head, phase: Math.floor(state.elapsed / this.tailMs) % 5, reacting: age < 1188 };
  }
};
if (typeof module !== 'undefined') module.exports = FoxMotion;
