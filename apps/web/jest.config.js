const nextJest = require('next/jest');

const createJestConfig = nextJest({ dir: './' });

const customJestConfig = {
  testEnvironment: 'jest-environment-jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    // Native optional dep of jsdom (via fabric.js) — see __mocks__/canvas.js.
    '^canvas$': '<rootDir>/__mocks__/canvas.js',
  },
};

module.exports = createJestConfig(customJestConfig);
