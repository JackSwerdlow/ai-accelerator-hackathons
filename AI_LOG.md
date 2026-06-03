# AI Usage Log

## Entry 1

### Prompt
Research GOV.UK multi-step form design and best practices.

### What AI Generated
Claude suggested:
- One question per page pattern
- Use of check answers page before submission
- Importance of accessibility (WCAG 2.2)
- Centralised state management in React

### What I Changed + Why
- Simplified the architecture to focus on core flow (start → questions → result)
- Decided to use a single state object for all answers to reduce complexity
- Prioritised accessibility early to avoid rework later