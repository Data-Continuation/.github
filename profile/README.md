# Data-Continuation

**Data-Continuation develops the machinery and formal structure needed to preserve work, state, evidence, and reconstruction paths across governed transitions.**

The organization focuses on continuity as more than storage: a useful continuation record must preserve how a prior state, transition, resulting state, evidence, and known gaps relate to one another.

## What belongs here

Repositories in this organization cover:

- continuation formalisms and executable formalism tests;
- Core-Lite workstream and transition-control tooling;
- reconstruction and evidence-intake surfaces;
- reusable product and runtime components that preserve bounded continuation;
- selected research and test harnesses for transition/recoverability behavior.

## Operating principle

A file or log is not automatically continuity. Continuity should remain reconstructable, scoped, and honest about missing or contradictory evidence.

Data-Continuation does not grant execution authority merely because state was preserved. Admission, transition authority, credentials, and consequence-bearing execution remain governed by their owning systems.
