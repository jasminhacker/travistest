module.exports = {
  'preset': 'ts-jest',
  'testEnvironment': 'jsdom',
  'moduleNameMapper': {
    '^@src/(.*)$': [
      '<rootDir>/ts/$1',
    ],
  },
  'setupFilesAfterEnv': ['<rootDir>/jest-setup.ts'],
};
