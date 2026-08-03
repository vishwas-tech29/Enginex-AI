// jsdom optionally loads the native `canvas` package (pulled in transitively
// by fabric.js) for real 2D canvas rendering. Its node-gyp build isn't
// portable across every dev machine (needs full native toolchain), and no
// test here actually renders pixels — so we stub it out rather than require
// a native compile step just to run `jest`.
module.exports = {};
