import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';

export default [
  {
    ignores: [
      'dist/**',
      'dist-new/**',
      'node_modules/**',
      'backend/**',
      'research/**',
    ],
  },
  {
    files: ['frontend/src/**/*.{js,jsx}'],
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: globals.browser,
    },
    rules: {
      ...js.configs.recommended.rules,
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      // Context modules intentionally co-locate their provider and consumer hook.
      'react-refresh/only-export-components': 'off',
      // eslint-plugin-react will be added during the frontend cleanup phase;
      // core no-unused-vars cannot recognize identifiers referenced only by JSX.
      'no-unused-vars': 'off',
    },
  },
];
