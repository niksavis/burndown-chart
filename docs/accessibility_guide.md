# Accessibility Guide

This document outlines the accessibility standards, practices, and implementation guidelines for the Burndown Chart application.

## WCAG Compliance Targets

The Burndown Chart application aims to meet the following standards:

- **WCAG 2.1 Level AA** compliance for all core features
- **WCAG 2.1 Level AAA** compliance where reasonably possible

## Core Accessibility Principles

### 1. Perceivable

Information and user interface components must be presentable to users in ways they can perceive.

#### Color Contrast

- Text must have a contrast ratio of at least **4.5:1** against its background (Level AA)
- Large text (18pt+) must have a contrast ratio of at least **3:1**
- UI components and graphical objects must have a contrast ratio of at least **3:1**

#### Text Alternatives

- All non-text content must have text alternatives
- Charts and data visualizations must have accessible text summaries
- Icons must have proper text labels or ARIA labels

#### Responsive Design

- Content must be responsive and adaptable to different viewport sizes
- No information should be lost when zooming up to 200%

### 2. Operable

User interface components and navigation must be operable by all users.

#### Keyboard Accessibility

- All functionality must be accessible using only a keyboard
- No keyboard traps (focus must not get stuck on any element)
- Focus order must be logical and intuitive
- Focus states must be clearly visible

#### Time Constraints

- If time limits exist, users must be able to extend, adjust, or turn them off

#### Navigation

- Skip links must be provided for bypassing navigation
- Multiple ways to find content should be available
- Page titles must be clear and descriptive

### 3. Understandable

Information and operation of the user interface must be understandable.

#### Readability

- Text must be readable and understandable
- Unusual words and abbreviations must be defined

#### Predictability

- Components that appear on multiple pages must work consistently
- Changes in context must not occur automatically without warning

#### Input Assistance

- Input errors must be identified and described to users
- Labels and instructions must be provided for form fields

### 4. Robust

Content must be robust enough to be interpreted by a wide variety of user agents, including assistive technologies.

#### Compatibility

- HTML must be well-formed with proper nesting
- ARIA attributes must be used correctly
- Custom controls must have appropriate roles and states

## Implementation Guidelines

### ARIA Attributes

Use ARIA attributes according to these principles:

1. **Use native HTML elements** whenever possible instead of ARIA
2. **Do not change native semantics** unless absolutely necessary
3. **Make all interactive elements keyboard accessible**
4. **Do not use `role="presentation"` or `aria-hidden="true"`** on focusable elements
5. **All interactive elements must have an accessible name**

### Icon-only Buttons

All icon-only buttons must:

1. Have an `aria-label` that describes the button's action
2. Include a tooltip that appears on hover
3. Have sufficient contrast against their background
4. Have a minimum touch target size of 44×44 pixels

Example:

```python
from ui.aria_utils import addAriaLabelToIconButton

# Create an icon-only button with proper accessibility
button = html.Button(
    html.I(className="fas fa-edit"),
    id="edit-button",
    className="icon-button"
)

# Enhance with ARIA label and tooltip
accessible_button = addAriaLabelToIconButton(button, "Edit item")
```

### Forms and Inputs

Form fields must:

1. Have explicit labels with `for` attributes matching input `id`
2. Include clear instructions
3. Provide error messages that are:
   - Descriptive and helpful
   - Associated with the relevant field using `aria-describedby`
   - Announced to screen readers when they appear

### Data Tables

Tables must:

1. Use proper HTML table elements (`<table>`, `<th>`, `<td>`, etc.)
2. Include appropriate headers with `scope` attributes
3. Have a clear caption or accessible name
4. Be properly structured for screen readers

### Keyboard Navigation

Implement keyboard navigation according to these principles:

1. Use logical tab order based on reading sequence
2. Make custom interactive elements focusable with `tabindex="0"`
3. Use standard keyboard patterns:
   - Enter/Space for buttons and links
   - Arrow keys for navigation within components
   - Escape to close dialogs and menus

## Testing Procedures

### Manual Testing Checklist

- [ ] Navigate the entire interface using only a keyboard
- [ ] Test with screen readers (NVDA, VoiceOver, or JAWS)
- [ ] Verify color contrast meets WCAG AA standards
- [ ] Check all form controls have proper labels
- [ ] Ensure all interactive elements have visible focus states
- [ ] Verify all images have appropriate alt text

### Automated Testing Tools

Use these tools to assist with accessibility testing:

1. **Color Contrast**: Use our custom contrast checker:

   ```sh
   python tools/contrast_checker.py assets/custom.css
   ```

2. **Keyboard Navigation**: Run the keyboard navigation checker in the browser console:

   ```text
   // Copy and paste the code from tools/keyboard_nav_checker.js
   ```

3. **Automated Testing**: Run axe-core tests on key components

## Resources

- [Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/TR/WCAG21/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)

## Maintenance and Review

Accessibility should be considered from the beginning of the development process:

1. **Design Phase**: Review wireframes and mockups for accessibility concerns
2. **Development**: Use accessible components and patterns
3. **Testing**: Include accessibility testing in QA processes
4. **Deployment**: Maintain accessibility through updates and new features

Regular accessibility audits should be conducted to ensure continued compliance with standards.
