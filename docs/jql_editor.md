# JQL Editor Guide

**Audience**: Users editing queries and developers extending the editor
**Part of**: [Documentation Index](readme.md)

## Overview

The JQL editor provides a CodeMirror-based input with syntax highlighting and real-time character counting. It is used in the settings panel for editing queries and in query creation workflows.

## User Features

### Character Count

- Displays a live character count in the format "X / 2000 characters".
- Warning state activates at 1800 characters.
- Count includes all characters, including whitespace and Unicode.

### Syntax Highlighting

- Powered by CodeMirror 5 with a custom JQL language mode.
- Highlights keywords, strings, operators, fields, and functions.
- Supports ScriptRunner functions for common extensions.
- Degrades to plain text if CodeMirror or the JQL mode is unavailable.

### ScriptRunner Function Support

The JQL mode recognizes the following ScriptRunner functions:

- linkedIssuesOf
- issuesInEpics
- subtasksOf
- parentsOf
- epicsOf
- hasLinks
- hasComments
- hasAttachments
- lastUpdated
- expression
- dateCompare
- aggregateExpression
- issueFieldMatch
- linkedIssuesOfRecursive
- workLogged
- issueFunction

## Developer Notes

### Core Files

- assets/jql_language_mode.js: CodeMirror mode and tokenization rules.
- assets/jql_editor_native.js: Editor initialization and synchronization.
- ui/jql_components.py: Character count logic and keyword registry.
- assets/components/forms.css: Character count styling and base highlight classes.

### Integration Pattern

- The editor renders in a container with a hidden input used by Dash callbacks.
- CodeMirror updates the hidden input on change; Dash reads the hidden input value.
- The custom mode registers token classes that map to CSS styles.

## Troubleshooting

- If syntax highlighting does not appear, verify CodeMirror and the JQL mode are loaded.
- If character count is missing, confirm the character count component is present in the layout.
