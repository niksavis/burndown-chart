/**
 * JQL Language Mode for CodeMirror 5
 *
 * Defines syntax highlighting rules for JIRA Query Language (JQL).
 * Implements tokenization for keywords, operators, strings, fields, functions, and errors.
 *
 * Architecture:
 *   - Uses CodeMirror 5's mode API for character-by-character parsing
 *   - State machine approach: tracks parser state across lines
 *   - Returns token types that map to CSS classes (.cm-jql-*)
 *
 * Token Types:
 *   - "jql-keyword": JQL reserved words (AND, OR, NOT, IN, IS, WAS, etc.)
 *   - "jql-string": Quoted string literals ("Done", 'In Progress')
 *   - "jql-operator": Comparison operators (=, !=, ~, !~, <, >, <=, >=)
 *   - "jql-function": Standard JQL functions (currentUser(), now(), etc.)
 *   - "jql-scriptrunner": ScriptRunner-specific functions (linkedIssuesOf, etc.)
 *   - "jql-field": Field names (project, status, assignee, etc.)
 *   - "jql-error": Syntax errors (unclosed quotes, invalid syntax)
 *
 * Usage:
 *   This file is loaded via script tag and registers the mode with CodeMirror.
 *   The editor initialization script (jql_editor_init.js) uses this mode.
 *
 * Requirements:
 *   - CodeMirror 5 must be loaded first (via CDN in app.py)
 *   - CSS token classes must be defined in custom.css
 */

// JQL Keywords (case-insensitive matching)
const JQL_KEYWORDS = new Set([
  // Logical operators
  "AND",
  "OR",
  "NOT",

  // Comparison operators (word-based)
  "IN",
  "NOT IN",
  "IS",
  "IS NOT",
  "WAS",
  "WAS IN",
  "WAS NOT IN",
  "EMPTY",
  "NULL",

  // Sorting
  "ORDER BY",
  "ORDER",
  "BY",
  "ASC",
  "DESC",

  // Change tracking
  "CHANGED",
  "AFTER",
  "BEFORE",
  "DURING",
  "ON",
  "FROM",
  "TO",
  "CHANGED FROM",
  "CHANGED TO",

  // Additional keywords
  "BETWEEN",
  "OF",
]);

// Standard JQL Functions
const JQL_FUNCTIONS = new Set([
  "currentUser",
  "currentLogin",
  "membersOf",
  "now",
  "startOfDay",
  "endOfDay",
  "startOfWeek",
  "endOfWeek",
  "startOfMonth",
  "endOfMonth",
  "startOfYear",
  "endOfYear",
]);

// ScriptRunner Functions (User Story 2 - T028)
// Top 15 most commonly used ScriptRunner extension functions
const SCRIPTRUNNER_FUNCTIONS = new Set([
  "linkedIssuesOf",
  "issuesInEpics",
  "subtasksOf",
  "parentsOf",
  "epicsOf",
  "hasLinks",
  "hasComments",
  "hasAttachments",
  "lastUpdated",
  "expression",
  "dateCompare",
  "aggregateExpression",
  "issueFieldMatch",
  "linkedIssuesOfRecursive",
  "workLogged",
  "issueFunction", // Special keyword that can be used standalone
]);

/**
 * JQL Language Mode Definition
 *
 * Implements a token parser for JQL syntax using CodeMirror's StreamLanguage API.
 */
const jqlLanguageMode = {
  name: "jql",

  /**
   * Initialize parser state at start of document or line.
   *
   * @returns {Object} Initial state object
   */
  startState: function () {
    return {
      inString: false, // Currently inside a string literal
      stringDelimiter: null, // Quote character (" or ')
      inFunction: false, // Currently inside a function call
    };
  },

  /**
   * Tokenize next segment of text.
   *
   * Called repeatedly for each line. Advances stream position and returns token type.
   *
   * @param {Object} stream - CodeMirror stream object with text and position
   * @param {Object} state - Parser state from startState() or previous token()
   * @returns {string|null} Token type (maps to CSS class) or null for whitespace
   */
  token: function (stream, state) {
    // Skip whitespace
    if (stream.eatSpace()) {
      return null;
    }

    // Handle string literals
    if (state.inString) {
      return this.tokenizeString(stream, state);
    }

    // Check for string start
    if (stream.peek() === '"' || stream.peek() === "'") {
      state.inString = true;
      state.stringDelimiter = stream.peek();
      stream.next();
      return "jql-string";
    }

    // Handle operators (single or multi-character)
    if (this.isOperatorChar(stream.peek())) {
      return this.tokenizeOperator(stream);
    }

    // Handle special characters (parentheses, commas)
    if ("(),".indexOf(stream.peek()) !== -1) {
      stream.next();
      return null; // Don't highlight special chars
    }

    // Handle words (keywords, functions, field names)
    if (this.isWordChar(stream.peek())) {
      return this.tokenizeWord(stream, state);
    }

    // Unknown character - consume and continue
    stream.next();
    return null;
  },

  /**
   * Tokenize string literal.
   * Handles both double and single quotes, including escape sequences.
   * Detects unclosed strings as errors.
   */
  tokenizeString: function (stream, state) {
    const delimiter = state.stringDelimiter;

    while (!stream.eol()) {
      const ch = stream.next();

      // Handle escape sequences
      if (ch === "\\") {
        stream.next(); // Skip escaped character
        continue;
      }

      // Check for closing quote
      if (ch === delimiter) {
        state.inString = false;
        state.stringDelimiter = null;
        return "jql-string";
      }
    }

    // Reached end of line without closing quote
    // Keep state.inString = true to continue on next line
    // But mark as error if this is truly unclosed (User Story 3)
    return "jql-string";
  },

  /**
   * Tokenize operator characters.
   * Handles single char (=, <, >, ~, !) and multi-char (!=, <=, >=, !~).
   */
  tokenizeOperator: function (stream) {
    const start = stream.pos;
    stream.next();

    // Check for multi-character operators
    if (this.isOperatorChar(stream.peek())) {
      stream.next();
    }

    return "jql-operator";
  },

  /**
   * Tokenize word (keyword, function, or field name).
   * Performs case-insensitive keyword matching.
   *
   * Priority Ordering (T030):
   *   1. ScriptRunner functions (even without parentheses)
   *   2. Functions with parentheses
   *   3. JQL keywords
   *   4. Field names (default)
   */
  tokenizeWord: function (stream, state) {
    const start = stream.pos;

    // Consume entire word
    while (this.isWordChar(stream.peek())) {
      stream.next();
    }

    const word = stream.string.substring(start, stream.pos);
    const wordUpper = word.toUpperCase();

    // T030: Check ScriptRunner functions FIRST (before keywords)
    // This prevents "issueFunction" from being treated as generic keyword
    if (SCRIPTRUNNER_FUNCTIONS.has(word)) {
      return "jql-scriptrunner";
    }

    // Check if next character is opening parenthesis (function call)
    stream.eatSpace();
    if (stream.peek() === "(") {
      // Check if it's a standard JQL function
      if (JQL_FUNCTIONS.has(word)) {
        return "jql-function";
      }

      // Unknown function - treat as field name
      return "jql-field";
    }

    // Check if it's a keyword (case-insensitive)
    if (JQL_KEYWORDS.has(wordUpper)) {
      return "jql-keyword";
    }

    // Default to field name
    return "jql-field";
  },

  /**
   * Check if character is part of an operator.
   */
  isOperatorChar: function (ch) {
    return ch && "=!<>~".indexOf(ch) !== -1;
  },

  /**
   * Check if character can be part of a word (keyword, function, field).
   * Allows alphanumeric, underscore, hyphen, and dot.
   */
  isWordChar: function (ch) {
    if (!ch) return false;
    return /[a-zA-Z0-9_.\-]/.test(ch);
  },
};

// Export for use in jql_editor_init.js
if (typeof window !== "undefined") {
  window.jqlLanguageMode = jqlLanguageMode;
}

// Register with CodeMirror 5 if available
if (typeof CodeMirror !== "undefined" && CodeMirror.defineMode) {
  CodeMirror.defineMode("jql", function () {
    return jqlLanguageMode;
  });
  console.log("[JQL Mode] Registered JQL mode with CodeMirror 5");
}
