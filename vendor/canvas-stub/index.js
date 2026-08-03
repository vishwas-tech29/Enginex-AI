// Stub for the native `canvas` package (see ../../docs/SETUP.md).
// jsdom optionally uses `canvas` for real pixel rendering in
// HTMLCanvasElement.getContext('2d'); nothing in this repo's test suite
// needs that, and node-canvas's native build isn't portable across dev
// machines without a full native toolchain. `pnpm.overrides` in the root
// package.json points every reference to `canvas` at this no-op instead.
module.exports = {};
