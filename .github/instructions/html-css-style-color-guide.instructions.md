---
applyTo: '**/*.html, **/*.css, assets/**/*.js'
description: 'HTML/CSS style and color guidance for accessible, professional UI changes'
---

# HTML CSS Style and Color Guide Instructions

Apply these rules for HTML/CSS styling work and related frontend scripts.

## Accessibility and Semantics

- Use semantic HTML first; use ARIA only when native semantics are insufficient.
- Preserve keyboard navigability and visible focus states.
- Maintain WCAG-compliant contrast for text and interactive elements.
- Prefer reduced-motion-safe interactions (`prefers-reduced-motion`) for animations.

## Color and Visual Rules

- Prefer neutral/light backgrounds and high-contrast foreground text.
- Use hot/saturated colors sparingly, mainly for alerts/warnings.
- Avoid low-contrast combinations and neon-like accents unless explicitly requested.
- Keep gradients subtle and within the same color family.

## Repository Design Constraints

- Reuse existing design tokens, variables, and theme primitives.
- Do not introduce ad-hoc hard-coded color systems when tokens exist.
- Keep styling changes minimal and scoped to requested UX behavior.

## Validation

1. Verify readability/contrast and focus visibility.
2. Run `get_errors` on changed HTML/CSS/JS files.
3. If style exceptions are needed, document the reason in completion notes.
