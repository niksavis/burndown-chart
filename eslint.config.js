'use strict';

// ESLint v9 flat config for browser-side Dash clientside JavaScript.
// Covers: assets/**/*.js   Excludes: assets/vendor/**
// Prettier owns all formatting (quotes, semicolons, line length).
// eslint-config-prettier disables any ESLint rules that would conflict.
const js = require('@eslint/js');
const prettier = require('eslint-config-prettier');

/** @type {import("eslint").Linter.Config[]} */
module.exports = [
  // Global ignores (must be a config object with only the `ignores` key)
  {
    ignores: ['assets/vendor/**', 'node_modules/**', '.venv/**', 'build/**'],
  },

  // Rules for first-party Dash clientside scripts
  {
    files: ['assets/**/*.js'],
    languageOptions: {
      ecmaVersion: 2020,
      // These are plain browser scripts loaded via <script>, not ES modules.
      sourceType: 'script',
      globals: {
        // Browser built-ins
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
        // DOM interfaces (available on window but referenced as bare names in scripts)
        Node: 'readonly',
        HTMLInputElement: 'readonly',
        HTMLTextAreaElement: 'readonly',
        // Third-party libraries loaded via external scripts
        CodeMirror: 'readonly', // JQL editor (loaded via /assets/vendor/codemirror/)
        io: 'readonly', // Socket.IO if used
        // Module-level state (namespace pattern used across asset scripts)
        mobileNavState: 'writable',
        // Dash runtime globals
        dash_clientside: 'writable',
        // Plotly (loaded separately via CDN / vendor bundle)
        Plotly: 'readonly',
      },
    },
    rules: {
      // Start from the recommended baseline
      ...js.configs.recommended.rules,

      // Rule overrides for Dash clientside code
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' }],
      // console.log is acceptable in Dash asset scripts
      'no-console': 'off',
      // Nudge toward strict equality but do not block builds
      eqeqeq: 'warn',
      // Security: eval executes arbitrary code in a browser context
      'no-eval': 'error',
      // Prefer explicit window.X over implicit globals
      'no-implicit-globals': 'warn',
    },
  },

  // Disable ESLint formatting rules that conflict with Prettier.
  // Prettier is the single source of truth for: quotes, semicolons,
  // trailing commas, line length, indentation.
  prettier,
];
