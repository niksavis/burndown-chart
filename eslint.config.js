'use strict';

const js = require('@eslint/js');
const prettier = require('eslint-config-prettier');

module.exports = [
  {
    ignores: ['assets/vendor/**', 'node_modules/**', '.venv/**', 'build/**'],
  },

  {
    files: ['assets/**/*.js'],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'script',
      globals: {
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        requestAnimationFrame: 'readonly',
        navigator: 'readonly',
        location: 'readonly',
        fetch: 'readonly',
        Event: 'readonly',
        CustomEvent: 'readonly',
        InputEvent: 'readonly',
        MutationObserver: 'readonly',
        ResizeObserver: 'readonly',
        Node: 'readonly',
        HTMLInputElement: 'readonly',
        HTMLTextAreaElement: 'readonly',
        CodeMirror: 'readonly',
        io: 'readonly',
        mobileNavState: 'writable',
        dash_clientside: 'writable',
        Plotly: 'readonly',
      },
    },
    rules: {
      ...js.configs.recommended.rules,

      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' }],
      'no-console': 'off',
      eqeqeq: 'warn',
      'no-eval': 'error',
      'no-implicit-globals': 'warn',
    },
  },

  prettier,
];
