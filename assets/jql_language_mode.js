(function () {
  'use strict';

  if (typeof CodeMirror !== 'undefined' && CodeMirror.modes && CodeMirror.modes.jql) {
    return;
  }

  const JQL_KEYWORDS = new Set([
    'AND',
    'OR',
    'NOT',

    'IN',
    'NOT IN',
    'IS',
    'IS NOT',
    'WAS',
    'WAS IN',
    'WAS NOT IN',
    'EMPTY',
    'NULL',

    'ORDER BY',
    'ORDER',
    'BY',
    'ASC',
    'DESC',

    'CHANGED',
    'AFTER',
    'BEFORE',
    'DURING',
    'ON',
    'FROM',
    'TO',
    'CHANGED FROM',
    'CHANGED TO',

    'BETWEEN',
    'OF',
  ]);

  const JQL_FUNCTIONS = new Set([
    'currentUser',
    'currentLogin',
    'membersOf',
    'now',
    'startOfDay',
    'endOfDay',
    'startOfWeek',
    'endOfWeek',
    'startOfMonth',
    'endOfMonth',
    'startOfYear',
    'endOfYear',
  ]);

  const SCRIPTRUNNER_FUNCTIONS = new Set([
    'linkedIssuesOf',
    'issuesInEpics',
    'subtasksOf',
    'parentsOf',
    'epicsOf',
    'hasLinks',
    'hasComments',
    'hasAttachments',
    'lastUpdated',
    'expression',
    'dateCompare',
    'aggregateExpression',
    'issueFieldMatch',
    'linkedIssuesOfRecursive',
    'workLogged',
    'issueFunction',
  ]);

  const jqlLanguageMode = {
    startState: function () {
      return {
        inString: false,
        stringDelimiter: null,
        inFunction: false,
      };
    },

    token: function (stream, state) {
      if (stream.eatSpace()) {
        return null;
      }

      if (state.inString) {
        return this.tokenizeString(stream, state);
      }

      if (stream.peek() === '"' || stream.peek() === "'") {
        state.inString = true;
        state.stringDelimiter = stream.peek();
        stream.next();
        return 'jql-string';
      }

      if (this.isOperatorChar(stream.peek())) {
        return this.tokenizeOperator(stream);
      }

      if ('(),'.indexOf(stream.peek()) !== -1) {
        stream.next();
        return null;
      }

      if (this.isWordChar(stream.peek())) {
        return this.tokenizeWord(stream, state);
      }

      stream.next();
      return null;
    },

    tokenizeString: function (stream, state) {
      const delimiter = state.stringDelimiter;

      while (!stream.eol()) {
        const ch = stream.next();

        if (ch === '\\') {
          stream.next();
          continue;
        }

        if (ch === delimiter) {
          state.inString = false;
          state.stringDelimiter = null;
          return 'jql-string';
        }
      }

      return 'jql-string';
    },

    tokenizeOperator: function (stream) {
      stream.next();

      if (this.isOperatorChar(stream.peek())) {
        stream.next();
      }

      return 'jql-operator';
    },

    tokenizeWord: function (stream, _state) {
      const start = stream.pos;

      while (this.isWordChar(stream.peek())) {
        stream.next();
      }

      const word = stream.string.substring(start, stream.pos);
      const wordUpper = word.toUpperCase();

      if (SCRIPTRUNNER_FUNCTIONS.has(word)) {
        return 'jql-scriptrunner';
      }

      stream.eatSpace();
      if (stream.peek() === '(') {
        if (JQL_FUNCTIONS.has(word)) {
          return 'jql-function';
        }

        return 'jql-field';
      }

      if (JQL_KEYWORDS.has(wordUpper)) {
        return 'jql-keyword';
      }

      return 'jql-field';
    },

    isOperatorChar: function (ch) {
      return ch && '=!<>~'.indexOf(ch) !== -1;
    },

    isWordChar: function (ch) {
      if (!ch) return false;
      return /[a-zA-Z0-9_.-]/.test(ch);
    },
  };

  if (typeof window !== 'undefined') {
    window.jqlLanguageMode = jqlLanguageMode;
  }

  if (typeof CodeMirror !== 'undefined' && CodeMirror.defineMode) {
    CodeMirror.defineMode('jql', function (_config, _parserConfig) {
      return jqlLanguageMode;
    });
  }
})();
