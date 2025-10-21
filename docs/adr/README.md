# Architecture Decision Records (ADR)

This directory contains records of architectural decisions made in this project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this structure:

- **Title:** Short descriptive name
- **Status:** Proposed | Accepted | Rejected | Deprecated | Superseded
- **Date:** When the decision was made
- **Context:** What is the issue we're facing?
- **Decision:** What decision did we make?
- **Consequences:** What are the positive/negative outcomes?

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-modular-architecture.md) | Modular Backend Architecture | Accepted | 2025-10-21 |
| [0002](0002-duplicate-detection-strategy.md) | Duplicate Detection Strategy | Accepted | 2025-10-20 |

## Creating a New ADR

1. Copy the template below
2. Number it sequentially (0003, 0004, etc.)
3. Fill in all sections
4. Update this README index

### Template

```markdown
# ADR-XXXX: [Title]

**Status:** [Proposed | Accepted | Rejected]  
**Date:** YYYY-MM-DD  
**Deciders:** [List of people involved]  
**Technical Story:** [Link to issue/story]

## Context

[Describe the context and problem statement]

## Decision

[Describe the decision made]

## Rationale

[Explain why this decision was made]

## Consequences

### Positive
- [List positive outcomes]

### Negative
- [List negative outcomes]

### Neutral
- [List neutral outcomes]

## Alternatives Considered

### 1. [Alternative Name]
**Reason for rejection:** [Explanation]

## References

- [Links to relevant documentation]
```

## Best Practices

1. **Keep them short:** 1-2 pages maximum
2. **Write when deciding:** Not after implementation
3. **Include alternatives:** Show what was considered
4. **Be honest:** Document trade-offs
5. **Update status:** Mark as superseded when replaced

## Further Reading

- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub](https://adr.github.io/)

